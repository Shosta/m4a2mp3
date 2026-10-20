import os
from pathlib import Path
from typing import Dict

from .artwork import ArtworkManager
from .qt_compat import QIcon, Qt, QTreeWidget, QTreeWidgetItem


class ResultTree:
    def __init__(self, tree: QTreeWidget, artwork: ArtworkManager, folder_icon: QIcon, audio_icon: QIcon) -> None:
        self.tree = tree
        self.artwork = artwork
        self.folder_icon = folder_icon
        self.audio_icon = audio_icon
        self.directories: Dict[str, QTreeWidgetItem] = {}

    def add_result(self, source: Path, result: str, root: Path) -> None:
        destination = source.with_suffix(".mp3")
        parent = self._directory(root, root)
        current = root
        for part in source.parent.relative_to(root).parts:
            current = current / part
            parent = self._directory(current, root)

        key = str(source)
        self.artwork.request(source)
        if result.startswith("ERREUR"):
            item = QTreeWidgetItem([f"ÉCHEC — {destination.name}: {result}"])
            item.setIcon(0, self.audio_icon)
        elif result.startswith("ignoré"):
            item = QTreeWidgetItem([f"IGNORÉ — {destination.name}: {result}"])
            item.setIcon(0, self.artwork.icons.get(key, self.audio_icon))
        else:
            item = QTreeWidgetItem([destination.name])
            item.setIcon(0, self.artwork.icons.get(key, self.audio_icon))
        item.setToolTip(0, str(destination))
        item.setData(0, self._user_role(), str(destination))
        if parent is None:
            self.tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
            parent.setExpanded(True)
        if not result.startswith("ERREUR") and key not in self.artwork.icons:
            self.artwork.targets.setdefault(key, []).append(item)

    def _directory(self, path: Path, root: Path) -> QTreeWidgetItem:
        key = os.path.normcase(str(path))
        item = self.directories.get(key)
        if item is None:
            item = QTreeWidgetItem([path.name or str(path)])
            item.setIcon(0, self.folder_icon)
            item.setToolTip(0, str(path))
            item.setData(0, self._user_role(), str(path))
            self.directories[key] = item
            if path == root:
                self.tree.addTopLevelItem(item)
            else:
                parent_item = self._directory(path.parent, root)
                parent_item.addChild(item)
                parent_item.setExpanded(True)
        elif item.parent() is None and self.tree.indexOfTopLevelItem(item) < 0:
            if path == root:
                self.tree.addTopLevelItem(item)
            else:
                self._directory(path.parent, root).addChild(item)
        return item

    def _user_role(self):
        return Qt.ItemDataRole.UserRole if hasattr(Qt, "ItemDataRole") else Qt.UserRole
