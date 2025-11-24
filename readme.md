# AERIS

AERIS simplifies aircraft livery management by automating distribution, synchronization, and incremental updates.  
Instead of redownloading massive archives, users receive only the changed files, keeping every aircraft up to date efficiently.

## Features

- Incremental updates for livery packs
- Multiple presets per aircraft
- Automatic handling of common zip layouts

---

## Installation

1. Go to the [Releases](https://github.com/itsdotbmp/AERIS/releases/) page and download the latest `AERIS.exe`.
2. Place the exe in a new, empty folder. For example:

```
AERIS/
└─ AERIS.exe
```

The program will create required configuration and data files around it.

3. Launch the program once. You will be prompted to either **create a new configuration** or **import an existing one**.

## Configuration

*Configuration is now handled entirely inside the application. The program no longer requires editing a JSON file manually.*

1. **DCS Liveries Folder** – The program will ask for the path to your DCS Saved Games liveries folder. You can type it in directly or paste it.

2. **Aircraft Presets** – You can either:

   * Create a new preset using the built-in editor.
   * Import an existing preset file (`*.set`) via the import screen. Most often, your squadron or group will provide a preset.

   **Import instructions:**

   * Place the preset file into the `presets` folder once it exists.
   * Use the import screen to select your preset (mark with **M**, accept with **A**).
   * After importing, you can set it as the default preset for the program.

3. Once your preset is set, press **Q** to return to the main menu.


## Using AERIS

1. Launch AERIS.
2. If multiple presets exist, choose one via the Choose Preset menu. The main menu shows the currently selected preset and target folder.
3. Navigate the menu with the arrow keys (↑↓). Select options with **Enter** or **A**.
4. To set a default preset, go to the **Config** menu and select the preset you want as default.
5. To update liveries:
   * Highlight **Start Update** and confirm.
   * A summary of changes appears. Accept to start or cancel to stop.
   * If files will be deleted, the program prompts before removing them. You can choose to keep them.

6. During the update:
   * Downloads occur first, then zip files are unpacked into the correct folders.
   * Progress is shown on screen.

7. When finished, a summary screen shows any errors or actions taken. You may continue from this screen.

Your liveries are now updated.

## Troubleshooting

* **Permissions:** Make sure the folder containing AERIS and your liveries folder are writable.
* **Config issues:** Because the config file format changed significantly, it is recommended to delete your old config file before running this version. The program will create a new one automatically.

---

## Advanced Usage and Repository Setup

Detailed instructions for repository maintainers, including zip file layout, version files, and multiple repo management, are available in the [Advanced Usage Documentation](https://itsdotbmp.github.io/AERIS/advanced_usage.html).
