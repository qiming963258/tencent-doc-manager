#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析提取的数据，查找真实业务内容
"""

import json
import base64
from pathlib import Path

def analyze_extracted_csv():
    """分析已提取的CSV文件"""
    csv_files = list(Path('.').glob('*decoded*.csv'))
    
    if not csv_files:
        print("没有找到解码的CSV文件")
        return
    
    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"分析文件: {latest_csv}")
    
    with open(latest_csv, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"总行数: {len(lines)}")
    
    # 统计内容类型
    system_keywords = ['font', 'color', 'style', 'calibri', 'arial', 'times']
    language_codes = ['jpan', 'hans', 'hant', 'arab', 'hebr', 'thai']
    color_codes = ['000000', 'FFFFFF', 'E8E8E8']
    
    system_count = 0
    language_count = 0
    color_count = 0
    other_count = 0
    
    unique_values = set()
    
    for line in lines:
        cells = line.split(',')
        for cell in cells:
            cell_clean = cell.strip('"').lower()
            unique_values.add(cell_clean)
            
            if any(k in cell_clean for k in system_keywords):
                system_count += 1
            elif any(l in cell_clean for l in language_codes):
                language_count += 1
            elif any(c in cell_clean for c in color_codes):
                color_count += 1
            else:
                other_count += 1
    
    print(f"\n内容分析:")
    print(f"  系统关键词: {system_count}")
    print(f"  语言代码: {language_count}")
    print(f"  颜色代码: {color_count}")
    print(f"  其他内容: {other_count}")
    print(f"  唯一值数量: {len(unique_values)}")
    
    # 查找可能的业务数据
    print(f"\n可能的业务数据:")
    business_data = []
    
    for value in unique_values:
        # 排除明显的系统信息
        if (len(value) > 2 and 
            not any(k in value for k in system_keywords + language_codes + color_codes) and
            not value.isdigit() and
            value not in ['', '*', ':', 'j', 'z', 'b']):
            business_data.append(value)
    
    if business_data:
        print(f"找到 {len(business_data)} 个可能的业务数据:")
        for i, data in enumerate(business_data[:20], 1):
            print(f"  {i}. {data}")
    else:
        print("  未找到明显的业务数据")
    
    return business_data

def check_document_metadata():
    """检查文档元数据"""
    print("\n" + "="*60)
    print("检查文档元数据")
    print("="*60)
    
    # 从原始EJS文件提取元数据
    test_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv"
    
    if not Path(test_file).exists():
        print("测试文件不存在")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip() == 'json' and i + 2 < len(lines):
            try:
                json_length = int(lines[i + 1])
                json_data = json.loads(lines[i + 2])
                
                print("文档元数据:")
                if 'bodyData' in json_data:
                    body = json_data['bodyData']
                    print(f"  标题: {body.get('initialTitle', 'N/A')}")
                    print(f"  内容长度: {len(body.get('cont', ''))}")
                    
                    # 检查是否有实际内容
                    cont = body.get('cont', '')
                    if cont:
                        print(f"  内容预览: {cont[:200]}...")
                
                if 'clientVars' in json_data:
                    client = json_data['clientVars']
                    print(f"  用户ID: {client.get('userId', 'N/A')}")
                    print(f"  文档ID: {client.get('docId', 'N/A')}")
                
                break
            except Exception as e:
                print(f"元数据解析失败: {e}")

def find_real_table_data():
    """深度查找真实表格数据"""
    print("\n" + "="*60)
    print("深度查找真实表格数据")
    print("="*60)
    
    # 检查related_sheet数据
    test_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718.csv"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找related_sheet
    import urllib.parse
    for line in content.split('\n'):
        if '%7B%22workbook%22' in line or 'related_sheet' in line:
            try:
                decoded = urllib.parse.unquote(line.strip())
                data = json.loads(decoded)
                
                if 'related_sheet' in data and data['related_sheet']:
                    print("找到related_sheet数据")
                    related_b64 = data['related_sheet']
                    
                    # 解码related_sheet
                    try:
                        related_bytes = base64.b64decode(related_b64)
                        print(f"  related_sheet大小: {len(related_bytes)} bytes")
                        
                        # 尝试zlib解压
                        import zlib
                        try:
                            decompressed = zlib.decompress(related_bytes)
                            print(f"  解压后大小: {len(decompressed)} bytes")
                            
                            # 查找可读内容
                            text = decompressed.decode('utf-8', errors='ignore')
                            
                            # 查找中文
                            import re
                            chinese = re.findall(r'[\u4e00-\u9fff]+', text)
                            if chinese:
                                print(f"  找到中文内容: {chinese[:10]}")
                            
                        except Exception as e:
                            print(f"  解压失败: {e}")
                            
                    except Exception as e:
                        print(f"  Base64解码失败: {e}")
                        
            except:
                continue

def main():
    """主函数"""
    print("="*60)
    print("分析提取的数据质量")
    print("="*60)
    
    # 1. 分析CSV内容
    business_data = analyze_extracted_csv()
    
    # 2. 检查文档元数据
    check_document_metadata()
    
    # 3. 深度查找表格数据
    find_real_table_data()
    
    print("\n" + "="*60)
    print("分析结论")
    print("="*60)
    
    if business_data and len(business_data) > 10:
        print("✅ 可能包含真实业务数据")
    else:
        print("⚠️ 主要是系统配置数据")
        print("\n原因分析:")
        print("1. 测试文档本身可能就是系统配置表")
        print("2. 真实数据可能在related_sheet中需要进一步解密")
        print("3. 需要用包含实际业务数据的文档测试")
        
    print("\n建议:")
    print("1. 使用包含真实业务数据的腾讯文档测试")
    print("2. 例如：销售报表、客户清单、产品目录等")
    print("3. 确保文档有实际的数据内容，而不是空表或配置表")

if __name__ == "__main__":
    main()