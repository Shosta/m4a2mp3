#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Optional
from core import (
    ConversionOptions as CoreConversionOptions,
    ConversionResult,
    ConversionStatus,
    SUPPORTED_AUDIO_EXTENSIONS,
    convert_file,
    ffmpeg_available,
    normalized_path_key,
)

from ui.qt_compat import QObject, QRunnable, QThreadPool, pyqtSignal

from ui.artwork import ArtworkManager
from ui.drop_tree import DropTreeWidget
from ui.i18n import LANGUAGES, translate
from ui.options import ConversionOptions, PreferencesDialog
from ui.qt_compat import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QIcon,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSize,
    QStyle,
    QSettings,
    QVBoxLayout,
    QWidget,
)
from ui.output_plan import prepare_output_plan, prepare_source_plan
from ui.result_tree import ResultTree, ResultTreeWidget
from ui.source_tree import SourceTree


class ConversionSignals(QObject):
    finished = pyqtSignal(object)


class ConversionTask(QRunnable):
    def __init__(
        self, source: Path, options: CoreConversionOptions, destination: Optional[Path] = None
    ) -> None:
        super().__init__()
        self.source = source
        self.options = options
        self.destination = destination
        self.signals = ConversionSignals()
        self.setAutoDelete(False)

    def run(self) -> None:
        try:
            result = convert_file(self.source, self.options, destination=self.destination)
        except Exception as exc:
            result = ConversionResult(self.source, ConversionStatus.ERROR, f"ERREUR : {exc}")
        self.signals.finished.emit(result)


class ConvertisseurQt(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("Shosta", "m4a2mp3")
        saved_language = str(self.settings.value("language", "fr"))
        self.language = saved_language if saved_language in {item["code"] for item in LANGUAGES} else "fr"
        self.setWindowTitle(translate(self.language, "M4A to MP3 Converter"))
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
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(12)

        self.folder_icon = QIcon.fromTheme(
            "folder", self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        )
        self.audio_icon = QIcon.fromTheme(
            "audio-x-generic", self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        )
        self.input_tree = DropTreeWidget()
        self.input_tree.setToolTip(
            translate(
                self.language,
                "Drop audio files or folders here. Select an item and press Delete to remove it.",
            )
        )
        self.input_tree.setIconSize(QSize(16, 16))
        self.artwork = ArtworkManager(self.input_tree, self.audio_icon)
        self.source_tree = SourceTree(self.input_tree, self.artwork)
        self.source_tree.status_callback = self._set_status
        self.source_tree.language = self.language
        self.input_tree.paths_dropped.connect(self.source_tree.add_paths)
        self.input_tree.delete_requested.connect(self.source_tree.remove_selected)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)
        self.add_files_button = QPushButton(
            self.audio_icon, translate(self.language, "Add audio files…")
        )
        self.add_files_button.clicked.connect(self._choose_files)
        action_bar.addWidget(self.add_files_button)
        self.add_folder_button = QPushButton(
            self.folder_icon, translate(self.language, "Add a folder…")
        )
        self.add_folder_button.clicked.connect(self._choose_folder)
        action_bar.addWidget(self.add_folder_button)
        action_bar.addSpacing(12)
        self.output_folder_label = QLabel(translate(self.language, "Output folder"))
        action_bar.addWidget(self.output_folder_label)
        self.output_folder_field = QLineEdit()
        self.output_folder_field.setPlaceholderText(
            translate(self.language, "Same folder as sources")
        )
        self.output_folder_field.setReadOnly(True)
        self.output_folder_field.setMinimumWidth(180)
        action_bar.addWidget(self.output_folder_field, 1)
        self.output_folder_button = QPushButton(translate(self.language, "Browse…"))
        self.output_folder_button.clicked.connect(self._choose_output_folder)
        action_bar.addWidget(self.output_folder_button)
        preferences_icon = QIcon.fromTheme(
            "preferences-system",
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView),
        )
        self.preferences_button = QPushButton(preferences_icon, "")
        self.preferences_button.setToolTip(translate(self.language, "Preferences"))
        self.preferences_button.setAccessibleName(translate(self.language, "Preferences"))
        self.preferences_button.clicked.connect(self._open_preferences)
        action_bar.addWidget(self.preferences_button)
        layout.addLayout(action_bar)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        left_column = QVBoxLayout()
        left_column.setSpacing(6)
        input_header = QHBoxLayout()
        input_header.setContentsMargins(0, 0, 0, 0)
        input_header_widget = QWidget()
        input_header_widget.setFixedHeight(28)
        input_header_widget.setLayout(input_header)
        self.input_header_label = QLabel(translate(self.language, "Audio inputs"))
        input_header.addWidget(self.input_header_label)
        input_header.addStretch(1)
        trash_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        self.clear_sources_button = QPushButton(
            trash_icon, translate(self.language, "Clear inputs")
        )
        self.clear_sources_button.clicked.connect(self._clear_sources)
        input_header.addWidget(self.clear_sources_button)
        left_column.addWidget(input_header_widget)
        left_column.addWidget(self.input_tree, 1)

        right_column = QVBoxLayout()
        right_column.setSpacing(6)
        results_header = QHBoxLayout()
        results_header.setContentsMargins(0, 0, 0, 0)
        results_header_widget = QWidget()
        results_header_widget.setFixedHeight(28)
        results_header_widget.setLayout(results_header)
        self.results_header_label = QLabel(translate(self.language, "Results"))
        results_header.addWidget(self.results_header_label)
        results_header.addStretch(1)
        self.clear_results_button = QPushButton(
            trash_icon, translate(self.language, "Clear results")
        )
        self.clear_results_button.clicked.connect(self._clear_results)
        results_header.addWidget(self.clear_results_button)
        right_column.addWidget(results_header_widget)
        self.output_tree = ResultTreeWidget()
        self.output_tree.delete_requested.connect(self._clear_results)
        self.output_tree.setHeaderHidden(True)
        self.output_tree.setIconSize(QSize(16, 16))
        self.results = ResultTree(
            self.output_tree, self.artwork, self.folder_icon, self.audio_icon
        )
        right_column.addWidget(self.output_tree, 1)
        columns.addLayout(left_column, 1)
        columns.addLayout(right_column, 1)
        layout.addLayout(columns, 1)

        footer = QHBoxLayout()
        footer.setSpacing(14)
        self.options = ConversionOptions(footer, self.language)
        footer.addSpacing(8)
        self.overwrite_check = QCheckBox(
            translate(self.language, "Overwrite existing files")
        )
        self.overwrite_check.setChecked(CoreConversionOptions().overwrite)
        footer.addWidget(self.overwrite_check)
        self.delete_check = QCheckBox(
            translate(self.language, "Delete source files after successful conversion")
        )
        footer.addWidget(self.delete_check)
        footer.addStretch(1)
        layout.addLayout(footer)

        bottom_bar = QHBoxLayout()
        self.status_label = QLabel(
            translate(self.language, "Drop audio files or folders into the input list.")
        )
        bottom_bar.addWidget(self.status_label, 1)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setMaximumWidth(220)
        bottom_bar.addWidget(self.progress)
        self.convert_button = QPushButton(translate(self.language, "Convert"))
        self.convert_button.setDefault(True)
        self.convert_button.clicked.connect(self._start_conversion)
        bottom_bar.addWidget(self.convert_button)
        layout.addLayout(bottom_bar)

        self.setCentralWidget(central)
        self._load_preferences()
        self._source_controls_enabled = True

    def _retranslate_ui(self) -> None:
        language = self.language
        tr = lambda text: translate(language, text)
        self.setWindowTitle(tr("M4A to MP3 Converter"))
        self.input_tree.setToolTip(
            tr("Drop audio files or folders here. Select an item and press Delete to remove it.")
        )
        self.add_files_button.setText(tr("Add audio files…"))
        self.add_folder_button.setText(tr("Add a folder…"))
        self.output_folder_label.setText(tr("Output folder"))
        self.output_folder_field.setPlaceholderText(tr("Same folder as sources"))
        self.output_folder_button.setText(tr("Browse…"))
        self.preferences_button.setToolTip(tr("Preferences"))
        self.preferences_button.setAccessibleName(tr("Preferences"))
        self.input_header_label.setText(tr("Audio inputs"))
        self.clear_sources_button.setText(tr("Clear inputs"))
        self.results_header_label.setText(tr("Results"))
        self.clear_results_button.setText(tr("Clear results"))
        self.overwrite_check.setText(tr("Overwrite existing files"))
        self.delete_check.setText(tr("Delete source files after successful conversion"))
        if not self.busy:
            if self.source_tree.sources:
                self.status_label.setText(
                    tr("{} file(s) in the list.").format(len(self.source_tree.sources))
                )
            else:
                self.status_label.setText(tr("Drop audio files or folders into the input list."))
        self.convert_button.setText(tr("Convert"))
        self.options.retranslate(language)
        self.source_tree.language = language
        self.results.retranslate(language)

    def _load_preferences(self) -> None:
        self.output_folder_field.setText(str(self.settings.value("output_folder", "")))
        quality = str(self.settings.value("quality", "0"))
        quality_index = self.options.quality_combo.findData(quality)
        self.options.quality_combo.setCurrentIndex(quality_index if quality_index >= 0 else 0)
        self.overwrite_check.setChecked(
            self.settings.value("overwrite", CoreConversionOptions().overwrite, type=bool)
        )
        self.delete_check.setChecked(self.settings.value("delete_sources", False, type=bool))

    def _open_preferences(self) -> None:
        self.preferences_dialog = PreferencesDialog(
            self.output_folder_field.text(),
            self.options.quality,
            self.overwrite_check.isChecked(),
            self.delete_check.isChecked(),
            language=self.language,
            parent=self,
        )
        dialog_exec = (
            self.preferences_dialog.exec
            if hasattr(self.preferences_dialog, "exec")
            else self.preferences_dialog.exec_
        )
        if dialog_exec():
            self.output_folder_field.setText(self.preferences_dialog.output_folder_field.text())
            self.options.quality_combo.setCurrentIndex(
                self.preferences_dialog.quality_combo.currentIndex()
            )
            self.overwrite_check.setChecked(self.preferences_dialog.overwrite_check.isChecked())
            self.delete_check.setChecked(self.preferences_dialog.delete_check.isChecked())
            self.settings.setValue("output_folder", self.output_folder_field.text())
            self.settings.setValue("quality", self.options.quality)
            self.settings.setValue("overwrite", self.overwrite_check.isChecked())
            self.settings.setValue("delete_sources", self.delete_check.isChecked())
            self.settings.setValue("language", self.preferences_dialog.language_combo.currentData())
            self.settings.sync()
            if self.language != self.preferences_dialog.language_combo.currentData():
                self.language = self.preferences_dialog.language_combo.currentData()
                self._retranslate_ui()

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _clear_results(self) -> None:
        self.results.clear()

    def _clear_sources(self) -> None:
        self.input_tree.selectAll()
        self.source_tree.remove_selected()

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            translate(self.language, "Choose audio files"),
            "",
            f"{translate(self.language, 'Audio files ({})').format(' '.join(f'*{extension}' for extension in sorted(SUPPORTED_AUDIO_EXTENSIONS)))};;{translate(self.language, 'All files (*)')}",
        )
        self.source_tree.add_paths([Path(path) for path in paths])

    def _choose_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, translate(self.language, "Choose an audio folder"))
        if path:
            self.source_tree.add_path(Path(path))

    def _choose_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, translate(self.language, "Choose output folder")
        )
        if path:
            self.output_folder_field.setText(path)
            self.settings.setValue("output_folder", path)
            self.settings.sync()

    def _start_conversion(self) -> None:
        if self.busy:
            return
        if not ffmpeg_available():
            QMessageBox.critical(
                self,
                translate(self.language, "ffmpeg not found"),
                translate(self.language, "Install ffmpeg and make sure it is available on PATH."),
            )
            return
        if not self.source_tree.sources:
            QMessageBox.information(
                self,
                translate(self.language, "No files"),
                translate(self.language, "Add M4A files or a folder before converting."),
            )
            return

        files = list(self.source_tree.sources.values())
        output_text = self.output_folder_field.text().strip()
        output_root = Path(output_text).resolve() if output_text else None
        plan = prepare_output_plan(files, output_root) if output_root else prepare_source_plan(files)
        self._output_root = output_root
        self._destinations = plan.destinations
        self.source_tree.set_destination_plan(self._destinations)
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
        self.status_label.setText(
            translate(self.language, "Conversion of {} file(s)…").format(self.total)
        )

        self.thread_pool.setMaxThreadCount(self.options.jobs)
        conversion_options = CoreConversionOptions(
            quality=quality,
            jobs=self.options.jobs,
            delete_sources=delete_sources,
            overwrite=overwrite,
        )
        for path, message in plan.failures.items():
            self.errors += 1
            self.done += 1
            destination = plan.failure_destinations.get(path, path.with_suffix(".mp3"))
            result = ConversionResult(path, ConversionStatus.ERROR, message)
            root = self.source_tree.roots.get(normalized_path_key(path), path.parent)
            failure_root = output_root if output_root and path in plan.failure_destinations else None
            self.results.add_result(result, root, destination, failure_root)

        for path in files:
            destination = plan.destinations.get(path)
            if destination is None:
                continue
            task = ConversionTask(path, conversion_options, destination)
            task.signals.finished.connect(self._on_conversion_finished)
            self.tasks.add(task)
            self.thread_pool.start(task)

        self.progress.setValue(self.done)
        self.output_tree.scrollToBottom()
        if self.done == self.total:
            self._finish_conversion()

    def _set_source_controls_enabled(self, enabled: bool) -> None:
        self.add_files_button.setEnabled(enabled)
        self.add_folder_button.setEnabled(enabled)
        self.output_folder_button.setEnabled(enabled)
        self.input_tree.setEnabled(enabled)

    def _on_conversion_finished(self, result: ConversionResult) -> None:
        self.tasks = {task for task in self.tasks if task.source != result.source}
        self.done += 1
        if result.status is ConversionStatus.ERROR:
            self.errors += 1
        root = self.source_tree.roots.get(normalized_path_key(result.source), result.source.parent)
        destination = self._destinations.get(result.source, result.source.with_suffix(".mp3"))
        output_root = self._output_root
        self.results.add_result(result, root, destination, output_root)
        self.output_tree.scrollToBottom()
        self.progress.setValue(self.done)

        if self.done >= self.total:
            self._finish_conversion()

    def _finish_conversion(self) -> None:
        self.busy = False
        self.convert_button.setEnabled(True)
        self._set_source_controls_enabled(True)
        self.status_label.setText(
            translate(self.language, "Finished: {} result(s) without errors, {} error(s).").format(
                self.total - self.errors, self.errors
            )
        )

    def closeEvent(self, event) -> None:
        if self.busy:
            question = QMessageBox(self)
            question.setIcon(
                QMessageBox.Icon.Question
                if hasattr(QMessageBox, "Icon")
                else QMessageBox.Question
            )
            question.setWindowTitle(translate(self.language, "Conversion in progress"))
            question.setText(
                translate(self.language, "A conversion is in progress. Do you really want to quit?")
            )
            yes = QMessageBox.StandardButton.Yes if hasattr(QMessageBox, "StandardButton") else QMessageBox.Yes
            no = QMessageBox.StandardButton.No if hasattr(QMessageBox, "StandardButton") else QMessageBox.No
            question.addButton(yes)
            question.addButton(no)
            question.button(yes).setText(translate(self.language, "Yes"))
            question.button(no).setText(translate(self.language, "No"))
            question.setDefaultButton(no)
            answer = question.exec() if hasattr(question, "exec") else question.exec_()
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
