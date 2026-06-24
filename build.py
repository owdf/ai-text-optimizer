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

# PyInstaller 参数
PARAMS = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",                     # 打包成单个 exe
    "--windowed",                    # 无控制台窗口
    "--name", "AI文本优化器",
    "--icon", "NONE",                # 无外部图标，使用内置
    "--add-data", f"prompt_templates.json{':' if sys.platform == 'win32' else ':'}.",
    "--add-data", f"config.example.json{':' if sys.platform == 'win32' else ':'}.",
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
    print("  AI文本优化器 - PyInstaller 打包")
    print("=" * 50)

    # 检查 PyInstaller 是否安装
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n[ERROR] 需要安装 PyInstaller:")
        print("  pip install pyinstaller")
        return 1

    print(f"\n[INFO] 开始打包...")
    print(f"[INFO] 入口: main.py")
    print(f"[INFO] 输出: dist/AI文本优化器.exe\n")

    result = subprocess.run(PARAMS, cwd=str(ROOT))

    if result.returncode == 0:
        exe_path = ROOT / "dist" / "AI文本优化器.exe"
        print(f"\n[SUCCESS] 打包完成!")
        print(f"[SUCCESS] 输出文件: {exe_path}")
    else:
        print(f"\n[FAILED] 打包失败，返回码: {result.returncode}")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
