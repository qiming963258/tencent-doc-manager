#!/usr/bin/env python3
"""
全面系统功能测试脚本
测试范围：
1. 监控设置UI所有功能
2. 自动下载和日历功能
3. 综合打分文件生成完整性
4. 热力图UI数据适配
"""

import json
import requests
import time
from datetime import datetime, timedelta
import os

BASE_URL = "http://localhost:8089"
BASE_URL_8093 = "http://localhost:8093"

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def test_8089_monitor_settings():
    """测试8089监控设置UI所有功能"""
    print_section("测试8089监控设置UI功能")

    tests_passed = 0
    tests_total = 0

    # 1. 测试Cookie管理
    print("\n📝 1. Cookie管理功能测试...")
    tests_total += 1
    try:
        response = requests.get(f"{BASE_URL}/api/get-cookies")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Cookie状态: {data.get('data', {}).get('status', 'unknown')}")
                tests_passed += 1
            else:
                print(f"   ❌ Cookie获取失败: {data.get('error')}")
        else:
            print(f"   ❌ API调用失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    # 2. 测试日历和自动下载配置
    print("\n📅 2. 日历和自动下载配置测试...")
    tests_total += 1
    try:
        response = requests.get(f"{BASE_URL}/api/get-schedule-config")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                config = data.get('data', {})
                print(f"   ✅ 自动下载状态: {'启用' if config.get('enabled') else '禁用'}")
                print(f"   ✅ 下载时间: {config.get('download_time', 'unknown')}")
                print(f"   ✅ 周下载频率: {config.get('weekly_days', [])}")
                tests_passed += 1
            else:
                print(f"   ❌ 配置获取失败")
        else:
            print(f"   ❌ API调用失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    # 3. 测试基线文件管理
    print("\n📁 3. 基线文件管理测试...")
    tests_total += 1
    try:
        response = requests.get(f"{BASE_URL}/api/baseline-files")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                files = data.get('files', [])
                current_week = data.get('current_week', 'unknown')
                print(f"   ✅ 当前周: W{current_week}")
                print(f"   ✅ 基线文件数量: {len(files)}")
                if files:
                    print(f"   ✅ 最新文件: {files[0]['name']}")
                tests_passed += 1
            else:
                print(f"   ❌ 基线文件获取失败")
        else:
            print(f"   ❌ API调用失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    # 4. 测试综合打分文件管理
    print("\n📊 4. 综合打分文件管理测试...")
    tests_total += 1
    try:
        response = requests.get(f"{BASE_URL}/api/list_comprehensive_files")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                files = data.get('files', [])
                print(f"   ✅ 综合打分文件数量: {len(files)}")
                if files:
                    latest = files[0]
                    print(f"   ✅ 最新文件: {latest['name']}")
                    print(f"   ✅ 周数: {latest.get('week', 'unknown')}")
                tests_passed += 1
            else:
                print(f"   ❌ 综合文件获取失败")
        else:
            print(f"   ❌ API调用失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    # 5. 测试文档链接管理
    print("\n🔗 5. 文档链接管理测试...")
    tests_total += 1
    try:
        response = requests.get(f"{BASE_URL}/api/get-download-links")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                links = data.get('data', {}).get('document_links', [])
                print(f"   ✅ 已配置文档数量: {len(links)}")
                for link in links[:3]:  # 显示前3个
                    print(f"   ✅ {link['name']}: {link['url'][:50]}...")
                tests_passed += 1
            else:
                print(f"   ❌ 链接获取失败")
        else:
            print(f"   ❌ API调用失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

    print(f"\n📈 监控设置测试结果: {tests_passed}/{tests_total} 通过")
    return tests_passed == tests_total

def test_comprehensive_data_integrity():
    """测试综合打分数据完整性"""
    print_section("测试综合打分文件完整性")

    # 检查最新的综合打分文件
    scoring_dir = "/root/projects/tencent-doc-manager/scoring_results/comprehensive"

    if not os.path.exists(scoring_dir):
        print("❌ 综合打分目录不存在")
        return False

    files = sorted([f for f in os.listdir(scoring_dir) if f.endswith('.json')], reverse=True)

    if not files:
        print("❌ 没有找到综合打分文件")
        return False

    latest_file = os.path.join(scoring_dir, files[0])
    print(f"📁 检查文件: {files[0]}")

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 验证必需字段
        required_fields = ['generation_time', 'week_number', 'table_scores', 'ui_data', 'total_modifications']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            print(f"❌ 缺少必需字段: {missing_fields}")
            return False

        print(f"✅ 生成时间: {data['generation_time']}")
        print(f"✅ 周数: {data['week_number']}")
        print(f"✅ 总修改数: {data['total_modifications']}")
        print(f"✅ 表格数量: {len(data['table_scores'])}")

        # 验证ui_data格式
        if 'ui_data' in data:
            ui_data = data['ui_data']
            if ui_data and isinstance(ui_data, list):
                print(f"✅ ui_data格式正确，包含 {len(ui_data)} 个表格")
                for table in ui_data[:2]:  # 检查前2个表格
                    if 'row_data' in table:
                        row_data = table['row_data']
                        print(f"   ✅ {table['table_name']}: {len(row_data)} 列数据")
                        # 验证heat_value和color
                        sample = row_data[0] if row_data else {}
                        if 'heat_value' in sample and 'color' in sample:
                            print(f"      ✅ 包含heat_value和color字段")
                        else:
                            print(f"      ❌ 缺少heat_value或color字段")
            else:
                print("❌ ui_data格式不正确")
                return False

        return True

    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

def test_heatmap_ui_adaptation():
    """测试热力图UI适配"""
    print_section("测试热力图UI数据适配")

    try:
        # 1. 获取当前数据源状态
        response = requests.get(f"{BASE_URL}/api/get_data_source")
        if response.status_code == 200:
            data = response.json()
            current_source = data.get('source', 'unknown')
            print(f"📊 当前数据源: {current_source}")

        # 2. 切换到综合打分模式
        response = requests.post(f"{BASE_URL}/api/switch_data_source", json={"source": "comprehensive"})
        if response.status_code == 200:
            print("✅ 已切换到综合打分模式")

        # 3. 获取热力图数据
        response = requests.get(f"{BASE_URL}/api/data")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                heatmap_data = data['data']['heatmap_data']
                statistics = data['data']['statistics']

                print(f"✅ 热力图矩阵大小: {len(heatmap_data)}×{len(heatmap_data[0]) if heatmap_data else 0}")
                print(f"✅ 总修改数: {statistics.get('total_changes', 0)}")
                print(f"✅ 非零单元格: {statistics.get('non_zero_cells', 0)}")
                print(f"✅ 热点单元格: {statistics.get('hot_cells', 0)}")

                # 验证热力值
                non_zero_count = sum(1 for row in heatmap_data for val in row if val > 0.05)
                if non_zero_count > 0:
                    print(f"✅ UI适配正常: 发现 {non_zero_count} 个非背景值单元格")
                    return True
                else:
                    print("❌ UI适配问题: 所有单元格都是背景色")
                    return False
            else:
                print(f"❌ 获取数据失败: {data.get('error')}")
                return False
        else:
            print(f"❌ API调用失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_auto_download_trigger():
    """测试自动下载触发功能"""
    print_section("测试自动下载触发功能")

    try:
        # 1. 获取当前调度配置
        response = requests.get(f"{BASE_URL}/api/get-schedule-config")
        if response.status_code != 200:
            print("❌ 无法获取调度配置")
            return False

        config = response.json().get('data', {})
        enabled = config.get('enabled', False)
        download_time = config.get('download_time', '10:00')

        print(f"📅 自动下载配置:")
        print(f"   - 状态: {'✅ 启用' if enabled else '❌ 禁用'}")
        print(f"   - 设定时间: {download_time}")

        # 2. 测试启用/禁用切换
        new_status = not enabled
        response = requests.post(f"{BASE_URL}/api/save-schedule-config", json={
            "enabled": new_status,
            "download_time": download_time,
            "weekly_days": config.get('weekly_days', [1, 3, 5])
        })

        if response.status_code == 200:
            print(f"✅ 成功切换自动下载状态到: {'启用' if new_status else '禁用'}")

            # 切换回原状态
            response = requests.post(f"{BASE_URL}/api/save-schedule-config", json={
                "enabled": enabled,
                "download_time": download_time,
                "weekly_days": config.get('weekly_days', [1, 3, 5])
            })
            print(f"✅ 已恢复原始状态: {'启用' if enabled else '禁用'}")
            return True
        else:
            print("❌ 无法切换自动下载状态")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_full_workflow_simulation():
    """模拟完整工作流程"""
    print_section("模拟完整工作流程测试")

    print("\n🚀 开始完整流程模拟...")

    # 1. 检查8093服务状态
    print("\n1️⃣ 检查8093下载服务...")
    try:
        response = requests.get(f"{BASE_URL_8093}/api/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ 8093服务状态: {status.get('status', 'unknown')}")
            if status.get('is_running'):
                print(f"   ⚠️ 工作流正在运行中，等待完成...")
                # 等待工作流完成
                for i in range(10):
                    time.sleep(5)
                    response = requests.get(f"{BASE_URL_8093}/api/status")
                    if response.status_code == 200:
                        status = response.json()
                        if not status.get('is_running'):
                            print(f"   ✅ 工作流已完成")
                            break
                    if i == 9:
                        print(f"   ⚠️ 工作流仍在运行，继续测试...")
        else:
            print(f"   ❌ 8093服务不可用")
    except:
        print(f"   ⚠️ 8093服务未启动")

    # 2. 检查CSV文件生成
    print("\n2️⃣ 检查CSV文件生成...")
    csv_dir = "/root/projects/tencent-doc-manager/csv_versions/2025_W41/midweek"
    if os.path.exists(csv_dir):
        files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
        print(f"   ✅ 找到 {len(files)} 个CSV文件")
        for f in files[:3]:
            print(f"      - {f}")
    else:
        print(f"   ⚠️ CSV目录不存在: {csv_dir}")

    # 3. 检查综合打分生成
    print("\n3️⃣ 检查综合打分文件生成...")
    comprehensive_integrity = test_comprehensive_data_integrity()

    # 4. 检查热力图UI显示
    print("\n4️⃣ 检查热力图UI显示...")
    ui_adaptation = test_heatmap_ui_adaptation()

    return comprehensive_integrity and ui_adaptation

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔥 腾讯文档智能监控系统 - 全面功能测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {
        "监控设置UI": False,
        "综合打分完整性": False,
        "热力图UI适配": False,
        "自动下载功能": False,
        "完整工作流": False
    }

    # 执行各项测试
    results["监控设置UI"] = test_8089_monitor_settings()
    results["综合打分完整性"] = test_comprehensive_data_integrity()
    results["热力图UI适配"] = test_heatmap_ui_adaptation()
    results["自动下载功能"] = test_auto_download_trigger()
    results["完整工作流"] = test_full_workflow_simulation()

    # 输出测试报告
    print("\n" + "=" * 60)
    print("📊 测试报告总结")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")

    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 所有测试通过！系统运行正常，链路完全打通！")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

    print("=" * 60)

if __name__ == "__main__":
    main()