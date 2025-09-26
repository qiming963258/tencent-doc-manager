#!/usr/bin/env python3
"""
修复损坏的XLSX文件问题
删除所有无法正常打开的XLSX文件
"""

import os
import openpyxl
from pathlib import Path
import shutil

def test_xlsx_file(file_path):
    """测试XLSX文件是否能正常打开"""
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        workbook.close()
        return True
    except Exception as e:
        if 'Fill' in str(e):
            return False
        # 其他错误也视为损坏
        return False

def scan_and_fix_xlsx_files(base_dir):
    """扫描并修复损坏的XLSX文件"""
    corrupted_files = []
    valid_files = []

    # 扫描所有XLSX文件
    for xlsx_file in Path(base_dir).rglob("*.xlsx"):
        if test_xlsx_file(xlsx_file):
            valid_files.append(str(xlsx_file))
        else:
            corrupted_files.append(str(xlsx_file))

    print(f"📊 扫描结果:")
    print(f"  ✅ 正常文件: {len(valid_files)}个")
    print(f"  ❌ 损坏文件: {len(corrupted_files)}个")

    if corrupted_files:
        print("\n🗑️ 删除损坏的文件:")
        for file_path in corrupted_files:
            print(f"  删除: {file_path}")
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"    ⚠️ 删除失败: {e}")

        print(f"\n✨ 已删除 {len(corrupted_files)} 个损坏文件")
    else:
        print("\n✨ 没有发现损坏的文件")

    return corrupted_files, valid_files

if __name__ == "__main__":
    # 扫描csv_versions目录
    csv_dir = "/root/projects/tencent-doc-manager/csv_versions"
    print(f"🔍 扫描目录: {csv_dir}")
    corrupted, valid = scan_and_fix_xlsx_files(csv_dir)

    # 扫描excel_outputs目录
    excel_dir = "/root/projects/tencent-doc-manager/excel_outputs"
    if os.path.exists(excel_dir):
        print(f"\n🔍 扫描目录: {excel_dir}")
        c2, v2 = scan_and_fix_xlsx_files(excel_dir)
        corrupted.extend(c2)
        valid.extend(v2)

    print(f"\n📈 总计:")
    print(f"  ✅ 保留正常文件: {len(valid)}个")
    print(f"  🗑️ 删除损坏文件: {len(corrupted)}个")