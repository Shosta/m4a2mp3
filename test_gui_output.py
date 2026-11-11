import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ui.output_plan import prepare_output_plan, prepare_source_plan


class OutputPlanTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.sources = [self.root / "one.m4a", self.root / "two.m4a", self.root / "three.m4a"]

    def test_reads_all_tags_before_returning_only_valid_noncolliding_destinations(self):
        events = []

        def read_tags(source):
            events.append(("tags", source.name))
            if source == self.sources[0]:
                raise ValueError("ffprobe failed: corrupt file")
            if source == self.sources[1]:
                return "Artist", "Shared"
            return "Artist", "Other"

        with patch("ui.output_plan.read_audio_tags", side_effect=read_tags):
            plan = prepare_output_plan(self.sources, self.root / "output")

        self.assertEqual(events, [("tags", "one.m4a"), ("tags", "two.m4a"), ("tags", "three.m4a")])
        self.assertEqual(plan.destinations, {
            self.sources[1]: self.root / "output" / "Artist" / "Shared" / "two.mp3",
            self.sources[2]: self.root / "output" / "Artist" / "Other" / "three.mp3",
        })
        self.assertEqual(plan.failures, {self.sources[0]: "ffprobe failed: corrupt file"})

    def test_unexpected_probe_exception_is_recorded_as_source_failure(self):
        def read_tags(source):
            if source == self.sources[0]:
                raise RuntimeError("unexpected probe failure")
            return "Artist", "Album"

        with patch("ui.output_plan.read_audio_tags", side_effect=read_tags):
            plan = prepare_output_plan(self.sources[:2], self.root / "output")

        self.assertEqual(plan.failures, {self.sources[0]: "unexpected probe failure"})
        self.assertEqual(
            plan.destinations,
            {self.sources[1]: self.root / "output" / "Artist" / "Album" / "two.mp3"},
        )

    def test_skips_every_collision_member_but_keeps_unrelated_destinations(self):
        sources = [self.root / "left" / "track.m4a", self.root / "right" / "track.m4a", self.sources[2]]
        tags = [("Artist", "Album"), ("artist", "album"), ("Other", "Record")]
        with patch("ui.output_plan.read_audio_tags", side_effect=tags):
            plan = prepare_output_plan(sources, self.root / "output")

        self.assertEqual(plan.destinations, {
            sources[2]: self.root / "output" / "Other" / "Record" / "three.mp3",
        })
        self.assertIn(sources[0], plan.failures)
        self.assertIn(sources[1], plan.failures)
        self.assertIn("collision", plan.failures[sources[0]].casefold())
        self.assertIn("collision", plan.failures[sources[1]].casefold())

    def test_uses_shared_output_root_for_each_planned_path(self):
        with patch("ui.output_plan.read_audio_tags", return_value=("A", "B")):
            plan = prepare_output_plan([self.sources[0]], self.root / "output")

        self.assertEqual(
            plan.destinations[self.sources[0]],
            self.root / "output" / "A" / "B" / "one.mp3",
        )

    def test_source_side_plan_does_not_read_tags_or_change_destinations(self):
        with patch("ui.output_plan.read_audio_tags") as read_tags:
            plan = prepare_source_plan(self.sources)

        read_tags.assert_not_called()
        self.assertEqual(plan.destinations, {
            source: source.with_suffix(".mp3") for source in self.sources
        })
        self.assertEqual(plan.failures, {})


if __name__ == "__main__":
    unittest.main()
