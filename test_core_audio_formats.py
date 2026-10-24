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


if __name__ == "__main__":
    unittest.main()
