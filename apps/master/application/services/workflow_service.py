import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.master.infrastructure.kafka.kafka_producer import get_kafka_producer
from apps.master.infrastructure.redis.redis_client import get_redis_client
from apps.master.application.use_cases.task_splitter import TaskSplitter
from apps.master.application.services.task_repository import get_task_repository
from packages.shared.logging.log_component import LOGGER
from packages.shared.settings.runtime import get_primary_db_url


@dataclass
class SingleWorkflowSubmitResult:
    tracer_id: str
    task_id: str


@dataclass
class BatchWorkflowSubmitResult:
    tracer_id: str
    total_tasks: int
    tasks: List[Any]


class WorkflowService:
    RETRYABLE_STATUSES = {"failed", "timeout", "cancelled"}

    @staticmethod
    async def _mark_task_cancelled_in_redis(task_id: str, redis_client, *, error_message: str) -> None:
        finished_at = datetime.now().isoformat()
        await redis_client.set_task_status(task_id=task_id, status="cancelled", progress=100, finished_at=finished_at)
        await redis_client.update_task_field(task_id, "error_message", error_message)

    @staticmethod
    async def _reset_task_for_retry_in_redis(task_id: str, redis_client) -> None:
        await redis_client.set_task_status(task_id=task_id, status="pending", progress=0)
        await redis_client.update_task_field(task_id, "worker_id", "")
        await redis_client.update_task_field(task_id, "started_at", "")
        await redis_client.update_task_field(task_id, "finished_at", "")
        await redis_client.update_task_field(task_id, "error_message", "")

    @classmethod
    async def cancel_task(cls, db_write: AsyncSession, task_id: str) -> Dict[str, Any]:
        task_repository = get_task_repository()
        task_data = await task_repository.query_task_by_id(db_write, task_id)
        if not task_data:
            return {"found": False, "cancelled": False, "status": None}

        current_status = task_data.get("status", "")
        if current_status != "pending":
            return {"found": True, "cancelled": False, "status": current_status}

        finished_at = datetime.now()
        cancel_message = "Task cancelled before execution"
        await task_repository.update_task_status(
            db=db_write,
            task_id=task_id,
            status="cancelled",
            progress=100,
            finished_at=finished_at,
            error_message=cancel_message,
        )
        await db_write.commit()

        redis_client = await get_redis_client()
        await cls._mark_task_cancelled_in_redis(task_id, redis_client, error_message=cancel_message)
        return {"found": True, "cancelled": True, "status": "cancelled"}

    @classmethod
    async def cancel_batch_tasks(cls, db_write: AsyncSession, tracer_id: str) -> Dict[str, Any]:
        task_repository = get_task_repository()
        tasks = await task_repository.query_tasks_by_parent_id(db_write, tracer_id)
        if not tasks:
            return {"found": False, "cancelled": 0, "skipped": 0, "total": 0}

        redis_client = await get_redis_client()
        cancelled = 0
        skipped = 0
        finished_at = datetime.now()
        cancel_message = "Task cancelled before execution"

        for task in tasks:
            task_id = task.get("task_id")
            if task.get("status") != "pending":
                skipped += 1
                continue

            await task_repository.update_task_status(
                db=db_write,
                task_id=task_id,
                status="cancelled",
                progress=100,
                finished_at=finished_at,
                error_message=cancel_message,
            )
            await cls._mark_task_cancelled_in_redis(task_id, redis_client, error_message=cancel_message)
            cancelled += 1

        await db_write.commit()
        return {"found": True, "cancelled": cancelled, "skipped": skipped, "total": len(tasks)}

    @classmethod
    async def retry_task(cls, db_write: AsyncSession, task_id: str) -> Dict[str, Any]:
        task_repository = get_task_repository()
        task_data = await task_repository.query_task_by_id(db_write, task_id)
        if not task_data:
            return {"found": False, "retried": False, "status": None}

        current_status = task_data.get("status", "")
        retry_count = int(task_data.get("retry_count", 0) or 0)
        max_retries = int(task_data.get("max_retries", 0) or 0)
        if current_status not in cls.RETRYABLE_STATUSES:
            return {"found": True, "retried": False, "status": current_status, "reason": "status"}
        if retry_count >= max_retries:
            return {"found": True, "retried": False, "status": current_status, "reason": "max_retries"}

        next_retry_count = retry_count + 1
        await task_repository.update_task_status(
            db=db_write,
            task_id=task_id,
            status="pending",
            worker_id="",
            progress=0,
            started_at=None,
            finished_at=None,
            error_message="",
            retry_count=next_retry_count,
        )
        await db_write.commit()

        redis_client = await get_redis_client()
        await cls._reset_task_for_retry_in_redis(task_id, redis_client)

        kafka_producer = await get_kafka_producer()
        try:
            await kafka_producer.send_task(
                task_id=task_data["task_id"],
                parent_task_id=task_data["parent_task_id"],
                task_type=task_data["task_type"],
                priority=task_data["priority"],
                payload=task_data["payload"],
                created_by=task_data.get("created_by", ""),
                retry_count=next_retry_count,
                max_retries=max_retries,
                timeout=int(task_data.get("timeout", 300) or 300),
                use_workflow_topic=task_data.get("task_type") == "workflow",
            )
        except Exception as exc:
            error_message = f"Retry dispatch failed: {exc}"
            await task_repository.update_task_status(
                db=db_write,
                task_id=task_id,
                status="failed",
                progress=100,
                error_message=error_message,
                retry_count=next_retry_count,
            )
            await db_write.commit()
            await redis_client.set_task_status(task_id=task_id, status="failed", progress=100)
            await redis_client.update_task_field(task_id, "error_message", error_message)
            raise

        return {"found": True, "retried": True, "retry_count": next_retry_count}

    @classmethod
    async def retry_batch_tasks(cls, db_write: AsyncSession, tracer_id: str) -> Dict[str, Any]:
        task_repository = get_task_repository()
        tasks = await task_repository.query_tasks_by_parent_id(db_write, tracer_id)
        if not tasks:
            return {"found": False, "retried": 0, "skipped": 0, "total": 0}

        retryable_tasks = []
        for task in tasks:
            status = task.get("status")
            retry_count = int(task.get("retry_count", 0) or 0)
            max_retries = int(task.get("max_retries", 0) or 0)
            if status in cls.RETRYABLE_STATUSES and retry_count < max_retries:
                retryable_tasks.append(task)

        skipped = len(tasks) - len(retryable_tasks)
        if not retryable_tasks:
            return {"found": True, "retried": 0, "skipped": skipped, "total": len(tasks)}

        redis_client = await get_redis_client()
        batch_tasks = []
        for task in retryable_tasks:
            next_retry_count = int(task.get("retry_count", 0) or 0) + 1
            await task_repository.update_task_status(
                db=db_write,
                task_id=task["task_id"],
                status="pending",
                worker_id="",
                progress=0,
                started_at=None,
                finished_at=None,
                error_message="",
                retry_count=next_retry_count,
            )
            await cls._reset_task_for_retry_in_redis(task["task_id"], redis_client)
            batch_tasks.append(
                {
                    "task_id": task["task_id"],
                    "parent_task_id": task["parent_task_id"],
                    "task_type": task["task_type"],
                    "priority": task["priority"],
                    "payload": task["payload"],
                    "created_by": task.get("created_by", ""),
                    "retry_count": next_retry_count,
                    "max_retries": int(task.get("max_retries", 3) or 3),
                    "timeout": int(task.get("timeout", 300) or 300),
                    "use_workflow_topic": task.get("task_type") == "workflow",
                }
            )
        await db_write.commit()

        kafka_producer = await get_kafka_producer()
        send_result = await kafka_producer.send_tasks_batch(batch_tasks)
        if send_result.get("failed", 0) > 0:
            failed_task_map = {task["task_id"]: task for task in retryable_tasks}
            failed_tasks = [
                failed_task_map[detail["task_id"]]
                for detail in send_result.get("details", [])
                if detail.get("status") == "failed" and detail.get("task_id") in failed_task_map
            ]
            if failed_tasks:
                await cls._mark_tasks_dispatch_failed(
                    db=db_write,
                    tasks=[
                        type("TaskRef", (), {"task_id": task["task_id"]})()
                        for task in failed_tasks
                    ],
                    error_message=f"Retry dispatch failed for {len(failed_tasks)} task(s)",
                )
                await cls._mark_failed_tasks_in_redis(
                    tasks=[
                        type("TaskRef", (), {"task_id": task["task_id"]})()
                        for task in failed_tasks
                    ],
                    redis_client=redis_client,
                    error_message=f"Retry dispatch failed for {len(failed_tasks)} task(s)",
                )

        return {
            "found": True,
            "retried": send_result.get("success", 0),
            "skipped": skipped + send_result.get("failed", 0),
            "total": len(tasks),
        }

    @staticmethod
    async def _mark_tasks_dispatch_failed(db: AsyncSession, tasks: List[Any], error_message: str) -> None:
        task_repository = get_task_repository()
        for task in tasks:
            await task_repository.update_task_status(
                db=db,
                task_id=task.task_id,
                status="failed",
                error_message=error_message,
            )
        await db.commit()

    @staticmethod
    async def _mark_failed_tasks_in_redis(tasks: List[Any], redis_client, error_message: str) -> None:
        for task in tasks:
            await redis_client.set_task_status(task_id=task.task_id, status="failed", progress=0)
            await redis_client.update_task_field(task.task_id, "error_message", error_message)

    @classmethod
    async def _handle_batch_dispatch_failure(
        cls,
        async_session,
        redis_client,
        tasks: List[Any],
        error_message: str,
    ) -> None:
        if not tasks:
            return

        async with async_session() as db:
            await cls._mark_tasks_dispatch_failed(db=db, tasks=tasks, error_message=error_message)

        await cls._mark_failed_tasks_in_redis(
            tasks=tasks,
            redis_client=redis_client,
            error_message=error_message,
        )

    @staticmethod
    def validate_workflow_data(workflow_data: Dict[str, Any], index: int | None = None) -> None:
        if not workflow_data:
            prefix = f"第 {index + 1} 个" if index is not None else ""
            raise ValueError(f"{prefix}工作流数据不能为空")
        if "nodes" not in workflow_data or "edges" not in workflow_data:
            prefix = f"第 {index + 1} 个" if index is not None else ""
            raise ValueError(f"{prefix}工作流数据必须包含 nodes 和 edges 字段")

    @classmethod
    async def submit_single_workflow(
        cls,
        db_write: AsyncSession,
        run_id: str,
        workflow: Dict[str, Any],
        variables: Dict[str, Any] | None,
        author: str,
    ) -> SingleWorkflowSubmitResult:
        cls.validate_workflow_data(workflow)

        task_splitter = TaskSplitter()
        task = await task_splitter.create_workflow_task(
            run_id=run_id,
            workflow=workflow,
            variables=variables,
            priority="normal",
            created_by=author,
        )

        task_repository = get_task_repository()
        save_success = await task_repository.save_task(
            db_write,
            task_id=task.task_id,
            parent_task_id=task.parent_task_id,
            task_type=task.task_type,
            priority=task.priority,
            status="pending",
            payload=task.payload,
            created_by=task.created_by,
        )
        if not save_success:
            raise RuntimeError(f"保存任务失败: task_id={task.task_id}")
        await db_write.commit()

        redis_client = await get_redis_client()
        await redis_client.set_task_status(task_id=task.task_id, status="pending", progress=0)

        kafka_producer = await get_kafka_producer()
        await kafka_producer.send_task(
            task_id=task.task_id,
            parent_task_id=task.parent_task_id,
            task_type=task.task_type,
            priority=task.priority,
            payload=task.payload,
            created_by=task.created_by,
            use_workflow_topic=True,
        )

        return SingleWorkflowSubmitResult(tracer_id=task.task_id, task_id=task.task_id)

    @classmethod
    async def submit_batch_workflows(
        cls,
        workflows: List[Dict[str, Any]],
        priority: str,
        author: str,
        report_id: str | None,
    ) -> BatchWorkflowSubmitResult:
        tracer_id = str(uuid.uuid4())
        task_splitter = TaskSplitter()
        tasks = await task_splitter.split_batch_workflow(
            workflows=workflows,
            priority=priority or "normal",
            created_by=author,
            parent_task_id=tracer_id,
            report_id=report_id,
        )
        if not tasks:
            raise ValueError("未生成任何任务")

        redis_client = await get_redis_client()
        await redis_client.set_task_status(task_id=tracer_id, status="pending", progress=0)
        return BatchWorkflowSubmitResult(tracer_id=tracer_id, total_tasks=len(tasks), tasks=tasks)

    @classmethod
    async def process_batch_tasks_async(cls, tasks, tracer_id) -> None:
        batch_size = 100
        total_tasks = len(tasks)
        LOGGER.logger.info(
            f"开始批量处理任务: tracer_id={tracer_id}, total={total_tasks}, batch_size={batch_size}"
        )

        kafka_producer = await get_kafka_producer()
        redis_client = await get_redis_client()
        engine = create_async_engine(get_primary_db_url())
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        try:
            for i in range(0, total_tasks, batch_size):
                batch = tasks[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_tasks + batch_size - 1) // batch_size
                LOGGER.logger.info(f"处理批次 {batch_num}/{total_batches}: {len(batch)} 个任务")

                try:
                    async with async_session() as db:
                        task_repository = get_task_repository()
                        for task in batch:
                            ok = await task_repository.save_task(
                                db,
                                task_id=task.task_id,
                                parent_task_id=task.parent_task_id,
                                task_type=task.task_type,
                                priority=task.priority,
                                status="pending",
                                payload=task.payload,
                                created_by=task.created_by,
                            )
                            if not ok:
                                raise RuntimeError(f"批次保存任务失败: task_id={task.task_id}")
                        await db.commit()

                    for task in batch:
                        await redis_client.set_task_status(
                            task_id=task.task_id, status="pending", progress=0
                        )

                    batch_tasks = [
                        {
                            "task_id": task.task_id,
                            "parent_task_id": task.parent_task_id,
                            "task_type": task.task_type,
                            "priority": task.priority,
                            "payload": task.payload,
                            "created_by": task.created_by,
                            "use_workflow_topic": True,
                        }
                        for task in batch
                    ]
                    send_result = await kafka_producer.send_tasks_batch(batch_tasks)
                    LOGGER.logger.info(
                        f"批次 {batch_num} Kafka发送结果: 成功={send_result['success']}, 失败={send_result['failed']}"
                    )
                    if send_result.get("failed", 0) > 0:
                        failed_task_map = {task.task_id: task for task in batch}
                        failed_tasks = [
                            failed_task_map[detail["task_id"]]
                            for detail in send_result.get("details", [])
                            if detail.get("status") == "failed" and detail.get("task_id") in failed_task_map
                        ]
                        if failed_tasks:
                            error_message = f"Kafka dispatch failed for {len(failed_tasks)} task(s)"
                            await cls._handle_batch_dispatch_failure(
                                async_session=async_session,
                                redis_client=redis_client,
                                tasks=failed_tasks,
                                error_message=error_message,
                            )
                            LOGGER.logger.warning(
                                f"批次 {batch_num} 有 {len(failed_tasks)} 个任务发送失败，已标记为 failed"
                            )
                    LOGGER.logger.info(f"批次 {batch_num}/{total_batches} 处理完成")

                    if i + batch_size < total_tasks:
                        await asyncio.sleep(0.1)
                except Exception as exc:
                    LOGGER.logger.error(f"批次 {batch_num} 处理失败: {exc}", exc_info=True)
                    await cls._handle_batch_dispatch_failure(
                        async_session=async_session,
                        redis_client=redis_client,
                        tasks=batch,
                        error_message=f"Kafka dispatch aborted: {exc}",
                    )
        finally:
            await engine.dispose()
