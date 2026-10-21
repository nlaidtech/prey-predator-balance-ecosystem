"""Deploy build/web to gh-pages branch on GitHub for instant browser access."""

import os
import shutil
import subprocess
import sys
import tempfile

def deploy():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    build_web_dir = os.path.join(repo_root, "build", "web")
    
    if not os.path.exists(build_web_dir):
        print(f"Error: {build_web_dir} does not exist. Run pygbag build first.")
        sys.exit(1)

    print("[1/4] Copying web build to temporary staging folder...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        for item in os.listdir(build_web_dir):
            s = os.path.join(build_web_dir, item)
            d = os.path.join(tmp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # Add .nojekyll so GitHub Pages doesn't ignore files
        with open(os.path.join(tmp_dir, ".nojekyll"), "w") as f:
            f.write("")

        print("[2/4] Initializing git in staging folder...")
        subprocess.run(["git", "init"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "config", "user.name", "nlaidtech"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "n.laid.142099.tc@umindanano.edu.ph"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "deploy: Wildlife Ecosystem Web Build to GitHub Pages"], cwd=tmp_dir, check=True)

        remote_url = "https://github.com/nlaidtech/prey-predator-balance-ecosystem.git"
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=tmp_dir, check=True)

        print("[3/4] Pushing to gh-pages branch on GitHub...")
        push_cmd = ["git", "push", "-u", "origin", "gh-pages", "--force"]
        res = subprocess.run(push_cmd, cwd=tmp_dir)

        if res.returncode == 0:
            print("\n[4/4] [SUCCESS] Pushed web build to gh-pages branch!")
            print("Web URL: https://nlaidtech.github.io/prey-predator-balance-ecosystem/")
        else:
            print(f"[ERROR] git push returned code {res.returncode}")
            sys.exit(res.returncode)

if __name__ == "__main__":
    deploy()
