#!/usr/bin/env python3

import sys
from pathlib import Path
from core import (
    ConversionOptions as CoreConversionOptions,
    ConversionResult,
    ConversionStatus,
    convert_file,
    ffmpeg_available,
)
from ui.qt_compat import QObject, QRunnable, QThreadPool, pyqtSignal

from ui.artwork import ArtworkManager
from ui.drop_tree import DropTreeWidget
from ui.options import ConversionOptions
from ui.qt_compat import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QIcon,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSize,
    QStyle,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)
from ui.result_tree import ResultTree
from ui.source_tree import SourceTree


class ConversionSignals(QObject):
    finished = pyqtSignal(object)


class ConversionTask(QRunnable):
    def __init__(self, source: Path, options: CoreConversionOptions) -> None:
        super().__init__()
        self.source = source
        self.options = options
        self.signals = ConversionSignals()
        self.setAutoDelete(False)

    def run(self) -> None:
        try:
            result = convert_file(self.source, self.options)
        except Exception as exc:
            result = ConversionResult(self.source, ConversionStatus.ERROR, f"ERREUR : {exc}")
        self.signals.finished.emit(result)


class ConvertisseurQt(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Convertisseur M4A vers MP3")
        self.setWindowIcon(QIcon(str(Path(__file__).with_name("m4a2mp3.png"))))
        self.resize(1050, 620)
        self.thread_pool = QThreadPool(self)
        self.tasks = set()
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
        self.input_tree = DropTreeWidget()
        self.input_tree.setToolTip(
            "Déposez des fichiers M4A ou des dossiers ici. "
            "Sélectionnez un élément puis appuyez sur Suppr pour le retirer."
        )
        self.folder_icon = QIcon.fromTheme(
            "folder", self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        )
        self.audio_icon = QIcon.fromTheme(
            "audio-x-generic", self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        )
        self.input_tree.setIconSize(QSize(16, 16))
        self.artwork = ArtworkManager(self.input_tree, self.audio_icon)
        self.source_tree = SourceTree(self.input_tree, self.artwork)
        self.source_tree.status_callback = self._set_status
        self.input_tree.paths_dropped.connect(self.source_tree.add_paths)
        self.input_tree.delete_requested.connect(self.source_tree.remove_selected)
        left_column.addWidget(self.input_tree)

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
        right_column.addWidget(QLabel("Fichiers convertis"))
        self.output_tree = QTreeWidget()
        self.output_tree.setHeaderHidden(True)
        self.output_tree.setIconSize(QSize(16, 16))
        self.results = ResultTree(
            self.output_tree, self.artwork, self.folder_icon, self.audio_icon
        )
        right_column.addWidget(self.output_tree)

        columns.addLayout(left_column, 1)
        columns.addLayout(controls)
        columns.addLayout(right_column, 1)
        layout.addLayout(columns, 1)

        options_layout = QHBoxLayout()
        self.options = ConversionOptions(options_layout)
        self.overwrite_check = QCheckBox("Écraser les MP3 existants")
        self.overwrite_check.setChecked(CoreConversionOptions().overwrite)
        options_layout.addWidget(self.overwrite_check)
        self.delete_check = QCheckBox("Supprimer les M4A après conversion réussie")
        options_layout.addWidget(self.delete_check)
        layout.addLayout(options_layout)

        self.status_label = QLabel(
            "Déposez des fichiers M4A ou des dossiers dans la liste de gauche."
        )
        layout.addWidget(self.status_label)
        self.setCentralWidget(central)
        self._source_controls_enabled = True

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Choisir des fichiers M4A",
            "",
            "Fichiers M4A (*.m4a);;Tous les fichiers (*)",
        )
        self.source_tree.add_paths([Path(path) for path in paths])

    def _choose_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if path:
            self.source_tree.add_path(Path(path))

    def _start_conversion(self) -> None:
        if self.busy:
            return
        if not ffmpeg_available():
            QMessageBox.critical(
                self,
                "ffmpeg introuvable",
                "Installez ffmpeg et assurez-vous qu’il est accessible dans le PATH.",
            )
            return
        if not self.source_tree.sources:
            QMessageBox.information(
                self, "Aucun fichier", "Ajoutez des fichiers M4A ou un dossier avant de convertir."
            )
            return

        files = list(self.source_tree.sources.values())
        quality = self.options.quality
        overwrite = self.overwrite_check.isChecked()
        delete_sources = self.delete_check.isChecked()
        self.busy = True
        self.total = len(files)
        self.done = 0
        self.errors = 0
        self.tasks.clear()
        self.progress.setRange(0, self.total)
        self.progress.setValue(0)
        self.convert_button.setEnabled(False)
        self._set_source_controls_enabled(False)
        self.status_label.setText(f"Conversion de {self.total} fichier(s)…")

        self.thread_pool.setMaxThreadCount(self.options.jobs)
        conversion_options = CoreConversionOptions(
            quality=quality,
            jobs=self.options.jobs,
            delete_sources=delete_sources,
            overwrite=overwrite,
        )
        for path in files:
            task = ConversionTask(path, conversion_options)
            task.signals.finished.connect(self._on_conversion_finished)
            self.tasks.add(task)
            self.thread_pool.start(task)

    def _set_source_controls_enabled(self, enabled: bool) -> None:
        self.add_files_button.setEnabled(enabled)
        self.add_folder_button.setEnabled(enabled)
        self.input_tree.setEnabled(enabled)

    def _on_conversion_finished(self, result: ConversionResult) -> None:
        self.tasks = {task for task in self.tasks if task.source != result.source}
        self.done += 1
        if result.status is ConversionStatus.ERROR:
            self.errors += 1
        root = self.source_tree.roots.get(str(result.source), result.source.parent)
        self.results.add_result(result, root)
        self.output_tree.scrollToBottom()
        self.progress.setValue(self.done)

        if self.done < self.total:
            return

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
        self.thread_pool.clear()
        self.artwork.shutdown()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    window = ConvertisseurQt()
    window.show()
    return app.exec() if hasattr(app, "exec") else app.exec_()


if __name__ == "__main__":
    sys.exit(main())
