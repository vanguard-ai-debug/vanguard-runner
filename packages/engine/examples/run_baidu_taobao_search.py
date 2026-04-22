#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百度搜索Agent + 淘宝搜索衣服示例
演示如何在同一个工作流中操作多个网站并切换
"""

import json
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from packages.engine.workflow_engine import WorkflowExecutor


def run_baidu_taobao_search():
    """运行百度和淘宝搜索工作流"""
    
    print("=" * 70)
    print("百度搜索Agent + 淘宝搜索衣服")
    print("=" * 70)
    print()
    
    # 加载workflow配置
    workflow_file = os.path.join(project_root, "examples", "baidu_taobao_search_example.json")
    
    try:
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_config = json.load(f)
        
        print("✅ 已加载workflow配置")
        print(f"📁 配置文件: {workflow_file}")
        print(f"📊 节点数量: {len(workflow_config.get('nodes', []))}")
        print()
        
        print("🚀 开始执行测试...")
        print()
        
        # 创建执行器（需要传入workflow_data）
        executor = WorkflowExecutor(workflow_config)
        
        # 执行workflow
        result = executor.execute()
        
        # 检查执行结果
        failed_steps = result.get_failed_steps()
        
        if result.status.value == "success":
            print()
            print("=" * 70)
            print("✅ 测试执行成功！")
            print("=" * 70)
            
            # 显示关键结果
            if failed_steps:
                print(f"\n⚠️  有 {len(failed_steps)} 个步骤失败:")
                for step in failed_steps:
                    print(f"  - {step.node_id}: {step.error}")
            
            # 显示搜索统计
            print("\n📊 执行统计:")
            print(f"  - 总节点数: {len(result.steps)}")
            successful_steps = result.get_successful_steps()
            print(f"  - 成功节点: {len(successful_steps)}")
            print(f"  - 失败节点: {len(failed_steps)}")
            
            # 尝试获取搜索结果
            print("\n🔍 搜索结果:")
            search_step = result.get_step("get_baidu_search_count")
            if search_step and search_step.output:
                if isinstance(search_step.output, dict):
                    search_count = search_step.output.get('text', 'N/A')
                    print(f"  - 百度搜索结果数量: {search_count}")
                else:
                    print(f"  - 百度搜索结果: {search_step.output}")
            else:
                print("  - 未获取到搜索结果")
            
            return 0
            
        else:
            print()
            print("=" * 70)
            print("❌ 测试执行失败！")
            print("=" * 70)
            
            if failed_steps:
                print(f"\n❌ 失败步骤 ({len(failed_steps)} 个):")
                for step in failed_steps:
                    print(f"\n  节点ID: {step.node_id}")
                    print(f"  节点类型: {step.node_type}")
                    print(f"  错误信息: {step.error}")
                    if step.output:
                        print(f"  输出: {step.output}")
            
            return 1
            
    except FileNotFoundError:
        print(f"❌ 错误: 找不到配置文件 {workflow_file}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ 错误: JSON解析失败 - {str(e)}")
        return 1
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 清理资源
        try:
            from packages.engine.src.core.ui.playwright.ui_manager import ui_manager
            ui_manager.run_async(ui_manager.close_browser)()
        except:
            pass


if __name__ == "__main__":
    exit_code = run_baidu_taobao_search()
    sys.exit(exit_code)
