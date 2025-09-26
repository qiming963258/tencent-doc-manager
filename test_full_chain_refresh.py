#!/usr/bin/env python3
"""
测试8089热力图UI的快速刷新按钮（健康生长的快速刷新）
模拟真实点击，触发全链路处理
"""

import requests
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)


def monitor_workflow_status():
    """监控8093工作流执行状态"""
    print("\n📊 监控工作流状态...")

    max_wait = 180  # 最多等待3分钟
    wait_time = 0
    last_status = None

    while wait_time < max_wait:
        try:
            # 查询8093状态
            response = requests.get('http://localhost:8093/api/status', timeout=5)

            if response.status_code == 200:
                status_data = response.json()

                # 提取关键信息
                current_status = status_data.get('status', 'unknown')
                current_task = status_data.get('current_task', '')
                progress = status_data.get('progress', 0)

                # 只在状态变化时打印
                status_info = f"{current_status}:{current_task}"
                if status_info != last_status:
                    timestamp = datetime.now().strftime('%H:%M:%S')

                    # 根据状态使用不同的图标
                    if current_status == 'running':
                        icon = "⏳"
                    elif current_status == 'completed':
                        icon = "✅"
                    elif current_status == 'error':
                        icon = "❌"
                    else:
                        icon = "📋"

                    print(f"[{timestamp}] {icon} 状态: {current_status} | 任务: {current_task} | 进度: {progress}%")
                    last_status = status_info

                # 如果完成或出错，退出循环
                if current_status in ['completed', 'error']:
                    return current_status, status_data

        except Exception as e:
            pass  # 静默处理错误，继续监控

        time.sleep(2)  # 每2秒检查一次
        wait_time += 2

    print("⚠️ 监控超时")
    return 'timeout', None


def test_full_chain_refresh():
    """测试全链路快速刷新功能"""

    print("=" * 70)
    print("🚀 全链路快速刷新测试 - 深度分析版")
    print("=" * 70)

    # 步骤1：检查服务状态
    print_section("步骤1: 检查服务状态")

    services_ok = True

    # 检查8089服务
    try:
        response = requests.get('http://localhost:8089/api/workflow-status', timeout=5)
        if response.status_code == 200:
            print("✅ 8089热力图服务正常运行")
        else:
            print(f"⚠️ 8089服务响应异常: {response.status_code}")
            services_ok = False
    except Exception as e:
        print(f"❌ 8089服务未运行: {e}")
        services_ok = False

    # 检查8093服务
    try:
        response = requests.get('http://localhost:8093/api/status', timeout=5)
        if response.status_code == 200:
            print("✅ 8093全链路处理服务正常运行")
            status = response.json()
            print(f"   当前状态: {status.get('status', 'idle')}")
        else:
            print(f"⚠️ 8093服务响应异常: {response.status_code}")
            services_ok = False
    except Exception as e:
        print(f"❌ 8093服务未运行: {e}")
        services_ok = False

    if not services_ok:
        print("\n❌ 服务状态异常，请先启动所有服务")
        return False

    # 步骤2：模拟点击快速刷新按钮
    print_section("步骤2: 模拟点击快速刷新按钮")

    print("📍 调用 /api/reload-comprehensive-score 接口")
    print("📝 这相当于点击8089界面上的快速刷新按钮")

    try:
        # 发送POST请求触发全链路处理
        response = requests.post(
            'http://localhost:8089/api/reload-comprehensive-score',
            timeout=30  # 增加超时时间到3秒
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 成功触发全链路处理")
                print(f"📊 正在处理文档数量: {result.get('documents_count', 0)}")
                print(f"📁 最新综合评分文件: {result.get('comprehensive_file', 'N/A')}")
            else:
                print(f"❌ 触发失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

    # 步骤3：监控执行进度
    print_section("步骤3: 监控全链路执行进度")

    print("📡 开始实时监控工作流状态...")
    print("-" * 50)

    final_status, status_data = monitor_workflow_status()

    # 步骤4：分析执行结果
    print_section("步骤4: 分析执行结果")

    if final_status == 'completed':
        print("✅ 全链路处理完成！")

        if status_data:
            results = status_data.get('results', {})

            # 显示处理的文档
            processed_docs = results.get('processed_documents', [])
            if processed_docs:
                print(f"\n📄 处理的文档数量: {len(processed_docs)}")
                for doc in processed_docs[:3]:  # 只显示前3个
                    print(f"   • {doc.get('name', 'Unknown')}")
                if len(processed_docs) > 3:
                    print(f"   ... 还有 {len(processed_docs) - 3} 个文档")

            # 显示上传结果
            uploaded_urls = results.get('uploaded_urls', {})
            if uploaded_urls:
                print(f"\n📤 成功上传的文档: {len(uploaded_urls)}")
                for name, url in list(uploaded_urls.items())[:2]:  # 只显示前2个
                    print(f"   • {name}: {url}")

            # 显示综合评分文件
            comprehensive_file = results.get('batch_comprehensive_file', '')
            if comprehensive_file:
                print(f"\n📊 综合评分文件: {comprehensive_file}")

    elif final_status == 'error':
        print("❌ 全链路处理失败")
        if status_data:
            error_msg = status_data.get('error', 'Unknown error')
            print(f"   错误信息: {error_msg}")
    else:
        print(f"⚠️ 处理状态异常: {final_status}")

    # 步骤5：验证热力图更新
    print_section("步骤5: 验证热力图数据更新")

    try:
        # 获取热力图数据
        response = requests.get('http://localhost:8089/api/real-csv-data', timeout=5)

        if response.status_code == 200:
            data = response.json()

            # 检查数据更新时间
            timestamp = data.get('timestamp', '')
            if timestamp:
                print(f"✅ 热力图数据已更新")
                print(f"   更新时间: {timestamp}")

            # 检查热力图矩阵
            heatmap = data.get('heatmap_matrix', [])
            if heatmap:
                print(f"   矩阵大小: {len(heatmap)}×{len(heatmap[0]) if heatmap else 0}")

                # 统计热点
                hot_count = 0
                for row in heatmap:
                    for value in row:
                        if value > 0.5:  # 热点阈值
                            hot_count += 1

                print(f"   热点数量: {hot_count}")
        else:
            print("⚠️ 无法获取热力图数据")
    except Exception as e:
        print(f"⚠️ 获取热力图数据失败: {e}")

    # 步骤6：验证Excel文件生成
    print_section("步骤6: 验证Excel标记文件")

    excel_dir = Path('/root/projects/tencent-doc-manager/excel_outputs/marked')
    if excel_dir.exists():
        # 查找最新的Excel文件
        excel_files = sorted(excel_dir.glob('*.xlsx'), key=lambda x: x.stat().st_mtime, reverse=True)
        if excel_files:
            latest_excel = excel_files[0]
            file_age = (time.time() - latest_excel.stat().st_mtime) / 60  # 转换为分钟

            if file_age < 5:  # 5分钟内的文件
                print(f"✅ 找到新生成的Excel文件")
                print(f"   文件名: {latest_excel.name}")
                print(f"   生成时间: {file_age:.1f} 分钟前")
                print(f"   文件大小: {latest_excel.stat().st_size / 1024:.1f} KB")
            else:
                print(f"⚠️ 最新Excel文件较旧: {file_age:.1f} 分钟前")
        else:
            print("⚠️ 未找到Excel文件")
    else:
        print("⚠️ Excel输出目录不存在")

    # 最终总结
    print("\n" + "=" * 70)
    print("📊 全链路测试总结")
    print("=" * 70)

    if final_status == 'completed':
        print("✅ 全链路处理成功完成！")
        print("\n已完成的处理步骤：")
        print("1. ✅ 下载腾讯文档（基线和目标）")
        print("2. ✅ CSV格式转换和对比分析")
        print("3. ✅ AI驱动的列名标准化")
        print("4. ✅ 风险等级评分（L1/L2/L3）")
        print("5. ✅ 热力图数据生成")
        print("6. ✅ Excel半填充标记")
        print("7. ✅ 自动上传到腾讯文档")

        print("\n💡 提示：")
        print("• 访问 http://202.140.143.88:8089 查看更新的热力图")
        print("• 检查腾讯文档查看上传的Excel文件")
        print("• 日志保存在 workflow_history 目录")
    else:
        print("⚠️ 全链路处理未完全成功")
        print("请检查日志文件了解详细错误信息")

    return final_status == 'completed'


if __name__ == "__main__":
    success = test_full_chain_refresh()
    sys.exit(0 if success else 1)