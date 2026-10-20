#!/usr/bin/env python3

import os
import shutil
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    from PyQt6.QtCore import QTimer, pyqtSignal
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    try:
        from PyQt5.QtCore import QTimer, Qt, pyqtSignal
        from PyQt5.QtWidgets import (
            QApplication,
            QCheckBox,
            QFileDialog,
                QHBoxLayout,
            QLabel,
            QListWidget,
            QMainWindow,
            QMessageBox,
            QProgressBar,
            QPushButton,
            QSpinBox,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise SystemExit("Installez PyQt6 ou PyQt5 pour lancer l’interface graphique.") from exc

from m4a2mp3 import convertir


class DropListWidget(QListWidget):
    paths_dropped = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

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


class ConvertisseurQt(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Convertisseur M4A vers MP3")
        self.resize(1050, 620)
        self.sources: Dict[str, Path] = {}
        self.destinations: Dict[str, Path] = {}
        self.executor: Optional[ThreadPoolExecutor] = None
        self.pending: Set[Future] = set()
        self.total = 0
        self.done = 0
        self.errors = 0
        self.busy = False
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        columns = QHBoxLayout()

        left_column = QVBoxLayout()
        left_column.addWidget(QLabel("Fichiers à convertir"))
        self.input_list = DropListWidget()
        self.input_list.paths_dropped.connect(self._add_paths)
        self.input_list.setToolTip("Déposez des fichiers M4A ou des dossiers ici")
        left_column.addWidget(self.input_list)

        controls = QVBoxLayout()
        self.add_files_button = QPushButton("Ajouter des fichiers…")
        self.add_files_button.clicked.connect(self._choose_files)
        controls.addWidget(self.add_files_button)
        self.add_folder_button = QPushButton("Ajouter un dossier…")
        self.add_folder_button.clicked.connect(self._choose_folder)
        controls.addWidget(self.add_folder_button)
        controls.addStretch(1)
        self.convert_button = QPushButton("Convertir  →")
        self.convert_button.clicked.connect(self._start_conversion)
        controls.addWidget(self.convert_button)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        controls.addWidget(self.progress)
        controls.addStretch(1)

        right_column = QVBoxLayout()
        right_column.addWidget(QLabel("Résultats"))
        self.output_list = QListWidget()
        right_column.addWidget(self.output_list)

        columns.addLayout(left_column, 1)
        columns.addLayout(controls)
        columns.addLayout(right_column, 1)
        layout.addLayout(columns, 1)

        options = QHBoxLayout()
        options.addWidget(QLabel("Qualité VBR (0–9)"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(0, 9)
        self.quality_spin.setValue(0)
        options.addWidget(self.quality_spin)
        options.addSpacing(12)
        options.addWidget(QLabel("Conversions simultanées"))
        self.jobs_spin = QSpinBox()
        self.jobs_spin.setRange(1, 32)
        self.jobs_spin.setValue(4)
        options.addWidget(self.jobs_spin)
        self.overwrite_check = QCheckBox("Écraser les MP3 existants")
        self.overwrite_check.setChecked(True)
        options.addWidget(self.overwrite_check)
        self.delete_check = QCheckBox("Supprimer les M4A après conversion réussie")
        options.addWidget(self.delete_check)
        layout.addLayout(options)

        self.status_label = QLabel("Déposez des fichiers M4A ou des dossiers dans la liste de gauche.")
        layout.addWidget(self.status_label)
        self.setCentralWidget(central)

    def _add_paths(self, paths: List[Path]) -> None:
        for path in paths:
            self._add_path(path)

    def _add_path(self, path: Path) -> None:
        if path.is_dir():
            try:
                for candidate in path.rglob("*"):
                    try:
                        if candidate.is_file() and candidate.suffix.lower() == ".m4a" and not candidate.name.startswith("._"):
                            self._add_file(candidate)
                    except OSError as exc:
                        self.status_label.setText(f"Impossible d’inspecter {candidate}: {exc}")
            except OSError as exc:
                self.status_label.setText(f"Impossible de parcourir {path}: {exc}")
        elif path.is_file() and path.suffix.lower() == ".m4a" and not path.name.startswith("._"):
            self._add_file(path)

    def _add_file(self, path: Path) -> None:
        path = path.resolve()
        key = os.path.normcase(str(path))
        destination_key = os.path.normcase(str(path.with_suffix(".mp3")))
        previous = self.destinations.get(destination_key)
        if previous is not None and previous != path:
            self.status_label.setText(f"Collision ignorée : {previous.name} et {path.name} produisent le même MP3.")
            return
        if key not in self.sources:
            self.sources[key] = path
            self.destinations[destination_key] = path
            self.input_list.addItem(str(path))
            self.status_label.setText(f"{len(self.sources)} fichier(s) dans la liste.")

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Choisir des fichiers M4A",
            "",
            "Fichiers M4A (*.m4a);;Tous les fichiers (*)",
        )
        self._add_paths([Path(path) for path in paths])

    def _choose_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if path:
            self._add_path(Path(path))

    def _start_conversion(self) -> None:
        if self.busy:
            return
        if shutil.which("ffmpeg") is None:
            QMessageBox.critical(self, "ffmpeg introuvable", "Installez ffmpeg et assurez-vous qu’il est accessible dans le PATH.")
            return
        if not self.sources:
            QMessageBox.information(self, "Aucun fichier", "Ajoutez des fichiers M4A ou un dossier avant de convertir.")
            return

        files = list(self.sources.values())
        quality = str(self.quality_spin.value())
        overwrite = self.overwrite_check.isChecked()
        delete_sources = self.delete_check.isChecked()
        self.busy = True
        self.total = len(files)
        self.done = 0
        self.errors = 0
        self.pending.clear()
        self.progress.setRange(0, self.total)
        self.progress.setValue(0)
        self.convert_button.setEnabled(False)
        self._set_source_controls_enabled(False)
        self.status_label.setText(f"Conversion de {self.total} fichier(s)…")

        self.executor = ThreadPoolExecutor(max_workers=self.jobs_spin.value())
        for path in files:
            self.pending.add(
                self.executor.submit(convertir, path, quality, delete_sources, overwrite)
            )
        QTimer.singleShot(100, self._poll_results)

    def _set_source_controls_enabled(self, enabled: bool) -> None:
        self.add_files_button.setEnabled(enabled)
        self.add_folder_button.setEnabled(enabled)
        self.input_list.setEnabled(enabled)

    def _poll_results(self) -> None:
        finished = [future for future in self.pending if future.done()]
        for future in finished:
            self.pending.remove(future)
            try:
                src, result = future.result()
            except Exception as exc:
                src, result = Path("Fichier inconnu"), f"ERREUR : {exc}"
            self.done += 1
            if result.startswith("ERREUR"):
                self.errors += 1
                self.output_list.addItem(f"ÉCHEC — {src}: {result}")
            elif result.startswith("ignoré"):
                self.output_list.addItem(f"IGNORÉ — {src.with_suffix('.mp3')}: {result}")
            else:
                self.output_list.addItem(f"{src.with_suffix('.mp3')} — {result}")
            self.output_list.scrollToBottom()
            self.progress.setValue(self.done)

        if self.pending:
            QTimer.singleShot(100, self._poll_results)
            return

        if self.executor is not None:
            self.executor.shutdown(wait=False)
            self.executor = None
        self.busy = False
        self.convert_button.setEnabled(True)
        self._set_source_controls_enabled(True)
        self.status_label.setText(
            f"Terminé : {self.total - self.errors} résultat(s) sans erreur, {self.errors} erreur(s)."
        )

    def closeEvent(self, event) -> None:
        if self.busy:
            answer = QMessageBox.question(
                self,
                "Conversion en cours",
                "Une conversion est en cours. Voulez-vous vraiment quitter ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                if hasattr(QMessageBox, "StandardButton")
                else QMessageBox.Yes | QMessageBox.No,
            )
            yes = QMessageBox.StandardButton.Yes if hasattr(QMessageBox, "StandardButton") else QMessageBox.Yes
            if answer != yes:
                event.ignore()
                return
        if self.executor is not None:
            self.executor.shutdown(wait=False, cancel_futures=True)
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    window = ConvertisseurQt()
    window.show()
    return app.exec() if hasattr(app, "exec") else app.exec_()


if __name__ == "__main__":
    sys.exit(main())
