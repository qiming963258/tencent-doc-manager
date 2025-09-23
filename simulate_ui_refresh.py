#!/usr/bin/env python3
"""
模拟8089监控界面的"立即刷新"按钮操作
使用真实腾讯文档进行全链路测试
"""

import json
import requests
import time
from datetime import datetime

print("=" * 70)
print("🔄 模拟监控界面「立即刷新」按钮")
print("=" * 70)

# 1. 先通过8089下载基线文件
print("\n1️⃣ 下载基线文件...")
baseline_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"

baseline_payload = {
    "url": baseline_url,
    "name": "测试文档-出国销售计划表-基线"
}

try:
    response = requests.post(
        "http://localhost:8089/api/baseline-files",
        json=baseline_payload,
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ 基线下载成功: {result.get('filename', 'unknown')}")
        else:
            print(f"⚠️ 基线下载失败: {result.get('error', 'unknown')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
except Exception as e:
    print(f"❌ 请求失败: {e}")

time.sleep(2)

# 2. 通过8093启动工作流
print("\n2️⃣ 启动8093工作流...")

# 模拟UI的启动请求
start_payload = {
    "url": baseline_url,
    "autoMode": True,
    "skipDownload": False  # 确保下载最新文档
}

try:
    response = requests.post(
        "http://localhost:8093/api/start",
        json=start_payload,
        timeout=5
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 工作流启动: {result.get('message', 'started')}")
    else:
        print(f"⚠️ 状态码: {response.status_code}")

except requests.exceptions.Timeout:
    print("⏱️ 请求超时（正常，工作流已开始）")
except Exception as e:
    print(f"❌ 启动失败: {e}")

# 3. 监控工作流进度
print("\n3️⃣ 监控工作流进度...")

for i in range(30):  # 监控30秒
    time.sleep(1)
    try:
        status_response = requests.get(
            "http://localhost:8093/api/status",
            timeout=2
        )
        if status_response.status_code == 200:
            status = status_response.json()
            current_state = status.get('current_state', 'unknown')

            # 显示进度
            if i % 5 == 0:  # 每5秒显示一次
                print(f"   [{i:2d}s] 状态: {current_state}")

            # 检查是否完成
            if current_state in ['completed', 'final']:
                print(f"\n✅ 工作流完成！")

                # 显示工作流结果
                if 'workflow_state' in status:
                    ws = status['workflow_state']
                    if ws.get('comprehensive_score_file'):
                        print(f"   综合打分文件: {ws['comprehensive_score_file']}")
                    if ws.get('marked_file'):
                        print(f"   标记Excel文件: {ws['marked_file']}")
                    if ws.get('upload_url'):
                        print(f"   上传URL: {ws['upload_url']}")
                break

    except Exception:
        pass  # 忽略临时错误

# 4. 检查生成的综合打分文件
print("\n4️⃣ 检查生成的综合打分文件...")

try:
    # 获取最新的综合打分文件
    response = requests.get("http://localhost:8089/api/list_comprehensive_files")
    if response.status_code == 200:
        result = response.json()
        files = result.get('files', [])
        if files:
            latest_file = files[0]  # 最新的文件
            print(f"✅ 找到最新文件: {latest_file['filename']}")

            # 加载并检查内容
            load_response = requests.get(
                f"http://localhost:8089/api/load-comprehensive-data?file={latest_file['path']}"
            )
            if load_response.status_code == 200:
                data = load_response.json()
                if data.get('success'):
                    score_data = data.get('data', {})

                    # 检查是否包含column_modifications_by_table
                    if 'column_modifications_by_table' in score_data:
                        print("✅ 包含column_modifications_by_table字段")

                        # 检查表名
                        tables = list(score_data['column_modifications_by_table'].keys())
                        print(f"   表格: {tables}")

                        if '测试表格' in tables:
                            print("❌ 警告：发现虚拟的'测试表格'数据！")
                        else:
                            print("✅ 没有虚拟数据，使用真实文档")

                    else:
                        print("❌ 缺少column_modifications_by_table字段")

                    # 检查是否使用标准19列
                    column_names = score_data.get('column_names', [])
                    if len(column_names) == 19:
                        print(f"✅ 使用标准19列")
                        # 检查第14-16列是否正确
                        if column_names[14] == '完成链接':
                            print("   ✅ 第14列正确：完成链接")
                        else:
                            print(f"   ❌ 第14列错误：{column_names[14]}")

except Exception as e:
    print(f"❌ 检查失败: {e}")

# 5. 总结
print("\n" + "=" * 70)
print("📊 测试总结:")
print("1. ✅ 应该使用真实的腾讯文档数据")
print("2. ✅ 表名应该是真实文档名，不是'测试表格'")
print("3. ✅ 应该包含column_modifications_by_table字段")
print("4. ✅ 应该使用标准19列（来自配置中心）")
print("5. ✅ 数据应该来自真实CSV对比，不是虚拟构造")
print("=" * 70)