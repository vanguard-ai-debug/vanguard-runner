# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.master.application.use_cases.task_splitter import Task as SplitTask
from apps.master.application.services.workflow_service import WorkflowService


def test_validate_workflow_data_empty():
    with pytest.raises(ValueError, match="工作流数据不能为空"):
        WorkflowService.validate_workflow_data({})


def test_validate_workflow_data_missing_edges():
    with pytest.raises(ValueError, match="nodes 和 edges"):
        WorkflowService.validate_workflow_data({"nodes": []}, index=2)


def test_submit_batch_raises_when_no_tasks():
    async def _run():
        with patch("apps.master.application.services.workflow_service.TaskSplitter") as ts_cls:
            ts_cls.return_value.split_batch_workflow = AsyncMock(return_value=[])
            with pytest.raises(ValueError, match="未生成任何任务"):
                await WorkflowService.submit_batch_workflows(
                    workflows=[
                        {"workflow": {"nodes": [], "edges": []}, "runId": "r1", "variables": {}}
                    ],
                    priority="normal",
                    author="tester",
                    report_id=None,
                )

    asyncio.run(_run())


def test_submit_single_save_fails_skips_downstream():
    async def _run():
        wf = {"nodes": [], "edges": [], "id": "w1"}
        task_obj = SplitTask(
            task_id="tid-1",
            parent_task_id="pid-1",
            task_type="workflow",
            priority="normal",
            payload={"k": 1},
            created_at=datetime.now(),
            created_by="u1",
        )
        db = AsyncMock()
        db.commit = AsyncMock()
        repo = AsyncMock()
        repo.save_task = AsyncMock(return_value=False)

        with patch("apps.master.application.services.workflow_service.TaskSplitter") as ts_cls:
            ts_cls.return_value.create_workflow_task = AsyncMock(return_value=task_obj)
            with patch(
                "apps.master.application.services.workflow_service.get_task_repository",
                return_value=repo,
            ):
                with patch("apps.master.application.services.workflow_service.get_redis_client") as gr:
                    with patch("apps.master.application.services.workflow_service.get_kafka_producer") as gk:
                        with pytest.raises(RuntimeError, match="保存任务失败"):
                            await WorkflowService.submit_single_workflow(
                                db_write=db,
                                run_id="run-1",
                                workflow=wf,
                                variables={},
                                author="u1",
                            )
                        db.commit.assert_not_called()
                        gr.assert_not_called()
                        gk.assert_not_called()

    asyncio.run(_run())


def test_submit_single_success_commits_and_sends():
    async def _run():
        wf = {"nodes": [], "edges": [], "id": "w1"}
        task_obj = SplitTask(
            task_id="tid-2",
            parent_task_id="pid-2",
            task_type="workflow",
            priority="normal",
            payload={"runId": "run-2"},
            created_at=datetime.now(),
            created_by="u2",
        )
        db = AsyncMock()
        db.commit = AsyncMock()

        redis = AsyncMock()
        redis.set_task_status = AsyncMock()
        kafka = AsyncMock()
        kafka.send_task = AsyncMock()
        repo = AsyncMock()
        repo.save_task = AsyncMock(return_value=True)

        with patch("apps.master.application.services.workflow_service.TaskSplitter") as ts_cls:
            ts_cls.return_value.create_workflow_task = AsyncMock(return_value=task_obj)
            with patch(
                "apps.master.application.services.workflow_service.get_task_repository",
                return_value=repo,
            ):
                with patch(
                    "apps.master.application.services.workflow_service.get_redis_client",
                    new=AsyncMock(return_value=redis),
                ):
                    with patch(
                        "apps.master.application.services.workflow_service.get_kafka_producer",
                        new=AsyncMock(return_value=kafka),
                    ):
                        result = await WorkflowService.submit_single_workflow(
                            db_write=db,
                            run_id="run-2",
                            workflow=wf,
                            variables={"a": 1},
                            author="u2",
                        )

        assert result.tracer_id == "tid-2"
        assert result.task_id == "tid-2"
        db.commit.assert_awaited_once()
        redis.set_task_status.assert_awaited_once()
        kafka.send_task.assert_awaited_once()

    asyncio.run(_run())


class _FakeAsyncSessionCM:
    def __init__(self, db):
        self._db = db

    async def __aenter__(self):
        return self._db

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_process_batch_tasks_async_one_batch():
    async def _run():
        task_obj = SplitTask(
            task_id="b1",
            parent_task_id="tracer-x",
            task_type="workflow",
            priority="normal",
            payload={},
            created_at=datetime.now(),
            created_by="u",
        )

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        def fake_sessionmaker(*_a, **_k):
            def factory():
                return _FakeAsyncSessionCM(mock_db)

            return factory

        redis = AsyncMock()
        redis.set_task_status = AsyncMock()
        redis.update_task_field = AsyncMock()
        kafka = AsyncMock()
        kafka.send_tasks_batch = AsyncMock(return_value={"success": 1, "failed": 0})
        repo = AsyncMock()
        repo.save_task = AsyncMock(return_value=True)

        with patch("apps.master.application.services.workflow_service.create_async_engine", return_value=mock_engine):
            with patch("apps.master.application.services.workflow_service.async_sessionmaker", side_effect=fake_sessionmaker):
                with patch(
                    "apps.master.application.services.workflow_service.get_redis_client",
                    new=AsyncMock(return_value=redis),
                ):
                    with patch(
                        "apps.master.application.services.workflow_service.get_kafka_producer",
                        new=AsyncMock(return_value=kafka),
                    ):
                        with patch(
                            "apps.master.application.services.workflow_service.get_task_repository",
                            return_value=repo,
                        ):
                            await WorkflowService.process_batch_tasks_async([task_obj], "tracer-x")

        mock_engine.dispose.assert_awaited()
        mock_db.commit.assert_awaited()
        kafka.send_tasks_batch.assert_awaited()
        assert redis.set_task_status.await_count >= 1

    asyncio.run(_run())


def test_process_batch_tasks_async_marks_failed_tasks_when_kafka_partial_failure():
    async def _run():
        task_ok = SplitTask(
            task_id="b-ok",
            parent_task_id="tracer-y",
            task_type="workflow",
            priority="normal",
            payload={},
            created_at=datetime.now(),
            created_by="u",
        )
        task_failed = SplitTask(
            task_id="b-failed",
            parent_task_id="tracer-y",
            task_type="workflow",
            priority="normal",
            payload={},
            created_at=datetime.now(),
            created_by="u",
        )

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        def fake_sessionmaker(*_a, **_k):
            def factory():
                return _FakeAsyncSessionCM(mock_db)

            return factory

        redis = AsyncMock()
        redis.set_task_status = AsyncMock()
        redis.update_task_field = AsyncMock()
        kafka = AsyncMock()
        kafka.send_tasks_batch = AsyncMock(
            return_value={
                "success": 1,
                "failed": 1,
                "details": [
                    {"task_id": "b-ok", "status": "success"},
                    {"task_id": "b-failed", "status": "failed", "error": "broker down"},
                ],
            }
        )
        repo = AsyncMock()
        repo.save_task = AsyncMock(return_value=True)
        repo.update_task_status = AsyncMock(return_value=True)

        with patch("apps.master.application.services.workflow_service.create_async_engine", return_value=mock_engine):
            with patch("apps.master.application.services.workflow_service.async_sessionmaker", side_effect=fake_sessionmaker):
                with patch(
                    "apps.master.application.services.workflow_service.get_redis_client",
                    new=AsyncMock(return_value=redis),
                ):
                    with patch(
                        "apps.master.application.services.workflow_service.get_kafka_producer",
                        new=AsyncMock(return_value=kafka),
                    ):
                        with patch(
                            "apps.master.application.services.workflow_service.get_task_repository",
                            return_value=repo,
                        ):
                            update_status = repo.update_task_status
                            await WorkflowService.process_batch_tasks_async(
                                [task_ok, task_failed],
                                "tracer-y",
                            )

        update_status.assert_awaited_once()
        _, kwargs = update_status.await_args
        assert kwargs["task_id"] == "b-failed"
        assert kwargs["status"] == "failed"
        redis.update_task_field.assert_awaited_once_with(
            "b-failed",
            "error_message",
            "Kafka dispatch failed for 1 task(s)",
        )
        mock_engine.dispose.assert_awaited()

    asyncio.run(_run())


def test_process_batch_tasks_async_marks_whole_batch_failed_when_dispatch_raises():
    async def _run():
        tasks = [
            SplitTask(
                task_id="b1",
                parent_task_id="tracer-z",
                task_type="workflow",
                priority="normal",
                payload={},
                created_at=datetime.now(),
                created_by="u",
            ),
            SplitTask(
                task_id="b2",
                parent_task_id="tracer-z",
                task_type="workflow",
                priority="normal",
                payload={},
                created_at=datetime.now(),
                created_by="u",
            ),
        ]

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        def fake_sessionmaker(*_a, **_k):
            def factory():
                return _FakeAsyncSessionCM(mock_db)

            return factory

        redis = AsyncMock()
        redis.set_task_status = AsyncMock()
        redis.update_task_field = AsyncMock()
        kafka = AsyncMock()
        kafka.send_tasks_batch = AsyncMock(side_effect=RuntimeError("broker unavailable"))
        repo = AsyncMock()
        repo.save_task = AsyncMock(return_value=True)
        repo.update_task_status = AsyncMock(return_value=True)

        with patch("apps.master.application.services.workflow_service.create_async_engine", return_value=mock_engine):
            with patch("apps.master.application.services.workflow_service.async_sessionmaker", side_effect=fake_sessionmaker):
                with patch(
                    "apps.master.application.services.workflow_service.get_redis_client",
                    new=AsyncMock(return_value=redis),
                ):
                    with patch(
                        "apps.master.application.services.workflow_service.get_kafka_producer",
                        new=AsyncMock(return_value=kafka),
                    ):
                        with patch(
                            "apps.master.application.services.workflow_service.get_task_repository",
                            return_value=repo,
                        ):
                            update_status = repo.update_task_status
                            await WorkflowService.process_batch_tasks_async(tasks, "tracer-z")

        assert update_status.await_count == 2
        assert redis.update_task_field.await_count == 2
        mock_engine.dispose.assert_awaited()

    asyncio.run(_run())


def test_retry_task_requeues_failed_task():
    async def _run():
        db = AsyncMock()
        db.commit = AsyncMock()
        repo = AsyncMock()
        repo.query_task_by_id = AsyncMock(
            return_value={
                "task_id": "task-r1",
                "parent_task_id": "tracer-r1",
                "task_type": "workflow",
                "priority": "normal",
                "payload": {"workflow": {"nodes": [], "edges": []}},
                "status": "failed",
                "retry_count": 0,
                "max_retries": 3,
                "timeout": 300,
                "created_by": "tester",
            }
        )
        repo.update_task_status = AsyncMock(return_value=True)
        redis = AsyncMock()
        redis.set_task_status = AsyncMock()
        redis.update_task_field = AsyncMock()
        kafka = AsyncMock()
        kafka.send_task = AsyncMock()

        with patch(
            "apps.master.application.services.workflow_service.get_task_repository",
            return_value=repo,
        ), patch(
            "apps.master.application.services.workflow_service.get_redis_client",
            new=AsyncMock(return_value=redis),
        ), patch(
            "apps.master.application.services.workflow_service.get_kafka_producer",
            new=AsyncMock(return_value=kafka),
        ):
            result = await WorkflowService.retry_task(db, "task-r1")

        assert result == {"found": True, "retried": True, "retry_count": 1}
        kafka.send_task.assert_awaited_once()
        repo.update_task_status.assert_awaited_once()
        db.commit.assert_awaited_once()

    asyncio.run(_run())


def test_retry_task_rejects_when_max_retries_reached():
    async def _run():
        db = AsyncMock()
        repo = AsyncMock()
        repo.query_task_by_id = AsyncMock(
            return_value={
                "task_id": "task-r2",
                "status": "failed",
                "retry_count": 3,
                "max_retries": 3,
            }
        )

        with patch(
            "apps.master.application.services.workflow_service.get_task_repository",
            return_value=repo,
        ):
            result = await WorkflowService.retry_task(db, "task-r2")

        assert result == {"found": True, "retried": False, "status": "failed", "reason": "max_retries"}

    asyncio.run(_run())


def test_retry_batch_tasks_only_requeues_retryable_items():
    async def _run():
        db = AsyncMock()
        db.commit = AsyncMock()
        repo = AsyncMock()
        repo.query_tasks_by_parent_id = AsyncMock(
            return_value=[
                {
                    "task_id": "task-b1",
                    "parent_task_id": "tracer-b",
                    "task_type": "workflow",
                    "priority": "normal",
                    "payload": {"workflow": {"nodes": [], "edges": []}},
                    "status": "failed",
                    "retry_count": 0,
                    "max_retries": 3,
                    "timeout": 300,
                    "created_by": "tester",
                },
                {
                    "task_id": "task-b2",
                    "parent_task_id": "tracer-b",
                    "task_type": "workflow",
                    "priority": "normal",
                    "payload": {"workflow": {"nodes": [], "edges": []}},
                    "status": "success",
                    "retry_count": 0,
                    "max_retries": 3,
                    "timeout": 300,
                    "created_by": "tester",
                },
            ]
        )
        repo.update_task_status = AsyncMock(return_value=True)
        redis = AsyncMock()
        redis.set_task_status = AsyncMock()
        redis.update_task_field = AsyncMock()
        kafka = AsyncMock()
        kafka.send_tasks_batch = AsyncMock(
            return_value={"success": 1, "failed": 0, "details": [{"task_id": "task-b1", "status": "success"}]}
        )

        with patch(
            "apps.master.application.services.workflow_service.get_task_repository",
            return_value=repo,
        ), patch(
            "apps.master.application.services.workflow_service.get_redis_client",
            new=AsyncMock(return_value=redis),
        ), patch(
            "apps.master.application.services.workflow_service.get_kafka_producer",
            new=AsyncMock(return_value=kafka),
        ):
            result = await WorkflowService.retry_batch_tasks(db, "tracer-b")

        assert result == {"found": True, "retried": 1, "skipped": 1, "total": 2}
        kafka.send_tasks_batch.assert_awaited_once()
        repo.update_task_status.assert_awaited_once()
        db.commit.assert_awaited_once()

    asyncio.run(_run())
