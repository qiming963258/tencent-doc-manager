#!/usr/bin/env python3
"""快速测试8094端口API"""
import requests
import json

# 测试端点
url = "http://localhost:8094/api/compare"

# 真实Cookie（从config.json读取）
with open('/root/projects/tencent-doc-manager/config.json', 'r') as f:
    config = json.load(f)
    cookie = config['cookie']

# 测试数据
form_data = {
    'baseline_type': 'url',
    'baseline_url': 'https://docs.qq.com/sheet/DWEFNU25TemFnZXJN',
    'baseline_cookie': cookie,
    'target_url': 'https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr',
    'target_cookie': cookie
}

print("发送请求到8094端口...")
print(f"Cookie长度: {len(cookie)}")

try:
    # 使用FormData格式发送
    response = requests.post(url, data=form_data, timeout=30)
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ 成功!")
            print(f"基线文件: {result.get('baseline_info', {})}")
            print(f"目标文件: {result.get('target_info', {})}")
            print(f"对比统计: {result.get('comparison_stats', {})}")
        else:
            print(f"❌ 失败: {result.get('error', '未知错误')}")
    else:
        print(f"HTTP错误: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("❌ 请求超时")
except Exception as e:
    print(f"❌ 异常: {e}")