import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set

from core import ffmpeg_environment

from .qt_compat import QObject, QRunnable, QIcon, QPixmap, QSize, Qt, QThreadPool, pyqtSignal


class ArtworkSignals(QObject):
    finished = pyqtSignal(str, object)


class ArtworkTask(QRunnable):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.signals = ArtworkSignals()
        self.setAutoDelete(False)

    def run(self) -> None:
        self.signals.finished.emit(str(self.path), self._extract())

    def _extract(self) -> Optional[bytes]:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error", "-i", str(self.path),
                    "-an", "-map", "0:v:0", "-frames:v", "1", str(temp_path),
                ],
                capture_output=True,
                env=ffmpeg_environment(),
                timeout=15,
                check=False,
            )
            if result.returncode == 0 and temp_path.is_file() and temp_path.stat().st_size:
                return temp_path.read_bytes()
        except (OSError, subprocess.SubprocessError):
            return None
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return None


class ArtworkManager(QObject):
    def __init__(self, tree, fallback_icon: QIcon, workers: int = 4) -> None:
        super().__init__(tree)
        self.tree = tree
        self.fallback_icon = fallback_icon
        self.icons: Dict[str, QIcon] = {}
        self.targets: Dict[str, List] = {}
        self.pending: Dict[str, ArtworkTask] = {}
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(workers)

    def request(self, path: Path, item=None) -> None:
        key = str(path)
        if item is not None:
            icon = self.icons.get(key)
            if icon is not None:
                item.setIcon(0, icon)
            else:
                self.targets.setdefault(key, []).append(item)
        if key in self.icons or key in self.pending:
            return
        task = ArtworkTask(path)
        task.signals.finished.connect(self._finished)
        self.pending[key] = task
        self.thread_pool.start(task)

    def _finished(self, key: str, data: Optional[bytes]) -> None:
        self.pending.pop(key, None)
        if not data:
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        icon = QIcon(pixmap.scaled(
            QSize(16, 16),
            Qt.AspectRatioMode.KeepAspectRatio if hasattr(Qt, "AspectRatioMode") else Qt.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation if hasattr(Qt, "TransformationMode") else Qt.SmoothTransformation,
        ))
        self.icons[key] = icon
        for item in self.targets.pop(key, []):
            item.setIcon(0, icon)

    def clear(self, path: Path) -> None:
        key = str(path)
        self.icons.pop(key, None)
        self.targets.pop(key, None)
        task = self.pending.pop(key, None)
        if task is not None:
            self.thread_pool.tryTake(task)

    def shutdown(self) -> None:
        self.thread_pool.clear()
