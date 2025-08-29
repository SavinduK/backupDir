import os
import json
import zipfile
from pathlib import Path
import shutil
import argparse

# Folders to ignore
IGNORED_DIRS = {"node_modules", ".expo", ".vscode"}
VERSION_FILE = "versionInfo.json"

# Backup directories
BACKUP_DIRS = [
    Path("D:/backup"),
    Path.home() / "Documents" / "backup"
]


def get_version():
    """Load or initialize versionInfo.json and increment version"""
    info_file = Path(VERSION_FILE)
    if info_file.exists():
        with open(info_file, "r") as f:
            data = json.load(f)
    else:
        data = {"version": 1}

    version = data["version"]
    data["version"] = version + 1  # increment for next run

    with open(info_file, "w") as f:
        json.dump(data, f, indent=4)

    return version


def create_zip(source_dir, zip_path):
    """Create zip archive excluding ignored folders and zip files"""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for root, dirs, files in os.walk(source_dir):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                if file.endswith(".zip"):
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, source_dir)
                zf.write(filepath, arcname=arcname)


def save_backup(zip_path):
    """Save zip into backup directories"""
    for backup in BACKUP_DIRS:
        backup.mkdir(parents=True, exist_ok=True)
        target_path = backup / zip_path.name
        shutil.copy(zip_path, target_path)
        print(f"Saved backup to {target_path}")


def main():
    parser = argparse.ArgumentParser(description="Backup directory into zip and save to backup folders.")
    parser.add_argument("--dir", default=".", help="Target directory to backup (default: current directory)")
    args = parser.parse_args()

    source_dir = Path(args.dir).resolve()
    version = get_version()
    dirname = source_dir.name

    # Create zip in memory location first (use temp path)
    temp_zip = Path.cwd() / f"{dirname}-{version}.zip"
    create_zip(source_dir, temp_zip)

    # Copy zip to backup directories
    save_backup(temp_zip)

    # Remove temporary zip in current directory
    temp_zip.unlink(missing_ok=True)

    # Print absolute path(s) of backup copies
    for backup in BACKUP_DIRS:
        print(str(backup / f"{dirname}-{version}.zip"))


if __name__ == "__main__":
    main()
