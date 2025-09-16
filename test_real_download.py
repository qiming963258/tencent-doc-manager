#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际下载功能（使用真实Cookie）
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
    "cookie": cookie_string,  # 使用真实Cookie
    "advanced_settings": {
        "upload_option": "new",
        "verbose_logging": True
    }
}

def test_download():
    """测试实际下载功能"""
    print("="*60)
    print("开始测试实际下载功能（使用真实Cookie）")
    print("="*60)
    
    # 1. 测试模块状态
    print("\n[1] 检查模块加载状态...")
    modules_resp = requests.get(f"{BASE_URL}/api/modules")
    if modules_resp.status_code == 200:
        modules = modules_resp.json()
        print(f"✅ 模块状态:")
        for module, status in modules.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {module}: {status}")
    
    # 2. 启动工作流
    print("\n[2] 启动下载工作流...")
    print(f"   基线URL: {TEST_CONFIG['baseline_url']}")
    print(f"   Cookie长度: {len(cookie_string)} 字符")
    
    start_resp = requests.post(
        f"{BASE_URL}/api/start",
        json=TEST_CONFIG,
        headers={"Content-Type": "application/json"}
    )
    
    if start_resp.status_code == 200:
        result = start_resp.json()
        print(f"✅ 工作流启动: {result}")
        
        # 3. 监控状态（监控30秒）
        print("\n[3] 监控执行状态（30秒）...")
        for i in range(30):
            time.sleep(1)
            status_resp = requests.get(f"{BASE_URL}/api/status")
            if status_resp.status_code == 200:
                status = status_resp.json()
                print(f"   [{i+1:2}/30] 状态: {status['status']:10} 进度: {status['progress']:3}% 任务: {status['current_task']}")
                
                # 显示最新日志
                if status['logs']:
                    latest_log = status['logs'][-1]
                    if latest_log['level'] in ['ERROR', 'WARNING']:
                        print(f"        [{latest_log['level']}] {latest_log['message']}")
                
                # 如果出错，显示详细错误
                if status['status'] == 'error':
                    print(f"\n❌ 执行出错!")
                    for log in status['logs'][-10:]:
                        if log['level'] == 'ERROR':
                            print(f"   {log['message']}")
                    break
                    
                # 如果完成，显示结果
                if status['status'] == 'completed':
                    print(f"\n✅ 执行完成!")
                    if status['results']:
                        print(f"   结果: {json.dumps(status['results'], indent=2, ensure_ascii=False)}")
                    break
    else:
        print(f"❌ 工作流启动失败: {start_resp.status_code}")
        print(f"   响应: {start_resp.text}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_download()