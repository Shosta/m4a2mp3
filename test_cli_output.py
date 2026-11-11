import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import core
import m4a2mp3


class CliOutputTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.sources = [self.root / "one.m4a", self.root / "two.m4a"]
        for source in self.sources:
            source.touch()

    def run_cli(self, arguments, files=None, tags=None):
        output = io.StringIO()
        files = self.sources if files is None else files
        with (
            patch("sys.argv", ["m4a2mp3.py", "--dossier", str(self.root), *arguments]),
            patch("m4a2mp3.ffmpeg_available", return_value=True),
            patch("m4a2mp3.discover_m4a", return_value=files),
            patch("m4a2mp3.read_audio_tags", side_effect=tags, create=True) as read_tags,
            patch("m4a2mp3.convert_file") as convert,
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            convert.side_effect = lambda source, options, destination=None: core.ConversionResult(
                source, core.ConversionStatus.SUCCESS, "converti"
            )
            try:
                status = m4a2mp3.main()
            except SystemExit as exc:
                status = exc.code
        return status, output.getvalue(), read_tags, convert

    def test_sortie_converts_to_metadata_hierarchy(self):
        output_root = self.root / "sorted"
        status, _, read_tags, convert = self.run_cli(
            ["--sortie", str(output_root)], tags=[("A Artist", "Album One"), ("B Artist", "Album Two")]
        )

        self.assertEqual(status, 0)
        self.assertEqual(read_tags.call_count, 2)
        destinations = {call.args[0]: call.kwargs["destination"] for call in convert.call_args_list}
        self.assertEqual(destinations, {
            self.sources[0]: output_root / "A Artist" / "Album One" / "one.mp3",
            self.sources[1]: output_root / "B Artist" / "Album Two" / "two.mp3",
        })

    def test_without_sortie_does_not_read_tags_and_preserves_existing_options_and_paths(self):
        status, _, read_tags, convert = self.run_cli(
            ["--qualite", "4", "--jobs", "2", "--supprimer", "--ne-pas-ecraser"],
            tags=None,
        )

        self.assertEqual(status, 0)
        read_tags.assert_not_called()
        self.assertEqual({call.args[0] for call in convert.call_args_list}, set(self.sources))
        for call in convert.call_args_list:
            self.assertEqual(call.args[1], core.ConversionOptions("4", 2, True, False))
            self.assertNotIn("destination", call.kwargs)

    def test_tag_failure_is_excluded_and_all_tags_are_read_before_any_conversion(self):
        events = []

        def read_tags(source):
            events.append(("tags", source))
            if source == self.sources[0]:
                raise ValueError("ffprobe failed: corrupt file")
            return "Artist", "Album"

        def convert(source, options, destination=None):
            events.append(("convert", source))
            return core.ConversionResult(source, core.ConversionStatus.SUCCESS, "converti")

        output = io.StringIO()
        with (
            patch("sys.argv", ["m4a2mp3.py", "--dossier", str(self.root), "--sortie", str(self.root / "out")]),
            patch("m4a2mp3.ffmpeg_available", return_value=True),
            patch("m4a2mp3.discover_m4a", return_value=self.sources),
            patch("m4a2mp3.read_audio_tags", side_effect=read_tags, create=True),
            patch("m4a2mp3.convert_file", side_effect=convert) as convert_mock,
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            try:
                status = m4a2mp3.main()
            except SystemExit as exc:
                status = exc.code

        self.assertEqual(status, 1)
        self.assertEqual([call.args[0] for call in convert_mock.call_args_list], [self.sources[1]])
        self.assertEqual([kind for kind, _ in events], ["tags", "tags", "convert"])
        self.assertIn("ffprobe failed: corrupt file", output.getvalue())
        self.assertIn("1 erreur(s)", output.getvalue())

    def test_only_members_of_casefolded_destination_collision_are_skipped(self):
        colliding_sources = [self.root / "album-a" / "track.m4a", self.root / "album-b" / "track.m4a"]
        unrelated_source = self.root / "unrelated.m4a"
        files = [*colliding_sources, unrelated_source]
        tags = [("Artist", "Album"), ("artist", "album"), ("Other", "Record")]
        output = io.StringIO()
        with (
            patch("sys.argv", ["m4a2mp3.py", "--dossier", str(self.root), "--sortie", str(self.root / "out")]),
            patch("m4a2mp3.ffmpeg_available", return_value=True),
            patch("m4a2mp3.discover_m4a", return_value=files),
            patch("m4a2mp3.read_audio_tags", side_effect=tags, create=True),
            patch("m4a2mp3.convert_file") as convert,
            contextlib.redirect_stdout(output),
        ):
            convert.side_effect = lambda source, options, destination=None: core.ConversionResult(
                source, core.ConversionStatus.SUCCESS, "converti"
            )
            status = m4a2mp3.main()

        self.assertEqual(status, 1)
        self.assertEqual([call.args[0] for call in convert.call_args_list], [unrelated_source])
        self.assertEqual(
            convert.call_args.kwargs["destination"],
            self.root / "out" / "Other" / "Record" / "unrelated.mp3",
        )
        self.assertIn("2 erreur(s)", output.getvalue())
        self.assertIn("collision", output.getvalue().casefold())


if __name__ == "__main__":
    unittest.main()
