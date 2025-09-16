#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版对比系统
"""

import requests
import json
import time
import sys

def test_comparison_system():
    """测试对比系统的完整流程"""
    
    base_url = "http://localhost:8094"
    
    print("="*60)
    print("🧪 腾讯文档对比测试系统 - 功能测试")
    print("="*60)
    
    # 1. 健康检查
    print("\n1️⃣ 执行健康检查...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        health_data = response.json()
        print(f"   ✅ 系统状态: {health_data['status']}")
        print(f"   📦 模块状态:")
        for module, status in health_data.get('modules_status', {}).items():
            status_icon = "✅" if status else "❌"
            print(f"      {status_icon} {module}")
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")
        return False
    
    # 2. 创建对比任务
    print("\n2️⃣ 创建对比任务...")
    
    # 测试数据
    test_data = {
        "baseline_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
        "baseline_cookie": "",  # 留空使用系统Cookie
        "baseline_format": "csv",
        "target_url": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",
        "target_cookie": "",
        "target_format": "csv"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/compare",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        result = response.json()
        
        if result.get('success'):
            task_id = result['task_id']
            print(f"   ✅ 任务创建成功")
            print(f"   📋 任务ID: {task_id}")
        else:
            print(f"   ❌ 任务创建失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False
    
    # 3. 监控任务状态
    print("\n3️⃣ 监控任务执行...")
    print("   ⏳ 等待任务完成...")
    
    max_wait = 60  # 最多等待60秒
    check_interval = 2  # 每2秒检查一次
    elapsed = 0
    last_progress = -1
    
    while elapsed < max_wait:
        try:
            response = requests.get(f"{base_url}/api/task/{task_id}", timeout=5)
            task_status = response.json()
            
            # 显示进度
            progress = task_status.get('progress', 0)
            if progress != last_progress:
                status = task_status.get('status', 'unknown')
                step = task_status.get('current_step', '')
                print(f"   📊 进度: {progress}% - {step} (状态: {status})")
                last_progress = progress
            
            # 检查是否完成
            if task_status.get('status') == 'completed':
                print(f"   ✅ 任务完成!")
                
                # 显示结果
                result = task_status.get('result', {})
                if result:
                    print("\n4️⃣ 对比结果:")
                    print(f"   📊 总差异数: {result.get('total_differences', 0)}")
                    print(f"   📈 相似度: {result.get('similarity_score', 0)}%")
                    print(f"   ⚠️  风险等级: {result.get('risk_level', 'N/A')}")
                    print(f"   ⏱️  处理时间: {result.get('processing_time', 0)}秒")
                
                return True
                
            elif task_status.get('status') == 'failed':
                print(f"   ❌ 任务失败: {task_status.get('error')}")
                return False
                
        except Exception as e:
            print(f"   ⚠️ 状态检查失败: {e}")
        
        time.sleep(check_interval)
        elapsed += check_interval
    
    print(f"   ⏱️ 任务超时 (等待了{max_wait}秒)")
    return False

def test_api_endpoints():
    """测试各个API端点"""
    
    base_url = "http://localhost:8094"
    
    print("\n" + "="*60)
    print("🔌 API端点测试")
    print("="*60)
    
    endpoints = [
        ("GET", "/", "主页"),
        ("GET", "/health", "健康检查"),
        ("GET", "/api/tasks", "任务列表"),
    ]
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            status_icon = "✅" if response.status_code == 200 else "❌"
            print(f"{status_icon} {method} {endpoint} - {description} (状态码: {response.status_code})")
            
        except Exception as e:
            print(f"❌ {method} {endpoint} - {description} (错误: {e})")

def main():
    """主测试函数"""
    
    print("\n🚀 开始测试增强版对比系统...")
    print(f"⏰ 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 确保服务正在运行
    try:
        response = requests.get("http://localhost:8094/health", timeout=2)
        if response.status_code != 200:
            print("❌ 服务未运行，请先启动 comparison_test_ui_enhanced.py")
            print("   运行命令: python3 comparison_test_ui_enhanced.py")
            return
    except:
        print("❌ 无法连接到服务 (端口8094)")
        print("   请确保服务正在运行:")
        print("   python3 /root/projects/tencent-doc-manager/comparison_test_ui_enhanced.py")
        return
    
    # 执行测试
    test_api_endpoints()
    
    if test_comparison_system():
        print("\n" + "="*60)
        print("✅ 所有测试通过!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ 测试失败，请检查日志")
        print("="*60)

if __name__ == "__main__":
    main()