#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寻找真实的用户业务数据
我们之前解析的可能只是元数据，真实的表格数据可能在其他地方
"""

import json
import urllib.parse
import base64
import zlib
from pathlib import Path

def analyze_full_ejs_structure():
    """完整分析EJS文件结构，寻找用户数据"""
    print("="*60)
    print("完整分析EJS文件，寻找用户业务数据")
    print("="*60)
    
    ejs_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv"
    
    with open(ejs_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"EJS文件总行数: {len(lines)}")
    
    # 详细分析每一行
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        print(f"\n第{i+1}行分析:")
        print(f"长度: {len(line)} 字符")
        
        if line == 'head':
            print("类型: EJS头部")
        elif line == 'json':
            print("类型: JSON段开始")
        elif line == 'text':
            print("类型: 文本段")
        elif line.isdigit():
            print(f"类型: 长度标识 ({line} 字符)")
        elif line.startswith('{') and line.endswith('}'):
            print("类型: JSON数据")
            try:
                data = json.loads(line)
                print(f"JSON Keys: {list(data.keys())}")
                
                # 检查bodyData中的实际内容
                if 'bodyData' in data:
                    body_data = data['bodyData']
                    print(f"bodyData Keys: {list(body_data.keys())}")
                    
                    # 查找可能包含用户数据的字段
                    if 'cont' in body_data:
                        cont = body_data['cont']
                        print(f"发现cont字段，长度: {len(cont)}")
                        
                        # 尝试解析cont字段（可能包含实际数据）
                        if isinstance(cont, str) and len(cont) > 100:
                            print("分析cont内容...")
                            analyze_cont_field(cont)
                    
                    # 检查其他可能的数据字段
                    for key, value in body_data.items():
                        if isinstance(value, str) and len(value) > 1000:
                            print(f"发现大数据字段 {key}: {len(value)} 字符")
            except Exception as e:
                print(f"JSON解析失败: {e}")
                
        elif line.startswith('%7B'):
            print("类型: URL编码数据")
            try:
                decoded = urllib.parse.unquote(line)
                data = json.loads(decoded)
                
                # 这是我们之前分析的workbook数据
                print("包含workbook等字段（已分析过）")
                
                # 但检查是否还有其他数据
                for key, value in data.items():
                    if key not in ['workbook', 'related_sheet', 'max_row', 'max_col']:
                        print(f"发现其他字段 {key}: {type(value)}")
                        if isinstance(value, str) and len(value) > 100:
                            print(f"  可能包含用户数据，长度: {len(value)}")
                            
            except Exception as e:
                print(f"URL解码失败: {e}")
        else:
            print(f"类型: 其他")
            if len(line) > 50:
                print(f"预览: {line[:100]}...")

def analyze_cont_field(cont_data):
    """分析bodyData.cont字段，可能包含实际用户数据"""
    print("\n  分析cont字段内容:")
    
    # cont字段可能是base64编码或其他格式
    try:
        # 尝试base64解码
        decoded = base64.b64decode(cont_data)
        print(f"  Base64解码成功: {len(decoded)} bytes")
        
        # 检查是否是压缩数据
        if decoded[:2] in [b'\x78\x01', b'\x78\x9c', b'\x78\xda']:
            print("  检测到zlib压缩")
            try:
                decompressed = zlib.decompress(decoded)
                print(f"  解压成功: {len(decompressed)} bytes")
                
                # 保存解压后的数据
                output_file = "cont_field_decompressed.bin"
                with open(output_file, 'wb') as f:
                    f.write(decompressed)
                print(f"  已保存: {output_file}")
                
                # 尝试解析内容
                try:
                    text = decompressed.decode('utf-8')
                    print(f"  UTF-8解码成功，查找用户数据...")
                    
                    # 查找可能的表格数据标识
                    keywords = ['小红书', '部门', '测试', 'cell', 'row', 'column', 'data']
                    found_keywords = [kw for kw in keywords if kw in text]
                    
                    if found_keywords:
                        print(f"  ✅ 找到用户数据关键词: {found_keywords}")
                        return analyze_user_data_content(text)
                    else:
                        print("  未找到明显的用户数据关键词")
                        
                except Exception as e:
                    print(f"  UTF-8解码失败: {e}")
                    
            except Exception as e:
                print(f"  zlib解压失败: {e}")
        else:
            print("  不是zlib压缩格式")
            
    except Exception as e:
        print(f"  Base64解码失败: {e}")
        
    # 尝试直接文本搜索
    if '小红书' in cont_data or '部门' in cont_data:
        print("  ✅ 在原始cont数据中找到用户关键词!")
        return True
    
    return False

def analyze_user_data_content(text_content):
    """分析可能的用户数据内容"""
    print("\n    详细分析用户数据:")
    
    # 查找表格相关内容
    import re
    
    # 查找中文内容
    chinese_pattern = r'[\u4e00-\u9fff]+'
    chinese_matches = re.findall(chinese_pattern, text_content)
    
    if chinese_matches:
        print(f"    找到中文内容: {len(chinese_matches)}个")
        for i, match in enumerate(chinese_matches[:10]):
            print(f"      {i+1}. {match}")
    
    # 查找数字
    number_pattern = r'\d+'
    numbers = re.findall(number_pattern, text_content)
    if len(numbers) > 10:
        print(f"    找到大量数字: {len(numbers)}个")
    
    # 查找可能的单元格引用
    cell_pattern = r'[A-Z]+\d+'
    cells = re.findall(cell_pattern, text_content)
    if cells:
        print(f"    找到单元格引用: {cells[:10]}")
    
    # 保存文本以便进一步分析
    with open('user_data_content.txt', 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    print(f"    用户数据已保存: user_data_content.txt")
    return True

def search_in_related_sheet():
    """检查related_sheet字段，可能包含实际数据"""
    print("\n" + "="*60)
    print("分析related_sheet字段")
    print("="*60)
    
    # 从之前的分析中，我们知道有related_sheet字段
    ejs_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv"
    
    with open(ejs_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找URL编码的数据行
    lines = content.split('\n')
    for line in lines:
        if line.startswith('%7B'):
            try:
                decoded = urllib.parse.unquote(line)
                data = json.loads(decoded)
                
                if 'related_sheet' in data:
                    related_sheet = data['related_sheet']
                    print(f"related_sheet长度: {len(related_sheet)}")
                    
                    # 尝试base64解码
                    try:
                        decoded_sheet = base64.b64decode(related_sheet)
                        print(f"Base64解码: {len(decoded_sheet)} bytes")
                        
                        # 检查压缩
                        if decoded_sheet[:2] in [b'\x78\x01', b'\x78\x9c', b'\x78\xda']:
                            decompressed = zlib.decompress(decoded_sheet)
                            print(f"zlib解压: {len(decompressed)} bytes")
                            
                            # 保存related_sheet数据
                            with open('related_sheet_data.bin', 'wb') as f:
                                f.write(decompressed)
                            
                            # 尝试分析内容
                            try:
                                text = decompressed.decode('utf-8', errors='ignore')
                                
                                # 查找用户数据
                                if '小红书' in text or '部门' in text or '测试' in text:
                                    print("✅ 在related_sheet中找到用户数据!")
                                    
                                    with open('related_sheet_text.txt', 'w', encoding='utf-8') as f:
                                        f.write(text)
                                    
                                    return analyze_actual_table_data(text)
                                else:
                                    print("related_sheet中未找到明显的用户数据")
                                    
                            except Exception as e:
                                print(f"related_sheet文本解码失败: {e}")
                                
                    except Exception as e:
                        print(f"related_sheet解码失败: {e}")
                        
            except Exception as e:
                continue
    
    return False

def analyze_actual_table_data(content):
    """分析实际的表格数据"""
    print("\n    分析实际表格数据:")
    
    # 这里应该包含真实的表格数据解析逻辑
    # 根据腾讯文档的格式特点进行解析
    
    lines = content.split('\n')
    print(f"    数据总行数: {len(lines)}")
    
    # 查找表格数据模式
    table_data = []
    for line in lines[:20]:  # 检查前20行
        if line.strip() and len(line) < 200:  # 合理的行长度
            print(f"    数据行: {line[:100]}...")
            table_data.append(line.strip())
    
    if table_data:
        print(f"    ✅ 找到 {len(table_data)} 行表格数据")
        return True
    
    return False

def main():
    """主函数 - 实际测试用户数据提取"""
    print("🧪 实际测试：提取真实用户业务数据")
    print("="*60)
    
    success_count = 0
    
    # 1. 完整分析EJS结构
    print("步骤1: 完整分析EJS文件结构")
    analyze_full_ejs_structure()
    
    # 2. 检查related_sheet字段
    print("\n步骤2: 分析related_sheet字段")
    if search_in_related_sheet():
        success_count += 1
    
    # 3. 检查其他可能的数据源
    print("\n步骤3: 检查生成的文件")
    
    files_to_check = [
        'cont_field_decompressed.bin',
        'related_sheet_data.bin', 
        'user_data_content.txt',
        'related_sheet_text.txt'
    ]
    
    found_files = []
    for file in files_to_check:
        if Path(file).exists():
            found_files.append(file)
            print(f"✅ 生成了: {file}")
    
    # 4. 最终评估
    print("\n" + "="*60)
    print("实际测试结果")
    print("="*60)
    
    if success_count > 0:
        print(f"✅ 成功找到用户数据源: {success_count}个")
        print("🎉 实际测试成功！我们能够提取真实的用户业务数据")
    else:
        print("❌ 未能找到明确的用户业务数据")
        print("💡 可能需要:")
        print("   1. 进一步分析protobuf结构")
        print("   2. 测试包含更多业务数据的文档")
        print("   3. 完善浏览器自动化方案")
    
    if found_files:
        print(f"\n📁 生成的分析文件: {len(found_files)}个")
        for file in found_files:
            size = Path(file).stat().st_size
            print(f"   {file}: {size:,} bytes")

if __name__ == "__main__":
    main()