# -*- coding: utf-8 -*-
"""
@author Jan
@date 2025-01-13
@packageName master.app.api.request
@className WorkflowRouter
@describe Workflow 执行接口 - 遵循 Master-Worker 架构
"""
import json
import os

from fastapi import APIRouter, Request, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.responses.base_resp import success_response, error_response, BaseRespModel
from packages.shared.logging.log_component import LOGGER
from packages.shared.settings.runtime import LOG_DIR
from packages.contracts.workflow_models import BatchWorkflowExecuteRequest, \
    WorkflowDebugExecuteRequest, WorkflowRunResultCallbackModel
from apps.master.infrastructure.db.database_async import get_db_write, get_db_read

from apps.master.infrastructure.redis.redis_client import get_redis_client
from apps.master.application.services.task_repository import get_task_repository
from fastapi.responses import StreamingResponse
from apps.master.api.routes.auth_guard import require_master_auth
from apps.master.application.services.workflow_service import WorkflowService

app = APIRouter(dependencies=[Depends(require_master_auth)])


async def _resolve_workflow_task_identifier(db_read: AsyncSession, tracer_id: str):
    task_repo = get_task_repository()
    task_data = await task_repo.query_task_by_id(db_read, tracer_id)
    if task_data:
        return tracer_id, task_data

    task_data = await task_repo.query_workflow_task_by_run_id(db_read, tracer_id)
    if task_data:
        return task_data.get("task_id"), task_data

    return None, None


@app.post("/workflow/debug/execute", tags=["工作流管理"], response_model=BaseRespModel, summary="调试工作流")
async def execute_workflow(
    request_data: WorkflowDebugExecuteRequest,
    request: Request,
    db_write: AsyncSession = Depends(get_db_write)
):
    """
    执行工作流 - 通过 Kafka 和执行机异步执行
    
    遵循 Master-Worker 架构：
    1. Master 端：创建任务并发送到 Kafka
    2. Worker 端：消费任务并执行工作流
    
    Args:
        request_data: 工作流执行请求，包含工作流定义、环境、变量等
        request: FastAPI Request 对象
        db_write: 数据库写入会话
        
    Returns:
        任务ID（tracerId），可用于查询执行状态和结果
    """
    author = request.state.user.username if hasattr(request.state, "user") else 'system'

    try:
        workflow_data = request_data.workflow
        WorkflowService.validate_workflow_data(workflow_data)
        LOGGER.logger.info(f"开始创建工作流任务: workflow_id={workflow_data.get('workflowId', 'unknown')}")
    except ValueError as e:
        LOGGER.logger.warning(f"工作流参数校验失败: {e}")
        return error_response(code=400, message=f"参数校验失败: {e}")

    try:
        submit_result = await WorkflowService.submit_single_workflow(
            db_write=db_write,
            run_id=request_data.run_id,
            workflow=request_data.workflow,
            variables=request_data.global_variables or {},
            author=author,
        )

        LOGGER.logger.info(
            f"工作流任务创建成功: task_id={submit_result.task_id}, tracerId={submit_result.tracer_id}"
        )

        return success_response({
            "tracerId": submit_result.tracer_id,
            "task_id": submit_result.task_id,
            "message": "工作流任务已提交，正在执行中"
        }, message="工作流任务提交成功")

    except ValueError as e:
        LOGGER.logger.error(f"工作流任务创建失败 - 参数错误: {str(e)}")
        return error_response(code=400, message=f"参数错误: {str(e)}")
    except Exception as e:
        LOGGER.logger.error(f"工作流任务创建失败: {str(e)}", exc_info=True)
        return error_response(code=500, message=f"工作流任务创建失败: {str(e)}")


@app.get("/workflow/{tracer_id}/status", tags=["工作流管理"], response_model=BaseRespModel, summary="查询工作流执行状态")
async def get_workflow_status(
    tracer_id: str,
    db_read: AsyncSession = Depends(get_db_read)
):
    """
    查询工作流执行状态 - 实时获取工作流的详细执行信息
    
    支持通过tracerId查询工作流的执行状态，包括：
    - 整体执行状态（pending/running/success/failed）
    - 执行进度
    - 每个步骤的详细执行信息（节点ID、状态、输出、错误等）
    - 执行时间和统计信息
    
    Args:
        tracer_id: 工作流追踪ID（即parent_task_id/task_id）
        db_read: 数据库读取会话
        
    Returns:
        工作流执行状态和详细结果
    """
    try:

        redis_client = await get_redis_client()
        
        resolved_task_id = tracer_id

        # 1. 优先从Redis查询（实时状态）
        task_info = await redis_client.get_task_status(resolved_task_id)
        
        if not task_info:
            # 2. Redis未命中，从数据库查询
            resolved_task_id, task_data = await _resolve_workflow_task_identifier(db_read, tracer_id)
            
            if not task_data:
                return error_response(code=404, message=f"工作流任务 {tracer_id} 不存在")
            
            # 构建基本状态信息
            return success_response({
                "tracer_id": tracer_id,
                "task_id": task_data.get("task_id"),
                "status": task_data.get("status", "unknown"),
                "progress": task_data.get("progress", 0),
                "worker_id": task_data.get("worker_id", ""),
                "started_at": task_data.get("started_at", ""),
                "finished_at": task_data.get("finished_at", ""),
                "source": "database",
                "result": None  # 数据库中没有保存详细结果
            })

        else:
            resolved_task_id, task_data = await _resolve_workflow_task_identifier(db_read, tracer_id)
            if resolved_task_id:
                task_info = task_info
            else:
                task_data = None
                resolved_task_id = tracer_id
        
        # 3. 从Redis读取详细结果（workflow专用）
        result_json = None
        try:
            result_field = await redis_client.client.hget(f"task:{resolved_task_id}", "result")
            if result_field:
                if isinstance(result_field, bytes):
                    result_json = json.loads(result_field.decode('utf-8'))
                else:
                    result_json = json.loads(result_field)
        except (json.JSONDecodeError, AttributeError) as e:
            LOGGER.logger.warning(f"Failed to parse workflow result from Redis: {e}")
            result_json = None
        
        # 4. 构建响应数据
        response_data = {
            "tracer_id": tracer_id,
            "task_id": resolved_task_id,
            "status": task_info.get("status", "unknown").decode('utf-8') if isinstance(task_info.get("status"), bytes) else task_info.get("status", "unknown"),
            "progress": int(task_info.get("progress", 0).decode('utf-8')) if isinstance(task_info.get("progress"), bytes) else int(task_info.get("progress", 0)),
            "worker_id": task_info.get("worker_id", b"").decode('utf-8') if isinstance(task_info.get("worker_id"), bytes) else task_info.get("worker_id", ""),
            "started_at": task_info.get("started_at", b"").decode('utf-8') if isinstance(task_info.get("started_at"), bytes) else task_info.get("started_at", ""),
            "finished_at": task_info.get("finished_at", b"").decode('utf-8') if isinstance(task_info.get("finished_at"), bytes) else task_info.get("finished_at", ""),
            "source": "redis",
            "result": result_json  # 详细的步骤执行结果
        }
        
        return success_response(response_data, message="查询成功")
        
    except Exception as e:
        LOGGER.logger.error(f"查询工作流状态失败: {str(e)}", exc_info=True)
        return error_response(code=500, message=f"查询失败: {str(e)}")

@app.post("/workflow/execute/batch", tags=["工作流管理"], response_model=BaseRespModel, summary="批量执行工作流")
async def batch_execute_workflow(
    request_data: BatchWorkflowExecuteRequest,
    request: Request,
    background_task: BackgroundTasks,
):
    """
    批量执行工作流 - 支持执行上千条工作流
    
    性能优化：
    1. 使用BackgroundTasks异步处理，API立即返回
    2. 分批处理任务，避免一次性处理太多导致超时
    3. 异步发送到Kafka，不阻塞主流程
    
    Args:
        request_data: 批量工作流执行请求
        request: FastAPI Request 对象
        background_task: 后台任务
        db_write: 数据库写入会话
        
    Returns:
        追踪ID（tracerId），可用于查询批量执行状态
    """
    try:
        if not request_data.workflows:
            return error_response(code=400, message="工作流列表不能为空")

        max_batch_size = request_data.max_batch_size or 1000
        if len(request_data.workflows) > max_batch_size:
            return error_response(
                code=400, 
                message=f"单次批量执行数量不能超过 {max_batch_size}，当前为 {len(request_data.workflows)}。请分批提交。"
            )
        for idx, workflow_item in enumerate(request_data.workflows):
            WorkflowService.validate_workflow_data(workflow_item.workflow, idx)

        author = request.state.user.username if hasattr(request.state, "user") else 'system'

        workflows_list = [
            {
                "workflow": item.workflow,
                "variables": item.variables or {},
                "runId": item.run_id
            }
            for item in request_data.workflows
        ]

        batch_result = await WorkflowService.submit_batch_workflows(
            workflows=workflows_list,
            priority=request_data.priority or "normal",
            author=author,
            report_id=request_data.report_id,
        )

        background_task.add_task(
            WorkflowService.process_batch_tasks_async,
            batch_result.tasks,
            batch_result.tracer_id,
        )
        LOGGER.logger.info(
            f"批量工作流任务已提交后台处理: tracer_id={batch_result.tracer_id}, task_count={batch_result.total_tasks}"
        )

        return success_response({
            "tracerId": batch_result.tracer_id,
            "total_tasks": batch_result.total_tasks,
            "message": f"已提交 {batch_result.total_tasks} 个工作流任务，正在后台处理中"
        }, message="批量工作流任务提交成功")
        
    except ValueError as e:
        LOGGER.logger.error(f"批量工作流任务创建失败 - 参数错误: {str(e)}")
        return error_response(code=400, message=f"参数错误: {str(e)}")
    except Exception as e:
        LOGGER.logger.error(f"批量工作流任务创建失败: {str(e)}", exc_info=True)
        return error_response(code=500, message=f"批量工作流任务创建失败: {str(e)}")


@app.get("/workflow/{tracerId}/batch/status", tags=["工作流管理"], response_model=BaseRespModel, summary="查询批量工作流执行状态")
async def get_batch_workflow_status(
    tracerId: str,
    db_read: AsyncSession = Depends(get_db_read)
):
    """
    查询批量工作流执行状态 - 获取批量任务的总体执行情况
    
    Args:
        tracerId: 批量任务追踪ID（parent_task_id）
        db_read: 数据库读取会话
        
    Returns:
        批量任务执行统计信息
    """
    try:
        redis_client = await get_redis_client()
        
        # 1. 使用 TaskRepository 查询所有子任务
        task_repository = get_task_repository()
        tasks_data = await task_repository.query_tasks_by_parent_id(db_read, tracerId)
        
        if not tasks_data:
            return error_response(code=404, message=f"批量任务 {tracerId} 不存在")
        
        # 2. 统计各状态任务数量
        status_count = {
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "cancelled": 0,
        }
        
        tasks_detail = []
        for task_data in tasks_data:
            status = task_data.get("status", "pending")
            if status in status_count:
                status_count[status] += 1
            
            tasks_detail.append({
                "task_id": task_data.get("task_id"),
                "status": status,
                "progress": task_data.get("progress", 0),
                "started_at": task_data.get("started_at") if task_data.get("started_at") else None,
                "finished_at": task_data.get("finished_at") if task_data.get("finished_at") else None,
                "worker_id": task_data.get("worker_id", ""),
                "error_message": task_data.get("error_message")
            })
        
        total = len(tasks_detail)
        completed = (
            status_count["success"]
            + status_count["failed"]
            + status_count["timeout"]
            + status_count["cancelled"]
        )
        success_rate = (status_count["success"] / total * 100) if total > 0 else 0
        
        # 3. 判断整体状态
        if status_count["running"] > 0 or status_count["pending"] > 0:
            overall_status = "running"
        elif status_count["cancelled"] == total:
            overall_status = "cancelled"
        elif status_count["failed"] > 0 or status_count["timeout"] > 0:
            overall_status = "completed_with_errors" if (status_count["success"] > 0 or status_count["cancelled"] > 0) else "failed"
        elif status_count["cancelled"] > 0:
            overall_status = "completed_with_cancellations" if status_count["success"] > 0 else "cancelled"
        else:
            overall_status = "success"
        
        # 4. 计算总体进度
        total_progress = sum(task["progress"] for task in tasks_detail) / total if total > 0 else 0
        
        return success_response({
            "tracer_id": tracerId,
            "overall_status": overall_status,
            "total": total,
            "completed": completed,
            "progress": round(total_progress, 2),
            "success_rate": round(success_rate, 2),
            "status_count": status_count,
            "tasks": tasks_detail[:100],  # 只返回前100个任务的详情，避免响应过大
            "has_more": len(tasks_detail) > 100
        }, message="查询成功")
        
    except Exception as e:
        LOGGER.logger.error(f"查询批量工作流状态失败: {str(e)}", exc_info=True)
        return error_response(code=500, message=f"查询失败: {str(e)}")


@app.post("/workflow/{tracerId}/batch/cancel", tags=["工作流管理"], response_model=BaseRespModel, summary="取消批量工作流中的待执行任务")
async def cancel_batch_workflow(
    tracerId: str,
    db_write: AsyncSession = Depends(get_db_write),
):
    try:
        result = await WorkflowService.cancel_batch_tasks(db_write, tracerId)
        if not result["found"]:
            return error_response(code=404, message=f"批量任务 {tracerId} 不存在")
        return success_response(
            {
                "tracer_id": tracerId,
                "cancelled": result["cancelled"],
                "skipped": result["skipped"],
                "total": result["total"],
            },
            message="批量任务取消处理完成",
        )
    except Exception as e:
        LOGGER.logger.error(f"取消批量工作流失败: {str(e)}", exc_info=True)
        return error_response(code=500, message=f"取消失败: {str(e)}")


@app.post("/workflow/{tracerId}/batch/retry", tags=["工作流管理"], response_model=BaseRespModel, summary="重试批量工作流中的失败任务")
async def retry_batch_workflow(
    tracerId: str,
    db_write: AsyncSession = Depends(get_db_write),
):
    try:
        result = await WorkflowService.retry_batch_tasks(db_write, tracerId)
        if not result["found"]:
            return error_response(code=404, message=f"批量任务 {tracerId} 不存在")
        return success_response(
            {
                "tracer_id": tracerId,
                "retried": result["retried"],
                "skipped": result["skipped"],
                "total": result["total"],
            },
            message="批量任务重试处理完成",
        )
    except Exception as e:
        LOGGER.logger.error(f"重试批量工作流失败: {str(e)}", exc_info=True)
        return error_response(code=500, message=f"重试失败: {str(e)}")


@app.get("/workflow/{tracerId}/console", tags=["工作流管理"], summary="获取工作流实时日志")
async def get_workflow_console_log(tracerId: str):
    """
    获取工作流实时执行日志
    
    支持流式输出，实时显示工作流执行日志和节点执行过程。
    日志内容包括：
    - 工作流开始/结束
    - 每个节点的执行开始/结束
    - 节点输入输出数据
    - 执行错误信息
    
    Args:
        tracerId: 工作流追踪ID（parent_task_id 或 task_id）
        
    Returns:
        流式响应，返回纯文本格式的日志内容
    """
    import asyncio
    from fastapi.responses import StreamingResponse

    log_file_path = os.path.join(LOG_DIR, f"{tracerId}.log")
    
    async def log_stream():
        """
        异步流式读取日志文件
        动态检测日志写入完成状态
        """
        max_wait_file = 300  # 等待文件创建最多5分钟
        wait_interval = 0.2  # 每次检查间隔0.2秒
        elapsed_time = 0
        
        # 等待文件存在且有内容
        while elapsed_time < max_wait_file:
            if os.path.exists(log_file_path):
                file_size = os.path.getsize(log_file_path)
                if file_size > 0:
                    break
            await asyncio.sleep(wait_interval)
            elapsed_time += wait_interval
        
        if not os.path.exists(log_file_path):
            yield "日志文件不存在，可能任务未开始执行\n"
            return
        
        try:
            # 流式读取并实时返回日志内容
            last_position = 0
            accumulated_content = ""  # 累积读取的内容，用于检测结束标记
            
            while True:
                if os.path.exists(log_file_path):
                    current_size = os.path.getsize(log_file_path)
                    
                    if current_size > last_position:
                        # 有新内容，读取并返回
                        try:
                            with open(log_file_path, "r", encoding="utf-8") as log_file:
                                log_file.seek(last_position)
                                new_content = log_file.read()
                                if new_content:
                                    yield new_content
                                    accumulated_content += new_content
                                    last_position = current_size
                                    
                                    # 检测是否包含结束标记
                                    if f"任务完成: {tracerId}" in accumulated_content or \
                                       "Console log handler removed" in accumulated_content or \
                                       "工作流执行完成" in accumulated_content:
                                        # 发现结束标记，再等待一小段时间确保所有内容都被写入
                                        await asyncio.sleep(1)
                                        # 读取剩余内容
                                        if os.path.exists(log_file_path):
                                            final_size = os.path.getsize(log_file_path)
                                            if final_size > last_position:
                                                with open(log_file_path, "r", encoding="utf-8") as log_file:
                                                    log_file.seek(last_position)
                                                    final_content = log_file.read()
                                                    if final_content:
                                                        yield final_content
                                        break
                        except IOError:
                            # 文件可能正在被写入，稍后重试
                            await asyncio.sleep(wait_interval)
                            continue
                    else:
                        # 文件大小没有变化，继续等待
                        pass
                else:
                    # 文件被删除，结束读取
                    break
                
                await asyncio.sleep(wait_interval)
            
        except Exception as e:
            error_msg = f"\n读取日志失败: {str(e)}\n"
            yield error_msg
    
    return StreamingResponse(log_stream(), media_type="text/plain; charset=utf-8")


@app.get("/workflow/{tracerId}/stream", tags=["工作流管理"], summary="工作流执行状态流式推送")
async def stream_workflow_status(tracerId: str):
    """
    工作流执行状态流式推送 - 使用 Server-Sent Events (SSE)
    
    实时推送工作流执行状态和节点执行进度，支持前端实时显示执行日志。
    
    推送的事件类型：
    - workflow_start: 工作流开始执行
    - node_start: 节点开始执行
    - node_end: 节点执行完成（包含状态、耗时等信息）
    - node_error: 节点执行失败
    - workflow_end: 工作流执行完成
    - progress: 执行进度更新
    
    Args:
        tracerId: 工作流追踪ID（parent_task_id 或 task_id）
        
    Returns:
        SSE 流式响应，返回 JSON 格式的事件数据
    """
    import asyncio
    from fastapi.responses import StreamingResponse
    
    async def event_stream():
        """SSE 事件流生成器"""
        redis_client = await get_redis_client()
        last_result_hash = None
        last_progress = -1
        last_status = None
        
        # 发送初始连接事件
        yield f"data: {json.dumps({'type': 'connected', 'tracerId': tracerId})}\n\n"
        
        max_wait_time = 3600  # 最多等待1小时
        check_interval = 0.5  # 每0.5秒检查一次
        elapsed_time = 0
        
        try:
            while elapsed_time < max_wait_time:
                # 从 Redis 获取任务状态
                task_info = await redis_client.get_task_status(tracerId)
                
                if task_info:
                    # 解析状态
                    status = task_info.get("status", b"").decode('utf-8') if isinstance(task_info.get("status"), bytes) else task_info.get("status", "unknown")
                    progress = int(task_info.get("progress", 0).decode('utf-8')) if isinstance(task_info.get("progress"), bytes) else int(task_info.get("progress", 0))
                    
                    # 获取详细结果
                    result_json = None
                    try:
                        result_field = await redis_client.client.hget(f"task:{tracerId}", "result")
                        if result_field:
                            if isinstance(result_field, bytes):
                                result_json = json.loads(result_field.decode('utf-8'))
                            else:
                                result_json = json.loads(result_field)
                    except (json.JSONDecodeError, AttributeError):
                        result_json = None
                    
                    # 状态变化时推送事件
                    if status != last_status:
                        if status == "running" and last_status != "running":
                            # 工作流开始
                            yield f"data: {json.dumps({'type': 'workflow_start', 'tracerId': tracerId, 'status': status})}\n\n"
                        elif status in ["success", "failed", "timeout"]:
                            # 工作流结束
                            yield f"data: {json.dumps({'type': 'workflow_end', 'tracerId': tracerId, 'status': status, 'result': result_json})}\n\n"
                            break
                        last_status = status
                    
                    # 进度更新时推送
                    if progress != last_progress:
                        yield f"data: {json.dumps({'type': 'progress', 'tracerId': tracerId, 'progress': progress, 'status': status})}\n\n"
                        last_progress = progress
                    
                    # 如果有结果数据，推送节点执行信息
                    if result_json and isinstance(result_json, dict):
                        steps = result_json.get("steps", [])
                        if steps:
                            # 计算当前完成的节点数
                            completed_steps = [s for s in steps if s.get("status") in ["SUCCESS", "FAILED", "SKIPPED"]]
                            current_count = len(completed_steps)
                            total_count = len(steps)
                            
                            # 检查是否有新完成的节点（通过比较结果哈希）
                            result_str = json.dumps(result_json, sort_keys=True)
                            result_hash = hash(result_str)
                            
                            if result_hash != last_result_hash:
                                # 有新节点完成，推送节点事件
                                for step in steps:
                                    step_status = step.get("status")
                                    if step_status in ["SUCCESS", "FAILED"]:
                                        yield f"data: {json.dumps({'type': 'node_end', 'tracerId': tracerId, 'node': step})}\n\n"
                                
                                # 推送进度更新
                                yield f"data: {json.dumps({'type': 'progress', 'tracerId': tracerId, 'progress': int((current_count / total_count * 100) if total_count > 0 else 0), 'completed': current_count, 'total': total_count, 'status': status})}\n\n"
                                
                                last_result_hash = result_hash
                            
                            # 如果所有节点都完成了，推送完成事件
                            if current_count == total_count and status in ["success", "failed"]:
                                yield f"data: {json.dumps({'type': 'workflow_end', 'tracerId': tracerId, 'status': status, 'result': result_json})}\n\n"
                                break
                
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
            
            # 发送结束事件
            yield f"data: {json.dumps({'type': 'stream_end', 'tracerId': tracerId})}\n\n"
            
        except asyncio.CancelledError:
            LOGGER.logger.info(f"SSE stream cancelled for tracerId: {tracerId}")
        except Exception as e:
            LOGGER.logger.error(f"SSE stream error for tracerId {tracerId}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )
