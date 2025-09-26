#!/usr/bin/env python3
"""验证Excel文件的填充类型是否兼容腾讯文档"""

import sys
import zipfile
import tempfile
import os
import xml.etree.ElementTree as ET
from pathlib import Path

def check_excel_fill_types(excel_file):
    """检查Excel文件中使用的填充类型"""

    print(f"🔍 检查Excel文件: {excel_file}")
    print("="*60)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 解压Excel文件（Excel实际是个ZIP文件）
        with zipfile.ZipFile(excel_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # 查找styles.xml文件
        styles_file = os.path.join(temp_dir, 'xl', 'styles.xml')
        if not os.path.exists(styles_file):
            print("❌ 无法找到styles.xml文件")
            return False

        # 解析styles.xml
        tree = ET.parse(styles_file)
        root = tree.getroot()

        # 命名空间
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

        # 查找所有的填充
        fills = root.findall('.//s:fills/s:fill', ns)

        print(f"📊 找到 {len(fills)} 个填充定义")
        print()

        incompatible_fills = []
        solid_fills = []
        other_fills = []

        for i, fill in enumerate(fills):
            pattern_fill = fill.find('s:patternFill', ns)
            if pattern_fill is not None:
                pattern_type = pattern_fill.get('patternType')

                # 获取颜色
                fg_color = pattern_fill.find('s:fgColor', ns)
                bg_color = pattern_fill.find('s:bgColor', ns)

                fg_rgb = fg_color.get('rgb') if fg_color is not None else None
                bg_rgb = bg_color.get('rgb') if bg_color is not None else None

                if pattern_type:
                    if pattern_type == 'solid':
                        solid_fills.append((i, pattern_type, fg_rgb))
                    elif pattern_type in ['lightUp', 'darkUp', 'lightDown', 'darkDown',
                                         'lightGrid', 'darkGrid', 'lightTrellis', 'darkTrellis']:
                        incompatible_fills.append((i, pattern_type, fg_rgb))
                    else:
                        other_fills.append((i, pattern_type, fg_rgb))

        # 输出报告
        print("✅ 腾讯文档兼容的填充（solid）:")
        if solid_fills:
            for idx, ptype, color in solid_fills:
                print(f"   填充#{idx}: {ptype} - 颜色: {color or '无'}")
        else:
            print("   无")

        print()
        print("❌ 腾讯文档不兼容的填充（图案填充）:")
        if incompatible_fills:
            for idx, ptype, color in incompatible_fills:
                print(f"   填充#{idx}: {ptype} - 颜色: {color or '无'}")
                print(f"      ⚠️ {ptype} 在腾讯文档中不会显示！")
        else:
            print("   无")

        print()
        print("⚪ 其他填充类型:")
        if other_fills:
            for idx, ptype, color in other_fills:
                print(f"   填充#{idx}: {ptype} - 颜色: {color or '无'}")
        else:
            print("   无")

        # 判断结果
        print()
        print("="*60)
        if incompatible_fills:
            print("❌ 检测结果：文件包含腾讯文档不兼容的填充类型")
            print(f"   发现 {len(incompatible_fills)} 个不兼容的填充")
            print("   这些填充在腾讯文档中将不会显示颜色")
            return False
        else:
            print("✅ 检测结果：文件填充类型与腾讯文档完全兼容")
            return True

def main():
    """主函数"""

    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        # 默认检查最新的涂色文件
        excel_dir = Path("/root/projects/tencent-doc-manager/excel_outputs/marked")
        excel_files = list(excel_dir.glob("*W40*.xlsx"))
        if excel_files:
            excel_file = max(excel_files, key=lambda p: p.stat().st_mtime)
            print(f"📁 使用最新的W40文件: {excel_file.name}")
        else:
            print("❌ 未找到W40的Excel文件")
            sys.exit(1)

    # 检查文件
    if not Path(excel_file).exists():
        print(f"❌ 文件不存在: {excel_file}")
        sys.exit(1)

    # 执行检查
    is_compatible = check_excel_fill_types(excel_file)

    # 返回结果
    sys.exit(0 if is_compatible else 1)

if __name__ == "__main__":
    main()