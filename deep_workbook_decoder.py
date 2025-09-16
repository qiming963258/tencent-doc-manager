#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度解析workbook数据 - 尝试多种解码方式
"""

import json
import urllib.parse
import base64
import gzip
import zlib
import io
from pathlib import Path

def try_all_decodings(data_bytes):
    """尝试所有可能的解码方式"""
    results = []
    
    # 1. 尝试gzip解压
    try:
        with gzip.open(io.BytesIO(data_bytes), 'rt', encoding='utf-8') as gz:
            result = gz.read()
        results.append(("gzip", True, len(result), result[:200]))
    except:
        results.append(("gzip", False, 0, None))
    
    # 2. 尝试zlib解压
    try:
        result = zlib.decompress(data_bytes).decode('utf-8')
        results.append(("zlib", True, len(result), result[:200]))
    except:
        results.append(("zlib", False, 0, None))
    
    # 3. 尝试直接UTF-8解码
    try:
        result = data_bytes.decode('utf-8')
        results.append(("utf-8", True, len(result), result[:200]))
    except:
        results.append(("utf-8", False, 0, None))
    
    # 4. 尝试UTF-16解码
    try:
        result = data_bytes.decode('utf-16')
        results.append(("utf-16", True, len(result), result[:200]))
    except:
        results.append(("utf-16", False, 0, None))
    
    # 5. 尝试GBK解码（中文编码）
    try:
        result = data_bytes.decode('gbk')
        results.append(("gbk", True, len(result), result[:200]))
    except:
        results.append(("gbk", False, 0, None))
    
    # 6. 尝试二次Base64解码
    try:
        second_decode = base64.b64decode(data_bytes)
        result = second_decode.decode('utf-8')
        results.append(("double-base64", True, len(result), result[:200]))
    except:
        results.append(("double-base64", False, 0, None))
    
    # 7. 检查是否是protobuf格式
    if len(data_bytes) > 10:
        # Protobuf通常以特定的字节开始
        if data_bytes[0] in [0x08, 0x10, 0x18, 0x20]:
            results.append(("protobuf", "可能", len(data_bytes), "二进制protobuf格式"))
    
    # 8. 检查是否是Excel二进制格式
    if data_bytes[:4] == b'PK\x03\x04':
        results.append(("xlsx", True, len(data_bytes), "Excel XLSX格式(ZIP)"))
    elif data_bytes[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
        results.append(("xls", True, len(data_bytes), "Excel XLS格式"))
    
    return results

def decode_workbook_deep(file_path):
    """深度解析workbook数据"""
    print(f"\n{'='*60}")
    print(f"深度解析: {Path(file_path).name}")
    print(f"{'='*60}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到包含workbook的行
    for i, line in enumerate(lines):
        if len(line) > 10000 and '%7B%22workbook%22' in line[:100]:
            print(f"找到workbook数据在第{i+1}行")
            
            # URL解码
            decoded = urllib.parse.unquote(line.strip())
            data = json.loads(decoded)
            
            workbook_b64 = data.get('workbook', '')
            print(f"Base64 workbook长度: {len(workbook_b64)}")
            
            # Base64解码
            workbook_bytes = base64.b64decode(workbook_b64)
            print(f"解码后字节数: {len(workbook_bytes)}")
            
            # 分析字节特征
            print(f"\n字节特征分析:")
            print(f"前16字节(hex): {workbook_bytes[:16].hex()}")
            print(f"前16字节(raw): {workbook_bytes[:16]}")
            
            # 检查是否是压缩数据的magic numbers
            if workbook_bytes[:2] == b'\x78\x9c':
                print("✅ 检测到zlib压缩标志(78 9c)")
            elif workbook_bytes[:2] == b'\x78\x01':
                print("✅ 检测到zlib压缩标志(78 01)")
            elif workbook_bytes[:2] == b'\x78\xda':
                print("✅ 检测到zlib压缩标志(78 da)")
            elif workbook_bytes[:2] == b'\x1f\x8b':
                print("✅ 检测到gzip压缩标志(1f 8b)")
            elif workbook_bytes[:4] == b'PK\x03\x04':
                print("✅ 检测到ZIP/XLSX格式标志")
            else:
                print("❓ 未知的数据格式")
            
            # 尝试所有解码方式
            print(f"\n尝试多种解码方式:")
            results = try_all_decodings(workbook_bytes)
            
            for method, success, length, preview in results:
                if success:
                    print(f"✅ {method}: 成功, 长度={length}")
                    if preview:
                        print(f"   预览: {preview[:100]}...")
                        
                        # 如果成功解码，保存结果
                        if length > 100 and (',' in str(preview) or '\t' in str(preview) or '{' in str(preview)):
                            output_file = file_path.replace('.csv', f'_{method}_decoded.txt').replace('.xlsx', f'_{method}_decoded.txt')
                            
                            # 获取完整数据
                            if method == "gzip":
                                with gzip.open(io.BytesIO(workbook_bytes), 'rt', encoding='utf-8') as gz:
                                    full_data = gz.read()
                            elif method == "zlib":
                                full_data = zlib.decompress(workbook_bytes).decode('utf-8')
                            else:
                                full_data = preview
                            
                            with open(output_file, 'w', encoding='utf-8') as f:
                                f.write(full_data)
                            print(f"   💾 保存到: {output_file}")
                            
                            # 分析数据格式
                            if ',' in full_data[:1000]:
                                print(f"   📊 检测到CSV格式")
                                # 尝试解析CSV
                                lines = full_data.split('\n')[:5]
                                for line_no, csv_line in enumerate(lines, 1):
                                    cells = csv_line.split(',')[:5]
                                    print(f"      行{line_no}: {cells}")
                            
                            return True
                            
                elif method in ["protobuf", "xlsx", "xls"]:
                    print(f"⚠️  {method}: {success}")
                else:
                    print(f"❌ {method}: 失败")
            
            # 如果所有方法都失败，尝试查找其他数据
            print(f"\n查找其他可能的表格数据...")
            
            # 检查related_sheet
            related = data.get('related_sheet', '')
            if related:
                print(f"发现related_sheet: {related[:100]}...")
            
            # 检查其他字段
            for key in ['max_row', 'max_col', 'end_row_index', 'end_col_index']:
                if key in data:
                    print(f"{key}: {data[key]}")
            
            break
    
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
        
        if decode_workbook_deep(file_path):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"深度解析完成")
    print(f"{'='*60}")
    
    if success_count > 0:
        print("✅ 成功解码workbook数据!")
        print("💡 现在可以将数据转换为标准Excel格式")
    else:
        print("⚠️  workbook数据使用了特殊的编码方式")
        print("💡 可能需要逆向工程分析腾讯文档的加密算法")

if __name__ == "__main__":
    main()