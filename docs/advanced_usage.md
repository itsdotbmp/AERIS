# AERIS Advanced Usage Guide

This guide is intended for repository maintainers and advanced users who want to host AERIS livery packs and manage multiple presets or repositories.

## Repository Rules

1. **Repository Location**
   A single AERIS repository must reside entirely within a single folder. All files that belong to the repository must be in this folder.

2. **Repository Membership**
   AERIS only manages files explicitly listed in the repository’s version file. Any other files in the folder are ignored.

3. **Subfolders**
   Subfolders can be used to organize multiple repositories. Each subfolder contains a complete, independent repository with its own version file and zip files. If subfolders are used, the user’s `config.json` must set `remote_subfolder` to point to the correct subfolder.

4. **Multiple Repositories**
   Multiple repositories can technically exist in the same folder if all their files are unique and do not collide, but this is strongly discouraged. The preferred method is one repository per folder.

**Example structure with multiple repositories using subfolders:**

```text
<repo-root>/
 ├─ 86vfw_f4e/                # Repository 1
 │   ├─ 86vfw-f4e_version.txt
 │   ├─ F4E_PhantomII.zip
 │   └─ ...
 └─ 86vfw_f16/                # Repository 2
     ├─ 86vfw-f16_version.txt
     ├─ F16C_FightingFalcon.zip
     └─ ...
```

## Version File Format

1. **Naming**
   The version file must be prefixed with the preset ID as configured in the user’s `config.json`.
   Example: `86vfw-f4e_version.txt` where `86vfw-f4e` is the preset ID.

2. **User-Facing Information**
   The top section of the version file should be readable by users. It can include:

   * Changelog description
   * Notes about the repository
   * URL to the repository
   * Support contacts

Example:

```
# Example Squadron Liveries — F-4E Phantom II (DCS)

This is the changelog for F-4E Phantom II liveries in DCS World.
It lists all file changes for each release so you can see what has
been added, updated, or removed.

The livery updates are provided by Example Squadron.
You can always check the latest version online:
https://example.com/dcsrepo/liveries/f-4e_version.txt

For questions or support, contact support@example.com.
```

3. **Release Lines**
   Each release starts with a line `release-<version>`. Subsequent lines list file changes in a semi-colon separated format:

```
action;filename.zip;optional message
```

* `action`: `new`, `update`, `delete`
* `filename.zip`: exact file name on the server (case sensitive)
* `optional message`: any notes for the user

Example:

```
release-2.1.1
update;COMMON_SEA_WRAP.zip
delete;Old_Livery_Folder.zip
new;COMMON_E1.zip;New Euro One files

release-2.1.0
new;COMMON_SEA_WRAP.zip
update;COMMON_SEA.zip

release-1.0.0
new;COMMON_SEA_WRAP.zip
update;COMMON_SEA.zip
new;Old_Livery_Folder.zip
```

## Zip File Layout Guidelines

AERIS can handle several common zip layouts, but following these standards ensures predictable behavior.

### Recommended

Zip file contains the livery files directly:

```text
F4E_PhantomII.zip
 ├─ description.lua
 ├─ texture.dds
 ├─ texture2.dds
```

AERIS will create a folder named after the zip inside the user's liveries folder and place the files there.

### Alternative Acceptable Layout

Zip contains a single folder named after the livery:

```text
F4E_PhantomII.zip
 └─ F4E_PhantomII/
     ├─ description.lua
     ├─ texture.dds
     ├─ texture2.dds
```

Files are extracted into the folder in the zip.

### Layouts to Avoid

Multiple liveries in a single zip or multiple top-level folders within a repository are discouraged. If unavoidable, AERIS will wrap them in a folder named after the zip, but predictable behavior is not guaranteed.

## Multiple Presets and Multi-Repo Management

AERIS supports multiple presets per user. Each preset should have a unique preset ID and its own version file.

* Prefer separate folders per repository to minimize collisions.
* If multiple repositories exist in subfolders, `remote_subfolder` must point to the correct folder for each preset in `config.json`.

Example preset JSON for users:

```json
"86vfw_f4e": {
    "name": "F-4E Phantom II",
    "folder": "f-4e-45mc",
    "remote_subfolder": null
},
"86vfw_f16": {
    "name": "F-16C Fighting Falcon",
    "folder": "f-16c/test",
    "remote_subfolder": "86vfw_f16"
}
```

* `"folder"`: target extraction folder in the user’s liveries folder
* `"remote_subfolder"`: optional; set if repository is in a subfolder

## Best Practices

* Keep version files human-readable; include preamble with contact info and repo URL.
* Only files listed in the version file are managed by AERIS.
* Always update the version file before uploading new zips.
* Test zip layouts locally before publishing.
* Use clear naming conventions for zips and version files.

## Troubleshooting

* **Missing or incorrect filenames** in version files prevent updates. Check case sensitivity.
* **Zip layout errors** may cause files to end up in unexpected folders. Follow recommended structure.
* **Multiple repositories in one folder**: avoid collisions; using separate folders is strongly recommended.
