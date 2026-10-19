"""Build standalone Windows application executable using PyInstaller."""

import os
import shutil
import subprocess
import sys

def build_app():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)

    print(f"[BUILD] Working directory: {repo_root}")
    
    # 1. Ensure icons exist
    ico_path = os.path.join(repo_root, "assets", "icon.ico")
    if not os.path.exists(ico_path):
        from tools.create_icon import create_app_icon
        create_app_icon()

    # 2. PyInstaller command arguments
    pyinstaller_cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",                           # No black console window
        "--name=WildlifeEcosystem",
        f"--icon={ico_path}",
        "--add-data=assets;assets",             # Include all textures, props & sprites
        "--hidden-import=pygame",
        "--hidden-import=pygame._sdl2",
        "--hidden-import=numpy",
        "--paths=.",
        os.path.join("src", "main.py")
    ]

    print("[BUILD] Running PyInstaller...")
    print(" ".join(pyinstaller_cmd))
    result = subprocess.run(pyinstaller_cmd)
    
    if result.returncode != 0:
        print("[ERROR] PyInstaller build failed!")
        sys.exit(result.returncode)

    exe_path = os.path.join(repo_root, "dist", "WildlifeEcosystem", "WildlifeEcosystem.exe")
    print(f"\n[BUILD SUCCESS] Standalone Application created at:")
    print(f"  --> {exe_path}")

    # 3. Create or update Windows Desktop Shortcut pointing to the compiled EXE
    try:
        desktop_dir = os.path.join(os.environ["USERPROFILE"], "Desktop")
        shortcut_path = os.path.join(desktop_dir, "Wildlife Ecosystem App.lnk")
        ps_cmd = (
            f'$WshShell = New-Object -ComObject WScript.Shell; '
            f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
            f'$Shortcut.TargetPath = "{exe_path}"; '
            f'$Shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"; '
            f'$Shortcut.IconLocation = "{ico_path}, 0"; '
            f'$Shortcut.Description = "Wildlife Ecosystem Standalone Game Application"; '
            f'$Shortcut.Save()'
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
        print(f"[OK] Created Desktop Shortcut: {shortcut_path}")
    except Exception as e:
        print(f"[WARN] Could not create desktop shortcut: {e}")

if __name__ == "__main__":
    build_app()
