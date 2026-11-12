try:
    from PyQt6.QtCore import QObject, QRunnable, QSize, Qt, QThreadPool, QSettings, pyqtSignal
    from PyQt6.QtGui import QIcon, QPixmap
    from PyQt6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QStyle,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QSpinBox,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    try:
        from PyQt5.QtCore import QObject, QRunnable, QSize, Qt, QThreadPool, QSettings, pyqtSignal
        from PyQt5.QtGui import QIcon, QPixmap
        from PyQt5.QtWidgets import (
            QAbstractItemView,
            QApplication,
            QCheckBox,
            QComboBox,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMainWindow,
            QMessageBox,
            QProgressBar,
            QPushButton,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QSpinBox,
            QStyle,
            QTreeWidget,
            QTreeWidgetItem,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise SystemExit("Installez PyQt6 ou PyQt5 pour lancer l’interface graphique.") from exc
