#!/usr/bin/env python3
"""测试中文文件名编码问题"""

# 模拟Flask传入的损坏的文件名
broken_filename = "tencent_å¯æ¬-å¯æ¬-æµè¯çæ¬-åºå½éå®è®¡åè¡¨_csv_20250909_2055_midweek_W37.csv"
correct_filename = "tencent_副本-副本-测试版本-出国销售计划表_csv_20250909_2055_midweek_W37.csv"

print(f"损坏的文件名: {broken_filename}")
print(f"正确的文件名: {correct_filename}")
print("=" * 50)

# 尝试修复
try:
    fixed = broken_filename.encode('latin-1').decode('utf-8')
    print(f"Latin-1 -> UTF-8 修复: {fixed}")
    print(f"修复成功: {fixed == correct_filename}")
except Exception as e:
    print(f"Latin-1 -> UTF-8 失败: {e}")

# 尝试其他方法
try:
    fixed = broken_filename.encode('utf-8', errors='ignore').decode('utf-8')
    print(f"UTF-8 忽略错误: {fixed}")
except Exception as e:
    print(f"UTF-8 忽略错误失败: {e}")

# 直接测试文件查找
import glob
from pathlib import Path

csv_dir = Path('/root/projects/tencent-doc-manager/csv_versions')
# 使用正确的文件名查找
pattern1 = str(csv_dir / '**' / correct_filename)
matches1 = glob.glob(pattern1, recursive=True)
print(f"\n使用正确文件名找到: {len(matches1)} 个文件")

# 使用损坏的文件名查找
pattern2 = str(csv_dir / '**' / broken_filename)
matches2 = glob.glob(pattern2, recursive=True)
print(f"使用损坏文件名找到: {len(matches2)} 个文件")