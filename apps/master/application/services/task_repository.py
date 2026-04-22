# -*- coding: utf-8 -*-
from __future__ import annotations

from apps.master.domain.repositories.task_repository import TaskRepository
from apps.master.infrastructure.db.repositories.task_repository import SQLAlchemyTaskRepository


def get_task_repository() -> TaskRepository:
    return SQLAlchemyTaskRepository()
