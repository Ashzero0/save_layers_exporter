from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton,
    QFileDialog, QMessageBox, QListWidgetItem, QLabel,
    QComboBox, QWidget, QHBoxLayout, QSizePolicy, QProgressBar
)
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.core import (
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsApplication
)
import os
import re
import tempfile


LAYER_ID_ROLE = Qt.UserRole + 1


class LayerItemWidget(QWidget):
    def __init__(self, layer):
        super().__init__()
        self.layer = layer

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)

        # Layer name
        self.label = QLabel(layer.name())
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.label)

        layout.addStretch()

        # Temporary layer icon
        if layer.dataProvider() and layer.dataProvider().name() == "memory":
            icon_label = QLabel()

            icon = QgsApplication.getThemeIcon("/mIconMemoryLayer.svg")
            if icon.isNull():
                icon = QgsApplication.getThemeIcon("/mIconTemporaryLayer.svg")
            if icon.isNull():
                icon = QgsApplication.getThemeIcon("/mIconWarning.svg")

            icon_label.setPixmap(icon.pixmap(16, 16))
            icon_label.setToolTip("Temporary layer")
            icon_label.setFixedSize(18, 18)
            layout.addWidget(icon_label)

        # Editing icon
        if layer.isEditable():
            icon_label = QLabel()
            icon = QgsApplication.getThemeIcon("/mActionToggleEditing.svg")
            if not icon.isNull():
                icon_label.setPixmap(icon.pixmap(16, 16))
            icon_label.setToolTip("Editing in progress")
            icon_label.setFixedSize(18, 18)
            layout.addWidget(icon_label)

        self.setLayout(layout)


class SaveLayersToFileDialog(QDialog):
    FORMAT_MAP = {
        "GeoJSON": ("GeoJSON", ".geojson"),
        "CSV": ("CSV", ".csv"),
        "ESRI Shapefile": ("ESRI Shapefile", ".shp"),
        "KML": ("KML", ".kml"),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Export layers")
        self.resize(500, 500)

        self.output_folder = ""

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select one or more vector layers:"))

        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.layer_list)

        layout.addWidget(QLabel("Choose output format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(list(self.FORMAT_MAP.keys()))
        layout.addWidget(self.format_combo)

        self.select_folder_btn = QPushButton("Choose output folder")
        self.select_folder_btn.clicked.connect(self.choose_folder)
        layout.addWidget(self.select_folder_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_layers)
        layout.addWidget(self.export_btn)

        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.setLayout(layout)

        self.populate_layers()

        project = QgsProject.instance()
        project.layersAdded.connect(self.populate_layers)
        project.layersRemoved.connect(self.populate_layers)

    def closeEvent(self, event):
        project = QgsProject.instance()
        try:
            project.layersAdded.disconnect(self.populate_layers)
        except Exception:
            pass
        try:
            project.layersRemoved.disconnect(self.populate_layers)
        except Exception:
            pass
        super().closeEvent(event)

    def populate_layers(self, *args):
        self.layer_list.clear()

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if not layer.isValid():
                continue

            widget = LayerItemWidget(layer)
            item = QListWidgetItem()
            item.setData(LAYER_ID_ROLE, layer.id())
            item.setSizeHint(widget.sizeHint())

            self.layer_list.addItem(item)
            self.layer_list.setItemWidget(item, widget)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose folder")
        if folder:
            self.output_folder = folder
            self.select_folder_btn.setText(f"Folder: {folder}")

    def sanitize_layer_name(self, name):
        """Create a filesystem-safe file basename."""
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
        safe = re.sub(r"\s+", " ", safe).strip()
        safe = safe.rstrip(". ")
        return safe or "layer"

    def unique_output_path(self, folder, base_name, extension):
        """Avoid overwriting existing files."""
        candidate = os.path.join(folder, base_name + extension)
        if not os.path.exists(candidate):
            return candidate

        index = 1
        while True:
            candidate = os.path.join(folder, f"{base_name}_{index}{extension}")
            if not os.path.exists(candidate):
                return candidate
            index += 1

    def save_style_to_temp_qml(self, layer):
        """Save layer style to a temporary QML file and return its path."""
        fd, qml_path = tempfile.mkstemp(suffix=".qml")
        os.close(fd)

        ok = layer.saveNamedStyle(qml_path)
        if isinstance(ok, tuple):
            ok = ok[0]

        if not ok:
            try:
                os.remove(qml_path)
            except Exception:
                pass
            return None

        return qml_path

    def export_one_layer(self, layer, driver_name, output_path):
        """
        Export one vector layer using writeAsVectorFormatV3.
        Returns (success: bool, message: str).
        """
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = driver_name
        options.fileEncoding = "UTF-8"

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            output_path,
            QgsProject.instance().transformContext(),
            options
        )

        if result[0] != QgsVectorFileWriter.NoError:
            return False, str(result)

        return True, output_path

    def replace_memory_layer_with_exported_file(self, original_layer, output_path, display_name):
        """
        Replace a memory layer with its exported disk-based version while preserving style.
        """
        qml_path = self.save_style_to_temp_qml(original_layer)

        project = QgsProject.instance()
        original_id = original_layer.id()

        project.removeMapLayer(original_id)

        new_layer = QgsVectorLayer(output_path, display_name, "ogr")
        if not new_layer.isValid():
            if qml_path and os.path.exists(qml_path):
                try:
                    os.remove(qml_path)
                except Exception:
                    pass
            return False, "Export succeeded, but reloading the exported layer failed."

        project.addMapLayer(new_layer)

        if qml_path and os.path.exists(qml_path):
            try:
                new_layer.loadNamedStyle(qml_path)
                new_layer.triggerRepaint()
            finally:
                try:
                    os.remove(qml_path)
                except Exception:
                    pass

        return True, "Temporary layer replaced successfully."

    def export_layers(self):
        if not self.output_folder:
            QMessageBox.warning(self, "Warning", "Please choose an output folder.")
            return

        selected_items = self.layer_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one layer.")
            return

        selected_format = self.format_combo.currentText()
        driver_name, extension = self.FORMAT_MAP[selected_format]

        total = len(selected_items)
        self.progress.setMaximum(total)
        self.progress.setValue(0)
        self.export_btn.setEnabled(False)

        success_count = 0
        failed = []

        for i, item in enumerate(selected_items, start=1):
            layer_id = item.data(LAYER_ID_ROLE)
            layer = QgsProject.instance().mapLayer(layer_id)

            if not layer or not layer.isValid():
                failed.append("Unknown layer: invalid or removed before export.")
                self.progress.setValue(i)
                QCoreApplication.processEvents()
                continue

            self.progress_label.setText(f"Exporting: {layer.name()}")
            QCoreApplication.processEvents()

            safe_name = self.sanitize_layer_name(layer.name())
            output_path = self.unique_output_path(self.output_folder, safe_name, extension)

            ok, message = self.export_one_layer(layer, driver_name, output_path)

            if not ok:
                failed.append(f"{layer.name()}: {message}")
                self.progress.setValue(i)
                QCoreApplication.processEvents()
                continue

            if layer.dataProvider() and layer.dataProvider().name() == "memory":
                replace_ok, replace_msg = self.replace_memory_layer_with_exported_file(
                    layer,
                    output_path,
                    safe_name
                )
                if not replace_ok:
                    failed.append(f"{safe_name}: {replace_msg}")
                else:
                    success_count += 1
            else:
                success_count += 1

            self.progress.setValue(i)
            QCoreApplication.processEvents()

        self.export_btn.setEnabled(True)
        self.progress_label.setText("Export completed.")

        if failed:
            summary = (
                f"Export finished.\n\n"
                f"Successful exports: {success_count}\n"
                f"Failed exports: {len(failed)}\n\n"
                f"Details:\n- " + "\n- ".join(failed[:20])
            )
            if len(failed) > 20:
                summary += f"\n- ... and {len(failed) - 20} more"

            QMessageBox.warning(self, "Export completed with warnings", summary)
        else:
            QMessageBox.information(
                self,
                "Success",
                f"Export completed successfully.\n\nExported layers: {success_count}"
            )
            self.accept()


dialog = SaveLayersToFileDialog()
dialog.exec_()