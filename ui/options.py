from core import DEFAULT_JOBS

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
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Préférences")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.output_folder_field = QLineEdit(output_folder)
        browse_button = QPushButton("Parcourir…")
        browse_button.clicked.connect(self._choose_output_folder)
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.output_folder_field, 1)
        folder_layout.addWidget(browse_button)
        form.addRow("Dossier de sortie", folder_layout)
        self.quality_combo = QComboBox()
        for label, value in [("Haute", "0"), ("Équilibrée", "4"), ("Compacte", "8")]:
            self.quality_combo.addItem(label, value)
        index = self.quality_combo.findData(quality)
        self.quality_combo.setCurrentIndex(index if index >= 0 else 0)
        form.addRow("Qualité audio", self.quality_combo)
        self.overwrite_check = QCheckBox("Écraser les fichiers existants")
        self.overwrite_check.setChecked(overwrite)
        form.addRow(self.overwrite_check)
        self.delete_check = QCheckBox("Supprimer les fichiers source après conversion réussie")
        self.delete_check.setChecked(delete_sources)
        form.addRow(self.delete_check)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            if hasattr(QDialogButtonBox, "StandardButton")
            else QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier de sortie", self.output_folder_field.text()
        )
        if path:
            self.output_folder_field.setText(path)


class ConversionOptions:
    def __init__(self, layout: QHBoxLayout) -> None:
        quality_layout = QVBoxLayout()
        quality_layout.addWidget(QLabel("Qualité audio"))
        self.quality_combo = QComboBox()
        quality_levels = [("Haute", "0"), ("Équilibrée", "4"), ("Compacte", "8")]
        for label, value in quality_levels:
            self.quality_combo.addItem(label, value)
        self.quality_combo.setCurrentIndex(0)
        self.quality_combo.setToolTip(
            "Encodage VBR : le débit varie selon le contenu audio. "
            "Une qualité supérieure produit généralement un fichier plus volumineux."
        )
        quality_layout.addWidget(self.quality_combo)
        self.quality_help = QLabel("Qualité supérieure = fichier généralement plus volumineux.")
        self.quality_help.setToolTip(
            "Le débit n’est pas fixe : il s’adapte au contenu audio (encodage VBR)."
        )
        quality_layout.addWidget(self.quality_help)
        layout.addLayout(quality_layout)
        layout.addSpacing(12)

    @property
    def quality(self) -> str:
        return str(self.quality_combo.currentData())

    @property
    def jobs(self) -> int:
        return DEFAULT_JOBS
