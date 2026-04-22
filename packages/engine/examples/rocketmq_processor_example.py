#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RocketMQ 处理器使用示例

演示如何使用 RocketmqProcessor 发送消息
"""

from packages.engine.src.core.processors.data.rocketmq_processor import RocketmqProcessor
from packages.engine.src.context import ExecutionContext


def test_rocketmq_processor():
    """测试 RocketMQ 处理器"""
    
    # 创建处理器实例
    processor = RocketmqProcessor()
    
    # 创建执行上下文
    context = ExecutionContext()
    
    # 模拟节点信息
    node_info = {
        "id": "rocketmq_test_node",
        "type": "rocketmq",
        "data": {
            "config": {
                "topic": "test_topic",
                "message_body": "Hello RocketMQ!",
                "environment": "dev",
                "site_tenant": "default",
                "tag": "test",
                "key": "test_key",
                "timeout": 30,
                "output_variable": "mq_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("=== RocketMQ 发送结果 ===")
        print(f"状态: {result['status']}")
        print(f"消息ID: {result.get('msg_id', 'N/A')}")
        print(f"主题: {result['topic']}")
        print(f"标签: {result['tag']}")
        print(f"键值: {result['key']}")
        print(f"消息内容: {result['message_body']}")
        print(f"消息: {result['message']}")
        
        # 检查结果是否保存到上下文
        if context.has_variable("mq_result"):
            saved_result = context.get_variable("mq_result")
            print(f"\n=== 保存到上下文的结果 ===")
            print(f"变量值: {saved_result}")
        
        return result
        
    except Exception as e:
        print(f"❌ RocketMQ 发送失败: {e}")
        return None


def test_rocketmq_processor_with_variables():
    """测试带变量的 RocketMQ 处理器"""
    
    # 创建处理器实例
    processor = RocketmqProcessor()
    
    # 创建执行上下文并设置变量
    context = ExecutionContext()
    context.set_variable("topic_name", "order_topic")
    context.set_variable("message_content", "Order created successfully")
    context.set_variable("order_id", "order_12345")
    context.set_variable("tenant", "US_AMZ")
    
    # 模拟节点信息（使用变量）
    node_info = {
        "id": "rocketmq_variable_test_node",
        "type": "rocketmq",
        "data": {
            "config": {
                "topic": "${topic_name}",
                "message_body": "${message_content}",
                "environment": "dev",
                "site_tenant": "${tenant}",
                "tag": "order",
                "key": "${order_id}",
                "timeout": 30,
                "output_variable": "order_mq_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("\n=== 带变量的 RocketMQ 发送结果 ===")
        print(f"状态: {result['status']}")
        print(f"消息ID: {result.get('msg_id', 'N/A')}")
        print(f"主题: {result['topic']}")
        print(f"标签: {result['tag']}")
        print(f"键值: {result['key']}")
        print(f"消息内容: {result['message_body']}")
        print(f"消息: {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 带变量的 RocketMQ 发送失败: {e}")
        return None


def test_rocketmq_processor_with_json_message():
    """测试发送 JSON 消息的 RocketMQ 处理器"""
    
    # 创建处理器实例
    processor = RocketmqProcessor()
    
    # 创建执行上下文
    context = ExecutionContext()
    context.set_variable("order_data", {
        "order_id": "order_67890",
        "user_id": "user_123",
        "amount": 99.99,
        "status": "created"
    })
    
    # 模拟节点信息（发送 JSON 消息）
    node_info = {
        "id": "rocketmq_json_test_node",
        "type": "rocketmq",
        "data": {
            "config": {
                "topic": "order_events",
                "message_body": "${order_data}",
                "environment": "dev",
                "site_tenant": "default",
                "tag": "order_created",
                "key": "${order_data.order_id}",
                "timeout": 30,
                "output_variable": "json_mq_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("\n=== JSON 消息 RocketMQ 发送结果 ===")
        print(f"状态: {result['status']}")
        print(f"消息ID: {result.get('msg_id', 'N/A')}")
        print(f"主题: {result['topic']}")
        print(f"标签: {result['tag']}")
        print(f"键值: {result['key']}")
        print(f"消息内容: {result['message_body']}")
        print(f"消息: {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ JSON 消息 RocketMQ 发送失败: {e}")
        return None


def test_rocketmq_processor_with_custom_headers():
    """测试带自定义请求头的 RocketMQ 处理器"""
    
    # 创建处理器实例
    processor = RocketmqProcessor()
    
    # 创建执行上下文
    context = ExecutionContext()
    context.set_variable("auth_token", "bearer_token_123")
    context.set_variable("request_id", "req_987654321")
    
    # 模拟节点信息（带自定义请求头）
    node_info = {
        "id": "rocketmq_headers_test_node",
        "type": "rocketmq",
        "data": {
            "config": {
                "topic": "secure_topic",
                "message_body": "Secure message content",
                "environment": "dev",
                "site_tenant": "default",
                "tag": "secure",
                "key": "secure_key",
                "timeout": 30,
                "custom_headers": {
                    "Authorization": "Bearer ${auth_token}",
                    "X-Request-ID": "${request_id}",
                    "X-Service": "order-service"
                },
                "output_variable": "secure_mq_result"
            }
        }
    }
    
    try:
        # 执行处理器
        result = processor.execute(node_info, context, {})
        
        print("\n=== 带自定义请求头的 RocketMQ 发送结果 ===")
        print(f"状态: {result['status']}")
        print(f"消息ID: {result.get('msg_id', 'N/A')}")
        print(f"主题: {result['topic']}")
        print(f"标签: {result['tag']}")
        print(f"键值: {result['key']}")
        print(f"消息内容: {result['message_body']}")
        print(f"消息: {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 带自定义请求头的 RocketMQ 发送失败: {e}")
        return None


def test_config_validation():
    """测试配置验证"""
    
    processor = RocketmqProcessor()
    
    print("\n=== 测试配置验证 ===")
    
    # 测试缺少必需字段
    try:
        processor.validate_config({})
        print("❌ 应该抛出验证错误")
    except Exception as e:
        print(f"✅ 正确捕获缺少字段错误: {e}")
    
    # 测试空的 topic
    try:
        processor.validate_config({
            "topic": "",
            "message_body": "test message"
        })
        print("❌ 应该抛出 topic 验证错误")
    except Exception as e:
        print(f"✅ 正确捕获 topic 验证错误: {e}")
    
    # 测试无效环境
    try:
        processor.validate_config({
            "topic": "test_topic",
            "message_body": "test message",
            "environment": "invalid_env"
        })
        print("❌ 应该抛出环境验证错误")
    except Exception as e:
        print(f"✅ 正确捕获环境验证错误: {e}")
    
    # 测试有效配置
    try:
        processor.validate_config({
            "topic": "test_topic",
            "message_body": "test message",
            "environment": "dev",
            "timeout": 60
        })
        print("✅ 有效配置验证通过")
    except Exception as e:
        print(f"❌ 有效配置验证失败: {e}")


if __name__ == "__main__":
    print("🚀 开始测试 RocketMQ 处理器")
    
    # 测试配置验证
    test_config_validation()
    
    # 测试基本功能
    print("\n" + "="*50)
    test_rocketmq_processor()
    
    # 测试变量功能
    print("\n" + "="*50)
    test_rocketmq_processor_with_variables()
    
    # 测试 JSON 消息
    print("\n" + "="*50)
    test_rocketmq_processor_with_json_message()
    
    # 测试自定义请求头
    print("\n" + "="*50)
    test_rocketmq_processor_with_custom_headers()
    
    print("\n🎉 RocketMQ 处理器测试完成")
