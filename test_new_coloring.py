#!/usr/bin/env python3
"""测试新的涂色配置"""

import sys
sys.path.append('/root/projects/tencent-doc-manager')

from intelligent_excel_marker import IntelligentExcelMarker
import json
from datetime import datetime

def test_coloring_with_real_data():
    """测试使用真实打分数据的涂色"""

    print("🎨 测试新的涂色配置")
    print("="*60)

    # 使用有实际变更的打分文件
    score_file = "/root/projects/tencent-doc-manager/scoring_results/detailed/detailed_score_tmpewdh0_p5_20250929_011949.json"
    excel_file = "/root/projects/tencent-doc-manager/excel_outputs/marked/tencent_副本-副本-测试版本-出国销售计划表_20250929_0121_midweek_W40_marked_20250929_012144_W00.xlsx"

    # 读取打分数据检查
    with open(score_file, 'r', encoding='utf-8') as f:
        score_data = json.load(f)

    print(f"📊 打分文件: {score_file}")
    print(f"  总变更数: {score_data['metadata']['total_modifications']}")
    print(f"  变更记录: {len(score_data['scores'])} 条")

    # 检查变更的风险分布
    risk_distribution = {}
    for score in score_data['scores']:
        risk_level = score.get('risk_assessment', {}).get('risk_level', 'UNKNOWN')
        risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

    print(f"\n🔥 风险分布:")
    for level, count in risk_distribution.items():
        print(f"  {level}: {count} 个")

    # 执行涂色
    print(f"\n🎨 开始涂色测试...")
    marker = IntelligentExcelMarker()

    # 生成新的输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"/root/projects/tencent-doc-manager/excel_outputs/marked/test_new_colors_{timestamp}.xlsx"

    # 应用涂色
    try:
        result = marker.apply_striped_coloring(excel_file, score_file, output_file)
        print(f"\n✅ 涂色完成: {result}")

        # 验证涂色效果
        import openpyxl
        wb = openpyxl.load_workbook(result)
        ws = wb.active

        colored_count = 0
        color_samples = []

        for row in ws.iter_rows():
            for cell in row:
                if cell.fill and cell.fill.patternType == 'solid':
                    fg_color = cell.fill.fgColor
                    if fg_color and fg_color.rgb and fg_color.rgb not in ['FFFFFFFF', '00000000']:
                        colored_count += 1
                        if len(color_samples) < 5:
                            color_samples.append({
                                'cell': cell.coordinate,
                                'color': fg_color.rgb,
                                'value': str(cell.value)[:20] if cell.value else ''
                            })

        print(f"\n📊 涂色验证:")
        print(f"  涂色单元格数: {colored_count}")
        print(f"\n  颜色样本:")
        for sample in color_samples:
            print(f"    {sample['cell']}: {sample['color']} - {sample['value']}")

        wb.close()

        return result

    except Exception as e:
        print(f"\n❌ 涂色失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_coloring_with_real_data()
    if result:
        print(f"\n✅ 测试成功！新涂色文件: {result}")
    else:
        print(f"\n❌ 测试失败")