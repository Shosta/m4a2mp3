from core import DEFAULT_JOBS

from .i18n import LANGUAGES, translate
from .qt_compat import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class PreferencesDialog(QDialog):
    def __init__(
        self,
        output_folder: str,
        quality: str,
        overwrite: bool,
        delete_sources: bool,
        language: str = "fr",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.language = language if language in {item["code"] for item in LANGUAGES} else "fr"
        self.setWindowTitle(translate(self.language, "Preferences"))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.form = form
        self.language_combo = QComboBox()
        for item in LANGUAGES:
            self.language_combo.addItem(f"{item['flag']}  {item['name']}", item["code"])
        selected_language = self.language_combo.findData(self.language)
        self.language_combo.setCurrentIndex(selected_language if selected_language >= 0 else 0)
        form.addRow(translate(self.language, "Language"), self.language_combo)
        self.output_folder_field = QLineEdit(output_folder)
        self.browse_button = QPushButton(translate(self.language, "Browse…"))
        self.browse_button.clicked.connect(self._choose_output_folder)
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.output_folder_field, 1)
        folder_layout.addWidget(self.browse_button)
        form.addRow(translate(self.language, "Output folder"), folder_layout)
        self.quality_combo = QComboBox()
        for label, value in [("High", "0"), ("Balanced", "4"), ("Compact", "8")]:
            self.quality_combo.addItem(translate(self.language, label), value)
        index = self.quality_combo.findData(quality)
        self.quality_combo.setCurrentIndex(index if index >= 0 else 0)
        form.addRow(translate(self.language, "Audio quality"), self.quality_combo)
        self.overwrite_check = QCheckBox(translate(self.language, "Overwrite existing files"))
        self.overwrite_check.setChecked(overwrite)
        form.addRow(self.overwrite_check)
        self.delete_check = QCheckBox(
            translate(self.language, "Delete source files after successful conversion")
        )
        self.delete_check.setChecked(delete_sources)
        form.addRow(self.delete_check)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            if hasattr(QDialogButtonBox, "StandardButton")
            else QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(
            QDialogButtonBox.StandardButton.Ok
            if hasattr(QDialogButtonBox, "StandardButton")
            else QDialogButtonBox.Ok
        ).setText(translate(self.language, "OK"))
        buttons.button(
            QDialogButtonBox.StandardButton.Cancel
            if hasattr(QDialogButtonBox, "StandardButton")
            else QDialogButtonBox.Cancel
        ).setText(translate(self.language, "Cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            translate(self.language, "Choose output folder"),
            self.output_folder_field.text(),
        )
        if path:
            self.output_folder_field.setText(path)


class ConversionOptions:
    def __init__(self, layout: QHBoxLayout, language: str = "fr") -> None:
        self.language = language
        quality_layout = QVBoxLayout()
        self.quality_label = QLabel()
        quality_layout.addWidget(self.quality_label)
        self.quality_combo = QComboBox()
        self.quality_levels = [("High", "0"), ("Balanced", "4"), ("Compact", "8")]
        for _, value in self.quality_levels:
            self.quality_combo.addItem("", value)
        self.quality_combo.setCurrentIndex(0)
        quality_layout.addWidget(self.quality_combo)
        self.quality_help = QLabel()
        quality_layout.addWidget(self.quality_help)
        layout.addLayout(quality_layout)
        layout.addSpacing(12)
        self.retranslate(language)

    def retranslate(self, language: str) -> None:
        self.language = language
        self.quality_label.setText(translate(language, "Audio quality"))
        for index, (label, _) in enumerate(self.quality_levels):
            self.quality_combo.setItemText(index, translate(language, label))
        self.quality_combo.setToolTip(
            translate(
                language,
                "The bitrate is variable and adapts to the audio content (VBR encoding).",
            )
            + " "
            + translate(language, "Higher quality generally means a larger file.")
        )
        self.quality_help.setText(translate(language, "High quality = generally larger file."))
        self.quality_help.setToolTip(
            translate(
                language,
                "The bitrate is variable and adapts to the audio content (VBR encoding).",
            )
        )

    @property
    def quality(self) -> str:
        return str(self.quality_combo.currentData())

    @property
    def jobs(self) -> int:
        return DEFAULT_JOBS
