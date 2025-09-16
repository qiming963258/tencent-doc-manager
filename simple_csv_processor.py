#!/usr/bin/env python3
"""
简单CSV处理器 - 绕过Excel格式问题，直接处理CSV
"""

import csv
import os
from pathlib import Path

def process_csv_file(csv_file):
    """
    处理CSV文件（腾讯文档可以直接导出CSV，没有格式问题）
    """
    print(f"📄 处理CSV文件: {csv_file}")
    
    # 读取CSV数据
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        data = list(reader)
    
    if not data:
        print("❌ 文件为空")
        return
    
    # 显示数据信息
    print(f"✅ 数据读取成功！")
    print(f"   行数: {len(data)}")
    print(f"   列数: {len(data[0]) if data else 0}")
    
    # 显示前几行
    print("\n📊 数据预览:")
    for i, row in enumerate(data[:5]):
        print(f"   第{i+1}行: {row[:5]}...")  # 只显示前5列
    
    return data

def csv_to_simple_excel(csv_file, output_file=None):
    """
    将CSV转换为简单的Excel文件（无格式，但兼容性好）
    """
    if not output_file:
        path = Path(csv_file)
        output_file = path.parent / f"{path.stem}.xlsx"
    
    print(f"🔄 转换CSV到Excel...")
    
    from openpyxl import Workbook
    
    # 读取CSV数据
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        data = list(reader)
    
    # 创建新的Excel工作簿
    wb = Workbook()
    ws = wb.active
    
    # 写入数据
    for row in data:
        ws.append(row)
    
    # 保存
    wb.save(output_file)
    print(f"✅ 已保存为Excel: {output_file}")
    
    return output_file

# 测试
if __name__ == "__main__":
    import sys
    
    print("🔧 CSV处理器（推荐用于腾讯文档）")
    print("="*50)
    print("💡 使用方法:")
    print("   1. 在腾讯文档中选择：文件 → 导出为 → CSV格式")
    print("   2. 使用本工具处理CSV文件")
    print("="*50)
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        if csv_file.endswith('.csv'):
            data = process_csv_file(csv_file)
            
            # 询问是否转换为Excel
            response = input("\n是否转换为Excel格式？(y/n): ")
            if response.lower() == 'y':
                csv_to_simple_excel(csv_file)
        else:
            print("⚠️ 请提供CSV文件")
    else:
        print("\n用法: python simple_csv_processor.py <CSV文件路径>")