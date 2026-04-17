# Save layers exporter 

# Installation

## Manual installation (recommended)

1. Install QGIS.  

2. Download or clone this repository:

```git clone https://github.com/Ashzero0/save_layers_exporter.git```

3. Create a .zip file containing:
save_layers_exporter/

├── __init__.py

├── metadata.txt

├── save_layers_exporter.py

├── exporter_dialog.py

├── resources.py

├── resources.qrc

├── icon.png

## Install the plugin in QGIS

4. Open QGIS and install the plugin:
Plugins > Manage and Install Plugins > Install from ZIP

Then select your .zip file.

5. The plugin is now installed.
You should see this icon in your toolbar:
<img width="121" height="112" alt="image" src="https://github.com/user-attachments/assets/447ec494-3b29-46b5-a4e0-0f010b7ff222" width="70"/>


# Plugin Usage
6. Work in QGIS and create temporary layers.

7. Save the layers you want to keep.
Open the plugin:

Click the Save Layers Exporter icon
or go to:
Plugins > Save Layers Exporter > Export Selected Layers

This window opens:

<img width="1307" height="1330" alt="image" src="https://github.com/user-attachments/assets/13499204-ff31-4dc0-ac9f-2ae543beedbb" width="420"/>



# How to use
✅ Select one or more layers by clicking on them.
When a layer name is highlighted, it means the layer is selected.

<img width="1309" height="1332" alt="image" src="https://github.com/user-attachments/assets/75840eba-4fb3-454b-84c0-ae6be5127ba2" width="420"/>

➡️ ❗ means the layer is a temporary layer
➡️ 🖊️ means the layer is currently being edited

✅ Select output format

Supported formats: GeoJSON, KML, ESRI Shapefile, CSV

<img width="1292" height="335" alt="image" src="https://github.com/user-attachments/assets/3be3ffa1-564c-455f-bcf5-b1d7a4e73b51" width="420"/>

✅ Select your destination folder
✅ Click Export


# Requirements
QGIS 3.22+
Windows / Linux / macOS

# Planned Future Improvements
The plugin should be available in the QGIS repository soon.
