import builtins
import os
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.qt_compat import QApplication

import core
import gui_qt
from ui.output_plan import OutputPlan


class GuiQtOutputTests(unittest.TestCase):
    def setUp(self):
        artwork_request = patch.object(gui_qt.ArtworkManager, "request")
        artwork_request.start()
        self.addCleanup(artwork_request.stop)

    def test_pyqt5_fallback_exports_line_edit(self):
        qt_core = types.ModuleType("PyQt5.QtCore")
        qt_gui = types.ModuleType("PyQt5.QtGui")
        qt_widgets = types.ModuleType("PyQt5.QtWidgets")
        for name in ("QObject", "QRunnable", "QSize", "Qt", "QThreadPool", "pyqtSignal"):
            setattr(qt_core, name, object)
        for name in ("QIcon", "QPixmap"):
            setattr(qt_gui, name, object)
        for name in (
            "QAbstractItemView", "QApplication", "QCheckBox", "QComboBox", "QFileDialog",
            "QHBoxLayout", "QLabel", "QLineEdit", "QListWidget", "QMainWindow", "QMessageBox",
            "QProgressBar", "QPushButton", "QSpinBox", "QStyle", "QTreeWidget",
            "QTreeWidgetItem", "QVBoxLayout", "QWidget",
        ):
            setattr(qt_widgets, name, object)
        qt_package = types.ModuleType("PyQt5")
        qt_package.__path__ = []
        real_import = builtins.__import__

        def pyqt5_only_import(name, *args, **kwargs):
            if name == "PyQt6" or name.startswith("PyQt6."):
                raise ImportError(name)
            return real_import(name, *args, **kwargs)

        with (
            patch.dict(sys.modules, {
                "PyQt5": qt_package,
                "PyQt5.QtCore": qt_core,
                "PyQt5.QtGui": qt_gui,
                "PyQt5.QtWidgets": qt_widgets,
            }),
            patch("builtins.__import__", side_effect=pyqt5_only_import),
        ):
            namespace = runpy.run_path(str(Path(__file__).parent / "ui" / "qt_compat.py"))

        self.assertIs(namespace["QLineEdit"], object)

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_conversion_options_offer_three_named_quality_levels_with_highest_default(self):
        from ui.options import ConversionOptions
        from ui.qt_compat import QHBoxLayout

        options = ConversionOptions(QHBoxLayout())

        self.assertEqual(options.quality_combo.count(), 3)
        self.assertEqual(
            [options.quality_combo.itemData(index) for index in range(3)],
            ["0", "4", "8"],
        )
        self.assertEqual(options.quality_combo.currentData(), "0")
        self.assertEqual(
            [options.quality_combo.itemText(index) for index in range(3)],
            ["Haute", "Équilibrée", "Compacte"],
        )
        self.assertEqual(options.jobs, 4)
        self.assertFalse(hasattr(options, "jobs_spin"))

    def test_main_window_uses_generic_source_labels(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)

        self.assertEqual(window.delete_check.text(), "Supprimer les fichiers source après conversion réussie")
        self.assertIn("fichiers audio", window.status_label.text())
        self.assertIn("fichiers audio", window.input_tree.toolTip())

    def test_add_buttons_show_audio_and_folder_icons(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)

        self.assertFalse(window.add_files_button.icon().isNull())
        self.assertFalse(window.add_folder_button.icon().isNull())
        self.assertEqual(window.add_files_button.icon().cacheKey(), window.audio_icon.cacheKey())
        self.assertEqual(window.add_folder_button.icon().cacheKey(), window.folder_icon.cacheKey())

    def test_result_panels_are_aligned_and_clear_button_has_trash_icon(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        window.show()
        self.app.processEvents()

        input_top = window.input_tree.mapTo(window, window.input_tree.rect().topLeft()).y()
        output_top = window.output_tree.mapTo(window, window.output_tree.rect().topLeft()).y()
        self.assertEqual(input_top, output_top)
        self.assertFalse(window.clear_results_button.icon().isNull())

    def test_clear_results_button_clears_only_the_results_view(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        source = Path("/music/track.m4a")
        window.results.add_result(
            core.ConversionResult(source, core.ConversionStatus.SUCCESS, "converti"),
            source.parent,
        )

        window.clear_results_button.click()

        self.assertEqual(window.output_tree.topLevelItemCount(), 0)
        self.assertEqual(window.source_tree.sources, {})

    def test_source_tree_adds_each_supported_audio_format_individually(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        with tempfile.TemporaryDirectory() as directory:
            sources = [Path(directory) / f"track{suffix}" for suffix in (".m4a", ".wav", ".aiff", ".aif")]
            for source in sources:
                source.touch()
                window.source_tree.add_path(source)

            self.assertEqual(set(window.source_tree.sources.values()), set(sources))

    def test_source_tree_recursively_adds_supported_audio_formats(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [root / f"track{suffix}" for suffix in (".m4a", ".wav", ".aiff", ".aif")]
            unsupported = root / "track.flac"
            for source in sources + [unsupported]:
                source.touch()

            window.source_tree.add_path(root)

            self.assertEqual(set(window.source_tree.sources.values()), set(sources))

    def test_file_dialog_filter_covers_supported_audio_formats(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        with patch.object(gui_qt.QFileDialog, "getOpenFileNames", return_value=([], "")) as dialog:
            window._choose_files()

        file_filter = dialog.call_args.args[3]
        for extension in (".m4a", ".wav", ".aiff", ".aif"):
            self.assertIn(extension, file_filter)

    def test_output_folder_selector_updates_common_destination_field(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)

        with patch.object(gui_qt.QFileDialog, "getExistingDirectory", return_value="/tmp/common-output"):
            window._choose_output_folder()

        self.assertEqual(window.output_folder_field.text(), "/tmp/common-output")

    def test_preflight_failures_are_shown_counted_and_never_submitted(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        source = Path("/music/broken.m4a")
        window.source_tree.sources = {os.path.normcase(str(source)): source}
        window.source_tree.roots = {os.path.normcase(str(source)): source.parent}
        output_root = Path("/tmp/common-output")
        failure = "ffprobe failed: corrupt file"

        with (
            patch.object(gui_qt, "ffmpeg_available", return_value=True),
            patch.object(window.output_folder_field, "text", return_value=str(output_root)),
            patch.object(gui_qt, "prepare_output_plan", return_value=OutputPlan({}, {source: failure}, {})),
            patch.object(window.thread_pool, "start") as start,
        ):
            window._start_conversion()

        start.assert_not_called()
        self.assertEqual(window.total, 1)
        self.assertEqual(window.done, 1)
        self.assertEqual(window.errors, 1)
        self.assertEqual(window.progress.value(), 1)
        self.assertIn("1 erreur(s)", window.status_label.text())
        self.assertEqual(window.output_tree.topLevelItemCount(), 1)
        self.assertIn(failure, window.output_tree.topLevelItem(0).child(0).text(0))

    def test_common_output_status_changes_to_conversion_when_tasks_are_submitted(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        self.addCleanup(lambda: setattr(window, "busy", False))
        source = Path("/music/track.m4a")
        destination = Path("/tmp/common-output/Artist/Album/track.mp3")
        window.source_tree.sources = {os.path.normcase(str(source)): source}
        window.source_tree.roots = {os.path.normcase(str(source)): source.parent}
        statuses_at_submission = []

        with (
            patch.object(gui_qt, "ffmpeg_available", return_value=True),
            patch.object(window.output_folder_field, "text", return_value="/tmp/common-output"),
            patch.object(
                gui_qt,
                "prepare_output_plan",
                return_value=OutputPlan({source: destination}, {}, {}),
            ),
            patch.object(
                window.thread_pool,
                "start",
                side_effect=lambda task: statuses_at_submission.append(window.status_label.text()),
            ),
        ):
            window._start_conversion()

        self.assertEqual(statuses_at_submission, ["Conversion de 1 fichier(s)…"])
        window.busy = False

    def test_preflight_failure_does_not_replace_active_conversion_status(self):
        window = gui_qt.ConvertisseurQt()
        self.addCleanup(window.artwork.shutdown)
        self.addCleanup(window.close)
        source = Path("/music/broken.m4a")
        active_source = Path("/music/active.m4a")
        another_active_source = Path("/music/another.m4a")
        output_root = Path("/tmp/common-output")
        failure = "ffprobe failed: corrupt file"
        window.source_tree.sources = {
            os.path.normcase(str(source)): source,
            os.path.normcase(str(active_source)): active_source,
            os.path.normcase(str(another_active_source)): another_active_source,
        }
        window.source_tree.roots = {
            os.path.normcase(str(source)): source.parent,
            os.path.normcase(str(active_source)): active_source.parent,
            os.path.normcase(str(another_active_source)): another_active_source.parent,
        }
        destination = output_root / "Artist" / "Album" / "active.mp3"
        another_destination = output_root / "Artist" / "Album" / "another.mp3"

        with (
            patch.object(gui_qt, "ffmpeg_available", return_value=True),
            patch.object(window.output_folder_field, "text", return_value=str(output_root)),
            patch.object(
                gui_qt,
                "prepare_output_plan",
                return_value=OutputPlan(
                    {active_source: destination, another_active_source: another_destination},
                    {source: failure},
                    {},
                ),
            ),
            patch.object(window.thread_pool, "start"),
        ):
            window._start_conversion()
            window._on_conversion_finished(
                core.ConversionResult(active_source, core.ConversionStatus.SUCCESS, "converti")
            )

        self.assertEqual(window.status_label.text(), "Conversion de 3 fichier(s)…")
        window.busy = False

    def test_conversion_task_passes_effective_destination_to_core(self):
        source = Path("/music/track.m4a")
        destination = Path("/output/Artist/Album/track.mp3")
        task = gui_qt.ConversionTask(source, core.ConversionOptions(), destination)
        emitted = []
        task.signals.finished.connect(emitted.append)
        expected = core.ConversionResult(source, core.ConversionStatus.SUCCESS, "converti")

        with patch("gui_qt.convert_file", return_value=expected) as convert:
            task.run()

        convert.assert_called_once_with(source, task.options, destination=destination)
        self.assertEqual(emitted, [expected])


if __name__ == "__main__":
    unittest.main()
