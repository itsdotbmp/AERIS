# AERIS

AERIS simplifies aircraft livery management by automating distribution, synchronization, and incremental updates.  
Instead of redownloading massive archives, users receive only the changed files, keeping every aircraft up to date efficiently.

## Features

- Incremental updates for livery packs
- Multiple presets per aircraft
- Automatic handling of common zip layouts

---

## Installation

1. Go to the [Releases](https://github.com/aeris/releases) page and download the latest `AERIS.exe`.
2. Place the exe in a new, empty folder. For example:

```
AERIS/
└─ AERIS.exe
````

This allows the program to create required configuration and data files around it.

3. Launch the program once. This will create the default configuration files.

Once you have the config files, you are ready to set up your first preset.

---

## Configuration

The program requires a `config.json` file. The first time you run AERIS, a default (mostly empty) config file is created. You must fill in a few critical fields.

1. **server_url** - the location of your livery server:
```json
"server_url": "https://example.com/folder"
````

Trailing commas are critical in JSON. Missing or extra commas will break the program.

2. **liveries_folder** - the path to your DCS liveries folder:
```json
"liveries_folder": "C:/Saved Games/DCS/Liveries"
```

Use forward slashes `/`. Backslashes `\` will cause errors.

3. **Aircraft Presets** - define each aircraft and distribution preset. Example:

```json
"aircrafts": {
    "86fw_f4e": {
        "name": "86th vFW - F-4E Phantom II",
        "folder": "f-4e-45mc",
        "remote_subfolder": null
    },
    "86fw_f-16c": {
        "name": "86th vFW - F-16C Fighting Falcon",
        "folder": "f-16c",
        "remote_subfolder": "f-16"
    }
}
```

* `"folder"` is the destination folder inside your `liveries_folder`.
* `"remote_subfolder"` is optional; use it if this preset pulls from a different server location.

After editing, completely quit and restart AERIS for changes to take effect.

---

## Using AERIS

1. Launch AERIS.
2. If multiple presets exist, choose one via the Choose Preset menu. The main menu shows the currently selected preset and target folder.
3. Navigate the menu with the arrow keys (↑↓). Select options with **Enter** or **A**.
4. To update liveries:
   * Highlight **Start Update** and confirm.
   * A summary of changes appears. Accept to start or cancel to stop.
   * If files will be deleted, the program prompts before removing them. You can choose to keep them.

5. During the update:
   * Downloads occur first, then zip files are unpacked into the correct folders.
   * Progress is shown on screen.

6. When finished, a summary screen shows any errors or actions taken. You may continue from this screen.

Your liveries are now updated.

---

## Troubleshooting

* JSON Errors: Extra or missing commas or using `\` instead of `/` will prevent AERIS from starting. Check your config carefully.
* Permissions: Make sure the folder containing AERIS and your liveries folder are writable.
* Presets: Restart AERIS after editing `config.json` to apply changes.

---

## Advanced Usage and Repository Setup

Detailed instructions for repository maintainers, including zip file layout, version files, and multiple repo management, are available in the [GitHub Documentation](https://github.com/aeris/docs).
