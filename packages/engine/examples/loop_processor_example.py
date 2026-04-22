#!/usr/bin/env python3
"""
循环控制器处理器使用示例

演示三种循环类型的使用方法：
1. 次数循环 (count_loop)
2. While 循环 (while_loop)  
3. ForEach 循环 (foreach_loop)
"""

import json
import time
from typing import Any

from packages.engine.src.core.processors.workflow.loop_processor import LoopProcessor
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


def test_count_loop():
    """测试次数循环"""
    print("\n" + "="*50)
    print("🔄 测试次数循环 (count_loop)")
    print("="*50)
    
    processor = LoopProcessor()
    context = MockContext()
    
    # 设置一些测试变量
    context.set_variable('loop_count', 3)
    context.set_variable('delay_time', 0.1)
    
    config = {
        'loop_type': 'count_loop',
        'count': '${loop_count}',  # 使用变量
        'delay': '${delay_time}',
        'sub_nodes': [
            {'type': 'log_message', 'message': '执行子任务'},
            {'type': 'sleep', 'duration': 0.05}
        ],
        'output_variable': 'count_loop_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ 次数循环执行成功:")
        print(f"   - 循环类型: {result['loop_type']}")
        print(f"   - 执行次数: {result['iterations']}")
        print(f"   - 结果数量: {len(result['results'])}")
        print(f"   - 上下文变量: {context.variables.get('count_loop_result', 'None')}")
        
    except Exception as e:
        print(f"❌ 次数循环执行失败: {e}")


def test_while_loop():
    """测试 While 循环"""
    print("\n" + "="*50)
    print("🔄 测试 While 循环 (while_loop)")
    print("="*50)
    
    processor = LoopProcessor()
    context = MockContext()
    
    # 设置条件变量
    context.set_variable('max_attempts', 3)
    context.set_variable('current_attempt', 0)
    
    config = {
        'loop_type': 'while_loop',
        'condition': 'iteration < 3',  # 简单条件
        'max_iterations': 5,
        'delay': 0.1,
        'sub_nodes': [
            {'type': 'log_message', 'message': 'While 循环子任务'},
            {'type': 'variable_extractor', 'variable': 'current_attempt', 'value': '${loop_index}'}
        ],
        'output_variable': 'while_loop_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ While 循环执行成功:")
        print(f"   - 循环类型: {result['loop_type']}")
        print(f"   - 执行次数: {result['iterations']}")
        print(f"   - 最大次数: {result['max_iterations']}")
        print(f"   - 结果数量: {len(result['results'])}")
        
    except Exception as e:
        print(f"❌ While 循环执行失败: {e}")


def test_foreach_loop():
    """测试 ForEach 循环"""
    print("\n" + "="*50)
    print("🔄 测试 ForEach 循环 (foreach_loop)")
    print("="*50)
    
    processor = LoopProcessor()
    context = MockContext()
    
    # 设置测试数据
    test_items = ['item1', 'item2', 'item3', 'item4']
    context.set_variable('test_items', test_items)
    context.set_variable('delay_time', 0.1)
    
    config = {
        'loop_type': 'foreach_loop',
        'items': '${test_items}',  # 使用变量
        'item_variable': 'current_item',
        'index_variable': 'item_index',
        'delay': '${delay_time}',
        'sub_nodes': [
            {'type': 'log_message', 'message': '处理项目: ${current_item}'},
            {'type': 'variable_extractor', 'variable': 'processed_item', 'value': '${current_item}_processed'}
        ],
        'output_variable': 'foreach_loop_result'
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ ForEach 循环执行成功:")
        print(f"   - 循环类型: {result['loop_type']}")
        print(f"   - 执行次数: {result['iterations']}")
        print(f"   - 项目数量: {result['items_count']}")
        print(f"   - 结果数量: {len(result['results'])}")
        
        # 显示每个项目的处理结果
        for i, item_result in enumerate(result['results']):
            print(f"   - 项目 {i+1}: {item_result['item']} -> 处理完成")
        
    except Exception as e:
        print(f"❌ ForEach 循环执行失败: {e}")


def test_validation():
    """测试配置验证"""
    print("\n" + "="*50)
    print("🔍 测试配置验证")
    print("="*50)
    
    processor = LoopProcessor()
    
    # 测试缺少必需参数
    try:
        processor.validate_config({})
        print("❌ 应该捕获缺少 loop_type 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少字段错误: {e.message}")
    
    # 测试无效的循环类型
    try:
        processor.validate_config({'loop_type': 'invalid_type'})
        print("❌ 应该捕获无效循环类型的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获无效类型错误: {e.message}")
    
    # 测试次数循环缺少 count
    try:
        processor.validate_config({'loop_type': 'count_loop'})
        print("❌ 应该捕获缺少 count 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 count 错误: {e.message}")
    
    # 测试 While 循环缺少 condition
    try:
        processor.validate_config({'loop_type': 'while_loop'})
        print("❌ 应该捕获缺少 condition 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 condition 错误: {e.message}")
    
    # 测试 ForEach 循环缺少 items
    try:
        processor.validate_config({'loop_type': 'foreach_loop'})
        print("❌ 应该捕获缺少 items 的错误")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少 items 错误: {e.message}")
    
    # 测试有效配置
    try:
        valid_config = {
            'loop_type': 'count_loop',
            'count': 3,
            'sub_nodes': [],
            'delay': 0.1
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
    
    processor = LoopProcessor()
    context = MockContext()
    
    # 设置变量
    context.set_variable('loop_times', 2)
    context.set_variable('wait_time', 0.05)
    context.set_variable('result_name', 'dynamic_result')
    
    config = {
        'loop_type': 'count_loop',
        'count': '${loop_times}',
        'delay': '${wait_time}',
        'output_variable': '${result_name}',
        'sub_nodes': [
            {'type': 'log_message', 'message': '动态渲染测试 - 第 ${loop_index + 1} 次'}
        ]
    }
    
    try:
        result = processor.execute(config, context)
        print(f"✅ 动态参数渲染测试成功:")
        print(f"   - 执行次数: {result['iterations']}")
        print(f"   - 上下文变量: {context.variables}")
        
    except Exception as e:
        print(f"❌ 动态参数渲染测试失败: {e}")


def main():
    """主函数"""
    print("🚀 开始测试循环控制器处理器")
    
    # 测试配置验证
    test_validation()
    
    # 测试次数循环
    test_count_loop()
    
    # 测试 While 循环
    test_while_loop()
    
    # 测试 ForEach 循环
    test_foreach_loop()
    
    # 测试动态参数渲染
    test_dynamic_rendering()
    
    print("\n🎉 循环控制器处理器测试完成")


if __name__ == '__main__':
    main()
