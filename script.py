import os
import json
import zipfile
from pathlib import Path
import shutil
import argparse
import subprocess

# --- CONFIGURATION ---
IGNORED_DIRS = {"node_modules", ".expo", ".vscode", ".git", "__pycache__", "android", "ios"}
VERSION_FILE = "versionInfo.json"

# Local Backup destinations
ZIP_BACKUP_DIR = Path("D:/backup")
FOLDER_BACKUP_ROOT = Path.home() / "Documents" / "backup"

# GitHub Destination (The local path to your cloned backup repo)
GITHUB_REPO_LOCAL_PATH = Path("C:/Users/K.G.S.Aman/Documents/github_backup/code-backup")

def get_version():
    """Manages the version counter in versionInfo.json"""
    info_file = Path(VERSION_FILE)
    data = {"version": 1}
    if info_file.exists():
        try:
            with open(info_file, "r") as f:
                data = json.load(f)
        except: pass

    version = data["version"]
    data["version"] = version + 1
    with open(info_file, "w") as f:
        json.dump(data, f, indent=4)
    return version

def create_zip(source_dir, zip_path, commit_msg=None):
    """Creates a ZIP archive and injects commit.txt"""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        if commit_msg:
            zf.writestr("commit.txt", f"Commit Message:\n{commit_msg}")
            
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                if file.endswith(".zip") or file == VERSION_FILE:
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, source_dir)
                zf.write(filepath, arcname=arcname)

def save_as_folder(source_dir, project_name, version, commit_msg=None):
    """Saves the backup as an unzipped folder: backup/project/project-v"""
    target_dir = FOLDER_BACKUP_ROOT / project_name / f"{project_name}-{version}"
    if target_dir.exists(): shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        rel_path = os.path.relpath(root, source_dir)
        dest_root = target_dir / rel_path
        dest_root.mkdir(parents=True, exist_ok=True)
        for file in files:
            if file.endswith(".zip") or file == VERSION_FILE: continue
            shutil.copy2(os.path.join(root, file), dest_root / file)

    if commit_msg:
        with open(target_dir / "commit.txt", "w") as f:
            f.write(f"Commit Message:\n{commit_msg}")
    return target_dir

def push_to_github(zip_file, folder_path, project_name, version, commit_msg):
    """Copies to local git repo and pushes to GitHub"""
    if not GITHUB_REPO_LOCAL_PATH.exists():
        print(f"❌ GitHub Repo path not found at {GITHUB_REPO_LOCAL_PATH}")
        return

    # Create project subfolder in the Git Repo
    repo_project_dir = GITHUB_REPO_LOCAL_PATH / project_name
    repo_project_dir.mkdir(parents=True, exist_ok=True)

    # Copy ZIP to repo
    shutil.copy2(zip_file, repo_project_dir / zip_file.name)

    # Copy Folder to repo
    repo_folder_dest = repo_project_dir / folder_path.name
    if repo_folder_dest.exists(): shutil.rmtree(repo_folder_dest)
    shutil.copytree(folder_path, repo_folder_dest)

    # Execute Git Commands
    print(f"🚀 Pushing v{version} to GitHub...")
    try:
        commands = [
            ["git", "add", "."],
            ["git", "commit", "-m", f"v{version}: {commit_msg or 'Automated Backup'}"],
            ["git", "push", "origin", "main"]
        ]
        for cmd in commands:
            subprocess.run(cmd, cwd=GITHUB_REPO_LOCAL_PATH, check=True, capture_output=True)
        print("✅ Successfully pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git Error: {e.stderr.decode()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Directory to backup")
    parser.add_argument("--github", action="store_true", help="Push backup to GitHub repo")
    parser.add_argument("--commit", help="Description of changes")
    args = parser.parse_args()

    source_dir = Path(args.dir).resolve()
    version = get_version()
    project_name = source_dir.name

    # 1. Create ZIP
    temp_zip = Path.cwd() / f"{project_name}-{version}.zip"
    create_zip(source_dir, temp_zip, args.commit)
    
    # 2. Save ZIP to D: Drive
    ZIP_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    final_zip = ZIP_BACKUP_DIR / temp_zip.name
    shutil.copy2(temp_zip, final_zip)

    # 3. Save as unzipped folder
    folder_path = save_as_folder(source_dir, project_name, version, args.commit)

    # 4. GitHub Push
    if args.github:
        push_to_github(final_zip, folder_path, project_name, version, args.commit)

    temp_zip.unlink(missing_ok=True)
    print(f"\n--- Backup v{version} for '{project_name}' Complete ---")
    print(f"ZIP: {final_zip}\nFolder: {folder_path}")

if __name__ == "__main__":
    main()