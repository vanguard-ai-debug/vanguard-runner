#!/usr/bin/env python3
"""
Redis 处理器使用示例

演示 Redis 处理器的各种操作：
1. 字符串操作 (GET, SET, DEL, EXISTS)
2. 哈希操作 (HGET, HSET, HDEL, HGETALL)
3. 列表操作 (LPUSH, RPUSH, LPOP, RPOP, LLEN)
4. 集合操作 (SADD, SREM, SMEMBERS, SISMEMBER)
5. 有序集合操作 (ZADD, ZREM, ZRANGE, ZSCORE)
6. 键操作 (KEYS, EXPIRE, TTL, TYPE)
"""

import json
import time
from typing import Any

from packages.engine.src.core.processors.data.redis_processor import RedisProcessor
from packages.engine.src.core.exceptions import ValidationError, ExecutionError


class MockContext:
    """模拟执行上下文"""
    
    def __init__(self):
        self.variables = {}
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
        print(f"  [Context] 设置变量: '{name}' = {value}")
    
    def get_variable(self, name: str):
        """获取变量"""
        return self.variables.get(name)


def test_string_operations():
    """测试字符串操作"""
    print("\n" + "="*50)
    print("🔤 测试字符串操作")
    print("="*50)
    
    processor = RedisProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('test_key', 'test_string_key')
    context.set_variable('test_value', 'Hello Redis!')
    
    # 测试 SET 操作
    config = {
        'operation': 'set',
        'key': '${test_key}',
        'value': '${test_value}',
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'output_variable': 'set_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ SET 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ SET 操作失败: {e}")
        return
    
    # 测试 GET 操作
    config = {
        'operation': 'get',
        'key': '${test_key}',
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'output_variable': 'get_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ GET 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ GET 操作失败: {e}")
    
    # 测试 EXISTS 操作
    config = {
        'operation': 'exists',
        'key': '${test_key}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ EXISTS 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ EXISTS 操作失败: {e}")
    
    # 测试 EXPIRE 操作
    config = {
        'operation': 'expire',
        'key': '${test_key}',
        'seconds': 60,
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ EXPIRE 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ EXPIRE 操作失败: {e}")
    
    # 测试 TTL 操作
    config = {
        'operation': 'ttl',
        'key': '${test_key}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ TTL 操作成功: {result['result']} 秒")
    except Exception as e:
        print(f"❌ TTL 操作失败: {e}")


def test_hash_operations():
    """测试哈希操作"""
    print("\n" + "="*50)
    print("🗂️ 测试哈希操作")
    print("="*50)
    
    processor = RedisProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('hash_key', 'user:1001')
    context.set_variable('field_name', 'name')
    context.set_variable('field_value', '张三')
    
    # 测试 HSET 操作
    config = {
        'operation': 'hset',
        'key': '${hash_key}',
        'field': '${field_name}',
        'value': '${field_value}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ HSET 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ HSET 操作失败: {e}")
        return
    
    # 测试 HGET 操作
    config = {
        'operation': 'hget',
        'key': '${hash_key}',
        'field': '${field_name}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ HGET 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ HGET 操作失败: {e}")
    
    # 测试 HGETALL 操作
    config = {
        'operation': 'hgetall',
        'key': '${hash_key}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ HGETALL 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ HGETALL 操作失败: {e}")


def test_list_operations():
    """测试列表操作"""
    print("\n" + "="*50)
    print("📋 测试列表操作")
    print("="*50)
    
    processor = RedisProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('list_key', 'task_queue')
    context.set_variable('task_values', ['任务1', '任务2', '任务3'])
    
    # 测试 LPUSH 操作
    config = {
        'operation': 'lpush',
        'key': '${list_key}',
        'values': '${task_values}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ LPUSH 操作成功: 插入了 {result['result']} 个元素")
    except Exception as e:
        print(f"❌ LPUSH 操作失败: {e}")
        return
    
    # 测试 LLEN 操作
    config = {
        'operation': 'llen',
        'key': '${list_key}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ LLEN 操作成功: 列表长度为 {result['result']}")
    except Exception as e:
        print(f"❌ LLEN 操作失败: {e}")
    
    # 测试 LRANGE 操作
    config = {
        'operation': 'lrange',
        'key': '${list_key}',
        'start': 0,
        'end': -1,
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ LRANGE 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ LRANGE 操作失败: {e}")


def test_set_operations():
    """测试集合操作"""
    print("\n" + "="*50)
    print("🔗 测试集合操作")
    print("="*50)
    
    processor = RedisProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('set_key', 'user_tags')
    context.set_variable('tag_values', ['python', 'redis', 'mongodb'])
    
    # 测试 SADD 操作
    config = {
        'operation': 'sadd',
        'key': '${set_key}',
        'values': '${tag_values}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ SADD 操作成功: 添加了 {result['result']} 个元素")
    except Exception as e:
        print(f"❌ SADD 操作失败: {e}")
        return
    
    # 测试 SMEMBERS 操作
    config = {
        'operation': 'smembers',
        'key': '${set_key}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ SMEMBERS 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ SMEMBERS 操作失败: {e}")
    
    # 测试 SISMEMBER 操作
    config = {
        'operation': 'sismember',
        'key': '${set_key}',
        'value': 'python',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ SISMEMBER 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ SISMEMBER 操作失败: {e}")


def test_sorted_set_operations():
    """测试有序集合操作"""
    print("\n" + "="*50)
    print("📊 测试有序集合操作")
    print("="*50)
    
    processor = RedisProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('zset_key', 'leaderboard')
    context.set_variable('scores', {'player1': 100, 'player2': 200, 'player3': 150})
    
    # 测试 ZADD 操作
    config = {
        'operation': 'zadd',
        'key': '${zset_key}',
        'members': '${scores}',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ ZADD 操作成功: 添加了 {result['result']} 个元素")
    except Exception as e:
        print(f"❌ ZADD 操作失败: {e}")
        return
    
    # 测试 ZRANGE 操作
    config = {
        'operation': 'zrange',
        'key': '${zset_key}',
        'start': 0,
        'end': -1,
        'withscores': True,
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ ZRANGE 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ ZRANGE 操作失败: {e}")
    
    # 测试 ZSCORE 操作
    config = {
        'operation': 'zscore',
        'key': '${zset_key}',
        'member': 'player2',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ ZSCORE 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ ZSCORE 操作失败: {e}")


def test_key_operations():
    """测试键操作"""
    print("\n" + "="*50)
    print("🔑 测试键操作")
    print("="*50)
    
    processor = RedisProcessor()
    context = MockContext()
    
    # 测试 KEYS 操作
    config = {
        'operation': 'keys',
        'pattern': 'test_*',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ KEYS 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ KEYS 操作失败: {e}")
    
    # 测试 TYPE 操作
    config = {
        'operation': 'type',
        'key': 'test_string_key',
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ TYPE 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ TYPE 操作失败: {e}")


def test_validation():
    """测试配置验证"""
    print("\n" + "="*50)
    print("🔍 测试配置验证")
    print("="*50)
    
    processor = RedisProcessor()
    
    # 测试缺少必需参数
    try:
        processor.validate_config({})
        print("❌ 应该捕获缺少 operation 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少字段错误: {e.message}")
    
    # 测试无效的操作类型
    try:
        processor.validate_config({'operation': 'invalid_operation'})
        print("❌ 应该捕获无效操作类型的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获无效类型错误: {e.message}")
    
    # 测试缺少 key 参数
    try:
        processor.validate_config({'operation': 'get'})
        print("❌ 应该捕获缺少 key 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 key 错误: {e.message}")
    
    # 测试缺少 value 参数
    try:
        processor.validate_config({'operation': 'set', 'key': 'test'})
        print("❌ 应该捕获缺少 value 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 value 错误: {e.message}")
    
    # 测试有效配置
    try:
        valid_config = {
            'operation': 'set',
            'key': 'test_key',
            'value': 'test_value',
            'host': 'localhost',
            'port': 6379,
            'db': 0
        }
        processor.validate_config(valid_config)
        print("✅ 有效配置验证通过")
    except Exception as e:
        print(f"❌ 有效配置验证失败: {e}")


def test_dynamic_rendering():
    """测试动态参数渲染"""
    print("\n" + "="*50)
    print("🎨 测试动态参数渲染")
    print("="*50)
    
    processor = RedisProcessor()
    context = MockContext()
    
    # 设置变量
    context.set_variable('redis_host', 'localhost')
    context.set_variable('redis_port', 6379)
    context.set_variable('redis_db', 0)
    context.set_variable('dynamic_key', 'dynamic_test_key')
    context.set_variable('dynamic_value', '动态渲染测试值')
    
    config = {
        'operation': 'set',
        'key': '${dynamic_key}',
        'value': '${dynamic_value}',
        'host': '${redis_host}',
        'port': '${redis_port}',
        'db': '${redis_db}',
        'output_variable': 'dynamic_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ 动态参数渲染测试成功:")
        print(f"   - 操作: {result['operation']}")
        print(f"   - 结果: {result['result']}")
        print(f"   - 上下文变量: {context.variables.get('dynamic_result', 'None')}")
        
    except Exception as e:
        print(f"❌ 动态参数渲染测试失败: {e}")


def main():
    """主函数"""
    print("🚀 开始测试 Redis 处理器")
    
    # 检查 Redis 模块是否可用
    try:
        import redis
        print("✅ Redis 模块已安装")
    except ImportError:
        print("❌ Redis 模块未安装，请运行: pip install redis")
        print("   跳过实际连接测试，只进行配置验证测试")
        
        # 只运行配置验证测试
        test_validation()
        return
    
    # 测试配置验证
    test_validation()
    
    # 测试各种操作
    test_string_operations()
    test_hash_operations()
    test_list_operations()
    test_set_operations()
    test_sorted_set_operations()
    test_key_operations()
    
    # 测试动态参数渲染
    test_dynamic_rendering()
    
    print("\n🎉 Redis 处理器测试完成")


if __name__ == '__main__':
    main()
