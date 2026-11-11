import sys
import tempfile
import types
import unittest
from pathlib import Path

from unittest.mock import patch

from core import normalized_path_key


qt_compat = types.ModuleType("ui.qt_compat")
qt_compat.QIcon = object
qt_compat.QStyle = types.SimpleNamespace(StandardPixmap=types.SimpleNamespace(SP_DirIcon=1, SP_FileIcon=2))
qt_compat.Qt = types.SimpleNamespace(ItemDataRole=types.SimpleNamespace(UserRole=32))
qt_compat.QTreeWidgetItem = object
artwork_module = types.ModuleType("ui.artwork")
artwork_module.ArtworkManager = object
drop_tree_module = types.ModuleType("ui.drop_tree")
drop_tree_module.DropTreeWidget = object
with patch.dict(sys.modules, {
    "ui.qt_compat": qt_compat,
    "ui.artwork": artwork_module,
    "ui.drop_tree": drop_tree_module,
}):
    from ui.source_tree import SourceTree


class SourceTreePlanTests(unittest.TestCase):
    def test_destination_bookkeeping_tracks_casefolded_path_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.m4a"
            second = root / "second.m4a"
            upper = root / "Artist" / "Album" / "same.mp3"
            lower = root / "artist" / "album" / "SAME.MP3"
            tree = SourceTree.__new__(SourceTree)
            tree.destinations = {}
            tree.source_destinations = {}

            tree.set_destination_plan({first: upper, second: lower})

            destination_key = normalized_path_key(upper)
            self.assertEqual(
                tree.destinations[destination_key],
                {normalized_path_key(first), normalized_path_key(second)},
            )
            self.assertEqual(
                tree.source_destinations[normalized_path_key(first)],
                destination_key,
            )


if __name__ == "__main__":
    unittest.main()
