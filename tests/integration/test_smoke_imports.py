# -*- coding: utf-8 -*-
import importlib


def test_master_app_smoke_import():
    module = importlib.import_module("apps.master.main")
    assert hasattr(module, "app")
    assert len(module.app.router.routes) >= 3


def test_worker_entrypoint_smoke_import():
    module = importlib.import_module("apps.worker.main")
    assert callable(module.main)


def test_engine_import_compatibility_smoke():
    package_module = importlib.import_module("packages.engine.workflow_engine")
    assert hasattr(package_module, "WorkflowExecutor")
