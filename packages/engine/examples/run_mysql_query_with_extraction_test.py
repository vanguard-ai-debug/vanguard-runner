#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL查询并提取变量测试用例
基于日志生成的测试用例

测试场景：
1. 执行MySQL查询，查询策略配置
2. 从查询结果中提取变量（strategy_name 和 trade_id）
3. 验证提取的变量是否正确
"""

import json
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from packages.engine.workflow_engine import WorkflowExecutor


def test_mysql_query_with_extraction():
    """测试MySQL查询并提取变量"""
    
    # 加载工作流定义
    workflow_file = os.path.join(os.path.dirname(__file__), "mysql_query_with_extraction_workflow.json")
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflow_data = json.load(f)
    
    print("=" * 80)
    print("MySQL查询并提取变量测试")
    print("=" * 80)
    print(f"工作流名称: {workflow_data.get('work_name', 'N/A')}")
    print(f"节点数量: {len(workflow_data.get('nodes', []))}")
    print()
    
    # 创建工作流执行器
    executor = WorkflowExecutor(workflow_data)
    
    # 加载工作流定义中的变量到执行上下文
    if "variables" in workflow_data:
        variables = workflow_data["variables"]
        for key, value in variables.items():
            executor.context.set_variable(key, value)
        print(f"已加载 {len(variables)} 个变量到执行上下文: {list(variables.keys())}")
        print()
    
    # 执行工作流
    print("开始执行工作流...")
    print("-" * 80)
    
    try:
        execution_result = executor.execute()
        
        # 检查执行结果
        print("\n" + "=" * 80)
        print("执行结果")
        print("=" * 80)
        print(f"执行状态: {execution_result.status.value}")
        print(f"总节点数: {len(execution_result.steps)}")
        print()
        
        # 遍历所有步骤
        for i, step in enumerate(execution_result.steps, 1):
            print(f"\n节点 {i}: {step.node_id} ({step.node_type})")
            print(f"  状态: {step.status.value}")
            if step.duration:
                print(f"  耗时: {step.duration:.3f}s")
            
            # 显示节点日志
            if step.logs:
                print(f"  日志长度: {len(step.logs)} 字符")
                # 完整显示所有日志
                print(f"  日志内容:\n{step.logs}")
            
            # 显示错误信息
            if step.error:
                print(f"  错误: {step.error}")
        
        # 验证提取的变量
        print("\n" + "=" * 80)
        print("验证提取的变量")
        print("=" * 80)
        
        context = executor.context
        strategy_name = context.get_variable("strategy_name")
        trade_id = context.get_variable("trade_id")
        
        print(f"strategy_name: {strategy_name}")
        print(f"trade_id: {trade_id}")
        
        # 验证变量是否正确提取
        if strategy_name:
            print(f"✅ strategy_name 提取成功: {strategy_name}")
        else:
            print("❌ strategy_name 未提取到")
        
        if trade_id:
            print(f"✅ trade_id 提取成功: {trade_id}")
        else:
            print("❌ trade_id 未提取到")
        
        # 验证预期值
        expected_strategy_name = "cynthiaAutoTest测试策略"
        if strategy_name == expected_strategy_name:
            print(f"✅ strategy_name 值正确: {strategy_name}")
        else:
            print(f"❌ strategy_name 值不匹配，期望: {expected_strategy_name}, 实际: {strategy_name}")
        
        expected_trade_id = 141
        if trade_id == expected_trade_id:
            print(f"✅ trade_id 值正确: {trade_id}")
        else:
            print(f"❌ trade_id 值不匹配，期望: {expected_trade_id}, 实际: {trade_id}")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
        return execution_result
        
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_mysql_query_with_extraction()
    
    if result and result.status.value == "success":
        print("\n✅ 所有测试通过")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
