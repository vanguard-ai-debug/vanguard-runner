# -*- coding: utf-8 -*-
"""
@author Fred.fan
@date 2025-10-14
@packageName master.app.models
@className TaskExecution
@describe 任务执行记录模型 - task_execution 表的 ORM 映射
"""
from sqlalchemy import Column, DateTime, Integer, JSON, String, Index
from sqlalchemy.dialects.mysql import VARCHAR
from apps.master.infrastructure.db.database_async import AsyncBase

__all__ = ["TaskExecution"]


class TaskExecution(AsyncBase):
    """任务执行记录表"""
    __tablename__ = 'task_execution'
    
    # 主键
    task_id = Column(String(64), primary_key=True, comment='任务ID')
    
    # 关联字段
    parent_task_id = Column(String(64), nullable=True, index=True, comment='父任务ID')
    
    # 任务基本信息
    task_type = Column(String(32), nullable=False, comment='任务类型')
    priority = Column(String(16), nullable=False, comment='优先级')
    status = Column(String(16), nullable=False, index=True, comment='状态')
    
    # 任务数据
    payload = Column(JSON, nullable=False, comment='任务数据（JSON格式）')
    
    # 执行信息
    worker_id = Column(String(64), nullable=True, comment='执行机ID')
    progress = Column(Integer, default=0, comment='进度（0-100）')
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment='重试次数')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    
    # 超时设置
    timeout = Column(Integer, default=300, comment='超时时间（秒）')
    
    # 错误信息
    error_message = Column(String(1024), nullable=True, comment='错误信息')
    
    # 用户信息
    created_by = Column(String(128), nullable=True, comment='创建人')
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, comment='创建时间')
    started_at = Column(DateTime, nullable=True, comment='开始时间')
    finished_at = Column(DateTime, nullable=True, comment='完成时间')
    
    # 索引
    __table_args__ = (
        Index('idx_parent_task_id', 'parent_task_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )

