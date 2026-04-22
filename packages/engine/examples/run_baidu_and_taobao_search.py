#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百度搜索人工智能 + 淘宝搜索衣服示例
基于原始百度搜索workflow，同时操作两个网站
"""

import json
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from packages.engine.workflow_engine import WorkflowExecutor


def run_baidu_and_taobao_search():
    """运行百度和淘宝搜索工作流"""
    
    print("=" * 70)
    print("百度搜索人工智能 + 淘宝搜索衣服")
    print("=" * 70)
    print()
    
    # 加载workflow配置
    workflow_file = os.path.join(project_root, "examples", "baidu_and_taobao_search.json")
    
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
            
            # 显示搜索结果
            print("\n🔍 搜索结果:")
            
            # 百度搜索结果
            baidu_result_step = result.get_step("verify_search_results")
            if baidu_result_step and baidu_result_step.output:
                if isinstance(baidu_result_step.output, dict):
                    text = baidu_result_step.output.get('text', 'N/A')
                    print(f"  - 百度搜索结果: {text if text else 'N/A'}")
            
            # 百度搜索统计
            baidu_summary_step = result.get_step("get_baidu_summary")
            if baidu_summary_step and baidu_summary_step.output:
                if isinstance(baidu_summary_step.output, dict):
                    summary = baidu_summary_step.output.get('text', 'N/A')
                    print(f"  - 百度搜索统计: {summary}")
            
            # 淘宝搜索结果
            taobao_result_step = result.get_step("verify_taobao_results")
            if taobao_result_step and taobao_result_step.output:
                if isinstance(taobao_result_step.output, dict):
                    text = taobao_result_step.output.get('text', 'N/A')
                    print(f"  - 淘宝搜索结果: {text if text else 'N/A'}")
            
            # 截图信息
            baidu_screenshot_step = result.get_step("capture_baidu_screenshot")
            if baidu_screenshot_step and baidu_screenshot_step.output:
                if isinstance(baidu_screenshot_step.output, dict):
                    screenshot_path = baidu_screenshot_step.output.get('diagnostic_info', {}).get('screenshot_path')
                    if screenshot_path:
                        print(f"  - 百度截图已保存: {screenshot_path}")
            
            taobao_screenshot_step = result.get_step("capture_taobao_screenshot")
            if taobao_screenshot_step and taobao_screenshot_step.output:
                if isinstance(taobao_screenshot_step.output, dict):
                    screenshot_path = taobao_screenshot_step.output.get('diagnostic_info', {}).get('screenshot_path')
                    if screenshot_path:
                        print(f"  - 淘宝截图已保存: {screenshot_path}")
            
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
    exit_code = run_baidu_and_taobao_search()
    sys.exit(exit_code)
