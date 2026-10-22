import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from core import discover_m4a, is_m4a

from .artwork import ArtworkManager
from .drop_tree import DropTreeWidget
from .qt_compat import QIcon, QStyle, Qt, QTreeWidgetItem


class SourceTree:
    def __init__(self, tree: DropTreeWidget, artwork: ArtworkManager) -> None:
        self.tree = tree
        self.artwork = artwork
        self.sources: Dict[str, Path] = {}
        self.roots: Dict[str, Path] = {}
        self.destinations: Dict[str, Path] = {}
        self.items: Dict[str, QTreeWidgetItem] = {}
        self.status_callback = lambda message: None
        self.folder_icon = QIcon.fromTheme("folder", tree.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.audio_icon = QIcon.fromTheme("audio-x-generic", tree.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

    def add_paths(self, paths: List[Path]) -> None:
        for path in paths:
            self.add_path(path)

    def add_path(self, path: Path) -> None:
        try:
            path = path.resolve()
            if path.is_dir():
                self._add_directory(path)
            elif is_m4a(path):
                self._add_file(path, reparent=False, root=path.parent)
        except OSError as exc:
            self.status_callback(f"Impossible d’inspecter {path}: {exc}")

    def _add_directory(self, path: Path, parent: Optional[QTreeWidgetItem] = None) -> Optional[QTreeWidgetItem]:
        audio_files = discover_m4a(
            path,
            on_error=lambda candidate, exc: self.status_callback(
                f"Impossible d’inspecter {candidate}: {exc}"
                if candidate != path
                else f"Impossible de parcourir {path}: {exc}"
            ),
        )
        if not audio_files:
            return None

        item = self._ensure_directory(path, parent)
        for audio_file in sorted(audio_files):
            directory_item = item
            current_path = path
            for part in audio_file.parent.relative_to(path).parts:
                current_path = current_path / part
                directory_item = self._ensure_directory(current_path, directory_item)
            self._add_file(audio_file, directory_item, root=path)
        item.setExpanded(True)
        return item

    def _ensure_directory(self, path: Path, parent: Optional[QTreeWidgetItem]) -> QTreeWidgetItem:
        key = os.path.normcase(str(path))
        item = self.items.get(key)
        if item is None:
            item = QTreeWidgetItem([path.name or str(path)])
            item.setIcon(0, self.folder_icon)
            item.setToolTip(0, str(path))
            item.setData(0, self._user_role(), str(path))
            self.items[key] = item
        self._attach(item, parent)
        return item

    def _add_file(
        self,
        path: Path,
        parent: Optional[QTreeWidgetItem] = None,
        reparent: bool = True,
        root: Optional[Path] = None,
    ) -> None:
        path = path.resolve()
        key = os.path.normcase(str(path))
        destination_key = os.path.normcase(str(path.with_suffix(".mp3")))
        previous = self.destinations.get(destination_key)
        if previous is not None and previous != path:
            self.status_callback(f"Collision ignorée : {previous.name} et {path.name} produisent le même MP3.")
            return

        is_new = key not in self.sources
        if is_new:
            self.sources[key] = path
            self.roots[key] = root or path.parent
            self.destinations[destination_key] = path
            item = QTreeWidgetItem([path.name])
            item.setIcon(0, self.audio_icon)
            item.setToolTip(0, str(path))
            item.setData(0, self._user_role(), str(path))
            self.items[key] = item
        if reparent or is_new:
            self._attach(self.items[key], parent)
        if is_new:
            self.artwork.request(path, self.items[key])
        self.status_callback(f"{len(self.sources)} fichier(s) dans la liste.")

    def _attach(self, item: QTreeWidgetItem, parent: Optional[QTreeWidgetItem]) -> None:
        if item.parent() is parent:
            if parent is not None or self.tree.indexOfTopLevelItem(item) >= 0:
                return
        if item.parent() is not None:
            item.parent().removeChild(item)
        else:
            index = self.tree.indexOfTopLevelItem(item)
            if index >= 0:
                self.tree.takeTopLevelItem(index)
        if parent is None:
            self.tree.addTopLevelItem(item)
        else:
            parent.addChild(item)

    def remove_selected(self) -> None:
        selected = self.tree.selectedItems()
        selected_ids = {id(item) for item in selected}
        roots = [item for item in selected if not self._has_selected_ancestor(item, selected_ids)]
        for item in roots:
            self._remove_item(item)
        self.status_callback(f"{len(self.sources)} fichier(s) dans la liste.")

    def _has_selected_ancestor(self, item: QTreeWidgetItem, selected_ids: Set[int]) -> bool:
        parent = item.parent()
        while parent is not None:
            if id(parent) in selected_ids:
                return True
            parent = parent.parent()
        return False

    def _remove_item(self, item: QTreeWidgetItem) -> None:
        removed_items = []
        stack = [item]
        while stack:
            current = stack.pop()
            removed_items.append(current)
            stack.extend(current.child(index) for index in range(current.childCount()))

        for removed_item in removed_items:
            value = removed_item.data(0, self._user_role())
            if not value:
                continue
            path = Path(value)
            key = os.path.normcase(str(path))
            if key in self.sources:
                self.sources.pop(key, None)
                self.roots.pop(key, None)
                self.destinations.pop(os.path.normcase(str(path.with_suffix(".mp3"))), None)
                self.artwork.clear(path)
            self.items.pop(key, None)

        parent = item.parent()
        if parent is None:
            index = self.tree.indexOfTopLevelItem(item)
            if index >= 0:
                self.tree.takeTopLevelItem(index)
        else:
            parent.removeChild(item)

        while parent is not None and parent.childCount() == 0:
            grandparent = parent.parent()
            value = parent.data(0, self._user_role())
            if value:
                self.items.pop(os.path.normcase(str(Path(value))), None)
            if grandparent is None:
                index = self.tree.indexOfTopLevelItem(parent)
                if index >= 0:
                    self.tree.takeTopLevelItem(index)
            else:
                grandparent.removeChild(parent)
            parent = grandparent

    def _user_role(self):
        return Qt.ItemDataRole.UserRole if hasattr(Qt, "ItemDataRole") else Qt.UserRole
