from core import DEFAULT_JOBS

from .qt_compat import QComboBox, QHBoxLayout, QLabel, QVBoxLayout


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
