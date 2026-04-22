# -*- coding: utf-8 -*-
"""
百度搜索功能测试脚本
测试百度搜索功能并验证搜索结果
"""

import json
import os

from packages.engine.workflow_engine import WorkflowExecutor


def run_baidu_search_test():
    """运行百度搜索测试"""
    
    print("=" * 70)
    print("百度搜索功能测试")
    print("=" * 70)
    
    # 读取workflow配置
    workflow_file = os.path.join(os.path.dirname(__file__), "baidu_search_test.json")
    
    try:
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        print("\n✅ 已加载workflow配置")
        print(f"📁 配置文件: {workflow_file}")
        print(f"📊 节点数量: {len(workflow.get('nodes', []))}")
        
        # 执行workflow
        print("\n🚀 开始执行测试...\n")
        
        executor = WorkflowExecutor(workflow)
        result = executor.execute()
        
        # 输出结果
        print("\n" + "=" * 70)
        if result.status == "success":
            print("✅ 测试执行成功！")
            print("=" * 70)
            
            # 显示关键结果
            print("\n📊 测试结果摘要:")
            
            # 搜索结果验证
            verify_result = result.get_node_result("verify_search_results")
            if verify_result:
                print(f"\n🔍 搜索结果验证:")
                result_data = verify_result.get('data', {})
                text = result_data.get('text', '')
                if text:
                    print(f"  ✓ 成功获取搜索结果")
                    print(f"  ✓ 结果文本长度: {len(text)} 字符")
                else:
                    print(f"  ⚠️  未能获取搜索结果文本")
            
            # 诊断信息
            diagnostic_result = result.get_node_result("capture_screenshot")
            if diagnostic_result:
                print(f"\n📸 诊断信息:")
                diagnostic_info = diagnostic_result.get('diagnostic_info', {})
                screenshot_path = diagnostic_info.get('screenshot_path')
                if screenshot_path:
                    print(f"  ✓ 截图已保存: {screenshot_path}")
                
                console_log_count = diagnostic_info.get('console_log_count', 0)
                print(f"  ✓ 控制台日志: {console_log_count} 条")
            
            print("\n" + "=" * 70)
            print("🎉 百度搜索功能测试完成！")
            
        else:
            print("❌ 测试执行失败！")
            print("=" * 70)
            
            # 获取失败的步骤
            failed_steps = result.get_failed_steps()
            if failed_steps:
                print(f"\n失败节点数: {len(failed_steps)}")
                for step in failed_steps:
                    print(f"\n节点ID: {step.node_id}")
                    print(f"节点类型: {step.node_type}")
                    if step.error:
                        print(f"错误信息: {step.error}")
            
            # 显示元数据
            if result.metadata:
                print(f"\n元数据: {result.metadata}")
        
        return result
        
    except FileNotFoundError:
        print(f"\n❌ 错误: 找不到workflow配置文件: {workflow_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"\n❌ 错误: workflow配置文件格式错误: {e}")
        return None
    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = run_baidu_search_test()
    
    # 根据测试结果返回退出码
    if result and result.status == "success":
        sys.exit(0)
    else:
        sys.exit(1)
