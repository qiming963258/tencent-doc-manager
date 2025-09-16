#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析下载的EJS文件，找出问题所在
"""

import json
import base64
import urllib.parse
import re
from pathlib import Path
import struct

def analyze_ejs_file(file_path):
    """深度分析EJS文件结构"""
    print(f"\n{'='*80}")
    print(f"深度分析文件: {Path(file_path).name}")
    print(f"文件大小: {Path(file_path).stat().st_size} bytes")
    print(f"{'='*80}")
    
    with open(file_path, 'rb') as f:
        raw_bytes = f.read()
    
    # 1. 检查文件格式
    print("\n1. 文件格式检查:")
    print(f"   前4字节(hex): {raw_bytes[:4].hex()}")
    print(f"   前4字节(ascii): {repr(raw_bytes[:4])}")
    
    # 检查是否是标准格式
    if raw_bytes[:4] == b'head':
        print("   ✅ 检测到标准EJS格式 (head标识)")
        return analyze_standard_ejs(file_path)
    elif raw_bytes[:4] == b'text':
        print("   ✅ 检测到text格式EJS")
        return analyze_text_ejs(file_path)
    elif b'"","' in raw_bytes[:20]:
        print("   ✅ 检测到CSV格式EJS")
        return analyze_csv_ejs(file_path)
    else:
        print("   ❓ 未知格式")
        return analyze_unknown_format(file_path)

def analyze_standard_ejs(file_path):
    """分析标准EJS格式(head/json/text)"""
    print("\n2. 标准EJS格式分析:")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    structure = {
        'format': 'standard_ejs',
        'sections': [],
        'has_workbook': False,
        'has_related_sheet': False,
        'metadata': None,
        'data_found': []
    }
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line == 'head':
            structure['sections'].append('head')
            print(f"   行{i+1}: 找到head标识")
            
        elif line == 'json':
            structure['sections'].append('json')
            if i + 2 < len(lines):
                json_length = int(lines[i + 1])
                json_data = lines[i + 2]
                print(f"   行{i+1}: JSON段, 长度={json_length}")
                
                try:
                    metadata = json.loads(json_data)
                    structure['metadata'] = metadata
                    
                    if 'bodyData' in metadata:
                        title = metadata['bodyData'].get('initialTitle', 'N/A')
                        print(f"      文档标题: {title}")
                        
                    if 'clientVars' in metadata:
                        user_id = metadata['clientVars'].get('userId', 'N/A')
                        print(f"      用户ID: {user_id}")
                        
                except Exception as e:
                    print(f"      JSON解析失败: {e}")
                    
        elif line == 'text':
            structure['sections'].append('text')
            print(f"   行{i+1}: text段")
            
        elif '%7B%22workbook%22' in line or 'workbook' in line:
            print(f"   行{i+1}: 找到workbook数据")
            structure['has_workbook'] = True
            
            # 分析workbook内容
            try:
                decoded = urllib.parse.unquote(line)
                data = json.loads(decoded)
                
                if 'workbook' in data:
                    wb_length = len(data['workbook'])
                    print(f"      workbook Base64长度: {wb_length}")
                    
                    # 尝试解码
                    wb_bytes = base64.b64decode(data['workbook'])
                    print(f"      解码后字节数: {len(wb_bytes)}")
                    print(f"      前4字节: {wb_bytes[:4].hex()}")
                    
                    # 检查压缩类型
                    if wb_bytes[:2] == b'\x78\x01':
                        print(f"      ✅ zlib压缩格式")
                    elif wb_bytes[:2] == b'\x78\x9c':
                        print(f"      ✅ zlib压缩格式(高压缩)")
                    elif wb_bytes[:2] == b'\x1f\x8b':
                        print(f"      ✅ gzip压缩格式")
                    else:
                        print(f"      ❓ 未知压缩格式")
                    
                if 'related_sheet' in data:
                    structure['has_related_sheet'] = True
                    rs_length = len(data['related_sheet'])
                    print(f"      related_sheet长度: {rs_length}")
                    
                    # 尝试解码
                    rs_bytes = base64.b64decode(data['related_sheet'])
                    print(f"      related_sheet解码后: {len(rs_bytes)} bytes")
                    
                if 'max_row' in data:
                    print(f"      表格大小: {data['max_row']} × {data['max_col']}")
                    
            except Exception as e:
                print(f"      解析失败: {e}")
        
        i += 1
    
    return structure

def analyze_text_ejs(file_path):
    """分析text格式EJS"""
    print("\n2. Text格式EJS分析:")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines[:10]):
        print(f"   行{i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
    
    # 查找workbook
    for line in lines:
        if 'workbook' in line:
            print("\n   找到workbook数据!")
            break
    
    return {'format': 'text_ejs', 'lines': len(lines)}

def analyze_csv_ejs(file_path):
    """分析CSV格式EJS"""
    print("\n2. CSV格式EJS分析:")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用CSV解析
    import csv
    import io
    
    csv_reader = csv.reader(io.StringIO(content))
    rows = list(csv_reader)
    
    print(f"   CSV行数: {len(rows)}")
    print(f"   第一行列数: {len(rows[0]) if rows else 0}")
    
    # 分析内容类型
    all_cells = []
    chinese_cells = []
    number_cells = []
    
    for row in rows:
        for cell in row:
            cell = cell.strip()
            if cell:
                all_cells.append(cell)
                
                # 检查是否包含中文
                if re.search(r'[\u4e00-\u9fff]', cell):
                    chinese_cells.append(cell)
                    
                # 检查是否是数字
                if cell.replace('.', '').replace('-', '').isdigit():
                    number_cells.append(cell)
    
    print(f"   总单元格数: {len(all_cells)}")
    print(f"   中文单元格: {len(chinese_cells)}")
    print(f"   数字单元格: {len(number_cells)}")
    
    # 查找关键信息
    print("\n   关键信息查找:")
    
    # 版本号
    for cell in all_cells:
        if re.match(r'\d+\.\d+\.\d+', cell):
            print(f"      版本号: {cell}")
            break
    
    # 工作表信息
    for cell in chinese_cells:
        if '工作表' in cell:
            print(f"      工作表: {cell}")
            break
    
    # 显示前10个中文内容
    if chinese_cells:
        print("\n   前10个中文内容:")
        for i, cell in enumerate(chinese_cells[:10], 1):
            print(f"      {i}. {cell}")
    
    # 检查是否有真实数据
    real_data = []
    for cell in all_cells:
        # 排除明显的系统信息
        if (len(cell) > 2 and 
            not any(k in cell.lower() for k in ['font', 'color', 'calibri', 'arial']) and
            not cell in ['*', ':', 'J', 'B', 'R']):
            real_data.append(cell)
    
    print(f"\n   可能的真实数据: {len(real_data)}个")
    if real_data:
        print("   示例:")
        for i, data in enumerate(real_data[:5], 1):
            print(f"      {i}. {data[:50]}...")
    
    return {
        'format': 'csv_ejs',
        'rows': len(rows),
        'total_cells': len(all_cells),
        'chinese_cells': len(chinese_cells),
        'real_data': len(real_data)
    }

def analyze_unknown_format(file_path):
    """分析未知格式"""
    print("\n2. 未知格式分析:")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # 显示前100字节
    print(f"   前100字节(hex):")
    print(f"   {data[:100].hex()}")
    
    # 尝试作为文本
    try:
        text = data.decode('utf-8')
        print(f"   UTF-8解码成功, 长度={len(text)}")
        
        # 查找关键词
        if 'workbook' in text:
            print("   ✅ 包含workbook关键词")
        if '工作表' in text:
            print("   ✅ 包含中文'工作表'")
            
    except:
        print("   ❌ 不是UTF-8文本")
    
    return {'format': 'unknown'}

def main():
    """主函数"""
    print("🔍 深度分析下载的EJS文件")
    print("="*80)
    
    # 分析所有下载的文件
    test_dir = Path('/root/projects/tencent-doc-manager/real_test_results')
    ejs_files = list(test_dir.glob('*.ejs'))
    
    if not ejs_files:
        # 尝试其他位置
        test_dir = Path('/root/projects/tencent-doc-manager')
        ejs_files = list(test_dir.glob('test_*.csv')) + list(test_dir.glob('test_*.xlsx'))
    
    print(f"找到 {len(ejs_files)} 个文件待分析")
    
    results = []
    for ejs_file in ejs_files:
        result = analyze_ejs_file(str(ejs_file))
        result['file'] = ejs_file.name
        results.append(result)
    
    # 总结
    print("\n" + "="*80)
    print("📊 分析总结")
    print("="*80)
    
    for result in results:
        print(f"\n文件: {result['file']}")
        print(f"   格式: {result.get('format', 'unknown')}")
        
        if result.get('has_workbook'):
            print(f"   ✅ 包含workbook数据")
        if result.get('has_related_sheet'):
            print(f"   ✅ 包含related_sheet数据")
        if result.get('chinese_cells'):
            print(f"   中文内容: {result['chinese_cells']}个")
        if result.get('real_data'):
            print(f"   可能的真实数据: {result['real_data']}个")
    
    # 问题诊断
    print("\n" + "="*80)
    print("🔍 问题诊断")
    print("="*80)
    
    csv_format_files = [r for r in results if r.get('format') == 'csv_ejs']
    if csv_format_files:
        print("\n问题原因：")
        print("1. 新下载的文档使用CSV格式而不是标准EJS格式")
        print("2. CSV格式中的数据已经部分解密，但仍包含编码内容")
        print("3. 中文内容存在但是乱码，可能是：")
        print("   - protobuf二进制数据误读为UTF-8")
        print("   - 需要额外的解码步骤")
        print("   - 测试文档本身是空白或只有格式没有数据")
        
        print("\n解决方案：")
        print("1. 需要识别并跳过protobuf编码的部分")
        print("2. 只提取真正的文本内容")
        print("3. 或者用包含实际数据的文档重新测试")

if __name__ == "__main__":
    main()