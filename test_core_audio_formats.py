import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import core


class SupportedAudioTests(unittest.TestCase):
    def test_accepts_supported_extensions_case_insensitively_and_excludes_mp3(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            supported = ["song.m4a", "song.WAV", "song.aiff", "song.AIF"]
            unsupported = ["song.mp3", "song.flac", "._song.wav"]
            for filename in supported + unsupported:
                (root / filename).touch()

            self.assertEqual(
                {path.name for path in core.discover_audio(root)},
                set(supported),
            )
            for filename in supported:
                self.assertTrue(core.is_supported_audio(root / filename))
            for filename in unsupported:
                self.assertFalse(core.is_supported_audio(root / filename))

    def test_legacy_m4a_helpers_keep_their_original_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            m4a = root / "track.m4a"
            wav = root / "track.wav"
            m4a.touch()
            wav.touch()

            self.assertEqual(core.discover_m4a(root), [m4a])
            self.assertTrue(core.is_m4a(m4a))
            self.assertFalse(core.is_m4a(wav))

    def test_discovery_recurses_and_returns_supported_inputs_in_sorted_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "album"
            nested.mkdir()
            (nested / "track.wav").touch()
            (root / "01.m4a").touch()
            (root / "02.aif").touch()

            self.assertEqual(
                [path.relative_to(root).as_posix() for path in core.discover_audio(root)],
                ["01.m4a", "02.aif", "album/track.wav"],
            )

    def test_collision_resolves_both_inputs_to_source_extension_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wav = root / "01.wav"
            aiff = root / "01.aiff"
            wav.touch()
            aiff.touch()

            destinations = core.output_path_for([wav, aiff])

            self.assertEqual(destinations[wav], root / "01.wav.mp3")
            self.assertEqual(destinations[aiff], root / "01.aiff.mp3")

    def test_single_input_keeps_legacy_mp3_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "01.wav"
            source.touch()

            self.assertEqual(core.output_path_for([source])[source], source.with_suffix(".mp3"))

    def test_output_path_for_marks_casefolded_destination_aliases_as_collisions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "Album" / "track.wav"
            second = root / "album" / "TRACK.wav"

            self.assertEqual(
                core.output_path_for([first, second]),
                {
                    first: root / "Album" / "track.wav.mp3",
                    second: root / "album" / "TRACK.wav.mp3",
                },
            )

    def test_convert_uses_resolved_destination_and_removes_source_only_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "01.wav"
            destination = Path(directory) / "01.wav.mp3"
            source.touch()

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"mp3")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("core.subprocess.run", side_effect=fake_ffmpeg) as run:
                result = core.convert_file(
                    source,
                    core.ConversionOptions(delete_sources=True),
                    destination=destination,
                )

            self.assertIs(result.status, core.ConversionStatus.SUCCESS)
            self.assertTrue(destination.is_file())
            self.assertFalse(source.exists())
            self.assertEqual(run.call_args.args[0][5], str(source))

    def test_failed_conversion_preserves_original_and_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "01.aiff"
            destination = Path(directory) / "01.aiff.mp3"
            source.write_bytes(b"original")

            with patch(
                "core.subprocess.run",
                return_value=subprocess.CompletedProcess([], 1, "", "bad input"),
            ):
                result = core.convert_file(source, core.ConversionOptions(delete_sources=True), destination)

            self.assertIs(result.status, core.ConversionStatus.ERROR)
            self.assertEqual(source.read_bytes(), b"original")
            self.assertFalse(destination.exists())

    def test_read_audio_tags_prefers_format_tags_and_handles_common_key_case(self):
        source = Path("song.m4a")
        probe_output = '{"format":{"tags":{"ARTIST":"Format Artist","Album":"Format Album"}},"streams":[{"codec_type":"audio","tags":{"artist":"Stream Artist","album":"Stream Album"}}]}'
        completed = subprocess.CompletedProcess([], 0, probe_output, "")

        with patch("core.subprocess.run", return_value=completed) as run:
            self.assertEqual(core.read_audio_tags(source), ("Format Artist", "Format Album"))

        self.assertEqual(run.call_args.args[0][:2], ["ffprobe", "-v"])
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertTrue(run.call_args.kwargs["text"])
        self.assertIn("timeout", run.call_args.kwargs)

    def test_read_audio_tags_falls_back_to_audio_stream_tags(self):
        source = Path("song.m4a")
        probe_output = '{"format":{"tags":{"title":"Only a title"}},"streams":[{"codec_type":"video","tags":{"artist":"Wrong Artist","album":"Wrong Album"}},{"codec_type":"audio","tags":{"ARTIST":"Stream Artist","ALBUM":"Stream Album"}}]}'

        with patch(
            "core.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, probe_output, ""),
        ):
            self.assertEqual(core.read_audio_tags(source), ("Stream Artist", "Stream Album"))

    def test_read_audio_tags_uses_unknown_labels_for_absent_and_empty_values(self):
        source = Path("song.m4a")
        probe_output = '{"format":{"tags":{"artist":" ","album":""}},"streams":[]}'

        with patch(
            "core.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, probe_output, ""),
        ):
            self.assertEqual(core.read_audio_tags(source), ("Artiste inconnu", "Album inconnu"))

    def test_read_audio_tags_rejects_failed_probe_and_invalid_json(self):
        source = Path("song.m4a")
        failures = [
            subprocess.CompletedProcess([], 1, "", "probe failed"),
            subprocess.CompletedProcess([], 0, "not json", ""),
            subprocess.CompletedProcess([], 0, "[]", ""),
        ]

        for completed in failures:
            with self.subTest(completed=completed):
                with patch("core.subprocess.run", return_value=completed):
                    with self.assertRaises(ValueError):
                        core.read_audio_tags(source)

        with patch("core.subprocess.run", side_effect=OSError("ffprobe missing")):
            with self.assertRaises(OSError):
                core.read_audio_tags(source)

        with patch("core.subprocess.run", side_effect=subprocess.TimeoutExpired("ffprobe", 30)):
            with self.assertRaises(ValueError):
                core.read_audio_tags(source)

    def test_output_path_from_tags_sanitizes_components_and_keeps_path_under_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "output"
            source = Path("track.m4a")

            destination = core.output_path_from_tags(
                source, root, "../Artist/../../outside", "/Album\\\\..\\\\escape"
            )

            self.assertEqual(destination.name, "track.mp3")
            relative_parts = destination.relative_to(root).parts
            self.assertEqual(len(relative_parts), 3)
            self.assertNotIn("..", relative_parts)
            self.assertTrue(destination.resolve().is_relative_to(root.resolve()))

    def test_output_path_from_tags_replaces_empty_components_with_unknown_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "output"

            destination = core.output_path_from_tags(Path("track.wav"), root, "...", " ")

            self.assertEqual(
                destination,
                root / "Artiste inconnu" / "Album inconnu" / "track.mp3",
            )

    def test_output_path_from_tags_sanitizes_windows_reserved_device_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "output"

            for reserved in ("CON", "nul.txt", "COM1", "Lpt9.log"):
                with self.subTest(reserved=reserved):
                    destination = core.output_path_from_tags(Path("track.wav"), root, reserved, "Album")
                    self.assertFalse(destination.parts[-3].split(".")[0].upper() in {
                        "CON", "PRN", "AUX", "NUL",
                        *(f"COM{number}" for number in range(1, 10)),
                        *(f"LPT{number}" for number in range(1, 10)),
                    })

    def test_convert_creates_destination_parent_and_places_temporary_file_there(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "01.wav"
            destination = root / "artist" / "album" / "01.mp3"
            source.touch()

            def fake_ffmpeg(command, **kwargs):
                temporary_path = Path(command[-1])
                self.assertEqual(temporary_path.parent, destination.parent)
                self.assertTrue(destination.parent.is_dir())
                temporary_path.write_bytes(b"mp3")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("core.subprocess.run", side_effect=fake_ffmpeg):
                result = core.convert_file(source, core.ConversionOptions(), destination)

            self.assertIs(result.status, core.ConversionStatus.SUCCESS)
            self.assertEqual(destination.read_bytes(), b"mp3")


if __name__ == "__main__":
    unittest.main()
