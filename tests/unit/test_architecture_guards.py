# -*- coding: utf-8 -*-
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _iter_python_files(*relative_dirs: str):
    for relative_dir in relative_dirs:
        base_dir = PROJECT_ROOT / relative_dir
        for path in base_dir.rglob("*.py"):
            if "__pycache__" not in path.parts:
                yield path


def test_worker_and_shared_layers_do_not_import_master_code():
    scanned_files = list(_iter_python_files("apps/worker", "packages/shared", "packages/engine"))
    violations = []

    for path in scanned_files:
        content = path.read_text(encoding="utf-8")
        if "apps.master" in content:
            violations.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert violations == [], f"发现跨层反向依赖: {violations}"


def test_runtime_config_is_loaded_only_via_shared_runtime_module():
    allowed_paths = {
        "packages/shared/settings/runtime.py",
        "packages/engine/src/core/processor_config.py",
    }
    violations = []

    for path in _iter_python_files("apps", "packages"):
        rel_path = path.relative_to(PROJECT_ROOT).as_posix()
        if rel_path in allowed_paths:
            continue

        content = path.read_text(encoding="utf-8")
        if "yaml.safe_load" in content or "configs/application.yml" in content or "APPLICATION_CONFIG_PATH" in content:
            violations.append(rel_path)

    assert violations == [], f"发现绕过共享 runtime 的配置读取: {violations}"


def test_worker_runtime_has_no_sys_path_mutation():
    violations = []

    for path in _iter_python_files("apps/worker"):
        content = path.read_text(encoding="utf-8")
        if "sys.path.insert" in content or "sys.path.append" in content:
            violations.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert violations == [], f"发现 Worker 运行时路径注入: {violations}"


def test_engine_core_does_not_import_top_level_workflow_engine_wrapper():
    violations = []

    for path in _iter_python_files("packages/engine/src"):
        content = path.read_text(encoding="utf-8")
        if "from workflow_engine import" in content or "import workflow_engine" in content:
            violations.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert violations == [], f"发现 engine 内部仍依赖顶层 workflow_engine 兼容入口: {violations}"


def test_engine_examples_and_tools_have_no_sys_path_mutation():
    allowed_paths = {
        "packages/engine/workflow_engine.py",
        "tests/unit/engine/test_processor_package_discovery.py",
    }
    violations = []

    for path in list(_iter_python_files("packages/engine/examples")) + list(_iter_python_files("packages/engine/src/tools")):
        rel_path = path.relative_to(PROJECT_ROOT).as_posix()
        if rel_path in allowed_paths:
            continue

        content = path.read_text(encoding="utf-8")
        if "sys.path.insert" in content or "sys.path.append" in content:
            violations.append(rel_path)

    assert violations == [], f"发现 engine 示例或工具脚本仍在修改 sys.path: {violations}"
