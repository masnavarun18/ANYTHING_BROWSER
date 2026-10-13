"""
ANYTHING BROWSER - Build Automation Script
Compiles the application into a standalone Windows executable bundle using PyInstaller.
"""

import os
import shutil
import subprocess
import sys


def build_executable():
    print("==================================================")
    print("Building ANYTHING BROWSER Standalone Windows Executable...")
    print("==================================================")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(root_dir, "dist")
    build_dir = os.path.join(root_dir, "build")
    main_py = os.path.join(root_dir, "src", "main.py")

    # Clean previous builds
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir, ignore_errors=True)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)

    python_exe = sys.executable

    cmd = [
        python_exe,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "AnythingBrowser",
        "--icon",
        os.path.join(root_dir, "assets", "logo.ico"),
        "--add-data",
        f"src{os.pathsep}src",
        "--add-data",
        f"assets{os.pathsep}assets",
        main_py,
    ]

    print(f"Executing build command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=root_dir)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "AnythingBrowser", "AnythingBrowser.exe")
        if os.path.exists(exe_path):
            print("\nBUILD SUCCESSFUL!")
            print(f"Executable output: {exe_path}")
            return exe_path
        else:
            print("\nBUILD ERROR: Executable not found after build.")
            sys.exit(1)
    else:
        print(f"\nBUILD FAILED with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build_executable()
