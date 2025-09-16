#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的EJS格式分析器 - 不依赖pandas
"""

import json
import urllib.parse
import base64
import gzip
import io
from pathlib import Path

def analyze_ejs_file(file_path):
    """分析EJS格式文件的结构"""
    print(f"\n{'='*60}")
    print(f"分析文件: {file_path}")
    print(f"{'='*60}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"文件行数: {len(lines)}")
    
    # 分析每一行
    for i, line in enumerate(lines[:10], 1):  # 只看前10行
        line = line.strip()
        if not line:
            continue
            
        print(f"\n第{i}行:")
        print(f"长度: {len(line)} 字符")
        
        # 检查行类型
        if line == 'head':
            print("类型: EJS文件头标识")
        elif line == 'json':
            print("类型: JSON数据开始标识")
        elif line == 'text':
            print("类型: 文本数据标识")
        elif line.isdigit():
            print(f"类型: 数据长度标识 ({line} 字符)")
        elif line.startswith('{'):
            print("类型: JSON对象")
            # 尝试解析JSON
            try:
                data = json.loads(line)
                print(f"JSON keys: {list(data.keys())[:5]}")
                
                # 检查关键字段
                if 'clientVars' in data:
                    print("  - 包含clientVars (用户信息)")
                if 'bodyData' in data:
                    print("  - 包含bodyData (文档数据)")
                    body = data['bodyData']
                    if isinstance(body, dict):
                        print(f"    bodyData keys: {list(body.keys())[:5]}")
                if 'workbook' in data:
                    print("  - 包含workbook (表格数据)")
                    
            except:
                print("  JSON解析失败")
        elif line.startswith('%'):
            print("类型: URL编码数据")
            print(f"前50字符: {line[:50]}...")
            
            # 尝试URL解码
            try:
                decoded = urllib.parse.unquote(line)
                print(f"URL解码后长度: {len(decoded)}")
                
                # 检查解码后是否是JSON
                if decoded.startswith('{'):
                    try:
                        decoded_data = json.loads(decoded)
                        print(f"URL解码后是JSON, keys: {list(decoded_data.keys())[:5]}")
                        
                        if 'workbook' in decoded_data:
                            workbook = decoded_data['workbook']
                            print(f"发现workbook字段, 长度: {len(workbook)}")
                            
                            # 尝试Base64解码workbook
                            try:
                                workbook_bytes = base64.b64decode(workbook)
                                print(f"Base64解码成功, 字节数: {len(workbook_bytes)}")
                                
                                # 尝试gzip解压
                                try:
                                    with gzip.open(io.BytesIO(workbook_bytes), 'rt', encoding='utf-8') as gz:
                                        workbook_data = gz.read()
                                    print(f"Gzip解压成功, 数据长度: {len(workbook_data)}")
                                    print(f"解压后数据预览: {workbook_data[:200]}...")
                                except:
                                    # 如果不是gzip，尝试直接解码
                                    try:
                                        workbook_text = workbook_bytes.decode('utf-8')
                                        print(f"直接UTF-8解码成功, 长度: {len(workbook_text)}")
                                        print(f"数据预览: {workbook_text[:200]}...")
                                    except:
                                        print("无法解码workbook数据")
                            except Exception as e:
                                print(f"Base64解码失败: {e}")
                    except:
                        print("URL解码后不是JSON")
            except:
                print("URL解码失败")
        else:
            print(f"类型: 其他")
            print(f"前50字符: {line[:50]}...")

def extract_table_data(file_path):
    """尝试提取表格数据"""
    print(f"\n{'='*60}")
    print("尝试提取表格数据...")
    print(f"{'='*60}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找包含workbook的行
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 100:
            continue
            
        # 如果是URL编码的数据
        if '%' in line[:100]:
            try:
                decoded = urllib.parse.unquote(line)
                if 'workbook' in decoded:
                    print(f"在第{i+1}行发现workbook数据")
                    
                    # 解析JSON
                    data = json.loads(decoded)
                    workbook = data.get('workbook', '')
                    
                    if workbook:
                        # Base64解码
                        try:
                            wb_bytes = base64.b64decode(workbook)
                            
                            # 尝试多种解码方式
                            # 1. 尝试gzip
                            try:
                                with gzip.open(io.BytesIO(wb_bytes), 'rt', encoding='utf-8') as gz:
                                    wb_data = gz.read()
                                print("✅ Gzip解压成功")
                            except:
                                # 2. 尝试直接UTF-8
                                try:
                                    wb_data = wb_bytes.decode('utf-8')
                                    print("✅ UTF-8解码成功")
                                except:
                                    # 3. 尝试其他编码
                                    wb_data = wb_bytes.decode('utf-8', errors='ignore')
                                    print("✅ UTF-8(忽略错误)解码成功")
                            
                            print(f"解码后数据长度: {len(wb_data)}")
                            
                            # 分析数据内容
                            if ',' in wb_data[:1000] or '\t' in wb_data[:1000]:
                                print("📊 看起来是CSV格式数据")
                                # 提取前几行
                                lines = wb_data.split('\n')[:10]
                                print("\n前10行数据:")
                                for j, line in enumerate(lines, 1):
                                    if line:
                                        print(f"  {j}: {line[:100]}{'...' if len(line) > 100 else ''}")
                                
                                # 保存为CSV文件
                                csv_file = file_path.replace('.csv', '_extracted.csv')
                                with open(csv_file, 'w', encoding='utf-8') as f:
                                    f.write(wb_data)
                                print(f"\n✅ 数据已保存到: {csv_file}")
                                
                                return True
                                
                            elif '[' in wb_data[:100] or '{' in wb_data[:100]:
                                print("📊 看起来是JSON格式数据")
                                try:
                                    json_data = json.loads(wb_data)
                                    print(f"JSON数据类型: {type(json_data)}")
                                    if isinstance(json_data, dict):
                                        print(f"Keys: {list(json_data.keys())[:10]}")
                                    elif isinstance(json_data, list):
                                        print(f"数组长度: {len(json_data)}")
                                        if json_data:
                                            print(f"第一个元素: {json_data[0]}")
                                except:
                                    print("JSON解析失败，但包含JSON特征")
                                    
                        except Exception as e:
                            print(f"Workbook解码失败: {e}")
                            
            except Exception as e:
                continue
    
    return False

def main():
    """主函数"""
    test_files = [
        "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv",
        "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_Excel格式_20250827_231720.xlsx"
    ]
    
    success_count = 0
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        # 分析文件结构
        analyze_ejs_file(file_path)
        
        # 提取表格数据
        if extract_table_data(file_path):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"分析完成: {success_count}/{len(test_files)} 文件成功提取数据")
    print(f"{'='*60}")
    
    if success_count > 0:
        print("✅ 成功从EJS格式提取表格数据!")
        print("💡 下一步: 可以将提取的数据转换为标准Excel格式")
    else:
        print("❌ 未能成功提取表格数据")
        print("💡 需要进一步分析EJS格式的编码方式")

if __name__ == "__main__":
    main()