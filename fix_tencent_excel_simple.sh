#!/bin/bash

echo "🔧 腾讯文档Excel修复工具"
echo "===================================="

if [ -z "$1" ]; then
    echo "用法: ./fix_tencent_excel_simple.sh <腾讯文档Excel文件>"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${INPUT_FILE%.xlsx}_fixed.xlsx"

echo "📥 输入文件: $INPUT_FILE"

# 方法1: 尝试用Python重新创建文件
echo "尝试方法1: Python重建文件..."
python3 -c "
import sys
from openpyxl import Workbook
import csv

input_file = '$INPUT_FILE'
output_file = '$OUTPUT_FILE'

try:
    # 尝试提取原始数据
    from openpyxl import load_workbook
    
    # 创建新工作簿
    new_wb = Workbook()
    new_ws = new_wb.active
    
    try:
        # 尝试只读模式
        wb = load_workbook(input_file, read_only=True, data_only=True)
        ws = wb.active
        
        # 复制数据
        for row in ws.iter_rows(values_only=True):
            new_ws.append(row)
        
        wb.close()
        new_wb.save(output_file)
        print('✅ 文件修复成功！')
        print(f'📄 输出: {output_file}')
        sys.exit(0)
    except:
        print('❌ 方法1失败')
        sys.exit(1)
except Exception as e:
    print(f'❌ 错误: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ 修复完成！"
    echo "📄 新文件: $OUTPUT_FILE"
    echo ""
    echo "现在可以："
    echo "1. 在8101服务中上传 $OUTPUT_FILE"
    echo "2. 或使用路径加载功能"
    exit 0
fi

echo ""
echo "💡 修复失败，建议："
echo "1. 在腾讯文档中重新导出为CSV格式"
echo "2. 或用Microsoft Excel打开后另存为"
echo "3. 或使用WPS Office打开后另存为"