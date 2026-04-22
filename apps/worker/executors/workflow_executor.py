# -*- coding: utf-8 -*-
"""
@author Fred.fan
@date 2025-10-14
@packageName worker.executors
@className WorkflowExecutor
@describe 工作流任务执行器
"""
import pprint
from typing import Dict, Any, List
from datetime import datetime
from packages.shared.logging.log_component import LOGGER
from packages.contracts.workflow_models import (
    WorkflowRunResultCallbackModel,
    ResultSummaryModel,
    StepCallbackModel,
    LogModel,
    ResponseData
)


class WorkflowExecutor:
    """工作流执行器"""
    
    @classmethod
    async def execute_workflow(cls, payload: dict, task_data: dict = None) -> Dict[str, Any]:
        """执行工作流"""
        pprint.pprint(payload)
        workflow_data = payload.get('workflow')
        environment = payload.get('environment')
        variables = payload.get('variables', {})
        
        task_id = task_data.get('task_id') if task_data else None
        parent_task_id = task_data.get('parent_task_id') if task_data else None
        run_id = payload.get('runId')
        # run_id = parent_task_id or task_id or workflow_data.get('id', 'unknown')
        
        # 使用 tracerId 作为日志标识（优先使用 parent_task_id，用于批量任务）
        tracer_id = parent_task_id or task_id or run_id
        
        LOGGER.logger.info(f"=" * 60)
        LOGGER.logger.info(f"开始执行工作流: workflow_id={workflow_data.get('id', 'unknown')}")
        LOGGER.logger.info(f"环境: {environment}")
        LOGGER.logger.info(f"运行ID: {run_id}")
        LOGGER.logger.info(f"追踪ID: {tracer_id}")
        LOGGER.logger.info(f"=" * 60)
        
        try:
            from packages.engine.workflow_engine import WorkflowExecutor as WorkflowEngineExecutor
            
            # 获取节点数量
            node_count = len(workflow_data.get('nodes', []))
            LOGGER.logger.info(f"工作流节点数: {node_count}")
            
            # 分片存储配置：节点数超过阈值时自动启用，避免内存溢出
            # 可通过环境变量调整阈值：WORKFLOW_SHARD_THRESHOLD（默认20）
            import os
            shard_threshold = int(os.environ.get('WORKFLOW_SHARD_THRESHOLD', '20'))
            enable_shard_storage = node_count >= shard_threshold
            
            if enable_shard_storage:
                LOGGER.logger.info(f"🗂️ 启用分片存储模式（节点数 {node_count} >= 阈值 {shard_threshold}）")
            
            # 使用默认的 WorkflowEngineExecutor 执行工作流
            executor = WorkflowEngineExecutor(
                workflow_data=workflow_data,
                environment=environment,
                enable_shard_storage=enable_shard_storage,
                task_id=task_id,
                run_id=run_id
            )
            
            if variables:
                for key, value in variables.items():
                    executor.context.set_variable(key, value)
                LOGGER.logger.info(f"已设置 {len(variables)} 个初始变量: {list(variables.keys())}")
            
            # 记录工作流开始执行
            LOGGER.logger.info(f"开始执行工作流引擎...")
            
            # 执行工作流
            # 注意：工作流引擎是同步的，使用线程池执行以避免阻塞事件循环
            # 这样即使工作流中有 time.sleep()，也不会阻塞整个 Worker 进程
            import asyncio
            import concurrent.futures
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor_pool:
                execution_result = await loop.run_in_executor(
                    executor_pool,
                    executor.execute
                )

            # 记录工作流执行完成
            LOGGER.logger.info(f"工作流引擎执行完成，开始处理结果...")
            
            status_value = execution_result.status.value if hasattr(execution_result.status, 'value') else str(execution_result.status)
            status_mapping = {
                "success": "SUCCESS",
                "failed": "FAILED",
                "running": "RUNNING",
                "pending": "PENDING",
                "cancelled": "CANCELLED"
            }
            formatted_status = status_mapping.get(status_value.lower(), status_value.upper())
            
            def datetime_to_timestamp(dt):
                if dt is None:
                    return None
                return int(dt.timestamp() * 1000)
            
            # 工作流总耗时（毫秒）- 直接使用 execution_result.duration
            duration_ms = int(execution_result.duration * 1000) if execution_result.duration else 0
            # 如果 duration 不存在或为 0，根据时间差计算
            if duration_ms == 0 and execution_result.start_time and execution_result.end_time:
                time_diff = execution_result.end_time - execution_result.start_time
                duration_ms = int(time_diff.total_seconds() * 1000)
            
            successful_steps = execution_result.get_successful_steps() if hasattr(execution_result, 'get_successful_steps') else []
            failed_steps = execution_result.get_failed_steps() if hasattr(execution_result, 'get_failed_steps') else []
            skipped_steps = execution_result.get_skipped_steps() if hasattr(execution_result, 'get_skipped_steps') else []
            pending_steps = []
            if execution_result.steps:
                for s in execution_result.steps:
                    step_status_val = s.status.value if hasattr(s.status, 'value') else str(s.status)
                    if step_status_val == "pending":
                        pending_steps.append(s)
            
            passed_count = len(successful_steps)
            failed_count = len(failed_steps)
            skipped_count = len(skipped_steps)
            pending_count = len(pending_steps)
            
            # ==================== 分片存储：加载完整步骤数据 ====================
            # 如果启用了分片存储，需要从 Redis 加载完整的步骤数据
            step_storage = None
            if enable_shard_storage and hasattr(executor, 'context') and executor.context.is_shard_storage_enabled():
                step_storage = executor.context.get_step_storage()
                if step_storage:
                    LOGGER.logger.info(f"🗂️ 分片存储模式：从 Redis 加载 {step_storage.get_step_count()} 个步骤的完整数据")
            # ==================== 分片存储结束 ====================
            
            formatted_steps = []
            for idx, step in enumerate(execution_result.steps):
                step_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
                step_status_mapped = status_mapping.get(step_status.lower(), step_status.upper())

                # step.output 已经包含了所有需要的数据：assertion, extract_vars, body, request, response 等
                step_output = step.output if step.output else {}
                step_metadata = getattr(step, 'metadata', {})
                
                # ==================== 内存优化：清理冗余数据 ====================
                # 移除 step_output 中的 variables 字段（每个节点都重复存储，导致数据量爆炸）
                # variables 对于回调结果没有意义，只会导致内存溢出
                if isinstance(step_output, dict) and 'variables' in step_output:
                    del step_output['variables']
                    LOGGER.logger.debug(f"[内存优化] 已移除节点 {step.node_id} 的 variables 字段")
                # ==================== 内存优化结束 ====================
                
                # ==================== 分片存储：检查并加载完整数据 ====================
                # 如果 step_output 标记为分片存储，从 Redis 加载完整数据
                if isinstance(step_output, dict) and step_output.get('_shard_stored'):
                    if step_storage:
                        try:
                            # 从 Redis 加载完整步骤数据
                            full_step_data = step_storage.load_step_result(idx, include_full_response=True)
                            if full_step_data and 'output' in full_step_data:
                                step_output = full_step_data['output']
                                LOGGER.logger.debug(f"[分片存储] 已加载节点 {step.node_id} 的完整数据")
                        except Exception as e:
                            LOGGER.logger.warning(f"[分片存储] 加载节点 {step.node_id} 数据失败: {e}")
                # ==================== 分片存储结束 ====================

                # 直接从 step.output 中提取数据
                request_data = {}
                response_data = {}
                assertion_logs = []
                extract_vars = {}


                if isinstance(step_output, dict):
                    # 直接提取 assertion（断言结果）- 已经是列表格式
                    assertion_logs = step_output.get('assertion') or []
                    if assertion_logs and not isinstance(assertion_logs, list):
                        assertion_logs = [assertion_logs]

                    # 直接提取 extract_vars（提取的变量）

                    extract_vars = step_output.get('extract_vars') or step_output.get('extracted_vars') or {}

                    # 提取请求数据（requestData）
                    metadata = step_output.get('metadata', {})
                    
                    # HTTP请求：从metadata.request获取
                    if step.node_type in ['http', 'http_request']:
                        request_data = metadata.get('request') or step_output.get('request', {})
                        response_data = step_output.get('response') or step_output.get('body', {})
                    else:
                        # 其他类型的处理器：将metadata中的请求相关信息作为request_data
                        if metadata:
                            # 对于不同类型的处理器，提取相应的请求字段
                            processor_type = step.node_type.lower() if step.node_type else ''
                            
                            # 定义不同处理器的请求字段
                            request_fields_map = {
                                'dubbo': ['application_name', 'interface_name', 'method_name', 'params', 'param_types', 'site_tenant'],
                                'rocketmq': ['topic', 'tag', 'key', 'message_body'],  # 添加message_body
                                # MySQL 节点请求信息：包含操作类型、影响行数、模板 SQL、参数以及仅用于展示的 executed_sql 预览
                                'mysql': ['operation', 'affected_rows', 'sql', 'params', 'executed_sql'],
                                'mongodb': ['operation', 'collection'],
                                'redis': ['operation', 'key'],
                            }
                            
                            # 获取该处理器类型需要提取的字段
                            request_fields = request_fields_map.get(processor_type, [])
                            
                            if request_fields:
                                # 优先从 metadata 中提取请求信息；若为空，则尝试从 error_details 中提取
                                source_dict = metadata or step_output.get("error_details") or {}
                                request_metadata = {
                                    k: v for k, v in source_dict.items() 
                                    if k in request_fields
                                }
                            else:
                                # 其他类型：使用整个metadata（排除响应相关的字段）
                                request_metadata = {
                                    k: v for k, v in metadata.items() 
                                    if k not in ['headers']  # headers通常是响应头
                                }
                            
                            # 只有当提取到字段时才设置request_data
                            if request_metadata:
                                request_data = request_metadata
                        
                        # 非 HTTP 请求，使用 body 作为响应数据
                        response_data = step_output.get('body', {})
                elif step_output:
                    # 如果 output 不是字典，直接作为响应数据
                    response_data = step_output

                step_name = step.node_id
                if workflow_data and 'nodes' in workflow_data:
                    for node in workflow_data['nodes']:
                        if node.get('id') == step.node_id:
                            # 优先使用节点的 stepName 字段，其次使用 data.label，最后使用 node_id
                            step_name = node.get('stepName') or node.get('data', {}).get('label') or step.node_id
                            break

                description = step.error if step.error else f"步骤执行{step_status_mapped}"

                # 计算步骤耗时（毫秒）
                # 优先使用 step.duration，如果不存在则根据 start_time 和 end_time 计算
                step_duration_ms = 0
                if step.duration is not None and step.duration > 0:
                    # step.duration 是秒（float），转换为毫秒
                    step_duration_ms = int(step.duration * 1000)
                elif step.start_time and step.end_time:
                    # 根据时间差计算耗时（datetime 对象相减得到 timedelta）
                    time_diff = step.end_time - step.start_time
                    # total_seconds() 返回秒（float），转换为毫秒
                    step_duration_ms = int(time_diff.total_seconds() * 1000)

                # 记录节点执行过程到日志
                LOGGER.logger.info(f"[节点 {idx + 1}/{len(execution_result.steps)}] {step_name} ({step.node_type})")
                LOGGER.logger.info(f"  状态: {step_status_mapped}")
                LOGGER.logger.info(f"  耗时: {step_duration_ms}ms")
                if step.error:
                    LOGGER.logger.error(f"  错误: {step.error}")
                if request_data:
                    LOGGER.logger.debug(f"  请求数据: {request_data}")
                if response_data:
                    LOGGER.logger.debug(f"  响应数据: {response_data}")
                if extract_vars:
                    LOGGER.logger.info(f"  提取变量: {list(extract_vars.keys())}")

                # 构建 ResponseData 对象
                response_data_obj = None
                if response_data or extract_vars or assertion_logs:
                    response_data_obj = {
                        "body": response_data if response_data else None,
                        "extractVars": extract_vars if extract_vars else None,
                        "assertion": assertion_logs if assertion_logs else None
                    }
                    # 移除 None 值
                    response_data_obj = {k: v for k, v in response_data_obj.items() if v is not None}
                    if not response_data_obj:
                        response_data_obj = None

                # 构建 ResponseData 对象
                response_data_model = None
                if response_data_obj:
                    try:
                        response_data_model = ResponseData(**response_data_obj)
                    except Exception as e:
                        LOGGER.logger.warning(f"构建 ResponseData 对象失败: {e}, 使用原始数据")
                        response_data_model = None

                # 构建 StepCallbackModel 对象
                step_model = StepCallbackModel(
                    step_id=step.node_id,
                    step_name=step_name,
                    step_type=step.node_type.upper() if step.node_type else "UNKNOWN",
                    order_num=idx + 1,
                    status=step_status_mapped,
                    start_time=datetime_to_timestamp(step.start_time),
                    end_time=datetime_to_timestamp(step.end_time),
                    duration_ms=step_duration_ms,
                    request_data=request_data if request_data else None,
                    response_data=response_data_model,
                    assertion=assertion_logs if assertion_logs else None,
                    extract_vars=extract_vars if extract_vars else None,
                    description=description
                )
                formatted_steps.append(step_model)

            # 构建 ResultSummaryModel 对象
            result_summary = ResultSummaryModel(
                summary=f"执行完成：成功 {passed_count} 个，失败 {failed_count} 个，跳过 {skipped_count} 个"
            )

            # 收集日志信息，直接从 step.logs 属性中获取
            # logs 是一个数组，每个元素是一条日志记录（对应一个节点）
            logs: List[LogModel] = []  # List[LogModel]: 日志数组（使用对象）
            try:
                for step in execution_result.steps:
                    # 检查 step 是否有 logs 属性且不为空
                    step_logs = getattr(step, 'logs', None)
                    if step_logs and step_logs.strip():
                        # 从日志内容中尝试解析日志级别（默认使用 INFO）
                        log_level = "INFO"
                        log_content_lower = step_logs.lower()
                        if "error" in log_content_lower:
                            log_level = "ERROR"
                        elif "warn" in log_content_lower or "warning" in log_content_lower:
                            log_level = "WARN"
                        elif "debug" in log_content_lower:
                            log_level = "DEBUG"
                        
                        # 使用节点的结束时间作为日志时间（如果没有则使用开始时间，再没有则使用当前时间）
                        log_timestamp = datetime_to_timestamp(step.end_time) if step.end_time else (
                            datetime_to_timestamp(step.start_time) if step.start_time else int(datetime.now().timestamp() * 1000)
                        )
                        
                        # 构建 LogModel 对象
                        log_entry = LogModel(
                            run_step_id=step.node_id,  # runStepId 对应节点ID（stepId）
                            step_id=None,  # stepId 字段保留为 None（根据接口定义）
                            level=log_level,
                            content=step_logs,  # 直接使用 step.logs 的内容
                            log_time=log_timestamp
                        )
                        logs.append(log_entry)
                        LOGGER.logger.debug(f"已为节点 {step.node_id} 添加日志记录（长度: {len(step_logs)} 字符）")
                
                if logs:
                    LOGGER.logger.info(f"已收集 {len(logs)} 条节点日志记录")
                else:
                    LOGGER.logger.debug(f"未找到任何节点日志（所有节点的 logs 属性为空或不存在）")
            except Exception as log_error:
                LOGGER.logger.warning(f"收集日志信息失败: {log_error}", exc_info=True)
                logs = []
            
            # 构建 WorkflowRunResultCallbackModel 对象
            result_model = WorkflowRunResultCallbackModel(
                run_id=run_id,
                status=formatted_status,
                start_time=datetime_to_timestamp(execution_result.start_time),
                end_time=datetime_to_timestamp(execution_result.end_time),
                duration_ms=duration_ms,
                total_steps=len(execution_result.steps),
                passed_count=passed_count,
                failed_count=failed_count,
                skipped_count=skipped_count,
                pending_count=pending_count,
                result_summary=result_summary,
                environment_name=environment or "",
                steps=formatted_steps,  # 已经是 StepCallbackModel 对象列表
                logs=logs  # 已经是 LogModel 对象列表
            )
            
            # 转换为字典用于返回（保持向后兼容）
            result_dict = result_model.model_dump(by_alias=True, exclude_none=False)
            
            # 记录工作流执行完成摘要
            LOGGER.logger.info(f"=" * 60)
            LOGGER.logger.info(f"工作流执行完成: runId={run_id}")
            LOGGER.logger.info(f"状态: {formatted_status}")
            LOGGER.logger.info(f"总节点数: {len(execution_result.steps)}")
            LOGGER.logger.info(f"成功: {passed_count}, 失败: {failed_count}, 跳过: {skipped_count}")
            if execution_result.duration:
                LOGGER.logger.info(f"总耗时: {execution_result.duration:.3f}s")
            LOGGER.logger.info(f"=" * 60)
            LOGGER.logger.info(f"任务完成: {tracer_id}")

            # 注意：已移除 print(result_dict)，避免打印大数据导致内存溢出
            # 如需调试，可使用 LOGGER.logger.debug 级别输出
            return {
                "success": status_value == "success",
                "result": result_dict,
                "message": "工作流执行成功" if status_value == "success" else "工作流执行失败"
            }
            
        except Exception as e:
            LOGGER.logger.error(f"Execute workflow error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"工作流执行失败: {str(e)}"
            }
