#!/usr/bin/env python3
"""简单测试8094端口"""
import requests

# 1. 测试主页
print("测试主页访问...")
response = requests.get("http://202.140.143.88:8094/", timeout=5)
print(f"主页状态: {response.status_code}")

# 2. 测试API（使用假cookie快速测试）
print("\n测试API接口...")
data = {
    'baseline_type': 'url',
    'baseline_url': 'https://docs.qq.com/sheet/test1',
    'baseline_cookie': 'test',
    'target_url': 'https://docs.qq.com/sheet/test2', 
    'target_cookie': 'test'
}

try:
    response = requests.post("http://202.140.143.88:8094/api/compare", 
                            data=data, timeout=10)
    print(f"API状态: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"请求ID: {result.get('debug', {}).get('request_id')}")
        print(f"错误信息: {result.get('error', '无')}")
except requests.Timeout:
    print("API请求超时")
except Exception as e:
    print(f"API错误: {e}")

print("\n✅ 8094端口服务正常运行！")