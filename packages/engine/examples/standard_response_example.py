#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准响应格式使用示例

演示如何使用统一的响应格式来改造现有处理器
"""

import time
from typing import Dict, Any
from packages.engine.src.models.response import ResponseBuilder, success_response, error_response
from packages.engine.src.core.processors import BaseProcessor
from packages.engine.src.context import ExecutionContext


# ========== 示例1：简单处理器 ==========

class SimpleProcessor(BaseProcessor):
    """简单处理器示例 - 使用便捷函数"""
    
    def execute(self, node_info: dict, context: ExecutionContext, 
                predecessor_results: dict) -> dict:
        start_time = time.time()
        
        try:
            # 模拟业务逻辑
            result = {"message": "Hello, World!"}
            duration = time.time() - start_time
            
            # 使用便捷函数返回成功响应
            return success_response(
                processor_type="simple",
                data=result,
                message="处理成功",
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return error_response(
                processor_type="simple",
                error=str(e),
                duration=duration
            )


# ========== 示例2：HTTP处理器（改进版） ==========

class ImprovedHttpProcessor(BaseProcessor):
    """改进的HTTP处理器 - 使用ResponseBuilder"""
    
    def execute(self, node_info: dict, context: ExecutionContext, 
                predecessor_results: dict) -> dict:
        start_time = time.time()
        
        try:
            # 模拟HTTP请求
            status_code = 200
            headers = {"Content-Type": "application/json"}
            body = {"user_id": 123, "username": "张三"}
            
            duration = time.time() - start_time
            
            # 使用专用的HTTP响应构建器
            return ResponseBuilder.from_http_response(
                status_code=status_code,
                headers=headers,
                body=body,
                duration=duration
            ).to_dict()
            
        except Exception as e:
            duration = time.time() - start_time
            return ResponseBuilder.error(
                processor_type="http_request",
                error=f"HTTP请求失败: {str(e)}",
                error_code="HTTP_ERROR",
                duration=duration
            ).to_dict()


# ========== 示例3：数据库处理器（改进版） ==========

class ImprovedDatabaseProcessor(BaseProcessor):
    """改进的数据库处理器 - 使用ResponseBuilder"""
    
    def execute(self, node_info: dict, context: ExecutionContext, 
                predecessor_results: dict) -> dict:
        start_time = time.time()
        
        try:
            # 模拟数据库查询
            operation = "select"
            results = [
                {"id": 1, "name": "张三"},
                {"id": 2, "name": "李四"}
            ]
            
            duration = time.time() - start_time
            
            # 使用专用的DB响应构建器
            return ResponseBuilder.from_db_response(
                operation=operation,
                data=results,
                affected_rows=len(results),
                duration=duration
            ).to_dict()
            
        except Exception as e:
            duration = time.time() - start_time
            return ResponseBuilder.error(
                processor_type="mysql",
                error=f"数据库操作失败: {str(e)}",
                error_code="DB_ERROR",
                error_details={
                    "operation": operation,
                    "sql": "SELECT * FROM users"
                },
                duration=duration
            ).to_dict()


# ========== 示例4：MQ处理器（改进版） ==========

class ImprovedMQProcessor(BaseProcessor):
    """改进的MQ处理器 - 使用ResponseBuilder"""
    
    def execute(self, node_info: dict, context: ExecutionContext, 
                predecessor_results: dict) -> dict:
        start_time = time.time()
        
        try:
            # 模拟MQ消息发送
            msg_id = "7F0000017F3F18B4AAC21B6A96A20000"
            topic = "test_topic"
            tag = "order_created"
            key = "order_12345"
            
            duration = time.time() - start_time
            
            # 使用专用的MQ响应构建器
            return ResponseBuilder.from_mq_response(
                msg_id=msg_id,
                topic=topic,
                tag=tag,
                key=key,
                duration=duration
            ).to_dict()
            
        except Exception as e:
            duration = time.time() - start_time
            return ResponseBuilder.error(
                processor_type="rocketmq",
                error=f"MQ消息发送失败: {str(e)}",
                error_code="MQ_SEND_ERROR",
                error_details={
                    "topic": topic,
                    "message": "测试消息"
                },
                duration=duration
            ).to_dict()


# ========== 示例5：循环处理器（改进版） ==========

class ImprovedLoopProcessor(BaseProcessor):
    """改进的循环处理器 - 使用ResponseBuilder"""
    
    def execute(self, node_info: dict, context: ExecutionContext, 
                predecessor_results: dict) -> dict:
        start_time = time.time()
        
        try:
            # 模拟循环处理
            items = ["item1", "item2", "item3"]
            results = []
            
            for i, item in enumerate(items):
                results.append({
                    "index": i,
                    "item": item,
                    "processed": True
                })
            
            duration = time.time() - start_time
            
            # 使用专用的Loop响应构建器
            return ResponseBuilder.from_loop_response(
                loop_type="foreach_loop",
                iterations=len(items),
                results=results,
                duration=duration
            ).to_dict()
            
        except Exception as e:
            duration = time.time() - start_time
            return ResponseBuilder.error(
                processor_type="loop",
                error=f"循环执行失败: {str(e)}",
                error_code="LOOP_ERROR",
                duration=duration
            ).to_dict()


# ========== 示例6：复杂处理器（多种场景） ==========

class ComplexProcessor(BaseProcessor):
    """复杂处理器示例 - 展示多种响应场景"""
    
    def execute(self, node_info: dict, context: ExecutionContext, 
                predecessor_results: dict) -> dict:
        start_time = time.time()
        processor_type = "complex"
        
        try:
            config = node_info.get("data", {}).get("config", {})
            mode = config.get("mode", "normal")
            
            if mode == "success":
                # 成功场景
                duration = time.time() - start_time
                return ResponseBuilder.success(
                    processor_type=processor_type,
                    data={"result": "success"},
                    message="操作成功完成",
                    metadata={"mode": mode},
                    duration=duration
                ).to_dict()
            
            elif mode == "failed":
                # 业务失败场景
                duration = time.time() - start_time
                return ResponseBuilder.failed(
                    processor_type=processor_type,
                    message="业务验证失败：数据不符合要求",
                    data={"validation_errors": ["字段A为空", "字段B格式错误"]},
                    metadata={"mode": mode},
                    duration=duration
                ).to_dict()
            
            elif mode == "error":
                # 系统错误场景
                raise RuntimeError("模拟系统错误")
            
            else:
                # 默认成功
                duration = time.time() - start_time
                return ResponseBuilder.success(
                    processor_type=processor_type,
                    data={"result": "default"},
                    duration=duration
                ).to_dict()
            
        except Exception as e:
            duration = time.time() - start_time
            return ResponseBuilder.error(
                processor_type=processor_type,
                error=str(e),
                error_code="EXECUTION_ERROR",
                error_details={
                    "exception_type": type(e).__name__,
                    "config": config
                },
                duration=duration
            ).to_dict()


# ========== 响应格式对比 ==========

def compare_old_vs_new():
    """对比旧格式和新格式"""
    
    print("=" * 80)
    print("响应格式对比示例")
    print("=" * 80)
    
    # 旧格式示例（混乱）
    print("\n【旧格式 - HTTP】")
    old_http = {
        "status_code": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {"user_id": 123}
    }
    print(old_http)
    
    print("\n【新格式 - HTTP】")
    new_http = ResponseBuilder.from_http_response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body={"user_id": 123},
        duration=0.123
    ).to_dict()
    print(new_http)
    
    print("\n" + "=" * 80)
    
    # 旧格式示例（混乱）
    print("\n【旧格式 - MySQL（格式1）】")
    old_mysql_1 = {
        "success": True,
        "data": [{"id": 1}],
        "affected_rows": 1
    }
    print(old_mysql_1)
    
    print("\n【旧格式 - MySQL（格式2）】")
    old_mysql_2 = {
        "status": "success",
        "status_code": 200,
        "body": {"data": [{"id": 1}], "row_count": 1},
        "operation": "select"
    }
    print(old_mysql_2)
    
    print("\n【新格式 - MySQL（统一）】")
    new_mysql = ResponseBuilder.from_db_response(
        operation="select",
        data=[{"id": 1}],
        affected_rows=1,
        duration=0.023
    ).to_dict()
    print(new_mysql)
    
    print("\n" + "=" * 80)


# ========== 测试运行 ==========

if __name__ == "__main__":
    print("🚀 标准响应格式示例\n")
    
    # 创建上下文
    context = ExecutionContext()
    
    # 测试简单处理器
    print("1️⃣  简单处理器测试")
    simple_proc = SimpleProcessor()
    result = simple_proc.execute({}, context, {})
    print(f"响应: {result}")
    print(f"状态: {result['status']}")
    print(f"数据: {result['data']}")
    print(f"耗时: {result['duration']:.3f}s\n")
    
    # 测试HTTP处理器
    print("2️⃣  HTTP处理器测试")
    http_proc = ImprovedHttpProcessor()
    result = http_proc.execute({}, context, {})
    print(f"响应: {result}")
    print(f"状态: {result['status']}")
    print(f"数据: {result['data']}")
    print(f"元数据: {result['metadata']}\n")
    
    # 测试数据库处理器
    print("3️⃣  数据库处理器测试")
    db_proc = ImprovedDatabaseProcessor()
    result = db_proc.execute({}, context, {})
    print(f"响应: {result}")
    print(f"状态: {result['status']}")
    print(f"数据: {result['data']}")
    print(f"影响行数: {result['metadata']['affected_rows']}\n")
    
    # 测试MQ处理器
    print("4️⃣  MQ处理器测试")
    mq_proc = ImprovedMQProcessor()
    result = mq_proc.execute({}, context, {})
    print(f"响应: {result}")
    print(f"消息ID: {result['data']['msg_id']}")
    print(f"主题: {result['metadata']['topic']}\n")
    
    # 测试循环处理器
    print("5️⃣  循环处理器测试")
    loop_proc = ImprovedLoopProcessor()
    result = loop_proc.execute({}, context, {})
    print(f"响应: {result}")
    print(f"迭代次数: {result['metadata']['iterations']}")
    print(f"结果数量: {result['metadata']['items_count']}\n")
    
    # 测试复杂处理器（成功场景）
    print("6️⃣  复杂处理器测试 - 成功场景")
    complex_proc = ComplexProcessor()
    result = complex_proc.execute(
        {"data": {"config": {"mode": "success"}}},
        context,
        {}
    )
    print(f"响应: {result}\n")
    
    # 测试复杂处理器（失败场景）
    print("7️⃣  复杂处理器测试 - 失败场景")
    result = complex_proc.execute(
        {"data": {"config": {"mode": "failed"}}},
        context,
        {}
    )
    print(f"响应: {result}\n")
    
    # 测试复杂处理器（错误场景）
    print("8️⃣  复杂处理器测试 - 错误场景")
    result = complex_proc.execute(
        {"data": {"config": {"mode": "error"}}},
        context,
        {}
    )
    print(f"响应: {result}\n")
    
    # 格式对比
    print("\n" + "=" * 80)
    compare_old_vs_new()
    
    print("\n✅ 所有测试完成！")

