# -*- coding: utf-8 -*-
"""
@author Fred.fan
@date 2025-10-14
@packageName master.app.api.request
@className TaskRouter
@describe 任务查询接口 - 主从架构任务状态查询
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from apps.master.infrastructure.db.database_async import get_db_read, get_db_write
from packages.shared.responses.base_resp import success_response, error_response
from apps.master.infrastructure.redis.redis_client import get_redis_client
from apps.master.application.services.task_repository import get_task_repository
from packages.shared.logging.log_component import LOGGER
from apps.master.api.routes.auth_guard import require_master_auth
from apps.master.application.services.workflow_service import WorkflowService

app = APIRouter(dependencies=[Depends(require_master_auth)])


@app.get("/task/{task_id}/status", tags=['任务管理'], summary="查询任务状态")
async def get_task_status(task_id: str, db_read: AsyncSession = Depends(get_db_read)):
    """
    查询任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    try:
        # 1. 优先从Redis查询
        redis_client = await get_redis_client()
        task_info = await redis_client.get_task_status(task_id)
        
        if task_info:
            return success_response({
                "task_id": task_id,
                "status": task_info.get("status"),
                "progress": int(task_info.get("progress", 0)),
                "worker_id": task_info.get("worker_id", ""),
                "started_at": task_info.get("started_at", ""),
                "finished_at": task_info.get("finished_at", ""),
                "source": "redis"
            })
        
        # 2. Redis未命中,查询数据库
        task_repo = get_task_repository()
        task_data = await task_repo.query_task_by_id(db_read, task_id)
        
        if task_data:
            return success_response({
                **task_data,
                "source": "database"
            })
        
        return error_response(code=404, message=f"Task {task_id} not found")
        
    except Exception as e:
        LOGGER.logger.error(f"Query task status error: {e}")
        return error_response(code=500, message=f"Query failed: {str(e)}")


@app.get("/task/{task_id}/result", tags=['任务管理'], summary="查询任务结果")
async def get_task_result(task_id: str, db_read: AsyncSession = Depends(get_db_read)):
    """
    查询任务结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务执行结果
    """
    try:
        from sqlalchemy import text
        
        # 查询任务结果
        sql = text("""
            SELECT task_id, worker_id, status, duration, result, 
                   error_message, stack_trace, created_at
            FROM task_result
            WHERE task_id = :task_id
        """)
        
        result = await db_read.execute(sql, {"task_id": task_id})
        row = result.fetchone()
        
        if row:
            import json
            return success_response({
                "task_id": row[0],
                "worker_id": row[1],
                "status": row[2],
                "duration": float(row[3]) if row[3] else 0,
                "result": json.loads(row[4]) if row[4] else {},
                "error_message": row[5],
                "stack_trace": row[6],
                "created_at": row[7].isoformat() if row[7] else ""
            })
        
        return error_response(code=404, message=f"Task result {task_id} not found")
        
    except Exception as e:
        LOGGER.logger.error(f"Query task result error: {e}")
        return error_response(code=500, message=f"Query failed: {str(e)}")


@app.get("/workers", tags=['任务管理'], summary="查询所有执行机状态")
async def get_workers():
    """
    查询所有执行机状态
    
    Returns:
        执行机列表
    """
    try:
        redis_client = await get_redis_client()
        workers = await redis_client.get_all_workers()
        
        worker_list = []
        for worker_id, worker_info in workers.items():
            worker_list.append({
                "worker_id": worker_id,
                "status": worker_info.get("status"),
                "current_tasks": int(worker_info.get("current_tasks", 0)),
                "max_tasks": int(worker_info.get("max_tasks", 5)),
                "cpu_usage": float(worker_info.get("cpu_usage", 0)),
                "memory_usage": float(worker_info.get("memory_usage", 0)),
                "ip": worker_info.get("ip", ""),
                "last_heartbeat": worker_info.get("last_heartbeat", "")
            })
        
        return success_response({
            "workers": worker_list,
            "total": len(worker_list)
        })
        
    except Exception as e:
        LOGGER.logger.error(f"Query workers error: {e}")
        return error_response(code=500, message=f"Query failed: {str(e)}")


@app.get("/queue/status", tags=['任务管理'], summary="查询队列状态")
async def get_queue_status(db_read: AsyncSession = Depends(get_db_read)):
    """
    查询队列状态
    
    Returns:
        队列统计信息
    """
    try:
        from sqlalchemy import text
        
        # 查询各状态任务数量
        sql = text("""
            SELECT status, COUNT(*) as count
            FROM task_execution
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
            GROUP BY status
        """)
        
        result = await db_read.execute(sql)
        rows = result.fetchall()
        
        status_count = {
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "cancelled": 0,
        }
        
        for row in rows:
            status = row[0]
            count = row[1]
            if status in status_count:
                status_count[status] = count
        
        return success_response({
            "pending": status_count["pending"],
            "running": status_count["running"],
            "completed": status_count["success"] + status_count["failed"] + status_count["timeout"],
            "success": status_count["success"],
            "failed": status_count["failed"],
            "timeout": status_count["timeout"],
            "cancelled": status_count["cancelled"],
            "total": sum(status_count.values())
        })
        
    except Exception as e:
        LOGGER.logger.error(f"Query queue status error: {e}")
        return error_response(code=500, message=f"Query failed: {str(e)}")


@app.post("/task/{task_id}/cancel", tags=['任务管理'], summary="取消待执行任务")
async def cancel_task(task_id: str, db_write: AsyncSession = Depends(get_db_write)):
    try:
        result = await WorkflowService.cancel_task(db_write, task_id)
        if not result["found"]:
            return error_response(code=404, message=f"Task {task_id} not found")
        if not result["cancelled"]:
            return error_response(
                code=409,
                message=f"Task {task_id} cannot be cancelled from status {result['status']}",
            )
        return success_response({"task_id": task_id, "status": "cancelled"}, message="任务已取消")
    except Exception as e:
        LOGGER.logger.error(f"Cancel task error: {e}")
        return error_response(code=500, message=f"Cancel failed: {str(e)}")


@app.post("/task/{task_id}/retry", tags=['任务管理'], summary="重试失败任务")
async def retry_task(task_id: str, db_write: AsyncSession = Depends(get_db_write)):
    try:
        result = await WorkflowService.retry_task(db_write, task_id)
        if not result["found"]:
            return error_response(code=404, message=f"Task {task_id} not found")
        if not result["retried"]:
            if result.get("reason") == "max_retries":
                return error_response(code=409, message=f"Task {task_id} has reached max retries")
            return error_response(
                code=409,
                message=f"Task {task_id} cannot be retried from status {result['status']}",
            )
        return success_response(
            {"task_id": task_id, "status": "pending", "retry_count": result["retry_count"]},
            message="任务已重新入队",
        )
    except Exception as e:
        LOGGER.logger.error(f"Retry task error: {e}")
        return error_response(code=500, message=f"Retry failed: {str(e)}")
