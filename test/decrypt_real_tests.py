#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用已验证的Python方法解密真实测试文档
"""

import json
import base64
import zlib
import urllib.parse
import re
from pathlib import Path
from datetime import datetime

def decrypt_ejs_document(ejs_file):
    """解密单个EJS文档"""
    print(f"\n{'='*60}")
    print(f"解密文档: {Path(ejs_file).name}")
    print(f"{'='*60}")
    
    try:
        # 读取EJS文件
        with open(ejs_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        print(f"文件行数: {len(lines)}")
        
        # 解析EJS结构
        metadata = None
        related_sheet_data = None
        max_row = 0
        max_col = 0
        
        # 1. 提取JSON元数据
        for i, line in enumerate(lines):
            if line.strip() == 'json' and i + 2 < len(lines):
                try:
                    json_length = int(lines[i + 1])
                    json_str = lines[i + 2]
                    metadata = json.loads(json_str)
                    print(f"✅ 找到JSON元数据")
                    
                    if metadata.get('bodyData', {}).get('initialTitle'):
                        print(f"   文档标题: {metadata['bodyData']['initialTitle']}")
                except:
                    pass
        
        # 2. 提取related_sheet数据
        for line in lines:
            if '%7B%22workbook%22' in line or 'workbook' in line:
                try:
                    decoded = urllib.parse.unquote(line.strip())
                    data = json.loads(decoded)
                    
                    max_row = data.get('max_row', 0)
                    max_col = data.get('max_col', 0)
                    print(f"✅ 表格结构: {max_row}行 × {max_col}列")
                    
                    if 'related_sheet' in data and data['related_sheet']:
                        print(f"✅ 找到related_sheet数据")
                        related_sheet_b64 = data['related_sheet']
                        
                        # Base64解码
                        related_bytes = base64.b64decode(related_sheet_b64)
                        print(f"   压缩数据: {len(related_bytes)} bytes")
                        
                        # zlib解压
                        try:
                            related_sheet_data = zlib.decompress(related_bytes)
                            print(f"   解压成功: {len(related_sheet_data)} bytes")
                        except:
                            print(f"   解压失败，尝试其他方法")
                            
                except Exception as e:
                    continue
        
        # 3. 提取表格数据
        if related_sheet_data:
            table_data = extract_table_data(related_sheet_data)
            
            # 4. 生成CSV
            csv_file = generate_csv_file(table_data, ejs_file)
            
            return {
                'success': True,
                'csv_file': csv_file,
                'rows': max_row,
                'cols': max_col,
                'cells': len(table_data.get('all_cells', [])),
                'chinese_count': len(table_data.get('chinese_content', []))
            }
        else:
            print("❌ 未找到related_sheet数据")
            return {'success': False, 'error': '未找到related_sheet数据'}
            
    except Exception as e:
        print(f"❌ 解密失败: {e}")
        return {'success': False, 'error': str(e)}

def extract_table_data(data):
    """从解压数据中提取表格内容"""
    print(f"\n提取表格数据...")
    
    result = {
        'chinese_content': [],
        'all_cells': []
    }
    
    # 提取中文内容
    try:
        text = data.decode('utf-8', errors='ignore')
        chinese_pattern = r'[\u4e00-\u9fff]+'
        chinese_matches = re.findall(chinese_pattern, text)
        
        # 去重并过滤
        unique_chinese = []
        for match in chinese_matches:
            if len(match) >= 1 and match not in unique_chinese:
                unique_chinese.append(match)
        
        result['chinese_content'] = unique_chinese
        print(f"   中文内容: {len(unique_chinese)}个")
        
        if unique_chinese:
            print(f"   前10个中文内容: {unique_chinese[:10]}")
        
    except Exception as e:
        print(f"   中文提取失败: {e}")
    
    # 提取ASCII内容
    ascii_content = []
    current_string = []
    
    for i, byte in enumerate(data):
        if 32 <= byte <= 126:  # 可打印ASCII
            current_string.append(chr(byte))
        else:
            if len(current_string) > 1:
                text = ''.join(current_string)
                if (not text.isspace() and 
                    len(text) < 200 and
                    not any(k in text.lower() for k in ['font', 'color', 'style'])):
                    ascii_content.append(text)
            current_string = []
    
    print(f"   ASCII内容: {len(ascii_content)}个")
    
    # 合并所有内容
    all_cells = result['chinese_content'] + ascii_content
    result['all_cells'] = all_cells
    
    print(f"   总单元格: {len(all_cells)}个")
    
    return result

def generate_csv_file(table_data, original_file):
    """生成CSV文件"""
    print(f"\n生成CSV文件...")
    
    if not table_data.get('all_cells'):
        print("   没有数据可生成CSV")
        return None
    
    # 基于文件名生成输出文件名
    base_name = Path(original_file).stem
    timestamp = datetime.now().strftime('%H%M%S')
    csv_file = Path(original_file).parent / f"{base_name}_decrypted_{timestamp}.csv"
    
    # 组织数据为表格
    cells = table_data['all_cells']
    
    # 简单按行组织（每10个单元格一行，可以根据实际调整）
    rows = []
    current_row = []
    
    for cell in cells:
        current_row.append(str(cell))
        if len(current_row) >= 10:  # 每行10列
            rows.append(current_row)
            current_row = []
    
    if current_row:
        rows.append(current_row)
    
    # 生成CSV内容
    csv_lines = []
    for row in rows:
        # 确保所有行都有相同的列数
        while len(row) < 10:
            row.append('')
        csv_line = ','.join(f'"{cell.replace(chr(34), chr(34)+chr(34))}"' for cell in row)
        csv_lines.append(csv_line)
    
    csv_content = '\n'.join(csv_lines)
    
    # 保存文件
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write(csv_content)
    
    print(f"   ✅ 已保存: {csv_file.name}")
    print(f"   包含 {len(rows)} 行, {len(cells)} 个单元格")
    
    # 预览前几行
    print(f"\n   前3行预览:")
    for i, line in enumerate(csv_lines[:3], 1):
        preview = line[:100] + ('...' if len(line) > 100 else '')
        print(f"     行{i}: {preview}")
    
    return str(csv_file)

def main():
    """主函数"""
    print("🚀 开始解密真实测试文档")
    print("="*60)
    
    # 找到下载的EJS文件
    test_dir = Path('/root/projects/tencent-doc-manager/real_test_results')
    ejs_files = list(test_dir.glob('*.ejs'))
    
    if not ejs_files:
        print("❌ 没有找到EJS文件")
        return
    
    print(f"找到 {len(ejs_files)} 个EJS文件")
    
    results = []
    success_count = 0
    
    # 依次解密每个文件
    for ejs_file in ejs_files:
        result = decrypt_ejs_document(str(ejs_file))
        results.append(result)
        
        if result['success']:
            success_count += 1
    
    # 总结
    print("\n" + "="*60)
    print("🎯 解密结果总结")
    print("="*60)
    
    print(f"总文件数: {len(ejs_files)}")
    print(f"解密成功: {success_count}")
    print(f"成功率: {success_count/len(ejs_files)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n✅ 成功解密的文件:")
        for i, (ejs_file, result) in enumerate(zip(ejs_files, results), 1):
            if result['success']:
                print(f"   {i}. {ejs_file.name}")
                print(f"      表格: {result['rows']}×{result['cols']}")
                print(f"      单元格: {result['cells']}个")
                print(f"      中文内容: {result['chinese_count']}个")
                print(f"      CSV文件: {Path(result['csv_file']).name}")
        
        print(f"\n🎉 真实测试成功！成功解密 {success_count} 份业务文档！")
    else:
        print(f"\n❌ 所有解密都失败，需要调试")

if __name__ == "__main__":
    main()