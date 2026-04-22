#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XXL-Job 处理器使用示例

演示如何使用 XxlJobProcessor 触发任务执行

注意：
- 本测试需要 XXL-Job 服务器运行
- 需要数据库连接来查询任务 ID
- 请根据实际情况修改配置参数
"""

import json

from packages.engine.src.core.processors.job.xxljob_processor import XxlJobProcessor
from packages.engine.src.context import ExecutionContext


def test_xxljob_processor_basic():
    """测试基本的 XXL-Job 处理器"""
    
    # 创建处理器实例
    processor = XxlJobProcessor()
    
    # 创建执行上下文
    context = ExecutionContext()
    
    # 模拟节点信息
    node_info = {
        "id": "xxljob_test_node",
        "type": "xxljob",
        "data": {
            "config": {
                "xxjob_url": "http://job.dev.example.com",  # 请修改为实际的 XXL-Job 地址
                "username": "admin",  # 请修改为实际的用户名
                "password": "123456",  # 请修改为实际的密码
                "executor_handler": "demoJobHandler",  # 请修改为实际的任务 Handler
                "executor_param": '{"param1": "value1", "param2": 123}',
                "site_tenant": "DEFAULT",
                "db_name": "xxl_job",  # 数据库名称，用于从上下文获取数据库配置
                "output_variable": "job_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("\n=== XXL-Job 任务触发结果 ===")
        print(f"状态: {result.get('status', 'N/A')}")
        print(f"成功: {result.get('body', {}).get('success', False)}")
        print(f"代码: {result.get('body', {}).get('code', 'N/A')}")
        print(f"消息: {result.get('body', {}).get('msg', 'N/A')}")
        print(f"内容: {result.get('body', {}).get('content', 'N/A')}")
        print(f"错误: {result.get('error', 'N/A')}")
        print(f"消息: {result.get('message', 'N/A')}")
        
        # 检查结果是否保存到上下文
        if context.has_variable("job_result"):
            saved_result = context.get_variable("job_result")
            print(f"\n=== 保存到上下文的结果 ===")
            print(f"变量值: {saved_result}")
        
        return result
        
    except Exception as e:
        print(f"❌ XXL-Job 任务触发失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_xxljob_processor_with_variables():
    """测试带变量的 XXL-Job 处理器"""
    
    # 创建处理器实例
    processor = XxlJobProcessor()
    
    # 创建执行上下文并设置变量
    context = ExecutionContext()
    context.set_variable("xxljob_url", "http://job.dev.example.com")
    context.set_variable("username", "admin")
    context.set_variable("password", "123456")
    context.set_variable("handler_name", "demoJobHandler")
    context.set_variable("task_id", 12345)
    context.set_variable("action", "process")
    context.set_variable("tenant", "US_AMZ")
    
    # 模拟节点信息（使用变量）
    node_info = {
        "id": "xxljob_variable_test_node",
        "type": "xxljob",
        "data": {
            "config": {
                "xxjob_url": "${xxljob_url}",
                "username": "${username}",
                "password": "${password}",
                "executor_handler": "${handler_name}",
                "executor_param": '{"taskId": ${task_id}, "action": "${action}"}',
                "site_tenant": "${tenant}",
                "db_name": "xxl_job",
                "output_variable": "variable_job_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("\n=== 带变量的 XXL-Job 任务触发结果 ===")
        print(f"状态: {result.get('status', 'N/A')}")
        print(f"成功: {result.get('body', {}).get('success', False)}")
        print(f"代码: {result.get('body', {}).get('code', 'N/A')}")
        print(f"消息: {result.get('body', {}).get('msg', 'N/A')}")
        print(f"内容: {result.get('body', {}).get('content', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 带变量的 XXL-Job 任务触发失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_xxljob_processor_with_db_client():
    """测试使用数据库客户端的 XXL-Job 处理器"""
    
    # 创建处理器实例
    processor = XxlJobProcessor()
    
    # 创建执行上下文
    context = ExecutionContext()
    
    # 如果需要使用数据库客户端，可以从上下文获取或创建
    # 方式1: 从上下文变量中获取 SQLClient 实例
    # from packages.engine.src.clients.sql_client import SQLClient
    # db_client = SQLClient(host="localhost", port=3306, user="root", password="root", database="xxl_job")
    # context.set_variable("xxl_job", db_client)
    
    # 方式2: 从上下文变量中获取数据库配置字典
    # db_config = {
    #     "host": "localhost",
    #     "port": 3306,
    #     "user": "root",
    #     "password": "root",
    #     "database": "xxl_job"
    # }
    # context.set_variable("xxl_job", db_config)
    
    # 模拟节点信息
    node_info = {
        "id": "xxljob_db_test_node",
        "type": "xxljob",
        "data": {
            "config": {
                "xxjob_url": "http://job.dev.example.com",
                "username": "admin",
                "password": "123456",
                "executor_handler": "demoJobHandler",
                "executor_param": '{"param": "value"}',
                "site_tenant": "DEFAULT",
                "db_name": "xxl_job",  # 从上下文变量中获取数据库配置
                "output_variable": "db_job_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("\n=== 使用数据库客户端的 XXL-Job 任务触发结果 ===")
        print(f"状态: {result.get('status', 'N/A')}")
        print(f"成功: {result.get('body', {}).get('success', False)}")
        print(f"代码: {result.get('body', {}).get('code', 'N/A')}")
        print(f"消息: {result.get('body', {}).get('msg', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 使用数据库客户端的 XXL-Job 任务触发失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_xxljob_processor_config_validation():
    """测试配置验证"""
    
    processor = XxlJobProcessor()
    
    print("\n=== 测试配置验证 ===")
    
    # 测试缺少必需字段 - xxjob_url
    try:
        invalid_config = {
            "executor_handler": "demoJobHandler"
        }
        processor.validate_config(invalid_config)
        print("❌ 应该抛出验证错误（缺少 xxjob_url）")
    except Exception as e:
        print(f"✅ 正确捕获缺少 xxjob_url 错误: {e}")
    
    # 测试缺少必需字段 - executor_handler
    try:
        invalid_config = {
            "xxjob_url": "http://job.dev.example.com"
        }
        processor.validate_config(invalid_config)
        print("❌ 应该抛出验证错误（缺少 executor_handler）")
    except Exception as e:
        print(f"✅ 正确捕获缺少 executor_handler 错误: {e}")
    
    # 测试空的 xxjob_url
    try:
        invalid_config = {
            "xxjob_url": "",
            "executor_handler": "demoJobHandler"
        }
        processor.validate_config(invalid_config)
        print("❌ 应该抛出验证错误（xxjob_url 为空）")
    except Exception as e:
        print(f"✅ 正确捕获 xxjob_url 为空错误: {e}")
    
    # 测试空的 executor_handler
    try:
        invalid_config = {
            "xxjob_url": "http://job.dev.example.com",
            "executor_handler": ""
        }
        processor.validate_config(invalid_config)
        print("❌ 应该抛出验证错误（executor_handler 为空）")
    except Exception as e:
        print(f"✅ 正确捕获 executor_handler 为空错误: {e}")
    
    # 测试有效配置
    try:
        valid_config = {
            "xxjob_url": "http://job.dev.example.com",
            "executor_handler": "demoJobHandler",
            "username": "admin",
            "password": "123456",
            "executor_param": '{"param": "value"}',
            "site_tenant": "DEFAULT"
        }
        processor.validate_config(valid_config)
        print("✅ 有效配置验证通过")
    except Exception as e:
        print(f"❌ 有效配置验证失败: {e}")


def test_xxljob_processor_with_json_param():
    """测试使用 JSON 参数的 XXL-Job 处理器"""
    
    # 创建处理器实例
    processor = XxlJobProcessor()
    
    # 创建执行上下文
    context = ExecutionContext()
    
    # 创建复杂的 JSON 参数
    param_data = {
        "taskId": 12345,
        "action": "process",
        "params": {
            "userId": 1001,
            "orderId": "order_12345",
            "amount": 99.99
        },
        "options": {
            "async": True,
            "retry": 3,
            "timeout": 300
        }
    }
    
    # 模拟节点信息（使用 JSON 参数）
    node_info = {
        "id": "xxljob_json_test_node",
        "type": "xxljob",
        "data": {
            "config": {
                "xxjob_url": "http://job.dev.example.com",
                "username": "admin",
                "password": "123456",
                "executor_handler": "demoJobHandler",
                "executor_param": json.dumps(param_data),  # 转换为 JSON 字符串
                "site_tenant": "DEFAULT",
                "db_name": "xxl_job",
                "output_variable": "json_job_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("\n=== 使用 JSON 参数的 XXL-Job 任务触发结果 ===")
        print(f"状态: {result.get('status', 'N/A')}")
        print(f"成功: {result.get('body', {}).get('success', False)}")
        print(f"代码: {result.get('body', {}).get('code', 'N/A')}")
        print(f"消息: {result.get('body', {}).get('msg', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 使用 JSON 参数的 XXL-Job 任务触发失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_xxljob_processor_required_and_optional_keys():
    """测试必需和可选配置键"""
    
    processor = XxlJobProcessor()
    
    print("\n=== 测试配置键 ===")
    
    # 获取必需的配置键
    required_keys = processor.get_required_config_keys()
    print(f"必需配置键: {required_keys}")
    assert 'xxjob_url' in required_keys, "xxjob_url 应该是必需配置键"
    assert 'executor_handler' in required_keys, "executor_handler 应该是必需配置键"
    print("✅ 必需配置键验证通过")
    
    # 获取可选的配置键
    optional_keys = processor.get_optional_config_keys()
    print(f"可选配置键: {optional_keys}")
    expected_optional = ['executor_param', 'site_tenant', 'address_list', 'username', 'password',
                         'app_code', 'db_name', 'output_variable']
    for key in expected_optional:
        assert key in optional_keys, f"{key} 应该是可选配置键"
    print("✅ 可选配置键验证通过")


if __name__ == "__main__":
    print("🚀 开始测试 XXL-Job 处理器")
    print("=" * 60)
    print("⚠️  注意: 本测试需要 XXL-Job 服务器运行")
    print("⚠️  注意: 请根据实际情况修改配置参数")
    print("=" * 60)
    
    # 测试配置验证
    test_xxljob_processor_config_validation()
    
    # 测试配置键
    print("\n" + "="*50)
    test_xxljob_processor_required_and_optional_keys()
    
    # 测试基本功能（需要实际配置）
    # print("\n" + "="*50)
    # test_xxljob_processor_basic()
    
    # 测试变量功能（需要实际配置）
    # print("\n" + "="*50)
    # test_xxljob_processor_with_variables()
    
    # 测试 JSON 参数（需要实际配置）
    # print("\n" + "="*50)
    # test_xxljob_processor_with_json_param()
    
    # 测试数据库客户端（需要实际配置）
    # print("\n" + "="*50)
    # test_xxljob_processor_with_db_client()
    
    print("\n🎉 XXL-Job 处理器测试完成")
    print("\n💡 提示: 取消注释上面的测试函数来运行实际的功能测试")
    print("💡 提示: 请确保 XXL-Job 服务器运行，并修改配置参数")
