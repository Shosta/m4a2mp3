from pathlib import Path
from typing import Optional

from .qt_compat import QAbstractItemView, QTreeWidget, Qt, QWidget, pyqtSignal
from .watermark import WatermarkMixin


class DropTreeWidget(WatermarkMixin, QTreeWidget):
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
        self._init_watermark(face="A", accent="#4a90d9")

    def paintEvent(self, event) -> None:
        # Le filigrane est peint en premier : les elements de la liste (s'il y
        # en a) restent dessines par-dessus, mais il n'apparait que si vide.
        self._paint_watermark_if_empty()
        super().paintEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == (Qt.Key.Key_Delete if hasattr(Qt, "Key") else Qt.Key_Delete):
            self.delete_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self.set_watermark_hover(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.set_watermark_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self.set_watermark_hover(False)
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.paths_dropped.emit(paths)
        event.acceptProposedAction()
