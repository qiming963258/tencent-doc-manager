#!/usr/bin/env python3
"""全链路测试脚本 - 深度检查各个阶段的文件和数据"""

import sys
import os
import json
import time
from datetime import datetime
import pytz

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

from production.core_modules.tencent_export_automation import TencentDocAutoExporter
from production.core_modules.week_time_manager import WeekTimeManager
from production.core_modules.adaptive_table_comparator import AdaptiveTableComparator

def log(msg, level="INFO"):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "📋",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "PROCESS": "🔄"
    }.get(level, "📌")
    print(f"[{timestamp}] {prefix} {msg}")

def test_full_workflow():
    """执行完整的全链路测试"""

    log("========== 开始全链路测试 ==========", "PROCESS")

    # 初始化组件
    wtm = WeekTimeManager()
    week_info = wtm.get_current_week_info()
    current_week = week_info['week_number']

    # 读取Cookie
    with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
        cookie_data = json.load(f)
    cookie_string = cookie_data.get('current_cookies', '')

    log(f"当前周数: W{current_week}", "INFO")
    log(f"Cookie长度: {len(cookie_string)} 字符", "INFO")

    # 测试文档URLs
    test_docs = [
        {
            "name": "出国销售计划表",
            "url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"
        },
        {
            "name": "小红书部门",
            "url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R?tab=000001"
        }
    ]

    # ========== 步骤1: 下载CSV文件 ==========
    log("步骤1: 下载CSV文件", "PROCESS")

    exporter = TencentDocAutoExporter()
    downloaded_files = []

    for doc in test_docs:
        log(f"下载: {doc['name']}", "INFO")
        result = exporter.export_document(
            url=doc['url'],
            cookies=cookie_string,
            format='csv'
        )

        if result['success']:
            file_path = result.get('file_path')
            log(f"下载成功: {file_path}", "SUCCESS")
            downloaded_files.append(file_path)

            # 检查文件内容
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024
                log(f"文件大小: {file_size:.1f} KB", "INFO")

                # 读取前几行检查格式
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:3]
                    log(f"前3行预览:", "INFO")
                    for i, line in enumerate(lines, 1):
                        print(f"  行{i}: {line[:100].strip()}")
        else:
            log(f"下载失败: {result.get('error', '未知错误')}", "ERROR")

    # ========== 步骤2: CSV对比分析 ==========
    log("步骤2: CSV对比分析", "PROCESS")

    if len(downloaded_files) >= 1:
        # 查找基线文件
        baseline_dir = f"/root/projects/tencent-doc-manager/csv_versions/2025_W{current_week}/baseline"
        baseline_files = []

        if os.path.exists(baseline_dir):
            for file in os.listdir(baseline_dir):
                if file.endswith('.csv') and not file.startswith('.'):
                    baseline_files.append(os.path.join(baseline_dir, file))

        log(f"找到 {len(baseline_files)} 个基线文件", "INFO")

        if baseline_files and downloaded_files:
            # 使用第一个基线和第一个下载文件进行对比
            baseline_file = baseline_files[0]
            target_file = downloaded_files[0]

            log(f"基线: {os.path.basename(baseline_file)}", "INFO")
            log(f"目标: {os.path.basename(target_file)}", "INFO")

            # 初始化对比器
            comparator = AdaptiveTableComparator()

            # 执行对比
            log("执行CSV对比...", "PROCESS")
            comparison_result = comparator.compare_files(baseline_file, target_file)

            # 保存对比结果
            result_dir = "/root/projects/tencent-doc-manager/comparison_results"
            os.makedirs(result_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(result_dir, f"test_comparison_{timestamp}.json")

            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_result, f, ensure_ascii=False, indent=2)

            log(f"对比结果保存到: {result_file}", "SUCCESS")

            # 分析对比结果
            if comparison_result:
                log("对比结果分析:", "INFO")
                print(f"  文档名称: {comparison_result.get('document_name', 'N/A')}")
                print(f"  总体相似度: {comparison_result.get('overall_similarity', 0):.2%}")
                print(f"  变更单元格数: {comparison_result.get('changed_cells_count', 0)}")

                # 检查标准化文件
                standardized_file = comparison_result.get('standardized_file')
                if standardized_file:
                    log(f"标准化文件: {standardized_file}", "SUCCESS")
                else:
                    log("未生成标准化文件", "WARNING")

                # 检查详细打分
                detailed_scores = comparison_result.get('detailed_scores', {})
                if detailed_scores:
                    log("详细打分数据存在", "SUCCESS")
                    print(f"  打分维度数: {len(detailed_scores)}")
                else:
                    log("缺少详细打分数据", "ERROR")

                # 检查综合打分
                comprehensive_score = comparison_result.get('comprehensive_score')
                if comprehensive_score:
                    log(f"综合打分: {comprehensive_score}", "SUCCESS")
                else:
                    log("缺少综合打分", "ERROR")

    else:
        log("文件不足，无法进行对比", "WARNING")

    # ========== 步骤3: 检查中间文件 ==========
    log("步骤3: 检查中间文件", "PROCESS")

    # 检查标准化后的文件
    standardized_dir = "/root/projects/tencent-doc-manager/csv_versions/standard_outputs"
    if os.path.exists(standardized_dir):
        files = os.listdir(standardized_dir)
        log(f"标准化输出目录包含 {len(files)} 个文件", "INFO")
        for file in files[-5:]:  # 显示最新的5个
            print(f"  - {file}")

    # ========== 步骤4: 检查打分结果 ==========
    log("步骤4: 检查打分结果", "PROCESS")

    scoring_dir = "/root/projects/tencent-doc-manager/scoring_results"
    if os.path.exists(scoring_dir):
        # 检查详细打分
        detailed_dir = os.path.join(scoring_dir, "detailed")
        if os.path.exists(detailed_dir):
            files = os.listdir(detailed_dir)
            log(f"详细打分目录包含 {len(files)} 个文件", "INFO")

        # 检查综合打分
        comprehensive_dir = os.path.join(scoring_dir, "comprehensive")
        if os.path.exists(comprehensive_dir):
            files = os.listdir(comprehensive_dir)
            log(f"综合打分目录包含 {len(files)} 个文件", "INFO")

            # 读取最新的综合打分文件
            if files:
                latest_file = sorted(files)[-1]
                file_path = os.path.join(comprehensive_dir, latest_file)
                log(f"最新综合打分文件: {latest_file}", "INFO")

                with open(file_path, 'r', encoding='utf-8') as f:
                    score_data = json.load(f)

                # 检查数据格式
                if 'ui_data' in score_data:
                    ui_data = score_data['ui_data']
                    log(f"UI数据格式正确，包含 {len(ui_data)} 个表格", "SUCCESS")
                else:
                    log("综合打分缺少ui_data字段", "ERROR")

    # ========== 步骤5: 检查UI适配性 ==========
    log("步骤5: 检查UI适配性", "PROCESS")

    # 检查8089端口服务
    import requests
    try:
        response = requests.get("http://localhost:8089/api/data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            log("8089 UI服务正常响应", "SUCCESS")

            # 检查数据结构
            if 'heatmap_data' in data:
                heatmap = data['heatmap_data']
                log(f"热力图数据: {len(heatmap)} 行", "INFO")

            if 'column_headers' in data:
                headers = data['column_headers']
                log(f"列标题数: {len(headers)}", "INFO")

        else:
            log(f"8089服务返回错误: {response.status_code}", "ERROR")
    except Exception as e:
        log(f"无法连接8089服务: {str(e)}", "ERROR")

    log("========== 全链路测试完成 ==========", "SUCCESS")

    # 生成测试报告
    report = {
        "test_time": datetime.now().isoformat(),
        "week_number": current_week,
        "downloaded_files": len(downloaded_files),
        "baseline_files_found": len(baseline_files) if 'baseline_files' in locals() else 0,
        "comparison_executed": 'comparison_result' in locals(),
        "standardized_file_generated": bool(comparison_result.get('standardized_file')) if 'comparison_result' in locals() else False,
        "detailed_scores_available": bool(comparison_result.get('detailed_scores')) if 'comparison_result' in locals() else False,
        "comprehensive_score_available": bool(comparison_result.get('comprehensive_score')) if 'comparison_result' in locals() else False,
        "ui_service_responsive": 'response' in locals() and response.status_code == 200 if 'response' in locals() else False
    }

    report_file = f"/root/projects/tencent-doc-manager/workflow_test_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    log(f"测试报告保存到: {report_file}", "SUCCESS")

    return report

if __name__ == "__main__":
    test_full_workflow()