#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XXL-Job 处理器测试运行脚本

运行 XXL-Job 处理器的测试用例
"""

from packages.engine.examples.xxljob_processor_example import (
    test_xxljob_processor_config_validation,
    test_xxljob_processor_required_and_optional_keys,
    test_xxljob_processor_basic,
    test_xxljob_processor_with_variables,
    test_xxljob_processor_with_json_param,
    test_xxljob_processor_with_db_client
)


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始测试 XXL-Job 处理器")
    print("=" * 60)
    print("⚠️  注意: 功能测试需要 XXL-Job 服务器运行")
    print("⚠️  注意: 请根据实际情况修改配置参数")
    print("=" * 60)
    
    # 测试配置验证（不需要服务器）
    print("\n" + "="*50)
    print("1️⃣  测试配置验证")
    print("="*50)
    test_xxljob_processor_config_validation()
    
    # 测试配置键（不需要服务器）
    print("\n" + "="*50)
    print("2️⃣  测试配置键")
    print("="*50)
    test_xxljob_processor_required_and_optional_keys()
    
    # 功能测试（需要服务器，默认注释）
    print("\n" + "="*50)
    print("3️⃣  功能测试（需要 XXL-Job 服务器）")
    print("="*50)
    print("💡 提示: 取消注释下面的代码来运行功能测试")
    print("💡 提示: 请确保 XXL-Job 服务器运行，并修改配置参数")
    
    # 取消注释以下代码来运行功能测试
    # print("\n" + "-"*50)
    # print("测试基本功能")
    # print("-"*50)
    # test_xxljob_processor_basic()
    
    # print("\n" + "-"*50)
    # print("测试变量功能")
    # print("-"*50)
    # test_xxljob_processor_with_variables()
    
    # print("\n" + "-"*50)
    # print("测试 JSON 参数")
    # print("-"*50)
    # test_xxljob_processor_with_json_param()
    
    # print("\n" + "-"*50)
    # print("测试数据库客户端")
    # print("-"*50)
    # test_xxljob_processor_with_db_client()
    
    print("\n" + "="*60)
    print("🎉 XXL-Job 处理器测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
