#!/usr/bin/env python3
"""
手动测试上传涂色后的Excel文件
"""

import asyncio
import json
import os
import sys
sys.path.append('/root/projects/tencent-doc-manager')

from production.core_modules.tencent_doc_upload_production_v3 import TencentDocProductionUploaderV3

async def test_upload():
    """测试上传涂色后的文件"""
    print("=" * 60)
    print("测试上传涂色后的Excel文件到腾讯文档")
    print("=" * 60)
    
    # 使用最新的涂色文件
    marked_file = "/root/projects/tencent-doc-manager/excel_outputs/marked/tencent_副本-副本-测试版本-出国销售计划表_20250912_1349_midweek_W37_marked_20250912_141019_W00.xlsx"
    
    if not os.path.exists(marked_file):
        print(f"❌ 文件不存在: {marked_file}")
        return False
    
    print(f"✅ 找到涂色文件: {marked_file}")
    
    # 验证文件确实有涂色
    import openpyxl
    wb = openpyxl.load_workbook(marked_file)
    ws = wb.active
    
    colored_cells = []
    for row in ws.iter_rows(min_row=1, max_row=20):  # 只检查前20行
        for cell in row:
            if cell.fill and cell.fill.patternType == 'solid':
                color_rgb = str(cell.fill.fgColor.rgb) if cell.fill.fgColor else None
                # 检查是否是风险颜色
                if color_rgb in ['FFFF0000', 'FFFFCCCC', 'FFFFE9E8', 'FFFFFF00']:
                    colored_cells.append({
                        'cell': f"{cell.column_letter}{cell.row}",
                        'value': cell.value,
                        'color': color_rgb
                    })
    wb.close()
    
    print(f"\n✅ 文件验证: 包含 {len(colored_cells)} 个风险涂色单元格")
    for cell_info in colored_cells[:5]:
        color_name = {
            'FFFF0000': '红色(极高风险)',
            'FFFFCCCC': '浅红色(高风险)',
            'FFFFE9E8': '浅橙色(中风险)',
            'FFFFFF00': '黄色(低风险)'
        }.get(cell_info['color'], '未知')
        print(f"  {cell_info['cell']}: {cell_info['value']} - {color_name}")
    
    # 加载Cookie
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies.json"
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie_data = json.load(f)
    
    print("\n开始上传到腾讯文档...")
    
    # 创建上传器并设置Cookie
    uploader = TencentDocProductionUploaderV3()
    uploader.cookie_string = cookie_data['cookie_string']
    
    # 执行上传
    result = await uploader.upload_file(marked_file)
    
    if result.get('success'):
        print(f"\n✅ 上传成功!")
        print(f"📎 文档链接: {result.get('url', '未获取到URL')}")
        return True
    else:
        print(f"\n❌ 上传失败: {result.get('error', '未知错误')}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_upload())
    exit(0 if success else 1)