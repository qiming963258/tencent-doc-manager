#!/usr/bin/env python3
"""
使用8093相同的上传方法测试上传涂色文件
"""

import sys
import json
import os
sys.path.append('/root/projects/tencent-doc-manager')

# 使用和8093相同的导入
try:
    from tencent_doc_uploader_ultimate import sync_upload_file
    print("✅ 使用 tencent_doc_uploader_ultimate")
except ImportError:
    try:
        from tencent_doc_uploader_fixed import sync_upload_file
        print("✅ 使用 tencent_doc_uploader_fixed")
    except ImportError:
        from tencent_doc_uploader import sync_upload_file
        print("✅ 使用 tencent_doc_uploader")

def test_upload_with_correct_method():
    """使用正确的方法上传涂色文件"""
    print("=" * 60)
    print("使用8093相同的上传方法测试")
    print("=" * 60)
    
    # 1. 找到最新的涂色文件
    marked_dir = "/root/projects/tencent-doc-manager/excel_outputs/marked/"
    marked_files = [f for f in os.listdir(marked_dir) if f.endswith('.xlsx')]
    if not marked_files:
        print("❌ 没有找到涂色文件")
        return False
    
    # 使用最新的文件
    latest_file = sorted(marked_files)[-1]
    marked_file = os.path.join(marked_dir, latest_file)
    print(f"✅ 找到涂色文件: {latest_file}")
    
    # 2. 验证文件确实有涂色
    import openpyxl
    wb = openpyxl.load_workbook(marked_file)
    ws = wb.active
    
    risk_count = 0
    risk_cells = []
    for row in ws.iter_rows(min_row=1, max_row=20):
        for cell in row:
            if cell.fill and cell.fill.patternType == 'solid':
                color_rgb = str(cell.fill.fgColor.rgb) if cell.fill.fgColor else None
                # 检查是否是我们的风险颜色
                if color_rgb in ['FFFF0000', 'FFFFCCCC', 'FFFFE9E8', 'FFFFFF00']:
                    risk_count += 1
                    risk_cells.append(f"{cell.column_letter}{cell.row}")
    wb.close()
    
    print(f"✅ 文件验证: 包含 {risk_count} 个风险涂色单元格")
    if risk_cells:
        print(f"   风险单元格: {', '.join(risk_cells[:10])}")
    
    # 3. 从规范位置加载Cookie
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies.json"
    print(f"\n从规范位置加载Cookie: {cookie_file}")
    
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie_data = json.load(f)
    
    cookie_string = cookie_data.get('cookie_string', '')
    if not cookie_string:
        print("❌ Cookie为空")
        return False
    
    print(f"✅ Cookie加载成功 (长度: {len(cookie_string)})")
    print(f"   最后更新: {cookie_data.get('last_updated', '未知')}")
    
    # 4. 使用和8093相同的上传参数
    print("\n开始上传到腾讯文档...")
    print(f"  文件: {marked_file}")
    print(f"  上传选项: new (创建新文档)")
    
    upload_result = sync_upload_file(
        marked_file,
        upload_option='new',  # 创建新文档
        target_url='',        # 空表示创建新文档
        cookie_string=cookie_string
    )
    
    if upload_result and upload_result.get('success'):
        print(f"\n✅ 上传成功!")
        print(f"📎 文档链接: {upload_result.get('url', '未获取到URL')}")
        return True
    else:
        error_msg = upload_result.get('error', '未知错误') if upload_result else '上传函数返回None'
        print(f"\n❌ 上传失败: {error_msg}")
        return False

if __name__ == "__main__":
    success = test_upload_with_correct_method()
    exit(0 if success else 1)