# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from apps.master.api.routes.task_router import (
    get_task_status,
    get_task_result,
    get_workers,
    get_queue_status,
    cancel_task,
    retry_task,
)


def test_get_task_status_prefers_redis_source():
    async def _run():
        redis = AsyncMock()
        redis.get_task_status = AsyncMock(
            return_value={
                "status": "running",
                "progress": "30",
                "worker_id": "worker-1",
                "started_at": "2026-04-17T10:00:00",
                "finished_at": "",
            }
        )

        with patch(
            "apps.master.api.routes.task_router.get_redis_client",
            new=AsyncMock(return_value=redis),
        ):
            with patch(
                "apps.master.api.routes.task_router.get_task_repository",
            ) as get_repo:
                response = await get_task_status("task-1", db_read=AsyncMock())

        assert response.code == 200
        assert response.data["source"] == "redis"
        assert response.data["status"] == "running"
        assert response.data["progress"] == 30
        get_repo.assert_not_called()

    asyncio.run(_run())


def test_get_task_status_falls_back_to_database_source():
    async def _run():
        redis = AsyncMock()
        redis.get_task_status = AsyncMock(return_value=None)

        repo = AsyncMock()
        repo.query_task_by_id = AsyncMock(
            return_value={
                "task_id": "task-2",
                "status": "success",
                "progress": 100,
                "worker_id": "worker-2",
            }
        )

        with patch(
            "apps.master.api.routes.task_router.get_redis_client",
            new=AsyncMock(return_value=redis),
        ):
            with patch(
                "apps.master.api.routes.task_router.get_task_repository",
                return_value=repo,
            ):
                response = await get_task_status("task-2", db_read=AsyncMock())

        assert response.code == 200
        assert response.data["source"] == "database"
        assert response.data["status"] == "success"
        repo.query_task_by_id.assert_awaited_once()

    asyncio.run(_run())


def test_cancel_task_marks_pending_task_cancelled():
    async def _run():
        with patch(
            "apps.master.api.routes.task_router.WorkflowService.cancel_task",
            new=AsyncMock(return_value={"found": True, "cancelled": True, "status": "cancelled"}),
        ):
            response = await cancel_task("task-3", db_write=AsyncMock())

        assert response.code == 200
        assert response.data["task_id"] == "task-3"
        assert response.data["status"] == "cancelled"

    asyncio.run(_run())


def test_cancel_task_rejects_non_pending_status():
    async def _run():
        with patch(
            "apps.master.api.routes.task_router.WorkflowService.cancel_task",
            new=AsyncMock(return_value={"found": True, "cancelled": False, "status": "running"}),
        ):
            response = await cancel_task("task-4", db_write=AsyncMock())

        assert response.code == 409
        assert "cannot be cancelled" in response.message

    asyncio.run(_run())


def test_retry_task_requeues_retryable_task():
    async def _run():
        with patch(
            "apps.master.api.routes.task_router.WorkflowService.retry_task",
            new=AsyncMock(return_value={"found": True, "retried": True, "retry_count": 2}),
        ):
            response = await retry_task("task-5", db_write=AsyncMock())

        assert response.code == 200
        assert response.data["task_id"] == "task-5"
        assert response.data["status"] == "pending"
        assert response.data["retry_count"] == 2

    asyncio.run(_run())


def test_retry_task_rejects_when_max_retries_reached():
    async def _run():
        with patch(
            "apps.master.api.routes.task_router.WorkflowService.retry_task",
            new=AsyncMock(
                return_value={"found": True, "retried": False, "status": "failed", "reason": "max_retries"}
            ),
        ):
            response = await retry_task("task-6", db_write=AsyncMock())

        assert response.code == 409
        assert "max retries" in response.message

    asyncio.run(_run())


def test_get_task_result_returns_result_payload():
    async def _run():
        db_read = AsyncMock()
        result = MagicMock()
        result.fetchone.return_value = (
            "task-r-1",
            "worker-1",
            "success",
            1.5,
            '{"hello":"world"}',
            "",
            "",
            datetime(2026, 4, 17, 12, 0, 0),
        )
        db_read.execute = AsyncMock(return_value=result)

        response = await get_task_result("task-r-1", db_read=db_read)

        assert response.code == 200
        assert response.data["task_id"] == "task-r-1"
        assert response.data["worker_id"] == "worker-1"
        assert response.data["status"] == "success"
        assert response.data["duration"] == 1.5
        assert response.data["result"] == {"hello": "world"}

    asyncio.run(_run())


def test_get_task_result_returns_404_when_missing():
    async def _run():
        db_read = AsyncMock()
        result = MagicMock()
        result.fetchone.return_value = None
        db_read.execute = AsyncMock(return_value=result)

        response = await get_task_result("task-r-2", db_read=db_read)

        assert response.code == 404
        assert "not found" in response.message

    asyncio.run(_run())


def test_get_workers_returns_worker_list():
    async def _run():
        redis = AsyncMock()
        redis.get_all_workers = AsyncMock(
            return_value={
                "worker-1": {
                    "status": "busy",
                    "current_tasks": "2",
                    "max_tasks": "5",
                    "cpu_usage": "11.5",
                    "memory_usage": "42.0",
                    "ip": "10.0.0.1",
                    "last_heartbeat": "1710000000",
                }
            }
        )

        with patch(
            "apps.master.api.routes.task_router.get_redis_client",
            new=AsyncMock(return_value=redis),
        ):
            response = await get_workers()

        assert response.code == 200
        assert response.data["total"] == 1
        assert response.data["workers"][0]["worker_id"] == "worker-1"
        assert response.data["workers"][0]["current_tasks"] == 2
        assert response.data["workers"][0]["cpu_usage"] == 11.5

    asyncio.run(_run())


def test_get_queue_status_aggregates_counts():
    async def _run():
        db_read = AsyncMock()
        result = MagicMock()
        result.fetchall.return_value = [
            ("pending", 3),
            ("running", 2),
            ("success", 4),
            ("failed", 1),
            ("timeout", 1),
            ("cancelled", 2),
        ]
        db_read.execute = AsyncMock(return_value=result)

        response = await get_queue_status(db_read=db_read)

        assert response.code == 200
        assert response.data["pending"] == 3
        assert response.data["running"] == 2
        assert response.data["success"] == 4
        assert response.data["failed"] == 1
        assert response.data["timeout"] == 1
        assert response.data["cancelled"] == 2
        assert response.data["completed"] == 6
        assert response.data["total"] == 13

    asyncio.run(_run())
