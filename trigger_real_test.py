#!/usr/bin/env python3
"""
触发8093真实全链路测试 - 使用真实腾讯文档
测试文档：测试文档-出国销售计划表
URL: https://docs.qq.com/sheet/DWEFNU25TemFnZXJN
"""

import json
import requests
import time
from datetime import datetime

print("=" * 70)
print("🚀 触发8093真实全链路测试")
print("=" * 70)

# 1. 检查基线文件是否存在
print("\n1️⃣ 检查基线文件...")
baseline_api = "http://localhost:8089/api/baseline-files"
baseline_response = requests.get(baseline_api)
baseline_data = baseline_response.json()

if baseline_data.get('success'):
    files = baseline_data.get('data', {}).get('files', [])
    if files:
        print(f"✅ 找到 {len(files)} 个基线文件")
        for file in files[:3]:  # 显示前3个
            print(f"   - {file['filename']}")
    else:
        print("⚠️ 没有基线文件，需要先下载基线")
else:
    print("❌ 无法获取基线文件状态")

# 2. 配置目标文档URL
target_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
print(f"\n2️⃣ 目标文档: 测试文档-出国销售计划表")
print(f"   URL: {target_url}")

# 3. 触发8093工作流
print("\n3️⃣ 触发8093工作流...")

trigger_data = {
    "url": target_url,
    "timestamp": datetime.now().isoformat()
}

try:
    # 触发下载和处理
    response = requests.post(
        "http://localhost:8093/api/trigger",
        json=trigger_data,
        timeout=5
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ 工作流触发成功")
            print(f"   - 工作流ID: {result.get('workflow_id', 'N/A')}")
        else:
            print(f"⚠️ 触发返回: {result.get('message', '未知错误')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")

except requests.exceptions.Timeout:
    print("⏱️ 请求超时，但工作流可能已开始")
except Exception as e:
    print(f"❌ 触发失败: {e}")

# 4. 等待并检查工作流状态
print("\n4️⃣ 检查工作流状态...")
time.sleep(3)

try:
    status_response = requests.get("http://localhost:8093/api/status")
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"   当前状态: {status.get('current_state', 'unknown')}")

        # 显示最近的日志
        logs = status.get('recent_logs', [])
        if logs:
            print("\n   最近日志:")
            for log in logs[-5:]:  # 显示最后5条
                print(f"   {log}")
    else:
        print("   无法获取状态")
except Exception as e:
    print(f"   状态检查失败: {e}")

# 5. 提示后续步骤
print("\n" + "=" * 70)
print("📋 后续步骤:")
print("1. 访问 http://202.140.143.88:8093 查看实时日志")
print("2. 等待工作流完成（约2-3分钟）")
print("3. 检查生成的综合打分文件")
print("4. 在8089查看热力图是否正确显示column_modifications")
print("=" * 70)

# 6. 检查是否会生成综合打分
print("\n5️⃣ 预期结果:")
print("✅ 应该生成包含真实数据的综合打分文件")
print("✅ column_modifications_by_table字段应该包含真实修改数据")
print("✅ 使用标准19列（配置中心定义）")
print("✅ 不应该有虚拟的'测试表格'数据")