#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import httpx


BASE_URL = os.getenv("MASTER_SMOKE_BASE_URL", "http://127.0.0.1:18100").rstrip("/")
WORKER_HEALTH_URL = os.getenv("WORKER_HEALTH_URL", "http://127.0.0.1:18080/health")
TIMEOUT_SECONDS = int(os.getenv("SMOKE_TIMEOUT_SECONDS", "60"))
MASTER_API_TOKEN = os.getenv("MASTER_API_TOKEN", "").strip()
REPORT_DIR = Path(os.getenv("REAL_SMOKE_REPORT_DIR", "deployments/logs/real-smoke"))


def auth_headers() -> Dict[str, str]:
    if not MASTER_API_TOKEN:
        return {}
    return {"X-Master-Token": MASTER_API_TOKEN}


def require_ok(response: httpx.Response, message: str) -> None:
    if response.status_code != 200:
        raise RuntimeError(f"{message}: HTTP {response.status_code} - {response.text}")


def write_report(name: str, payload: Dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = REPORT_DIR / f"{timestamp}-{name}.json"
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def wait_terminal_status(client: httpx.Client, tracer_id: str, *, timeout_seconds: int) -> Dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_payload: Dict[str, Any] | None = None
    while time.time() < deadline:
        response = client.get(f"/workflow/{tracer_id}/status", headers=auth_headers())
        require_ok(response, f"查询工作流状态失败 tracer_id={tracer_id}")
        payload = response.json()
        last_payload = payload
        status = payload.get("data", {}).get("status")
        if status in {"success", "failed", "timeout", "cancelled"}:
            return payload
        time.sleep(1)
    raise RuntimeError(f"任务在超时前未达到终态 tracer_id={tracer_id}: last={last_payload}")


def run_case(client: httpx.Client, *, name: str, workflow: Dict[str, Any], variables: Dict[str, Any] | None = None) -> None:
    run_id = f"smoke-{name}-{uuid.uuid4().hex[:8]}"
    request_body = {
        "runId": run_id,
        "workflow": workflow,
        "globalVariables": variables or {},
    }
    submit_payload: Dict[str, Any] | None = None
    tracer_id = ""
    task_id = ""
    final_payload: Dict[str, Any] | None = None
    run_id_payload: Dict[str, Any] | None = None
    try:
        print(f"[case:{name}] submit runId={run_id}")
        response = client.post("/workflow/debug/execute", json=request_body, headers=auth_headers())
        require_ok(response, f"提交任务失败 case={name}")
        submit_payload = response.json()
        if submit_payload.get("code") != 200:
            raise RuntimeError(f"提交任务失败 case={name}: {submit_payload}")

        tracer_id = submit_payload["data"]["tracerId"]
        task_id = submit_payload["data"]["task_id"]
        final_payload = wait_terminal_status(client, tracer_id=tracer_id, timeout_seconds=TIMEOUT_SECONDS)
        final_data = final_payload.get("data", {})
        final_status = final_data.get("status")
        if final_status != "success":
            raise RuntimeError(f"任务执行失败 case={name}: {json.dumps(final_payload, ensure_ascii=False)}")

        print(
            f"[case:{name}] ok task_id={task_id} tracer_id={tracer_id} "
            f"worker_id={final_data.get('worker_id')} progress={final_data.get('progress')}"
        )

        run_id_response = client.get(f"/workflow/{run_id}/status", headers=auth_headers())
        require_ok(run_id_response, f"按 runId 查询失败 case={name}")
        run_id_payload = run_id_response.json()
        if run_id_payload.get("code") != 200:
            raise RuntimeError(f"按 runId 查询失败 case={name}: {run_id_payload}")
    except Exception as exc:
        report_path = write_report(
            name,
            {
                "case": name,
                "run_id": run_id,
                "task_id": task_id,
                "tracer_id": tracer_id,
                "request": request_body,
                "submit_payload": submit_payload,
                "final_payload": final_payload,
                "run_id_payload": run_id_payload,
                "error": str(exc),
            },
        )
        raise RuntimeError(f"{exc} | failure_report={report_path}") from exc


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        master_health = client.get("/health")
        require_ok(master_health, "Master 健康检查失败")
        worker_health = httpx.get(WORKER_HEALTH_URL, timeout=10.0)
        require_ok(worker_health, "Worker 健康检查失败")

        workers_response = client.get("/workers", headers=auth_headers())
        require_ok(workers_response, "查询 Worker 列表失败")
        workers_payload = workers_response.json()
        worker_total = workers_payload.get("data", {}).get("total", 0)
        print(f"[env] master={BASE_URL} worker_health={WORKER_HEALTH_URL} worker_total={worker_total}")
        if worker_total != 1:
            print("[warn] 当前活跃 Worker 数量不是 1，结果可能受旧进程干扰", file=sys.stderr)

        run_case(
            client,
            name="empty",
            workflow={
                "id": "smoke-empty-workflow",
                "nodes": [],
                "edges": [],
            },
            variables={"case": "empty"},
        )
        run_case(
            client,
            name="log-message",
            workflow={
                "id": "smoke-log-workflow",
                "nodes": [
                    {
                        "id": "log_1",
                        "type": "log_message",
                        "name": "记录消息",
                        "data": {
                            "config": {
                                "message": "smoke log node: ${case}",
                                "level": "info",
                            }
                        },
                        "position": {"x": 100, "y": 100},
                    }
                ],
                "edges": [],
            },
            variables={"case": "log-message"},
        )
        run_case(
            client,
            name="http-request",
            workflow={
                "id": "smoke-http-workflow",
                "nodes": [
                    {
                        "id": "http_health",
                        "type": "http_request",
                        "name": "调用健康接口",
                        "data": {
                            "config": {
                                "url": f"{BASE_URL}/health",
                                "method": "GET",
                                "headers": {"Accept": "application/json"},
                                "timeout": 10,
                                "verify_ssl": False,
                            }
                        },
                        "position": {"x": 100, "y": 100},
                    }
                ],
                "edges": [],
            },
            variables={"case": "http-request"},
        )

    print("[done] real workflow smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
