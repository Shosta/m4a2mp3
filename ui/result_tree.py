import os
from pathlib import Path
from typing import Dict, Optional

from core import ConversionResult, ConversionStatus, normalized_path_key

from .artwork import ArtworkManager
from .i18n import translate
from .qt_compat import QIcon, Qt, QTreeWidget, QTreeWidgetItem, pyqtSignal


class ResultTreeWidget(QTreeWidget):
    delete_requested = pyqtSignal()

    def keyPressEvent(self, event) -> None:
        delete_key = Qt.Key.Key_Delete if hasattr(Qt, "Key") else Qt.Key_Delete
        if event.key() == delete_key:
            self.delete_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class ResultTree:
    def __init__(self, tree: QTreeWidget, artwork: ArtworkManager, folder_icon: QIcon, audio_icon: QIcon) -> None:
        self.tree = tree
        self.artwork = artwork
        self.folder_icon = folder_icon
        self.audio_icon = audio_icon
        self.directories: Dict[str, QTreeWidgetItem] = {}
        self.language = "fr"

    def retranslate(self, language: str) -> None:
        self.language = language
        role = self._user_role() + 1
        stack = [self.tree.topLevelItem(index) for index in range(self.tree.topLevelItemCount())]
        while stack:
            item = stack.pop()
            stack.extend(item.child(index) for index in range(item.childCount()))
            metadata = item.data(0, role)
            if metadata:
                status, destination, message = metadata
                label = translate(language, status)
                item.setText(
                    0,
                    f"{label} — {destination}: {self._translate_result_message(message)}",
                )

    def clear(self) -> None:
        self.tree.clear()
        self.directories.clear()
        self.artwork.icons.clear()
        self.artwork.targets.clear()

    def add_result(
        self,
        result: ConversionResult,
        root: Path,
        destination: Optional[Path] = None,
        output_root: Optional[Path] = None,
    ) -> None:
        source = result.source
        destination = destination or source.with_suffix(".mp3")
        tree_root = output_root or root
        relative_destination = destination.relative_to(tree_root) if output_root else None
        parent = self._directory(tree_root, tree_root) if output_root is None else None
        current = tree_root
        directory_parts = (
            relative_destination.parts[:-1]
            if relative_destination
            else source.parent.relative_to(root).parts
        )
        for part in directory_parts:
            current = current / part
            parent = self._directory(current, tree_root, include_root=output_root is None)

        key = str(source)
        self.artwork.request(source)
        if result.status is ConversionStatus.ERROR:
            item = QTreeWidgetItem(
                [
                    f"{translate(self.language, 'Failed')} — {destination.name}: "
                    f"{self._translate_result_message(result.message)}"
                ]
            )
            item.setIcon(0, self.audio_icon)
        elif result.status is ConversionStatus.SKIPPED:
            item = QTreeWidgetItem(
                [
                    f"{translate(self.language, 'Skipped')} — {destination.name}: "
                    f"{self._translate_result_message(result.message)}"
                ]
            )
            item.setIcon(0, self.artwork.icons.get(key, self.audio_icon))
        else:
            item = QTreeWidgetItem([destination.name])
            item.setIcon(0, self.artwork.icons.get(key, self.audio_icon))
        item.setToolTip(0, str(destination))
        item.setData(0, self._user_role(), str(destination))
        if result.status is ConversionStatus.ERROR:
            item.setData(
                0,
                self._user_role() + 1,
                ("Failed", destination.name, result.message),
            )
        elif result.status is ConversionStatus.SKIPPED:
            item.setData(
                0,
                self._user_role() + 1,
                ("Skipped", destination.name, result.message),
            )
        if parent is None:
            self.tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
            parent.setExpanded(True)
        if result.status is not ConversionStatus.ERROR and key not in self.artwork.icons:
            self.artwork.targets.setdefault(key, []).append(item)

    def _directory(
        self, path: Path, root: Path, include_root: bool = True
    ) -> Optional[QTreeWidgetItem]:
        if path == root and not include_root:
            return None
        key = normalized_path_key(path)
        item = self.directories.get(key)
        if item is None:
            item = QTreeWidgetItem([path.name or str(path)])
            item.setIcon(0, self.folder_icon)
            item.setToolTip(0, str(path))
            item.setData(0, self._user_role(), str(path))
            self.directories[key] = item
            if path == root:
                if include_root:
                    self.tree.addTopLevelItem(item)
            else:
                parent_item = self._directory(path.parent, root, include_root)
                if parent_item is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                    parent_item.setExpanded(True)
        elif item.parent() is None and self.tree.indexOfTopLevelItem(item) < 0:
            if path == root:
                if include_root:
                    self.tree.addTopLevelItem(item)
            else:
                parent_item = self._directory(path.parent, root, include_root)
                if parent_item is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
        return item

    def _result_message_key(self, message: str) -> str:
        if message.startswith("ERREUR :"):
            return "Conversion error"
        if message.startswith("ignoré ("):
            return "Conversion skipped"
        if message.startswith("collision de destination :"):
            return "Output collision"
        if "tag" in message.casefold() or "métadonnée" in message.casefold():
            return "Output tags error"
        return message

    def _translate_result_message(self, message: str) -> str:
        key = self._result_message_key(message)
        translated = translate(self.language, key)
        if key == "Conversion error" and message.startswith("ERREUR :"):
            return translated + message[len("ERREUR :") :]
        if key in {"Output collision", "Output tags error"} and ":" in message:
            return translated + message[message.index(":") :]
        return translated

    def _user_role(self):
        return Qt.ItemDataRole.UserRole if hasattr(Qt, "ItemDataRole") else Qt.UserRole
