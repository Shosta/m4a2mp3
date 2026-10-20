from pathlib import Path
from typing import Optional

from .qt_compat import QAbstractItemView, QTreeWidget, Qt, QWidget, pyqtSignal


class DropTreeWidget(QTreeWidget):
    paths_dropped = pyqtSignal(list)
    delete_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setHeaderHidden(True)
        selection_mode = (
            QAbstractItemView.SelectionMode.ExtendedSelection
            if hasattr(QAbstractItemView, "SelectionMode")
            else QAbstractItemView.ExtendedSelection
        )
        self.setSelectionMode(selection_mode)

    def keyPressEvent(self, event) -> None:
        if event.key() == (Qt.Key.Key_Delete if hasattr(Qt, "Key") else Qt.Key_Delete):
            self.delete_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.paths_dropped.emit(paths)
        event.acceptProposedAction()
