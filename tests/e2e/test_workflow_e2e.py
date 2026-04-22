# -*- coding: utf-8 -*-
import uuid

import httpx

from tests.e2e._helpers import (
    auth_headers,
    base_url,
    poll_task_status,
    query_task_row,
    redis_client,
    require_business_e2e_enabled,
)


def test_workflow_debug_execute_e2e():
    require_business_e2e_enabled()

    run_id = f"e2e-{uuid.uuid4()}"
    request_body = {
        "runId": run_id,
        "workflow": {
            "id": "e2e-empty-workflow",
            "nodes": [],
            "edges": [],
        },
        "globalVariables": {
            "case": "e2e",
        },
    }

    with httpx.Client(base_url=base_url(), timeout=10.0) as client:
        submit_response = client.post("/workflow/debug/execute", json=request_body, headers=auth_headers())
        assert submit_response.status_code == 200, submit_response.text
        submit_payload = submit_response.json()
        assert submit_payload["code"] == 200, submit_payload

        task_id = submit_payload["data"]["task_id"]
        tracer_id = submit_payload["data"]["tracerId"]

        task_status_payload = poll_task_status(client, task_id)
        workflow_status_response = client.get(f"/workflow/{tracer_id}/status", headers=auth_headers())

    final_status = task_status_payload["data"]["status"]
    assert final_status == "success", task_status_payload
    assert workflow_status_response.status_code == 200, workflow_status_response.text
    workflow_payload = workflow_status_response.json()
    assert workflow_payload["code"] == 200, workflow_payload
    assert workflow_payload["data"]["status"] == "success"

    db_row = query_task_row(task_id)
    assert db_row is not None
    assert db_row["status"] == "success"
    assert db_row["progress"] == 100

    redis_task = redis_client().hgetall(f"task:{task_id}")
    assert redis_task.get("status") == "success"
    assert redis_task.get("progress") == "100"
