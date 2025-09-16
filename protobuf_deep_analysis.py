#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析protobuf数据结构，尝试逆向工程表格数据
"""

import struct
import json
from pathlib import Path

def analyze_protobuf_structure(data):
    """详细分析protobuf结构"""
    print("="*60)
    print("深度protobuf结构分析")
    print("="*60)
    
    print(f"数据总长度: {len(data)} bytes")
    
    # 分析字段结构
    fields = []
    i = 0
    field_count = 0
    
    while i < len(data) and field_count < 100:  # 分析前100个字段
        try:
            if i >= len(data):
                break
            
            # 读取tag
            tag = data[i]
            if tag == 0:
                i += 1
                continue
                
            field_number = tag >> 3
            wire_type = tag & 0x07
            
            field_info = {
                'offset': i,
                'tag': tag,
                'field_number': field_number,
                'wire_type': wire_type,
                'data': None
            }
            
            i += 1
            
            if wire_type == 0:  # varint
                value = 0
                shift = 0
                while i < len(data) and data[i] & 0x80:
                    value |= (data[i] & 0x7F) << shift
                    shift += 7
                    i += 1
                if i < len(data):
                    value |= data[i] << shift
                    i += 1
                field_info['data'] = ('varint', value)
                
            elif wire_type == 1:  # 64-bit
                if i + 8 <= len(data):
                    value = struct.unpack('<Q', data[i:i+8])[0]
                    field_info['data'] = ('fixed64', value)
                i += 8
                
            elif wire_type == 2:  # length-delimited
                # 读取长度
                length = 0
                shift = 0
                start_i = i
                while i < len(data):
                    b = data[i]
                    length |= (b & 0x7F) << shift
                    i += 1
                    if not (b & 0x80):
                        break
                    shift += 7
                
                if length < 10000 and i + length <= len(data):  # 合理的长度
                    content = data[i:i+length]
                    
                    # 尝试解析内容
                    try:
                        # 尝试UTF-8字符串
                        text = content.decode('utf-8')
                        if text.isprintable() or any(ord(c) > 127 for c in text):
                            field_info['data'] = ('string', text)
                        else:
                            field_info['data'] = ('bytes', content[:50])
                    except:
                        # 可能是嵌套消息或二进制数据
                        field_info['data'] = ('bytes', content[:50])
                    
                i += length
                
            elif wire_type == 5:  # 32-bit
                if i + 4 <= len(data):
                    value = struct.unpack('<I', data[i:i+4])[0]
                    field_info['data'] = ('fixed32', value)
                i += 4
                
            else:
                i += 1
                continue
            
            fields.append(field_info)
            field_count += 1
            
        except Exception as e:
            i += 1
            continue
    
    return fields

def find_table_data(fields):
    """在protobuf字段中查找表格数据"""
    print("\n查找表格相关数据:")
    
    table_fields = []
    
    for field in fields:
        if field['data'] is None:
            continue
            
        data_type, value = field['data']
        
        # 查找字符串字段（可能包含表格数据）
        if data_type == 'string' and len(value) > 10:
            # 检查是否包含表格相关关键词
            if any(keyword in value.lower() for keyword in ['cell', 'row', 'col', 'sheet', 'table', '工作表']):
                table_fields.append({
                    'field': field['field_number'],
                    'type': 'table_string',
                    'value': value[:200]
                })
                print(f"  字段{field['field_number']} (表格字符串): {value[:100]}...")
            
            # 检查是否是颜色代码
            elif any(color in value for color in ['#', '000000', 'FFFFFF', 'rgb']):
                table_fields.append({
                    'field': field['field_number'],
                    'type': 'color',
                    'value': value
                })
                print(f"  字段{field['field_number']} (颜色): {value}")
                
            # 检查是否是字体信息
            elif any(font in value for font in ['Calibri', 'Arial', 'Times', '宋体', '微软雅黑']):
                table_fields.append({
                    'field': field['field_number'],
                    'type': 'font',
                    'value': value
                })
                print(f"  字段{field['field_number']} (字体): {value}")
        
        # 查找数值字段（可能是坐标或大小）
        elif data_type == 'varint' and 0 < value < 10000:
            # 可能的行列数
            if value == 166 or value == 21:  # 我们知道的表格大小
                table_fields.append({
                    'field': field['field_number'],
                    'type': 'dimension',
                    'value': value
                })
                print(f"  字段{field['field_number']} (表格维度): {value}")
    
    return table_fields

def extract_cell_data(data):
    """尝试提取单元格数据"""
    print("\n尝试提取单元格数据:")
    
    # 方法1：查找重复的数据模式
    patterns = {}
    i = 0
    while i < len(data) - 8:
        # 查找4字节模式
        pattern = data[i:i+4]
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(i)
        i += 1
    
    # 找出重复次数多的模式（可能是单元格分隔符）
    frequent_patterns = {k: v for k, v in patterns.items() if len(v) > 5}
    
    if frequent_patterns:
        print(f"  找到{len(frequent_patterns)}个高频模式:")
        for pattern, positions in list(frequent_patterns.items())[:5]:
            print(f"    {pattern.hex()}: 出现{len(positions)}次")
    
    # 方法2：查找ASCII字符串（可能的单元格内容）
    cell_contents = []
    current_string = []
    
    for i, byte in enumerate(data):
        if 32 <= byte <= 126:  # 可打印ASCII
            current_string.append(chr(byte))
        else:
            if len(current_string) > 2:
                text = ''.join(current_string)
                if not text.isspace() and not all(c.isdigit() for c in text):
                    cell_contents.append((i - len(current_string), text))
            current_string = []
    
    if cell_contents:
        print(f"  找到{len(cell_contents)}个可能的单元格内容:")
        for pos, content in cell_contents[:10]:
            print(f"    位置{pos}: {content}")
    
    # 方法3：查找数值序列
    numbers = []
    for i in range(0, len(data) - 4, 1):
        try:
            # 尝试读取各种数值格式
            formats = [
                ('<i', 'int32'),
                ('<I', 'uint32'), 
                ('<f', 'float32'),
                ('<d', 'float64'),
            ]
            
            for fmt, name in formats:
                try:
                    value = struct.unpack(fmt, data[i:i+struct.calcsize(fmt)])[0]
                    
                    # 检查是否是合理的数值
                    if name.startswith('float'):
                        if not (-1e6 < value < 1e6) or abs(value) < 1e-10:
                            continue
                    elif name.startswith('int'):
                        if not (-1000000 < value < 1000000):
                            continue
                    
                    numbers.append((i, name, value))
                    break
                except:
                    continue
                    
        except:
            continue
    
    if numbers:
        print(f"  找到{len(numbers)}个数值:")
        # 按类型分组
        by_type = {}
        for pos, dtype, val in numbers:
            if dtype not in by_type:
                by_type[dtype] = []
            by_type[dtype].append((pos, val))
        
        for dtype, values in by_type.items():
            print(f"    {dtype}: {len(values)}个")
            for pos, val in values[:5]:
                print(f"      位置{pos}: {val}")
    
    return cell_contents, numbers

def reverse_engineer_schema(fields):
    """尝试逆向工程protobuf schema"""
    print("\n逆向工程可能的.proto结构:")
    
    print("message TencentSheetData {")
    
    # 按字段号排序
    sorted_fields = sorted([f for f in fields if f['data']], key=lambda x: x['field_number'])
    
    for field in sorted_fields[:20]:  # 只显示前20个字段
        field_num = field['field_number']
        data_type, value = field['data']
        
        if data_type == 'string':
            print(f"  string field_{field_num} = {field_num}; // {value[:50]}...")
        elif data_type == 'varint':
            if value < 256:
                print(f"  int32 field_{field_num} = {field_num}; // {value}")
            else:
                print(f"  int64 field_{field_num} = {field_num}; // {value}")
        elif data_type == 'bytes':
            print(f"  bytes field_{field_num} = {field_num}; // {len(value)} bytes")
        elif data_type in ['fixed32', 'fixed64']:
            print(f"  {data_type.replace('fixed', 'int')} field_{field_num} = {field_num}; // {value}")
    
    print("}")

def main():
    """主函数"""
    # 读取解压后的protobuf数据
    protobuf_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718_nodejs_decoded.bin"
    
    if not Path(protobuf_file).exists():
        print(f"需要先运行Node.js解压脚本生成: {protobuf_file}")
        return
    
    with open(protobuf_file, 'rb') as f:
        data = f.read()
    
    print(f"开始分析protobuf数据: {protobuf_file}")
    
    # 1. 分析字段结构
    fields = analyze_protobuf_structure(data)
    
    print(f"\n找到 {len(fields)} 个protobuf字段")
    
    # 2. 查找表格相关数据
    table_fields = find_table_data(fields)
    
    # 3. 尝试提取单元格数据
    cell_contents, numbers = extract_cell_data(data)
    
    # 4. 逆向工程schema
    reverse_engineer_schema(fields)
    
    # 5. 生成分析报告
    report = {
        'total_fields': len(fields),
        'table_fields': len(table_fields),
        'cell_contents': len(cell_contents),
        'numbers_found': len(numbers),
        'fields_detail': [
            {
                'field': f['field_number'],
                'type': f['data'][0] if f['data'] else 'unknown',
                'preview': str(f['data'][1])[:100] if f['data'] else None
            }
            for f in fields[:50]  # 前50个字段
        ]
    }
    
    with open('protobuf_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n分析报告已保存: protobuf_analysis_report.json")
    
    print("\n" + "="*60)
    print("分析结论")
    print("="*60)
    
    if table_fields:
        print(f"✅ 找到 {len(table_fields)} 个表格相关字段")
    if cell_contents:
        print(f"✅ 找到 {len(cell_contents)} 个可能的单元格内容")
    if numbers:
        print(f"✅ 找到 {len(numbers)} 个数值数据")
    
    print("\n下一步:")
    print("1. 进一步分析字段关系")
    print("2. 尝试构建完整的.proto定义")
    print("3. 或者继续优化浏览器自动化方案")

if __name__ == "__main__":
    main()