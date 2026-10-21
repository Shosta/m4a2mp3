import subprocess
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Set

from m4a2mp3 import _ffmpeg_environment

from .qt_compat import QIcon, QPixmap, QSize, Qt, QTimer, QTreeWidget, QTreeWidgetItem


class ArtworkManager:
    def __init__(self, tree: QTreeWidget, fallback_icon: QIcon, workers: int = 4) -> None:
        self.tree = tree
        self.fallback_icon = fallback_icon
        self.icons: Dict[str, QIcon] = {}
        self.targets: Dict[str, List[QTreeWidgetItem]] = {}
        self.pending: Dict[Future, str] = {}
        self.submitted: Set[str] = set()
        self.executor = ThreadPoolExecutor(max_workers=workers)
        self.timer = QTimer(tree)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._poll)

    def request(self, path: Path, item: Optional[QTreeWidgetItem] = None) -> None:
        key = str(path)
        if item is not None:
            icon = self.icons.get(key)
            if icon is not None:
                item.setIcon(0, icon)
            else:
                self.targets.setdefault(key, []).append(item)
        if key in self.icons or key in self.submitted:
            return
        self.submitted.add(key)
        future = self.executor.submit(self._extract, path)
        self.pending[future] = key
        if not self.timer.isActive():
            self.timer.start()

    def _extract(self, path: Path) -> Optional[bytes]:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error", "-i", str(path),
                    "-an", "-map", "0:v:0", "-frames:v", "1", str(temp_path),
                ],
                capture_output=True,
                env=_ffmpeg_environment(),
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

    def _poll(self) -> None:
        finished = [future for future in self.pending if future.done()]
        for future in finished:
            key = self.pending.pop(future)
            try:
                data = future.result()
            except Exception:
                data = None
            if not data:
                continue
            pixmap = QPixmap()
            if not pixmap.loadFromData(data):
                continue
            icon = QIcon(pixmap.scaled(
                QSize(16, 16),
                Qt.AspectRatioMode.KeepAspectRatio if hasattr(Qt, "AspectRatioMode") else Qt.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation if hasattr(Qt, "TransformationMode") else Qt.SmoothTransformation,
            ))
            self.icons[key] = icon
            for item in self.targets.pop(key, []):
                item.setIcon(0, icon)
        if not self.pending:
            self.timer.stop()

    def clear(self, path: Path) -> None:
        key = str(path)
        self.icons.pop(key, None)
        self.targets.pop(key, None)
        for future, pending_key in list(self.pending.items()):
            if pending_key == key:
                future.cancel()
                self.pending.pop(future, None)

    def shutdown(self) -> None:
        self.timer.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
