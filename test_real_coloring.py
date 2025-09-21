#!/usr/bin/env python3
"""
真正执行Excel涂色功能
使用Excel MCP和IntelligentExcelMarker
"""

import os
import json
import sys
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')

def test_real_coloring():
    """测试真实的涂色功能"""

    print("\n" + "="*60)
    print("🎨 测试真实Excel涂色功能")
    print("="*60)

    # 找到要涂色的文件
    midweek_dir = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek"

    # 使用最新的XLSX文件
    xlsx_files = [f for f in os.listdir(midweek_dir) if f.endswith('.xlsx') and 'colored' not in f]
    if not xlsx_files:
        print("❌ 没有找到未涂色的XLSX文件")
        return None

    source_file = os.path.join(midweek_dir, sorted(xlsx_files)[-1])
    print(f"📄 源文件: {os.path.basename(source_file)}")
    print(f"📏 文件大小: {os.path.getsize(source_file):,} bytes")

    # 1. 首先生成打分文件
    print("\n🔍 步骤1: 生成打分文件...")

    from intelligent_excel_marker import DetailedScoreGenerator

    # 创建模拟打分数据（实际应该从对比分析生成）
    score_data = {
        "metadata": {
            "target_file": os.path.basename(source_file),
            "generated_at": datetime.now().isoformat(),
            "week": "W38"
        },
        "statistics": {
            "total_cells": 1000,
            "changed_cells": 20
        },
        "cell_scores": {
            # 模拟一些变更的单元格
            "A2": {
                "old_value": "100",
                "new_value": "150",
                "change_type": "numeric_increase",
                "risk_level": "HIGH",
                "column_level": "L1",
                "score": 30,
                "color_code": "FF0000"
            },
            "B3": {
                "old_value": "计划",
                "new_value": "完成",
                "change_type": "text_change",
                "risk_level": "MEDIUM",
                "column_level": "L2",
                "score": 60,
                "color_code": "FFA500"
            },
            "C4": {
                "old_value": "2025-01-01",
                "new_value": "2025-02-01",
                "change_type": "date_change",
                "risk_level": "LOW",
                "column_level": "L3",
                "score": 80,
                "color_code": "00FF00"
            },
            "D5": {
                "old_value": "",
                "new_value": "新增内容",
                "change_type": "addition",
                "risk_level": "MEDIUM",
                "column_level": "L2",
                "score": 60,
                "color_code": "FFA500"
            },
            "E6": {
                "old_value": "删除内容",
                "new_value": "",
                "change_type": "deletion",
                "risk_level": "HIGH",
                "column_level": "L1",
                "score": 30,
                "color_code": "FF0000"
            }
        }
    }

    # 保存打分文件
    score_dir = "/root/projects/tencent-doc-manager/scoring_results/detailed"
    os.makedirs(score_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    doc_name = os.path.basename(source_file).replace('.xlsx', '')
    score_file = os.path.join(score_dir, f"detailed_scores_{doc_name}_{timestamp}.json")

    with open(score_file, 'w', encoding='utf-8') as f:
        json.dump(score_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 打分文件已生成: {os.path.basename(score_file)}")
    print(f"   - 变更单元格数: {len(score_data['cell_scores'])}")

    # 2. 执行涂色
    print("\n🎨 步骤2: 应用涂色...")

    from intelligent_excel_marker import IntelligentExcelMarker

    marker = IntelligentExcelMarker()

    # 输出文件路径
    output_file = source_file.replace('.xlsx', '_colored_real.xlsx')

    try:
        # 调用涂色方法
        result = marker.apply_striped_coloring(source_file, score_file, output_file)
        print(f"✅ 涂色完成: {os.path.basename(result)}")

        # 验证涂色效果
        print("\n📊 步骤3: 验证涂色效果...")

        import openpyxl
        wb = openpyxl.load_workbook(result)
        ws = wb.active

        # 检查涂色的单元格
        colored_cells = []
        for cell_ref in score_data['cell_scores'].keys():
            cell = ws[cell_ref]
            if cell.fill and cell.fill.patternType:
                colored_cells.append({
                    'cell': cell_ref,
                    'pattern': cell.fill.patternType,
                    'fg_color': cell.fill.fgColor.value if cell.fill.fgColor else None,
                    'bg_color': cell.fill.bgColor.value if cell.fill.bgColor else None
                })

        print(f"✅ 已涂色单元格数: {len(colored_cells)}")
        for info in colored_cells[:3]:  # 显示前3个
            print(f"   - {info['cell']}: 图案={info['pattern']}, 颜色={info['fg_color']}")

        wb.close()

        return result

    except Exception as e:
        print(f"❌ 涂色失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_mcp_coloring():
    """使用Excel MCP服务进行涂色"""

    print("\n" + "="*60)
    print("🎨 测试Excel MCP涂色功能")
    print("="*60)

    midweek_dir = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek"
    xlsx_files = [f for f in os.listdir(midweek_dir) if f.endswith('.xlsx') and 'colored' not in f]

    if not xlsx_files:
        print("❌ 没有找到未涂色的XLSX文件")
        return None

    source_file = os.path.join(midweek_dir, sorted(xlsx_files)[-1])

    print(f"📄 源文件: {os.path.basename(source_file)}")

    # Excel MCP格式化示例
    print("\n使用Excel MCP进行单元格格式化...")
    print("📋 涂色配置:")
    print("   - A1:C3 - 红色背景（高风险）")
    print("   - D4:F6 - 黄色背景（中风险）")
    print("   - G7:I9 - 绿色背景（低风险）")

    # 注意：实际MCP调用需要在主程序中使用mcp__excel__format_range
    # 这里只是准备参数
    format_configs = [
        {
            "filepath": source_file,
            "sheet_name": "Sheet1",  # 或实际的工作表名
            "start_cell": "A1",
            "end_cell": "C3",
            "bg_color": "#FF0000",  # 红色
            "bold": True
        },
        {
            "filepath": source_file,
            "sheet_name": "Sheet1",
            "start_cell": "D4",
            "end_cell": "F6",
            "bg_color": "#FFFF00",  # 黄色
            "bold": False
        },
        {
            "filepath": source_file,
            "sheet_name": "Sheet1",
            "start_cell": "G7",
            "end_cell": "I9",
            "bg_color": "#00FF00",  # 绿色
            "bold": False
        }
    ]

    print("\n✅ MCP涂色配置已准备")
    print("⚠️  注意：需要在支持MCP的环境中调用mcp__excel__format_range")

    return format_configs

if __name__ == "__main__":
    # 测试方法1：使用IntelligentExcelMarker
    print("\n🔧 方法1: 使用IntelligentExcelMarker")
    result = test_real_coloring()

    if result:
        print(f"\n✅ 涂色文件已生成: {result}")

    # 测试方法2：准备MCP配置
    print("\n🔧 方法2: Excel MCP配置")
    mcp_configs = test_mcp_coloring()

    if mcp_configs:
        print(f"\n✅ 已准备{len(mcp_configs)}个MCP涂色配置")