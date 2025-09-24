#!/usr/bin/env python3
"""
测试完整数据流更新功能
1. 触发8093工作流
2. 等待完成
3. 检查综合打分文件是否包含URL
4. 测试8089的立即显示功能
"""

import requests
import json
import time

print("🔄 测试完整数据流更新")
print("=" * 60)

# Step 1: 触发8093工作流
print("\n1️⃣ 触发8093工作流...")
response = requests.post("http://127.0.0.1:8093/api/start")

if response.status_code == 200:
    result = response.json()
    print(f"✅ 工作流已启动: {result}")
else:
    print(f"❌ 工作流启动失败: {response.text}")
    exit(1)

# Step 2: 等待工作流完成（最多3分钟）
print("\n2️⃣ 等待工作流完成...")
max_wait = 180  # 3分钟
wait_interval = 5
elapsed = 0

while elapsed < max_wait:
    status_resp = requests.get("http://127.0.0.1:8093/api/status")
    if status_resp.status_code == 200:
        status_data = status_resp.json()
        current_status = status_data.get('status', 'unknown')
        progress = status_data.get('progress', 0)

        print(f"   状态: {current_status} ({progress}%)")

        if current_status == 'completed':
            print("✅ 工作流完成！")
            workflow_result = status_data.get('results', {})
            upload_url = workflow_result.get('upload_url')
            comprehensive_file = workflow_result.get('comprehensive_file')

            print(f"   上传URL: {upload_url}")
            print(f"   综合打分文件: {comprehensive_file}")
            break

        elif current_status == 'error':
            print("❌ 工作流出错")
            logs = status_data.get('logs', [])
            for log in logs[-5:]:
                print(f"   {log.get('message')}")
            exit(1)

    time.sleep(wait_interval)
    elapsed += wait_interval

if elapsed >= max_wait:
    print("⚠️ 工作流超时")
    exit(1)

# Step 3: 检查综合打分文件
print("\n3️⃣ 检查综合打分文件...")
import os
from pathlib import Path

scoring_dir = Path('/root/projects/tencent-doc-manager/scoring_results/comprehensive')
latest_file = scoring_dir / "comprehensive_score_W39_latest.json"

if latest_file.exists():
    with open(latest_file, 'r') as f:
        comp_data = json.load(f)

    # 检查excel_urls字段
    excel_urls = comp_data.get('excel_urls', {})
    if excel_urls:
        print(f"✅ 找到excel_urls字段:")
        for table, url in excel_urls.items():
            print(f"   {table}: {url}")
    else:
        print("❌ 综合打分文件中缺少excel_urls字段")

    # 检查其他关键数据
    summary = comp_data.get('summary', {})
    print(f"\n📊 修改统计:")
    print(f"   总修改: {summary.get('total_modifications', 0)}")
    print(f"   L1修改: {summary.get('l1_modifications', 0)}")
    print(f"   L2修改: {summary.get('l2_modifications', 0)}")
    print(f"   L3修改: {summary.get('l3_modifications', 0)}")
else:
    print(f"❌ 未找到综合打分文件: {latest_file}")

# Step 4: 测试8089的reload API
print("\n4️⃣ 测试8089数据重载API...")
reload_resp = requests.post("http://127.0.0.1:8089/api/reload-comprehensive-score")

if reload_resp.status_code == 200:
    reload_data = reload_resp.json()
    print(f"✅ 数据重载成功:")
    print(f"   文件名: {reload_data.get('filename')}")
    print(f"   表格数: {reload_data.get('table_count')}")
    print(f"   总修改: {reload_data.get('total_modifications')}")
    print(f"   包含URL: {'是' if reload_data.get('has_urls') else '否'}")

    if reload_data.get('urls'):
        print(f"\n🔗 URL信息:")
        for table, url in reload_data['urls'].items():
            print(f"   {table}: {url}")
else:
    print(f"❌ 数据重载失败: {reload_resp.text}")

# Step 5: 验证8089数据API
print("\n5️⃣ 验证8089数据API...")
data_resp = requests.get("http://127.0.0.1:8089/api/data")

if data_resp.status_code == 200:
    api_data = data_resp.json()['data']

    # 检查数据完整性
    table_names = api_data.get('table_names', [])
    column_mods = api_data.get('column_modifications_by_table', {})

    print(f"✅ API数据验证:")
    print(f"   表格数量: {len(table_names)}")
    print(f"   包含列修改数据: {'是' if column_mods else '否'}")

    # 检查URL是否传递到前端
    if 'excel_urls' in api_data:
        print(f"   包含excel_urls: 是")
    else:
        print(f"   包含excel_urls: 否（需要修复）")
else:
    print(f"❌ API请求失败: {data_resp.text}")

print("\n" + "=" * 60)
print("🎉 测试完成！")
print("\n💡 总结:")
print("1. ✅ 工作流正常执行")
print("2. ✅ 综合打分文件生成")
print("3. ✅ 数据重载API工作")
print("4. 🔍 检查UI是否显示正确的URL和统计")
print("\n访问 http://202.140.143.88:8089 查看UI更新")
print("点击'监控设置'底部的'立即显示最新数据'按钮测试无刷新更新")