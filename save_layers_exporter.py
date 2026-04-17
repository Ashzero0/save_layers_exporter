from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from . import resources
from .exporter_dialog import SaveLayersToFileDialog


class SaveLayersExporterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.menu_name = "Save Layers Exporter"

    def initGui(self):
        self.action = QAction(
            QIcon(":/plugins/save_layers_exporter/icon.png"),
            "Export Selected Layers",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)

        self.iface.addPluginToMenu(self.menu_name, self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginMenu(self.menu_name, self.action)
            self.iface.removeToolBarIcon(self.action)

    def run(self):
        dialog = SaveLayersToFileDialog(self.iface.mainWindow())
        dialog.exec_()