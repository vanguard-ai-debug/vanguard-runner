# -*- coding: utf-8 -*-
"""
任务拆分器（精简版）：仅支持 workflow 任务创建与批量拆分。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from packages.shared.logging.log_component import LOGGER


@dataclass
class Task:
    """任务数据类"""

    task_id: str
    parent_task_id: str
    task_type: str
    priority: str
    payload: Dict[str, Any]
    created_at: datetime
    created_by: str = ""


class TaskSplitter:
    """仅 workflow：单任务创建 + 批量子任务拆分"""

    def _get_priority(self, priority_str: str) -> str:
        priority_map = {"urgent": "urgent", "high": "high", "normal": "normal"}
        return priority_map.get((priority_str or "normal").lower(), "normal")

    async def split_batch_workflow(
        self,
        workflows: List[Dict[str, Any]],
        priority: str = "normal",
        created_by: str = "",
        parent_task_id: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> List[Task]:
        if parent_task_id is None:
            parent_task_id = str(uuid.uuid4())
        tasks: List[Task] = []

        LOGGER.logger.info(
            f"拆分批量工作流: parent_task_id={parent_task_id}, count={len(workflows)}, report_id={report_id}"
        )

        for workflow_item in workflows:
            tasks.append(
                Task(
                    task_id=str(uuid.uuid4()),
                    parent_task_id=parent_task_id,
                    task_type="workflow",
                    priority=self._get_priority(priority),
                    payload={
                        "workflow": workflow_item.get("workflow"),
                        "environment": workflow_item.get("environment"),
                        "variables": workflow_item.get("variables", {}),
                        "runId": workflow_item.get("runId"),
                        "reportId": report_id,
                    },
                    created_at=datetime.now(),
                    created_by=created_by,
                )
            )

        LOGGER.logger.info(f"批量工作流拆分完成: sub_tasks={len(tasks)}")
        return tasks

    async def create_workflow_task(
        self,
        workflow: Dict[str, Any],
        run_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        created_by: str = "",
    ) -> Task:
        task_id = str(uuid.uuid4())
        LOGGER.logger.info(f"创建工作流任务: task_id={task_id}, workflow_id={workflow.get('id', 'unknown')}")

        return Task(
            task_id=task_id,
            parent_task_id=task_id,
            task_type="workflow",
            priority=self._get_priority(priority),
            payload={
                "runId": run_id,
                "workflow": workflow,
                "variables": variables or {},
            },
            created_at=datetime.now(),
            created_by=created_by,
        )
