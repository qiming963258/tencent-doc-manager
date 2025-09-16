#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试8093端口API下载功能
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:8093"
TEST_CONFIG = {
    "baseline_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",  # 测试版本-小红书部门
    "target_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",  # 同一个文档作为测试
    "cookie": "test_cookie_string",  # 测试Cookie
    "advanced_settings": {
        "upload_option": "new",
        "verbose_logging": True
    }
}

def test_api():
    """测试API功能"""
    print("="*60)
    print("开始测试8093端口API功能")
    print("="*60)
    
    # 1. 测试模块状态
    print("\n[1] 检查模块加载状态...")
    modules_resp = requests.get(f"{BASE_URL}/api/modules")
    if modules_resp.status_code == 200:
        modules = modules_resp.json()
        print(f"✅ 模块状态获取成功:")
        for module, status in modules.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {module}: {status}")
    else:
        print(f"❌ 无法获取模块状态: {modules_resp.status_code}")
    
    # 2. 启动工作流
    print("\n[2] 启动测试工作流...")
    start_resp = requests.post(
        f"{BASE_URL}/api/start",
        json=TEST_CONFIG,
        headers={"Content-Type": "application/json"}
    )
    
    if start_resp.status_code == 200:
        result = start_resp.json()
        print(f"✅ 工作流启动成功: {result}")
        execution_id = result.get('execution_id')
        
        # 3. 监控状态（只监控10秒）
        print("\n[3] 监控执行状态（10秒）...")
        for i in range(10):
            time.sleep(1)
            status_resp = requests.get(f"{BASE_URL}/api/status")
            if status_resp.status_code == 200:
                status = status_resp.json()
                print(f"   [{i+1}/10] 状态: {status['status']}, 进度: {status['progress']}%, 任务: {status['current_task']}")
                
                # 显示最新日志
                if status['logs']:
                    latest_log = status['logs'][-1]
                    print(f"        最新日志: [{latest_log['level']}] {latest_log['message']}")
                
                # 如果出错，显示错误信息
                if status['status'] == 'error':
                    print(f"\n❌ 执行出错!")
                    for log in status['logs'][-5:]:
                        if log['level'] == 'ERROR':
                            print(f"   错误: {log['message']}")
                    break
                    
                # 如果完成，显示结果
                if status['status'] == 'completed':
                    print(f"\n✅ 执行完成!")
                    if status['results']:
                        print(f"   结果: {json.dumps(status['results'], indent=2, ensure_ascii=False)}")
                    break
            else:
                print(f"   无法获取状态: {status_resp.status_code}")
    else:
        print(f"❌ 工作流启动失败: {start_resp.status_code}")
        print(f"   响应: {start_resp.text}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_api()