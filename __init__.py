def classFactory(iface):
    from .save_layers_exporter import SaveLayersExporterPlugin
    return SaveLayersExporterPlugin(iface)