"""
PyInstaller 打包脚本
运行: python build.py

生成单个 .exe 文件到 dist/ 目录
"""

import subprocess
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent

# Windows 用 ';'，Unix 用 ':'
_DATA_SEP = ";" if sys.platform == "win32" else ":"

# PyInstaller 参数
PARAMS = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",                     # 打包成单个 exe
    "--windowed",                    # 无控制台窗口
    "--name", "AITextOptimizer",
    "--icon", "NONE",                # 无外部图标，使用内置
    "--add-data", f"config.example.json{_DATA_SEP}.",
    "--hidden-import", "pystray._win32",
    "--hidden-import", "PIL._imagingtk",
    "--hidden-import", "PIL.ImageTk",
    "--collect-submodules", "customtkinter",
    "--collect-submodules", "pynput",
    "--collect-submodules", "pystray",
    "--noconfirm",
    "--clean",
    str(ROOT / "main.py"),
]


def main():
    print("=" * 50)
    print("  AI Text Optimizer - PyInstaller build")
    print("=" * 50)

    # 检查 PyInstaller 是否安装
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n[ERROR] PyInstaller is required:")
        print("  pip install pyinstaller")
        return 1

    print("\n[INFO] Starting build...")
    print("[INFO] Entry point: main.py")
    print("[INFO] Output: dist/AITextOptimizer.exe\n")

    result = subprocess.run(PARAMS, cwd=str(ROOT))

    if result.returncode == 0:
        exe_path = ROOT / "dist" / "AITextOptimizer.exe"
        print("\n[SUCCESS] Build completed.")
        print(f"[SUCCESS] Output file: {exe_path}")
    else:
        print(f"\n[FAILED] Build exited with code {result.returncode}.")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
