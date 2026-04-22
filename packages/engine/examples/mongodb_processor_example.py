#!/usr/bin/env python3
"""
MongoDB 处理器使用示例

演示 MongoDB 处理器的各种操作：
1. 文档操作 (INSERT, FIND, UPDATE, DELETE)
2. 集合操作 (CREATE_COLLECTION, DROP_COLLECTION, LIST_COLLECTIONS)
3. 索引操作 (CREATE_INDEX, DROP_INDEX, LIST_INDEXES)
4. 聚合操作 (AGGREGATE)
5. 计数操作 (COUNT)
"""

import json
import time
from typing import Any

from packages.engine.src.core.processors.data.mongodb_processor import MongoDBProcessor
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


def test_document_operations():
    """测试文档操作"""
    print("\n" + "="*50)
    print("📄 测试文档操作")
    print("="*50)
    
    processor = MongoDBProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('db_name', 'test_db')
    context.set_variable('collection_name', 'users')
    context.set_variable('user_doc', {
        'name': '张三',
        'age': 25,
        'email': 'zhangsan@example.com',
        'city': '北京'
    })
    
    # 测试 INSERT_ONE 操作
    config = {
        'operation': 'insert_one',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'document': '${user_doc}',
        'host': 'localhost',
        'port': 27017,
        'output_variable': 'insert_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ INSERT_ONE 操作成功: {result['result']}")
        inserted_id = result['result']['inserted_id']
        context.set_variable('inserted_id', inserted_id)
    except Exception as e:
        print(f"❌ INSERT_ONE 操作失败: {e}")
        return
    
    # 测试 FIND_ONE 操作
    config = {
        'operation': 'find_one',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'filter': {'_id': '${inserted_id}'},
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ FIND_ONE 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ FIND_ONE 操作失败: {e}")
    
    # 测试 UPDATE_ONE 操作
    config = {
        'operation': 'update_one',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'filter': {'_id': '${inserted_id}'},
        'update': {'$set': {'age': 26, 'updated_at': '2024-01-01'}},
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ UPDATE_ONE 操作成功: 匹配 {result['result']['matched_count']} 个，修改 {result['result']['modified_count']} 个")
    except Exception as e:
        print(f"❌ UPDATE_ONE 操作失败: {e}")
    
    # 测试 FIND 操作
    config = {
        'operation': 'find',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'filter': {'age': {'$gte': 20}},
        'projection': {'name': 1, 'age': 1, 'email': 1},
        'sort': [('age', -1)],
        'limit': 10,
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ FIND 操作成功: 找到 {len(result['result'])} 个文档")
    except Exception as e:
        print(f"❌ FIND 操作失败: {e}")


def test_bulk_operations():
    """测试批量操作"""
    print("\n" + "="*50)
    print("📦 测试批量操作")
    print("="*50)
    
    processor = MongoDBProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('db_name', 'test_db')
    context.set_variable('collection_name', 'products')
    context.set_variable('product_docs', [
        {'name': '商品1', 'price': 100, 'category': '电子产品'},
        {'name': '商品2', 'price': 200, 'category': '服装'},
        {'name': '商品3', 'price': 300, 'category': '电子产品'}
    ])
    
    # 测试 INSERT_MANY 操作
    config = {
        'operation': 'insert_many',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'documents': '${product_docs}',
        'host': 'localhost',
        'port': 27017,
        'output_variable': 'bulk_insert_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ INSERT_MANY 操作成功: 插入了 {len(result['result']['inserted_ids'])} 个文档")
    except Exception as e:
        print(f"❌ INSERT_MANY 操作失败: {e}")
        return
    
    # 测试 COUNT_DOCUMENTS 操作
    config = {
        'operation': 'count_documents',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'filter': {'category': '电子产品'},
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ COUNT_DOCUMENTS 操作成功: 电子产品有 {result['result']} 个")
    except Exception as e:
        print(f"❌ COUNT_DOCUMENTS 操作失败: {e}")


def test_collection_operations():
    """测试集合操作"""
    print("\n" + "="*50)
    print("🗂️ 测试集合操作")
    print("="*50)
    
    processor = MongoDBProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('db_name', 'test_db')
    context.set_variable('new_collection', 'test_collection')
    
    # 测试 CREATE_COLLECTION 操作
    config = {
        'operation': 'create_collection',
        'database': '${db_name}',
        'collection': '${new_collection}',
        'options': {'capped': False, 'size': 1000000},
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ CREATE_COLLECTION 操作成功: {result['result']}")
    except Exception as e:
        print(f"❌ CREATE_COLLECTION 操作失败: {e}")
    
    # 测试 LIST_COLLECTIONS 操作
    config = {
        'operation': 'list_collections',
        'database': '${db_name}',
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ LIST_COLLECTIONS 操作成功: 找到 {len(result['result'])} 个集合")
        for collection in result['result']:
            print(f"   - {collection['name']}")
    except Exception as e:
        print(f"❌ LIST_COLLECTIONS 操作失败: {e}")


def test_index_operations():
    """测试索引操作"""
    print("\n" + "="*50)
    print("🔍 测试索引操作")
    print("="*50)
    
    processor = MongoDBProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('db_name', 'test_db')
    context.set_variable('collection_name', 'users')
    
    # 测试 CREATE_INDEX 操作
    config = {
        'operation': 'create_index',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'index': [('email', 1)],
        'options': {'unique': True, 'name': 'email_unique'},
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ CREATE_INDEX 操作成功: 索引名 {result['result']}")
    except Exception as e:
        print(f"❌ CREATE_INDEX 操作失败: {e}")
    
    # 测试 LIST_INDEXES 操作
    config = {
        'operation': 'list_indexes',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ LIST_INDEXES 操作成功: 找到 {len(result['result'])} 个索引")
        for index in result['result']:
            print(f"   - {index['name']}")
    except Exception as e:
        print(f"❌ LIST_INDEXES 操作失败: {e}")


def test_aggregation_operations():
    """测试聚合操作"""
    print("\n" + "="*50)
    print("📊 测试聚合操作")
    print("="*50)
    
    processor = MongoDBProcessor()
    context = MockContext()
    
    # 设置测试变量
    context.set_variable('db_name', 'test_db')
    context.set_variable('collection_name', 'orders')
    context.set_variable('aggregation_pipeline', [
        {'$match': {'status': 'completed'}},
        {'$group': {
            '_id': '$category',
            'total_amount': {'$sum': '$amount'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'total_amount': -1}}
    ])
    
    # 测试 AGGREGATE 操作
    config = {
        'operation': 'aggregate',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'pipeline': '${aggregation_pipeline}',
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ AGGREGATE 操作成功: 聚合结果 {len(result['result'])} 个")
        for item in result['result']:
            print(f"   - {item}")
    except Exception as e:
        print(f"❌ AGGREGATE 操作失败: {e}")
    
    # 测试 DISTINCT 操作
    config = {
        'operation': 'distinct',
        'database': '${db_name}',
        'collection': '${collection_name}',
        'field': 'category',
        'filter': {'status': 'completed'},
        'host': 'localhost',
        'port': 27017
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ DISTINCT 操作成功: 唯一值 {result['result']}")
    except Exception as e:
        print(f"❌ DISTINCT 操作失败: {e}")


def test_validation():
    """测试配置验证"""
    print("\n" + "="*50)
    print("🔍 测试配置验证")
    print("="*50)
    
    processor = MongoDBProcessor()
    
    # 测试缺少必需参数
    try:
        processor.validate_config({})
        print("❌ 应该捕获缺少 operation 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少字段错误: {e.message}")
    
    # 测试缺少 database 参数
    try:
        processor.validate_config({'operation': 'find'})
        print("❌ 应该捕获缺少 database 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 database 错误: {e.message}")
    
    # 测试缺少 collection 参数
    try:
        processor.validate_config({'operation': 'find', 'database': 'test'})
        print("❌ 应该捕获缺少 collection 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 collection 错误: {e.message}")
    
    # 测试缺少 filter 参数
    try:
        processor.validate_config({'operation': 'find', 'database': 'test', 'collection': 'users'})
        print("❌ 应该捕获缺少 filter 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 filter 错误: {e.message}")
    
    # 测试有效配置
    try:
        valid_config = {
            'operation': 'find',
            'database': 'test_db',
            'collection': 'users',
            'filter': {'age': {'$gte': 18}},
            'host': 'localhost',
            'port': 27017
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
    
    processor = MongoDBProcessor()
    context = MockContext()
    
    # 设置变量
    context.set_variable('mongodb_host', 'localhost')
    context.set_variable('mongodb_port', 27017)
    context.set_variable('dynamic_db', 'dynamic_test_db')
    context.set_variable('dynamic_collection', 'dynamic_test_collection')
    context.set_variable('dynamic_doc', {'name': '动态文档', 'value': '动态值'})
    
    config = {
        'operation': 'insert_one',
        'database': '${dynamic_db}',
        'collection': '${dynamic_collection}',
        'document': '${dynamic_doc}',
        'host': '${mongodb_host}',
        'port': '${mongodb_port}',
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
    print("🚀 开始测试 MongoDB 处理器")
    
    # 检查 MongoDB 模块是否可用
    try:
        from pymongo import MongoClient
        print("✅ MongoDB 模块已安装")
    except ImportError:
        print("❌ MongoDB 模块未安装，请运行: pip install pymongo")
        print("   跳过实际连接测试，只进行配置验证测试")
        
        # 只运行配置验证测试
        test_validation()
        return
    
    # 测试配置验证
    test_validation()
    
    # 测试各种操作
    test_document_operations()
    test_bulk_operations()
    test_collection_operations()
    test_index_operations()
    test_aggregation_operations()
    
    # 测试动态参数渲染
    test_dynamic_rendering()
    
    print("\n🎉 MongoDB 处理器测试完成")


if __name__ == '__main__':
    main()
