#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查8093系统关键步骤
"""

import requests
import json
import time

# 读取真实Cookie
with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
    cookie_data = json.load(f)
    cookie_string = cookie_data.get('cookie_string', '')

# 测试配置
BASE_URL = "http://localhost:8093"
TEST_CONFIG = {
    "baseline_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",  # 测试版本-小红书部门
    "target_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",  # 同一个文档作为测试
    "cookie": cookie_string,
    "advanced_settings": {
        "upload_option": "new",
        "verbose_logging": True
    }
}

def quick_check():
    """快速检查关键步骤"""
    print("="*60)
    print("🚀 8093系统快速检查")
    print("="*60)
    
    # 1. 检查模块状态
    print("\n✅ 检查模块加载...")
    modules_resp = requests.get(f"{BASE_URL}/api/modules")
    if modules_resp.status_code == 200:
        modules = modules_resp.json()
        loaded = sum(1 for v in modules.values() if v)
        total = len(modules)
        print(f"   模块加载: {loaded}/{total} 成功")
        if loaded < total:
            for module, status in modules.items():
                if not status:
                    print(f"   ❌ {module} 未加载")
    
    # 2. 启动工作流
    print("\n✅ 启动测试工作流...")
    start_resp = requests.post(
        f"{BASE_URL}/api/start",
        json=TEST_CONFIG,
        headers={"Content-Type": "application/json"}
    )
    
    if start_resp.status_code == 200:
        result = start_resp.json()
        execution_id = result.get('execution_id')
        print(f"   执行ID: {execution_id}")
        
        # 3. 监控关键步骤（最多60秒）
        print("\n✅ 监控执行进度...")
        last_task = ""
        completed_tasks = []
        
        for i in range(60):
            time.sleep(1)
            status_resp = requests.get(f"{BASE_URL}/api/status")
            if status_resp.status_code == 200:
                status = status_resp.json()
                
                # 记录完成的任务
                if status['current_task'] != last_task:
                    if last_task and last_task not in completed_tasks:
                        completed_tasks.append(last_task)
                        print(f"   ✓ 完成: {last_task}")
                    last_task = status['current_task']
                    if last_task:
                        print(f"   → 执行: {last_task}")
                
                # 检查状态
                if status['status'] == 'error':
                    print(f"\n❌ 执行失败!")
                    # 显示错误日志
                    for log in status['logs'][-5:]:
                        if log['level'] == 'ERROR':
                            print(f"   错误: {log['message']}")
                    break
                    
                elif status['status'] == 'completed':
                    print(f"\n🎉 执行成功!")
                    results = status.get('results', {})
                    
                    # 显示结果统计
                    if results:
                        print("\n📊 执行结果:")
                        if results.get('baseline_file'):
                            print(f"   ✓ 基线文件: {os.path.basename(results['baseline_file'])}")
                        if results.get('target_file'):
                            print(f"   ✓ 目标文件: {os.path.basename(results['target_file'])}")
                        if results.get('score_file'):
                            print(f"   ✓ 打分文件: {os.path.basename(results['score_file'])}")
                        if results.get('marked_file'):
                            print(f"   ✓ 标记文件: {os.path.basename(results['marked_file'])}")
                        if results.get('upload_url'):
                            print(f"   ✓ 上传链接: {results['upload_url']}")
                        if results.get('execution_time'):
                            print(f"   ⏱ 执行时间: {results['execution_time']}")
                    break
        else:
            print(f"\n⚠️ 执行超时（60秒）")
            print(f"   当前任务: {last_task}")
            print(f"   已完成任务: {len(completed_tasks)}个")
    else:
        print(f"❌ 启动失败: {start_resp.status_code}")
    
    print("\n" + "="*60)
    print("检查完成")
    print("="*60)

if __name__ == "__main__":
    import os
    quick_check()