from .qt_compat import QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout


class ConversionOptions:
    def __init__(self, layout: QHBoxLayout) -> None:
        quality_layout = QVBoxLayout()
        quality_layout.addWidget(QLabel("Qualité audio"))
        self.quality_combo = QComboBox()
        quality_levels = [
            "0 — Qualité maximale",
            "1 — Très élevée",
            "2 — Élevée",
            "3 — Bonne",
            "4 — Bonne",
            "5 — Standard",
            "6 — Standard",
            "7 — Réduite",
            "8 — Faible",
            "9 — Qualité minimale",
        ]
        for value, label in enumerate(quality_levels):
            self.quality_combo.addItem(label, str(value))
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

        self.jobs_label = QLabel("Conversions simultanées")
        layout.addWidget(self.jobs_label)
        self.jobs_spin = QSpinBox()
        self.jobs_spin.setRange(1, 6)
        self.jobs_spin.setValue(4)
        self.jobs_spin.valueChanged.connect(self._update_jobs_label)
        layout.addWidget(self.jobs_spin)

    def _update_jobs_label(self, value: int) -> None:
        if value == 6:
            self.jobs_label.setText("Conversions simultanées\n(maximum : 6)")
        else:
            self.jobs_label.setText("Conversions simultanées")

    @property
    def quality(self) -> str:
        return str(self.quality_combo.currentData())

    @property
    def jobs(self) -> int:
        return self.jobs_spin.value()
