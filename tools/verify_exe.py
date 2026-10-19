"""Verify that the compiled WildlifeEcosystem.exe launches without crashing."""

import os
import subprocess
import time

def verify_exe():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe_path = os.path.join(repo_root, "dist", "WildlifeEcosystem", "WildlifeEcosystem.exe")
    
    if not os.path.exists(exe_path):
        print(f"[FAIL] Executable not found at {exe_path}")
        return False

    print(f"[TEST] Starting {exe_path}...")
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    proc = subprocess.Popen([exe_path], env=env, cwd=os.path.dirname(exe_path))
    
    time.sleep(2.5)
    ret = proc.poll()
    if ret is not None:
        print(f"[FAIL] Process exited prematurely with code {ret}")
        return False
    
    print(f"[PASS] Executable is running healthy (PID {proc.pid}). Terminating test instance...")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("[PASS] Executable verification passed!")
    return True

if __name__ == "__main__":
    verify_exe()
