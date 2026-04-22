# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class TaskRepository(ABC):
    """任务仓储接口。"""

    @abstractmethod
    async def save_task(
        self,
        db: AsyncSession,
        task_id: str,
        parent_task_id: str,
        task_type: str,
        priority: str,
        status: str,
        payload: Dict[str, Any],
        created_by: str = "",
        retry_count: int = 0,
        max_retries: int = 3,
        timeout: int = 300,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: str,
        status: str,
        worker_id: str = "",
        progress: int = 0,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_message: str = "",
        retry_count: int | None = None,
        max_retries: int | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def query_task_by_id(self, db: AsyncSession, task_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def query_workflow_task_by_run_id(self, db: AsyncSession, run_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def query_tasks_by_parent_id(self, db: AsyncSession, parent_task_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError
