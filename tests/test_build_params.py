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
    assert f"prompt_templates.json{sep}." in joined
    assert f"config.example.json{sep}." in joined
    # 旧 bug：两边都是 :
    if sys.platform == "win32":
        assert "prompt_templates.json:." not in joined
