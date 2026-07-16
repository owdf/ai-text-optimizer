"""build.py 参数回归"""

import sys
from pathlib import Path


def test_add_data_separator():
    # 动态校验 build 模块中的分隔符逻辑
    sep = ";" if sys.platform == "win32" else ":"
    # 导入会执行模块级常量
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "build.py"
    spec = importlib.util.spec_from_file_location("build_mod", path)
    mod = importlib.util.module_from_spec(spec)
    # 避免 main() 执行；只加载常量
    # build.py 在 import 时不会调用 main
    spec.loader.exec_module(mod)
    assert mod._DATA_SEP == sep
    joined = " ".join(mod.PARAMS)
    assert f"config.example.json{sep}." in joined
    # 旧 bug：Windows 上错误使用了 ':' 分隔符。
    if sys.platform == "win32":
        assert "config.example.json:." not in joined


def test_packaged_data_sources_exist():
    """PyInstaller 的 --add-data 源文件必须真实存在。"""
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    path = root / "build.py"
    spec = importlib.util.spec_from_file_location("build_data_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    for index, arg in enumerate(mod.PARAMS):
        if arg != "--add-data":
            continue
        source = mod.PARAMS[index + 1].split(mod._DATA_SEP, 1)[0]
        assert (root / source).is_file(), f"Missing packaged data file: {source}"


def test_executable_uses_portable_ascii_name():
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    path = root / "build.py"
    spec = importlib.util.spec_from_file_location("build_name_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    name_index = mod.PARAMS.index("--name") + 1
    assert mod.PARAMS[name_index] == "AITextOptimizer"
