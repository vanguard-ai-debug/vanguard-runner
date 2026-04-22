# -*- coding: utf-8 -*-
"""
增强UI处理器使用示例
展示新增的UI处理器功能的使用方法
"""

import json
from packages.engine.workflow_engine import WorkflowExecutor


# ============= 示例1：智能等待和选择器自愈 =============
def example_smart_wait_and_healing():
    """智能等待和选择器自愈示例"""
    workflow = {
        "nodes": [
            {
                "id": "launch",
                "type": "browser_launch",
                "data": {
                    "config": {
                        "operation": "launch",
                        "browser_type": "chromium",
                        "headless": False
                    }
                }
            },
            {
                "id": "navigate",
                "type": "ui_navigation",
                "data": {
                    "config": {
                        "operation": "navigate",
                        "url": "https://example.com"
                    }
                }
            },
            {
                "id": "smart_wait",
                "type": "smart_wait",
                "data": {
                    "config": {
                        "operation": "smart_wait",
                        "wait_types": ["network_idle", "dom_stable"],
                        "timeout": 30000
                    }
                }
            },
            {
                "id": "wait_element",
                "type": "smart_wait",
                "data": {
                    "config": {
                        "operation": "element_visible",
                        "selector": "#dynamic-button",
                        "timeout": 30000,
                        "max_retries": 3,
                        "backoff_factor": 1.5
                    }
                }
            }
        ],
        "edges": [
            {"source": "launch", "target": "navigate"},
            {"source": "navigate", "target": "smart_wait"},
            {"source": "smart_wait", "target": "wait_element"}
        ]
    }
    
    executor = WorkflowExecutor(workflow)
    result = executor.execute()
    
    print(f"✅ 智能等待示例完成: {result.status}")


# ============= 示例2：可观测性和诊断 =============
def example_observability():
    """可观测性和诊断示例"""
    workflow = {
        "nodes": [
            {
                "id": "launch",
                "type": "browser_launch",
                "data": {
                    "config": {
                        "operation": "launch",
                        "browser_type": "chromium"
                    }
                }
            },
            {
                "id": "start_monitoring",
                "type": "observability",
                "data": {
                    "config": {
                        "operation": "start_monitoring",
                        "monitor_types": ["console", "network", "performance"]
                    }
                }
            },
            {
                "id": "navigate",
                "type": "ui_navigation",
                "data": {
                    "config": {
                        "operation": "navigate",
                        "url": "https://example.com"
                    }
                }
            },
            {
                "id": "capture_diagnostic",
                "type": "observability",
                "data": {
                    "config": {
                        "operation": "capture_diagnostic",
                        "node_id": "page_loaded",
                        "capture_screenshot": True,
                        "capture_dom": True,
                        "capture_console": True,
                        "capture_network": True,
                        "capture_performance": True
                    }
                }
            },
            {
                "id": "stop_monitoring",
                "type": "observability",
                "data": {
                    "config": {
                        "operation": "stop_monitoring"
                    }
                }
            },
            {
                "id": "save_report",
                "type": "observability",
                "data": {
                    "config": {
                        "operation": "save_diagnostic_report",
                        "report_name": "test_diagnostic_report"
                    }
                }
            }
        ],
        "edges": [
            {"source": "launch", "target": "start_monitoring"},
            {"source": "start_monitoring", "target": "navigate"},
            {"source": "navigate", "target": "capture_diagnostic"},
            {"source": "capture_diagnostic", "target": "stop_monitoring"},
            {"source": "stop_monitoring", "target": "save_report"}
        ]
    }
    
    executor = WorkflowExecutor(workflow)
    result = executor.execute()
    
    # 获取诊断信息
    diagnostic_data = result.get_node_result("capture_diagnostic")
    if diagnostic_data:
        print(f"📊 诊断信息:")
        print(f"  - 截图: {diagnostic_data['diagnostic_info']['screenshot_path']}")
        print(f"  - DOM: {diagnostic_data['diagnostic_info']['dom_path']}")
        print(f"  - 控制台日志: {diagnostic_data['diagnostic_info']['console_log_count']}条")
        print(f"  - 网络请求: {diagnostic_data['diagnostic_info']['network_request_count']}个")


# ============= 示例3：AI辅助元素定位 =============
def example_ai_assisted():
    """AI辅助元素定位示例"""
    workflow = {
        "nodes": [
            {
                "id": "launch",
                "type": "browser_launch",
                "data": {
                    "config": {
                        "operation": "launch",
                        "browser_type": "chromium"
                    }
                }
            },
            {
                "id": "navigate",
                "type": "ui_navigation",
                "data": {
                    "config": {
                        "operation": "navigate",
                        "url": "https://example.com/login"
                    }
                }
            },
            {
                "id": "find_by_description",
                "type": "ai_assisted",
                "data": {
                    "config": {
                        "operation": "find_by_description",
                        "description": "用户名输入框",
                        "use_ai": False  # 使用启发式方法
                    }
                }
            },
            {
                "id": "heal_selector",
                "type": "ai_assisted",
                "data": {
                    "config": {
                        "operation": "auto_heal_selector",
                        "failed_selector": "#old-button-id",
                        "healing_strategy": "heuristic"
                    }
                }
            },
            {
                "id": "suggest_selectors",
                "type": "ai_assisted",
                "data": {
                    "config": {
                        "operation": "suggest_selectors",
                        "element_description": "登录按钮"
                    }
                }
            }
        ],
        "edges": [
            {"source": "launch", "target": "navigate"},
            {"source": "navigate", "target": "find_by_description"},
            {"source": "find_by_description", "target": "heal_selector"},
            {"source": "heal_selector", "target": "suggest_selectors"}
        ]
    }
    
    executor = WorkflowExecutor(workflow)
    result = executor.execute()
    
    print(f"🤖 AI辅助示例完成: {result.status}")


# ============= 示例4：视觉回归测试 =============
def example_visual_regression():
    """视觉回归测试示例"""
    workflow = {
        "nodes": [
            {
                "id": "launch",
                "type": "browser_launch",
                "data": {
                    "config": {
                        "operation": "launch",
                        "browser_type": "chromium"
                    }
                }
            },
            {
                "id": "navigate",
                "type": "ui_navigation",
                "data": {
                    "config": {
                        "operation": "navigate",
                        "url": "https://example.com"
                    }
                }
            },
            # 首次运行：捕获基线
            {
                "id": "capture_baseline",
                "type": "visual_regression",
                "data": {
                    "config": {
                        "operation": "capture_baseline",
                        "baseline_name": "homepage_v1",
                        "full_page": True
                    }
                }
            },
            # 后续运行：进行对比
            # {
            #     "id": "visual_compare",
            #     "type": "visual_regression",
            #     "data": {
            #         "config": {
            #             "operation": "visual_compare",
            #             "baseline_name": "homepage_v1",
            #             "threshold": 0.01,  # 1%差异阈值
            #             "save_diff": True
            #         }
            #     }
            # },
            # 获取对比报告
            {
                "id": "get_report",
                "type": "visual_regression",
                "data": {
                    "config": {
                        "operation": "get_comparison_report"
                    }
                }
            }
        ],
        "edges": [
            {"source": "launch", "target": "navigate"},
            {"source": "navigate", "target": "capture_baseline"},
            {"source": "capture_baseline", "target": "get_report"}
        ]
    }
    
    executor = WorkflowExecutor(workflow)
    result = executor.execute()
    
    baseline_data = result.get_node_result("capture_baseline")
    if baseline_data:
        print(f"🎨 基线图像已保存: {baseline_data['baseline_path']}")


# ============= 示例5：性能监控 =============
def example_performance_monitoring():
    """性能监控示例"""
    workflow = {
        "nodes": [
            {
                "id": "launch",
                "type": "browser_launch",
                "data": {
                    "config": {
                        "operation": "launch",
                        "browser_type": "chromium"
                    }
                }
            },
            {
                "id": "measure_page_load",
                "type": "performance",
                "data": {
                    "config": {
                        "operation": "measure_page_load",
                        "url": "https://example.com",
                        "wait_until": "networkidle"
                    }
                }
            },
            {
                "id": "get_metrics",
                "type": "performance",
                "data": {
                    "config": {
                        "operation": "get_performance_metrics"
                    }
                }
            },
            {
                "id": "analyze_resources",
                "type": "performance",
                "data": {
                    "config": {
                        "operation": "analyze_resource_loading"
                    }
                }
            },
            {
                "id": "generate_report",
                "type": "performance",
                "data": {
                    "config": {
                        "operation": "generate_performance_report",
                        "report_name": "performance_test_report"
                    }
                }
            }
        ],
        "edges": [
            {"source": "launch", "target": "measure_page_load"},
            {"source": "measure_page_load", "target": "get_metrics"},
            {"source": "get_metrics", "target": "analyze_resources"},
            {"source": "analyze_resources", "target": "generate_report"}
        ]
    }
    
    executor = WorkflowExecutor(workflow)
    result = executor.execute()
    
    perf_data = result.get_node_result("measure_page_load")
    if perf_data and perf_data['performance_metrics']:
        metrics = perf_data['performance_metrics']
        print(f"⚡ 性能指标:")
        print(f"  - 总加载时间: {metrics['total_time']}ms")
        print(f"  - 首次渲染: {metrics['first_paint']}ms")
        print(f"  - DOM就绪: {metrics['dom_interactive']}ms")


# ============= 示例6：响应式测试 =============
def example_responsive_testing():
    """响应式测试示例"""
    workflow = {
        "nodes": [
            {
                "id": "launch",
                "type": "browser_launch",
                "data": {
                    "config": {
                        "operation": "launch",
                        "browser_type": "chromium"
                    }
                }
            },
            {
                "id": "test_responsive",
                "type": "responsive",
                "data": {
                    "config": {
                        "operation": "test_responsive_layout",
                        "url": "https://example.com",
                        "devices": ["iphone_13", "ipad_pro", "desktop_fhd"],
                        "capture_screenshots": True
                    }
                }
            },
            {
                "id": "test_orientation",
                "type": "responsive",
                "data": {
                    "config": {
                        "operation": "test_orientation",
                        "device_name": "iphone_13",
                        "url": "https://example.com"
                    }
                }
            },
            {
                "id": "test_breakpoints",
                "type": "responsive",
                "data": {
                    "config": {
                        "operation": "test_breakpoints",
                        "url": "https://example.com",
                        "breakpoints": [
                            {"name": "mobile", "width": 375},
                            {"name": "tablet", "width": 768},
                            {"name": "desktop", "width": 1024}
                        ]
                    }
                }
            }
        ],
        "edges": [
            {"source": "launch", "target": "test_responsive"},
            {"source": "test_responsive", "target": "test_orientation"},
            {"source": "test_orientation", "target": "test_breakpoints"}
        ]
    }
    
    executor = WorkflowExecutor(workflow)
    result = executor.execute()
    
    responsive_data = result.get_node_result("test_responsive")
    if responsive_data:
        print(f"📱 响应式测试完成:")
        for device, data in responsive_data['results'].items():
            print(f"  - {device}: {data['screenshot_path']}")


# ============= 示例7：综合测试工作流 =============
def example_comprehensive_workflow():
    """综合测试工作流示例"""
    workflow = {
        "nodes": [
            # 1. 启动浏览器
            {
                "id": "launch",
                "type": "browser_launch",
                "data": {
                    "config": {
                        "operation": "launch",
                        "browser_type": "chromium",
                        "headless": False
                    }
                }
            },
            
            # 2. 开始监控
            {
                "id": "start_monitoring",
                "type": "observability",
                "data": {
                    "config": {
                        "operation": "start_monitoring",
                        "monitor_types": ["console", "network", "performance"]
                    }
                }
            },
            
            # 3. 测量页面加载性能
            {
                "id": "measure_performance",
                "type": "performance",
                "data": {
                    "config": {
                        "operation": "measure_page_load",
                        "url": "https://example.com"
                    }
                }
            },
            
            # 4. 智能等待页面加载完成
            {
                "id": "smart_wait",
                "type": "smart_wait",
                "data": {
                    "config": {
                        "operation": "smart_wait",
                        "wait_types": ["network_idle", "dom_stable"]
                    }
                }
            },
            
            # 5. 捕获视觉基线
            {
                "id": "visual_baseline",
                "type": "visual_regression",
                "data": {
                    "config": {
                        "operation": "capture_baseline",
                        "baseline_name": "homepage",
                        "full_page": True
                    }
                }
            },
            
            # 6. 响应式测试
            {
                "id": "responsive_test",
                "type": "responsive",
                "data": {
                    "config": {
                        "operation": "test_responsive_layout",
                        "url": "https://example.com",
                        "devices": ["iphone_13", "desktop_fhd"]
                    }
                }
            },
            
            # 7. AI辅助查找元素
            {
                "id": "find_element",
                "type": "ai_assisted",
                "data": {
                    "config": {
                        "operation": "find_by_description",
                        "description": "搜索按钮"
                    }
                }
            },
            
            # 8. 捕获完整诊断信息
            {
                "id": "capture_diagnostic",
                "type": "observability",
                "data": {
                    "config": {
                        "operation": "capture_diagnostic",
                        "node_id": "final_state",
                        "capture_screenshot": True,
                        "capture_dom": True,
                        "capture_console": True,
                        "capture_network": True,
                        "capture_performance": True
                    }
                }
            },
            
            # 9. 停止监控
            {
                "id": "stop_monitoring",
                "type": "observability",
                "data": {
                    "config": {
                        "operation": "stop_monitoring"
                    }
                }
            },
            
            # 10. 生成报告
            {
                "id": "generate_reports",
                "type": "performance",
                "data": {
                    "config": {
                        "operation": "generate_performance_report",
                        "report_name": "comprehensive_test_report"
                    }
                }
            }
        ],
        "edges": [
            {"source": "launch", "target": "start_monitoring"},
            {"source": "start_monitoring", "target": "measure_performance"},
            {"source": "measure_performance", "target": "smart_wait"},
            {"source": "smart_wait", "target": "visual_baseline"},
            {"source": "visual_baseline", "target": "responsive_test"},
            {"source": "responsive_test", "target": "find_element"},
            {"source": "find_element", "target": "capture_diagnostic"},
            {"source": "capture_diagnostic", "target": "stop_monitoring"},
            {"source": "stop_monitoring", "target": "generate_reports"}
        ]
    }
    
    print("🚀 开始执行综合测试工作流...")
    
    executor = WorkflowExecutor(workflow)
    result = executor.execute()
    
    if result.status == "success":
        print("\n✅ 综合测试工作流执行成功！")
        
        # 打印关键结果
        print("\n📊 关键结果:")
        
        # 性能数据
        perf_data = result.get_node_result("measure_performance")
        if perf_data:
            print(f"\n⚡ 性能指标:")
            metrics = perf_data.get('performance_metrics', {})
            print(f"  - 总加载时间: {metrics.get('total_time', 'N/A')}ms")
            print(f"  - 首次渲染: {metrics.get('first_paint', 'N/A')}ms")
        
        # 视觉基线
        visual_data = result.get_node_result("visual_baseline")
        if visual_data:
            print(f"\n🎨 视觉基线:")
            print(f"  - 基线图像: {visual_data.get('baseline_path', 'N/A')}")
        
        # 响应式测试
        responsive_data = result.get_node_result("responsive_test")
        if responsive_data:
            print(f"\n📱 响应式测试:")
            for device in responsive_data.get('results', {}).keys():
                print(f"  - {device}: ✓")
        
        # 诊断信息
        diagnostic_data = result.get_node_result("capture_diagnostic")
        if diagnostic_data:
            print(f"\n🔍 诊断信息:")
            info = diagnostic_data.get('diagnostic_info', {})
            print(f"  - 截图: {info.get('screenshot_path', 'N/A')}")
            print(f"  - 控制台日志: {info.get('console_log_count', 0)}条")
            print(f"  - 网络请求: {info.get('network_request_count', 0)}个")
    else:
        print(f"\n❌ 测试失败: {result.error}")


if __name__ == "__main__":
    print("=" * 60)
    print("Workflow Engine - 增强UI处理器示例")
    print("=" * 60)
    
    # 运行示例（取消注释需要运行的示例）
    
    # example_smart_wait_and_healing()
    # example_observability()
    # example_ai_assisted()
    # example_visual_regression()
    # example_performance_monitoring()
    # example_responsive_testing()
    
    # 运行综合示例
    example_comprehensive_workflow()
