#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控主从架构系统状态
"""
import requests
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8100"

def clear_screen():
    """清屏 - 使用 ANSI 转义序列避免闪烁"""
    # 移动光标到屏幕顶部，而不是清空整个屏幕
    print('\033[H', end='')
    # 或者使用传统清屏（会闪烁）
    # import os
    # os.system('cls' if os.name == 'nt' else 'clear')

def get_queue_status():
    """获取队列状态"""
    try:
        resp = requests.get(f"{BASE_URL}/queue/status", timeout=3)
        if resp.status_code == 200:
            return resp.json()["data"]
    except Exception as e:
        return None

def get_workers_status():
    """获取执行机状态"""
    try:
        resp = requests.get(f"{BASE_URL}/workers", timeout=3)
        if resp.status_code == 200:
            return resp.json()["data"]
    except Exception as e:
        return None

def print_header():
    """打印头部"""
    print("=" * 80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def print_queue_status(queue_data):
    """打印队列状态"""
    if not queue_data:
        print("\n❌ 无法获取队列状态")
        return
    
    print("\n📊 队列状态:")
    print(f"  待处理 (Pending):   {queue_data.get('pending', 0):>5}")
    print(f"  执行中 (Running):   {queue_data.get('running', 0):>5}")
    print(f"  已完成 (Completed): {queue_data.get('completed', 0):>5}")
    print(f"  成功 (Success):     {queue_data.get('success', 0):>5}")
    print(f"  失败 (Failed):      {queue_data.get('failed', 0):>5}")
    print(f"  总计 (Total):       {queue_data.get('total', 0):>5}")
    
    # 计算成功率
    total = queue_data.get('completed', 0)
    if total > 0:
        success_rate = (queue_data.get('success', 0) / total) * 100
        print(f"  成功率:             {success_rate:>5.1f}%")

def print_workers_status(workers_data):
    """打印执行机状态"""
    if not workers_data:
        print("\n❌ 无法获取执行机状态")
        return
    
    workers = workers_data.get('workers', [])
    total = workers_data.get('total', 0)
    
    print(f"\n🤖 执行机状态 (共 {total} 个):")
    
    if not workers:
        print("  ⚠️  没有在线的执行机")
        return
    
    for i, worker in enumerate(workers, 1):
        worker_id = worker.get('worker_id', 'unknown')
        status = worker.get('status', 'unknown')
        current_tasks = worker.get('current_tasks', 0)
        max_tasks = worker.get('max_tasks', 0)
        cpu_usage = worker.get('cpu_usage', 0)
        memory_usage = worker.get('memory_usage', 0)
        ip = worker.get('ip', 'unknown')
        
        # 状态图标
        status_icon = "🟢" if status == "idle" else "🔵" if status == "busy" else "🔴"
        
        print(f"\n  {status_icon} 执行机 #{i}: {worker_id}")
        print(f"     状态:     {status}")
        print(f"     任务:     {current_tasks}/{max_tasks}")
        print(f"     CPU:      {cpu_usage:.1f}%")
        print(f"     内存:     {memory_usage:.1f}%")
        print(f"     IP:       {ip}")

def print_summary(queue_data, workers_data):
    """打印摘要"""
    print("\n" + "-" * 80)
    
    # 系统健康状态
    is_healthy = True
    issues = []
    
    if not workers_data or workers_data.get('total', 0) == 0:
        is_healthy = False
        issues.append("没有在线的执行机")
    
    if queue_data and queue_data.get('pending', 0) > 100:
        issues.append(f"待处理任务过多 ({queue_data['pending']})")
    
    if queue_data and queue_data.get('failed', 0) > 10:
        issues.append(f"失败任务较多 ({queue_data['failed']})")
    
    if is_healthy and not issues:
        print("✅ 系统运行正常")
    else:
        print("⚠️  系统存在问题:")
        for issue in issues:
            print(f"   - {issue}")
    
    print("-" * 80)
    print("\n按 Ctrl+C 退出监控")

def monitor():
    """主监控循环"""
    print("🚀 启动系统监控...")
    print("连接到:", BASE_URL)
    print()
    
    # 启用 ANSI 转义序列支持（Windows）
    import os
    if os.name == 'nt':
        os.system('')
    
    # 隐藏光标
    print('\033[?25l', end='')
    
    try:
        first_run = True
        while True:
            if not first_run:
                clear_screen()
            first_run = False
            
            # 获取数据
            queue_data = get_queue_status()
            workers_data = get_workers_status()
            
            # 打印信息
            print_header()
            print_queue_status(queue_data)
            print_workers_status(workers_data)
            print_summary(queue_data, workers_data)
            
            # 等待刷新
            time.sleep(5)
            
    except KeyboardInterrupt:
        # 显示光标
        print('\033[?25h', end='')
        print("\n\n👋 监控已停止")
        sys.exit(0)
    except Exception as e:
        # 显示光标
        print('\033[?25h', end='')
        print(f"\n\n❌ 监控错误: {e}")
        sys.exit(1)
    finally:
        # 确保退出时显示光标
        print('\033[?25h', end='')

if __name__ == "__main__":
    monitor()
