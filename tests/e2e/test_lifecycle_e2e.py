# -*- coding: utf-8 -*-
import uuid

import httpx

from tests.e2e._helpers import (
    auth_headers,
    base_url,
    insert_running_task,
    poll_task_status,
    poll_task_status_value,
    query_task_row,
    redis_client,
    require_business_e2e_enabled,
)


def test_failed_workflow_can_be_retried_e2e():
    require_business_e2e_enabled()

    run_id = f"e2e-failed-{uuid.uuid4()}"
    request_body = {
        "runId": run_id,
        "workflow": {
            "id": "e2e-invalid-workflow",
            "nodes": [
                {
                    "id": "bad-node",
                    "type": "unsupported_node_type",
                    "data": {"label": "bad-node", "config": {}},
                }
            ],
            "edges": [],
        },
    }

    with httpx.Client(base_url=base_url(), timeout=10.0) as client:
        submit_response = client.post("/workflow/debug/execute", json=request_body, headers=auth_headers())
        assert submit_response.status_code == 200, submit_response.text
        submit_payload = submit_response.json()
        task_id = submit_payload["data"]["task_id"]

        first_terminal = poll_task_status(client, task_id)
        assert first_terminal["data"]["status"] == "failed", first_terminal

        retry_response = client.post(f"/task/{task_id}/retry", headers=auth_headers())
        assert retry_response.status_code == 200, retry_response.text
        retry_payload = retry_response.json()
        assert retry_payload["code"] == 200, retry_payload
        assert retry_payload["data"]["retry_count"] == 1

        pending_payload = poll_task_status_value(client, task_id, "pending", timeout_seconds=15)
        assert pending_payload["data"]["status"] == "pending"

        second_terminal = poll_task_status(client, task_id)
        assert second_terminal["data"]["status"] == "failed", second_terminal

    db_row = query_task_row(task_id)
    assert db_row is not None
    assert db_row["status"] == "failed"
    assert db_row["retry_count"] == 1


def test_stale_running_task_is_recovered_to_pending_e2e():
    require_business_e2e_enabled()

    task_id = f"e2e-recover-{uuid.uuid4()}"
    dead_worker_id = "worker-dead-e2e"

    insert_running_task(task_id, worker_id=dead_worker_id)
    redis_cli = redis_client()
    redis_cli.hset(
        f"task:{task_id}",
        mapping={
            "status": "running",
            "progress": "10",
            "worker_id": dead_worker_id,
            "started_at": "2026-01-01T00:00:00",
            "finished_at": "",
            "error_message": "",
        },
    )
    redis_cli.delete(f"worker:{dead_worker_id}")

    with httpx.Client(base_url=base_url(), timeout=10.0) as client:
        recovered = poll_task_status_value(client, task_id, "pending", timeout_seconds=45)

    assert recovered["data"]["status"] == "pending"
    assert recovered["data"]["progress"] == 0

    db_row = query_task_row(task_id)
    assert db_row is not None
    assert db_row["status"] == "pending"
    assert db_row["worker_id"] == ""
    assert db_row["progress"] == 0
