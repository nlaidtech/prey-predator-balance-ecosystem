"""Create a GitHub Release v1.0.0 and upload the standalone Windows zip executable."""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

def get_github_token():
    try:
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True,
            text=True,
            check=True
        )
        for line in proc.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception as e:
        print(f"Error fetching git credential: {e}")
    return None

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_path = os.path.join(repo_root, "dist", "WildlifeEcosystem-Windows-x64.zip")
    
    if not os.path.exists(zip_path):
        print(f"Zip file not found: {zip_path}")
        sys.exit(1)

    token = get_github_token()
    if not token:
        print("No GitHub token found in git credential manager.")
        sys.exit(1)

    repo = "nlaidtech/prey-predator-balance-ecosystem"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "WildlifeEcosystem-Releaser"
    }

    print(f"Checking existing releases for {repo}...")
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            releases = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Failed to list releases: {e}")
        releases = []

    release = None
    for r in releases:
        if r.get("tag_name") == "v1.0.0":
            release = r
            print("Found existing v1.0.0 release.")
            break

    if not release:
        print("Creating release v1.0.0...")
        release_data = {
            "tag_name": "v1.0.0",
            "target_commitish": "main",
            "name": "Wildlife Ecosystem v1.0.0 - Windows Desktop Application",
            "body": (
                "## 🌿 Wildlife Ecosystem Standalone Windows Application (v1.0.0)\n\n"
                "Download the pre-compiled, self-contained Windows application below to run the ecosystem simulator without needing to install Python or dependencies.\n\n"
                "### 📥 Download & Play:\n"
                "1. Download **`WildlifeEcosystem-Windows-x64.zip`** below.\n"
                "2. Extract the `.zip` archive anywhere on your PC.\n"
                "3. Double-click **`WildlifeEcosystem.exe`** to launch instantly!\n\n"
                "### 🎮 Features:\n"
                "- 5 Territorial Biomes (Highlands, Forest, River, Thickets, Meadow)\n"
                "- 6 Wildlife Species (Wolf, Rabbit, Deer, Mountain Goat, Fox, Bear)\n"
                "- Smooth camera panning, zooming, minimap radar, and click-to-inspect animal HUD\n"
                "- 60 FPS 2.5D Animated Sprites, Top-Down 360°, and Plain Shapes view modes\n"
                "- Official Wildlife Ecosystem logo badge and pause banner"
            ),
            "draft": False,
            "prerelease": False
        }
        create_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases",
            data=json.dumps(release_data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(create_req) as resp:
                release = json.loads(resp.read().decode())
                print(f"[OK] Created release ID {release['id']}")
        except urllib.error.HTTPError as e:
            print(f"HTTP Error creating release: {e.code} - {e.read().decode()}")
            sys.exit(1)

    # Check if asset already uploaded
    asset_name = "WildlifeEcosystem-Windows-x64.zip"
    for a in release.get("assets", []):
        if a.get("name") == asset_name:
            print(f"Asset {asset_name} already uploaded (ID {a['id']}). Deleting to re-upload fresh copy...")
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/assets/{a['id']}",
                headers=headers,
                method="DELETE"
            )
            with urllib.request.urlopen(del_req) as del_resp:
                print("Deleted old asset.")

    upload_url = release["upload_url"].split("{")[0] + f"?name={asset_name}"
    print(f"Uploading {zip_path} ({os.path.getsize(zip_path) / (1024*1024):.1f} MB) to {upload_url}...")

    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/zip",
        "User-Agent": "WildlifeEcosystem-Releaser"
    }

    with open(zip_path, "rb") as f:
        file_bytes = f.read()

    up_req = urllib.request.Request(upload_url, data=file_bytes, headers=upload_headers, method="POST")
    try:
        with urllib.request.urlopen(up_req) as up_resp:
            result = json.loads(up_resp.read().decode())
            print(f"[SUCCESS] Uploaded {asset_name}!")
            print(f"Direct Download URL: {result.get('browser_download_url')}")
    except urllib.error.HTTPError as e:
        print(f"Upload failed: {e.code} - {e.read().decode()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
