import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.qt_compat import QApplication, QIcon, QTreeWidget
from ui.result_tree import ResultTree

import core


class Artwork:
    icons = {}
    targets = {}

    def request(self, path):
        pass


class ResultTreeOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.tree = QTreeWidget()
        self.result_tree = ResultTree(self.tree, Artwork(), QIcon(), QIcon())

    def test_result_is_nested_under_actual_artist_album_destination(self):
        source = self.root / "incoming" / "track.m4a"
        output_root = self.root / "organized"
        destination = output_root / "Artist" / "Album" / "track.mp3"
        result = core.ConversionResult(source, core.ConversionStatus.SUCCESS, "converti")

        self.result_tree.add_result(result, source.parent, destination, output_root)

        artist = self.tree.topLevelItem(0)
        album = artist.child(0)
        track = album.child(0)
        self.assertEqual(artist.text(0), "Artist")
        self.assertEqual(album.text(0), "Album")
        self.assertEqual(track.text(0), "track.mp3")
        self.assertEqual(track.toolTip(0), str(destination))
        self.assertEqual(track.data(0, self.result_tree._user_role()), str(destination))

    def test_result_without_common_output_keeps_source_directory_hierarchy(self):
        source = self.root / "incoming" / "track.m4a"
        destination = source.with_suffix(".mp3")
        result = core.ConversionResult(source, core.ConversionStatus.SUCCESS, "converti")

        self.result_tree.add_result(result, self.root, destination)

        self.assertEqual(self.tree.topLevelItem(0).text(0), self.root.name)
        self.assertEqual(self.tree.topLevelItem(0).child(0).text(0), "incoming")
        self.assertEqual(self.tree.topLevelItem(0).child(0).child(0).text(0), "track.mp3")


if __name__ == "__main__":
    unittest.main()
