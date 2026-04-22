#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XXL-Job 单节点批量执行测试脚本

使用 workflow 批量执行接口测试单个节点的 XXL-Job 工作流
"""

import json
import requests
from typing import Dict, Any, List


def load_workflow_from_file(file_path: str) -> Dict[str, Any]:
    """从文件加载工作流配置"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_batch_request(workflow: Dict[str, Any], variables: Dict[str, Any] = None, run_id: str = None) -> Dict[str, Any]:
    """
    创建批量执行请求
    
    Args:
        workflow: 工作流定义
        variables: 初始变量（可选）
        run_id: 运行ID（可选）
    
    Returns:
        批量执行请求字典
    """
    batch_item = {
        "workflow": workflow,
    }
    
    if variables:
        batch_item["variables"] = variables
    
    if run_id:
        batch_item["runId"] = run_id
    
    return {
        "workflows": [batch_item],
        "priority": "normal",
        "maxBatchSize": 1000
    }


def batch_execute_workflow_api(base_url: str, request_data: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    调用批量执行工作流API
    
    Args:
        base_url: API基础URL（例如：http://localhost:8000）
        request_data: 批量执行请求数据
        headers: 请求头（可选，用于认证等）
    
    Returns:
        API响应结果
    """
    url = f"{base_url}/workflow/execute/batch"
    
    if headers is None:
        headers = {
            "Content-Type": "application/json"
        }
    
    try:
        response = requests.post(url, json=request_data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        raise


def query_batch_status(base_url: str, tracer_id: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    查询批量执行状态
    
    Args:
        base_url: API基础URL
        tracer_id: 追踪ID
        headers: 请求头（可选）
    
    Returns:
        状态查询结果
    """
    url = f"{base_url}/workflow/{tracer_id}/batch/status"
    
    if headers is None:
        headers = {
            "Content-Type": "application/json"
        }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 状态查询失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        raise


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 XXL-Job 单节点批量执行测试")
    print("=" * 60)
    
    # 配置参数
    api_base_url = "http://localhost:8000"  # 根据实际情况修改
    workflow_file = Path(__file__).parent / "xxljob_single_node_batch_test.json"
    
    # 检查文件是否存在
    if not workflow_file.exists():
        print(f"❌ 工作流文件不存在: {workflow_file}")
        return
    
    # 加载工作流
    print(f"\n📂 加载工作流文件: {workflow_file}")
    workflow = load_workflow_from_file(str(workflow_file))
    print(f"✅ 工作流加载成功: {workflow.get('work_name', 'Unknown')}")
    print(f"   工作流ID: {workflow.get('work_id', 'Unknown')}")
    print(f"   节点数量: {len(workflow.get('nodes', []))}")
    
    # 提取变量（可选，可以覆盖）
    variables = workflow.get("variables", {})
    
    # 创建批量执行请求
    print("\n📝 创建批量执行请求...")
    batch_request = create_batch_request(
        workflow=workflow,
        variables=variables,
        run_id="test_run_001"
    )
    
    print(f"✅ 批量请求创建成功")
    print(f"   工作流数量: {len(batch_request['workflows'])}")
    print(f"   优先级: {batch_request['priority']}")
    
    # 打印请求详情（可选）
    print("\n📋 批量执行请求详情:")
    print(json.dumps(batch_request, indent=2, ensure_ascii=False))
    
    # 调用批量执行API
    print(f"\n🌐 调用批量执行API: {api_base_url}/workflow/execute/batch")
    print("⚠️  注意: 请确保API服务正在运行")
    print("⚠️  注意: 请根据实际情况修改 api_base_url")
    
    try:
        response = batch_execute_workflow_api(api_base_url, batch_request)
        
        print("\n✅ 批量执行请求提交成功!")
        print(f"📊 响应结果:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 提取tracer_id
        if response.get("code") == 200 and "data" in response:
            tracer_id = response.get("data", {}).get("tracerId")
            if tracer_id:
                print(f"\n🔍 追踪ID: {tracer_id}")
                print(f"💡 可以使用以下命令查询执行状态:")
                print(f"   GET {api_base_url}/workflow/{tracer_id}/batch/status")
                
                # 可选：自动查询状态（等待一段时间后）
                # import time
                # print("\n⏳ 等待5秒后查询状态...")
                # time.sleep(5)
                # status = query_batch_status(api_base_url, tracer_id)
                # print(f"📊 执行状态:")
                # print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print(f"\n⚠️  响应格式异常，请检查API返回结果")
            
    except Exception as e:
        print(f"\n❌ 批量执行失败: {str(e)}")
        print(f"💡 提示:")
        print(f"   1. 检查API服务是否运行: {api_base_url}")
        print(f"   2. 检查网络连接")
        print(f"   3. 检查认证信息（如需要）")
        return
    
    print("\n" + "=" * 60)
    print("🎉 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
