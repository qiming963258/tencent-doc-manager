#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解码CSV格式中嵌入的protobuf数据
"""

import csv
import re
from pathlib import Path
from datetime import datetime

def extract_protobuf_from_csv_ejs(file_path):
    """从CSV-EJS文件中提取protobuf数据"""
    print(f"\n{'='*60}")
    print(f"解码CSV-protobuf混合文档: {Path(file_path).name}")
    print(f"{'='*60}")
    
    # 读取原始二进制数据
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    
    # 查找protobuf数据起始位置
    proto_markers = [b'\x08\x01\x1a', b'\x08\x01\x12', b'\x1a\x08']
    proto_start = -1
    
    for marker in proto_markers:
        pos = raw_data.find(marker)
        if pos > 0:
            proto_start = pos
            print(f"找到protobuf数据起始位置: {proto_start}")
            break
    
    if proto_start < 0:
        print("未找到protobuf数据")
        return None
    
    # 提取protobuf部分
    proto_data = raw_data[proto_start:]
    
    # 解析protobuf字段
    extracted_data = parse_protobuf_fields(proto_data)
    
    # 提取所有中文内容
    chinese_content = extract_all_chinese(raw_data)
    
    return {
        'proto_data': proto_data,
        'extracted_fields': extracted_data,
        'chinese_content': chinese_content,
        'csv_part': raw_data[:proto_start]
    }

def parse_protobuf_fields(data):
    """解析protobuf字段"""
    fields = []
    i = 0
    
    while i < len(data):
        # protobuf wire type
        if i >= len(data):
            break
            
        tag = data[i]
        wire_type = tag & 0x07
        field_num = tag >> 3
        
        i += 1
        
        if wire_type == 2:  # Length-delimited (string, bytes)
            # 读取varint长度
            length = 0
            shift = 0
            while i < len(data):
                byte = data[i]
                i += 1
                length |= (byte & 0x7F) << shift
                if not (byte & 0x80):
                    break
                shift += 7
            
            # 读取数据
            if i + length <= len(data):
                field_data = data[i:i+length]
                i += length
                
                # 尝试解码为UTF-8
                try:
                    text = field_data.decode('utf-8', errors='ignore')
                    if text and any('\u4e00' <= c <= '\u9fff' for c in text):
                        fields.append({
                            'field_num': field_num,
                            'type': 'chinese_text',
                            'value': text
                        })
                    elif text and len(text) > 1:
                        fields.append({
                            'field_num': field_num,
                            'type': 'text',
                            'value': text
                        })
                except:
                    pass
        else:
            # 跳过其他wire types
            if wire_type == 0:  # Varint
                while i < len(data) and data[i] & 0x80:
                    i += 1
                i += 1
            elif wire_type == 1:  # 64-bit
                i += 8
            elif wire_type == 5:  # 32-bit
                i += 4
    
    return fields

def extract_all_chinese(data):
    """提取所有中文内容"""
    chinese_texts = []
    i = 0
    
    while i < len(data) - 2:
        # UTF-8中文字符范围
        if 0xe4 <= data[i] <= 0xe9:
            # 尝试解码3字节UTF-8
            if i + 2 < len(data):
                try:
                    char = data[i:i+3].decode('utf-8', errors='strict')
                    if '\u4e00' <= char <= '\u9fff':
                        # 继续读取连续的中文
                        j = i + 3
                        chinese_str = char
                        
                        while j < len(data) - 2:
                            if 0xe4 <= data[j] <= 0xe9:
                                try:
                                    next_char = data[j:j+3].decode('utf-8', errors='strict')
                                    if '\u4e00' <= next_char <= '\u9fff':
                                        chinese_str += next_char
                                        j += 3
                                    else:
                                        break
                                except:
                                    break
                            else:
                                break
                        
                        if len(chinese_str) >= 2:  # 至少2个字符
                            chinese_texts.append(chinese_str)
                        i = j
                        continue
                except:
                    pass
        i += 1
    
    return chinese_texts

def decode_csv_part(csv_data):
    """解码CSV部分"""
    try:
        csv_text = csv_data.decode('utf-8', errors='ignore')
        rows = []
        
        # 解析CSV
        import io
        reader = csv.reader(io.StringIO(csv_text))
        for row in reader:
            if any(cell.strip() for cell in row):
                rows.append(row)
        
        return rows
    except Exception as e:
        print(f"CSV解码错误: {e}")
        return []

def main():
    """主函数"""
    print("🔧 CSV-Protobuf混合格式解码器")
    print("="*60)
    
    test_dir = Path('/root/projects/tencent-doc-manager/real_test_results')
    ejs_files = [
        'DWEVjZndkR2xVSWJN_CSV_20250828_102625.ejs',  # 小红书部门
        'DRFppYm15RGZ2WExN_CSV_20250828_102627.ejs',  # 回国销售计划
        'DRHZrS1hOS3pwRGZB_CSV_20250828_102630.ejs'   # 出国销售计划
    ]
    
    for ejs_file in ejs_files:
        file_path = test_dir / ejs_file
        if not file_path.exists():
            continue
            
        result = extract_protobuf_from_csv_ejs(str(file_path))
        
        if result:
            print(f"\n提取结果:")
            print(f"  CSV部分大小: {len(result['csv_part'])} bytes")
            print(f"  Protobuf部分大小: {len(result['proto_data'])} bytes")
            print(f"  提取字段数: {len(result['extracted_fields'])}")
            print(f"  中文内容数: {len(result['chinese_content'])}")
            
            # 显示前10个中文内容
            if result['chinese_content']:
                print(f"\n中文内容示例:")
                for i, text in enumerate(result['chinese_content'][:10], 1):
                    print(f"  {i}. {text}")
            
            # 解码CSV部分
            csv_rows = decode_csv_part(result['csv_part'])
            if csv_rows:
                print(f"\nCSV行数: {len(csv_rows)}")
                print(f"第一行内容: {csv_rows[0][:5] if csv_rows else '无'}")
            
            # 保存提取的中文内容
            output_file = file_path.with_suffix('.chinese.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                for text in result['chinese_content']:
                    f.write(text + '\n')
            print(f"\n中文内容已保存到: {output_file.name}")

if __name__ == "__main__":
    main()