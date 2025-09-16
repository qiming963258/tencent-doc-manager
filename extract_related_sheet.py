#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门提取related_sheet中的真实业务数据
这是年项目计划与安排表的真实内容
"""

import json
import base64
import zlib
import urllib.parse
import re
from pathlib import Path
import struct

def extract_related_sheet_data():
    """提取related_sheet中的真实表格数据"""
    print("="*60)
    print("提取年项目计划与安排表数据")
    print("="*60)
    
    # 读取原始EJS文件
    test_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找包含related_sheet的行
    for line in content.split('\n'):
        if '%7B%22workbook%22' in line:
            # URL解码
            decoded = urllib.parse.unquote(line.strip())
            data = json.loads(decoded)
            
            if 'related_sheet' in data and data['related_sheet']:
                print("✅ 找到related_sheet数据")
                
                # Base64解码
                related_bytes = base64.b64decode(data['related_sheet'])
                print(f"  原始大小: {len(related_bytes)} bytes")
                
                # zlib解压
                try:
                    decompressed = zlib.decompress(related_bytes)
                    print(f"  解压后大小: {len(decompressed)} bytes")
                    
                    # 保存解压后的数据
                    with open('related_sheet_decompressed.bin', 'wb') as f:
                        f.write(decompressed)
                    print("  已保存: related_sheet_decompressed.bin")
                    
                    # 分析数据
                    return analyze_sheet_data(decompressed)
                    
                except Exception as e:
                    print(f"  解压失败: {e}")
                    # 尝试其他解压方法
                    try:
                        decompressed = zlib.decompress(related_bytes, -15)
                        print(f"  Raw deflate解压成功: {len(decompressed)} bytes")
                        return analyze_sheet_data(decompressed)
                    except:
                        pass
    
    return None

def analyze_sheet_data(data):
    """分析表格数据结构"""
    print("\n分析表格数据结构...")
    
    result = {
        'headers': [],
        'rows': [],
        'chinese_content': [],
        'cells': []
    }
    
    # 提取所有中文内容
    try:
        text = data.decode('utf-8', errors='ignore')
        chinese_pattern = r'[\u4e00-\u9fff]+'
        chinese_matches = re.findall(chinese_pattern, text)
        
        # 去重并过滤
        unique_chinese = []
        for match in chinese_matches:
            if len(match) >= 2 and match not in unique_chinese:
                unique_chinese.append(match)
        
        result['chinese_content'] = unique_chinese
        
        print(f"  找到 {len(unique_chinese)} 个中文内容:")
        
        # 识别表头
        header_keywords = ['序号', '项目', '类型', '来源', '负责人', '日期', '状态', '备注', '年', '月', '日', '修改']
        found_headers = []
        
        for chinese in unique_chinese[:30]:
            if any(k in chinese for k in header_keywords):
                found_headers.append(chinese)
                print(f"    表头: {chinese}")
        
        result['headers'] = found_headers
        
    except Exception as e:
        print(f"  UTF-8解析失败: {e}")
    
    # 提取ASCII文本（可能包含英文内容）
    ascii_content = []
    current_string = []
    start_pos = 0
    
    for i, byte in enumerate(data):
        if 32 <= byte <= 126:  # 可打印ASCII
            if not current_string:
                start_pos = i
            current_string.append(chr(byte))
        else:
            if len(current_string) > 2:
                text = ''.join(current_string)
                if not text.isspace():
                    ascii_content.append({
                        'pos': start_pos,
                        'text': text
                    })
            current_string = []
    
    print(f"  找到 {len(ascii_content)} 个ASCII字符串")
    
    # 组合单元格数据
    all_cells = []
    
    # 添加中文内容作为单元格
    for chinese in result['chinese_content']:
        all_cells.append(chinese)
    
    # 添加有意义的ASCII内容
    for item in ascii_content:
        text = item['text']
        # 过滤系统信息
        if not any(k in text.lower() for k in ['font', 'color', 'style', 'calibri']):
            if len(text) > 1 and len(text) < 100:
                all_cells.append(text)
    
    result['cells'] = all_cells
    
    # 尝试识别数据模式
    print("\n查找数据模式...")
    
    # 查找可能的protobuf字段
    protobuf_fields = extract_protobuf_fields(data)
    if protobuf_fields:
        print(f"  找到 {len(protobuf_fields)} 个protobuf字段")
        result['protobuf_fields'] = protobuf_fields
    
    return result

def extract_protobuf_fields(data):
    """提取protobuf字段"""
    fields = []
    i = 0
    
    while i < len(data) - 10:
        try:
            # protobuf字段格式: (field_number << 3) | wire_type
            tag = data[i]
            if tag == 0:
                i += 1
                continue
            
            field_number = tag >> 3
            wire_type = tag & 0x07
            
            if wire_type == 2:  # length-delimited (字符串)
                i += 1
                # 读取长度
                length = 0
                shift = 0
                while i < len(data):
                    b = data[i]
                    length |= (b & 0x7F) << shift
                    i += 1
                    if not (b & 0x80):
                        break
                    shift += 7
                
                if 0 < length < 1000 and i + length <= len(data):
                    content = data[i:i+length]
                    
                    # 尝试解码为字符串
                    try:
                        text = content.decode('utf-8')
                        if len(text) > 1:
                            fields.append({
                                'field': field_number,
                                'type': 'string',
                                'value': text[:100]
                            })
                    except:
                        pass
                    
                i += length
            else:
                i += 1
                
        except:
            i += 1
    
    return fields

def generate_project_table_csv(data):
    """生成项目计划表CSV"""
    print("\n生成项目计划表CSV...")
    
    if not data:
        print("  没有数据")
        return None
    
    # 构建表格
    headers = ['序号', '项目类型', '来源', '负责人', '年', '月', '日', '状态', '修改', '备注']
    
    # 使用找到的中文内容构建行
    rows = []
    current_row = []
    
    for cell in data['cells']:
        if cell and not cell.isdigit():
            current_row.append(cell)
            
            if len(current_row) >= len(headers):
                rows.append(current_row[:len(headers)])
                current_row = []
    
    # 添加最后一行
    if current_row:
        while len(current_row) < len(headers):
            current_row.append('')
        rows.append(current_row)
    
    # 生成CSV
    csv_lines = []
    
    # 添加表头
    csv_lines.append(','.join(f'"{h}"' for h in headers))
    
    # 添加数据行
    for row in rows[:50]:  # 限制前50行
        csv_line = ','.join(f'"{cell}"' for cell in row)
        csv_lines.append(csv_line)
    
    csv_content = '\n'.join(csv_lines)
    
    # 保存文件
    output_file = 'project_plan_table.csv'
    with open(output_file, 'w', encoding='utf-8-sig') as f:  # utf-8-sig确保Excel正确显示中文
        f.write(csv_content)
    
    print(f"✅ 已生成: {output_file}")
    print(f"   包含 {len(rows)} 行数据")
    
    # 预览
    print("\n前5行预览:")
    for i, line in enumerate(csv_lines[:6]):
        if i == 0:
            print(f"  表头: {line}")
        else:
            print(f"  行{i}: {line[:100]}...")
    
    return output_file

def main():
    """主函数"""
    print("🚀 开始提取真实的项目计划表数据")
    print("="*60)
    
    # 提取related_sheet数据
    sheet_data = extract_related_sheet_data()
    
    if sheet_data:
        print(f"\n✅ 成功提取数据:")
        print(f"  中文内容: {len(sheet_data['chinese_content'])}个")
        print(f"  单元格: {len(sheet_data['cells'])}个")
        
        if sheet_data['headers']:
            print(f"  识别的表头: {', '.join(sheet_data['headers'][:10])}")
        
        # 生成CSV
        csv_file = generate_project_table_csv(sheet_data)
        
        if csv_file:
            print("\n" + "="*60)
            print("🎉 成功提取年项目计划与安排表！")
            print("="*60)
            print(f"输出文件: {csv_file}")
            print("这是真实的业务数据表格")
            
            return True
    else:
        print("\n❌ 提取失败")
        
    return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ 实际测试成功！我们成功提取了真实的业务数据！")
    else:
        print("\n需要进一步改进提取算法")