#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解码腾讯文档workbook数据，验证表格内容
"""

import json
import urllib.parse
import base64
import gzip
import io
from pathlib import Path

def decode_ejs_workbook(file_path):
    """解码EJS格式文件中的workbook数据"""
    print(f"🔍 解码文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) < 8:
        print("❌ 文件行数不足")
        return None
    
    # 第8行包含URL编码的workbook数据
    encoded_data = lines[7].strip()  # 第8行，索引7
    
    print(f"📦 编码数据长度: {len(encoded_data)} 字符")
    print(f"🔡 数据预览: {encoded_data[:100]}...")
    
    try:
        # Step 1: URL解码
        url_decoded = urllib.parse.unquote(encoded_data)
        print(f"✅ URL解码成功，长度: {len(url_decoded)}")
        
        # Step 2: 尝试解析JSON
        try:
            json_data = json.loads(url_decoded)
            print(f"✅ JSON解析成功")
            
            if 'workbook' in json_data:
                workbook_data = json_data['workbook']
                print(f"📊 找到workbook字段，长度: {len(workbook_data)}")
                
                # Step 3: workbook数据通常是Base64编码的压缩数据
                try:
                    # 尝试Base64解码
                    decoded_bytes = base64.b64decode(workbook_data)
                    print(f"✅ Base64解码成功，字节数: {len(decoded_bytes)}")
                    
                    # Step 4: 尝试gzip解压缩
                    try:
                        with gzip.open(io.BytesIO(decoded_bytes), 'rt', encoding='utf-8') as gz_file:
                            uncompressed_data = gz_file.read()
                        print(f"✅ Gzip解压缩成功，长度: {len(uncompressed_data)}")
                        
                        # 分析解压后的数据
                        analyze_workbook_content(uncompressed_data)
                        return uncompressed_data
                        
                    except Exception as e:
                        print(f"⚠️ Gzip解压缩失败: {e}")
                        print("🔍 尝试直接分析Base64解码后的数据...")
                        
                        # 尝试作为文本分析
                        try:
                            text_data = decoded_bytes.decode('utf-8', errors='ignore')
                            analyze_workbook_content(text_data)
                            return text_data
                        except:
                            print("❌ 无法解析为文本")
                            return None
                    
                except Exception as e:
                    print(f"❌ Base64解码失败: {e}")
                    # 尝试直接分析workbook字符串
                    analyze_workbook_content(workbook_data)
                    return workbook_data
            
            else:
                print("❌ 未找到workbook字段")
                print(f"🔍 可用字段: {list(json_data.keys())}")
                return None
                
        except Exception as e:
            print(f"❌ JSON解析失败: {e}")
            return None
    
    except Exception as e:
        print(f"❌ URL解码失败: {e}")
        return None

def analyze_workbook_content(content):
    """分析workbook内容，查找表格相关数据"""
    print(f"\n📊 分析workbook内容...")
    print(f"📏 内容长度: {len(content)} 字符")
    
    # 检查表格相关关键词
    table_keywords = [
        # 英文关键词
        'cell', 'row', 'column', 'sheet', 'worksheet', 'table',
        'A1', 'B1', 'C1', 'data', 'value', 'formula',
        # 中文关键词  
        '单元格', '行', '列', '工作表', '表格', '数据',
        # Excel/Spreadsheet术语
        'xlsx', 'xls', 'csv', 'spreadsheet'
    ]
    
    found_keywords = []
    for keyword in table_keywords:
        if keyword.lower() in content.lower():
            # 计算出现次数
            count = content.lower().count(keyword.lower())
            found_keywords.append((keyword, count))
    
    if found_keywords:
        print(f"✅ 发现表格相关关键词:")
        for keyword, count in found_keywords[:10]:  # 只显示前10个
            print(f"   - {keyword}: {count} 次")
    else:
        print("⚠️ 未发现明显的表格关键词")
    
    # 查找数字模式（可能是单元格数据）
    import re
    
    # 查找可能的单元格引用 (如 A1, B2, C3)
    cell_refs = re.findall(r'[A-Z]+\d+', content)
    if cell_refs:
        print(f"✅ 发现 {len(cell_refs)} 个可能的单元格引用:")
        print(f"   示例: {cell_refs[:10]}")
    
    # 查找数字数据
    numbers = re.findall(r'\b\d+\.?\d*\b', content)
    if len(numbers) > 20:  # 如果有很多数字，可能包含表格数据
        print(f"✅ 发现大量数字数据: {len(numbers)} 个数字")
        print(f"   示例: {numbers[:10]}")
    
    # 显示内容片段用于分析
    print(f"\n📝 内容片段分析:")
    
    # 显示前500字符
    print(f"前500字符:")
    print(content[:500])
    
    # 如果内容很长，也显示中间和末尾的一些内容
    if len(content) > 1000:
        mid_pos = len(content) // 2
        print(f"\n中间500字符 (位置 {mid_pos}):")
        print(content[mid_pos:mid_pos+500])
        
        print(f"\n最后500字符:")
        print(content[-500:])

def main():
    """主函数"""
    print("🚀 解码腾讯文档workbook数据")
    
    test_files = [
        "/root/projects/tencent-doc-manager/downloads/test_direct_1_csv.csv",
        "/root/projects/tencent-doc-manager/downloads/test_direct_3_csv.csv"
    ]
    
    results = {}
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        print("\n" + "="*60)
        
        decoded_data = decode_ejs_workbook(file_path)
        
        results[file_path] = {
            "success": decoded_data is not None,
            "data_length": len(decoded_data) if decoded_data else 0
        }
    
    # 总结
    print("\n" + "="*60)
    print("🎯 解码结果总结")
    print("="*60)
    
    successful = 0
    for file_path, result in results.items():
        filename = Path(file_path).name
        status = "✅" if result["success"] else "❌"
        print(f"{status} {filename}: {'成功' if result['success'] else '失败'}")
        if result["success"]:
            print(f"   📏 数据长度: {result['data_length']} 字符")
            successful += 1
    
    print(f"\n🎉 解码完成: {successful}/{len(results)} 文件成功")
    
    if successful > 0:
        print("✅ 确认文件包含可解码的表格数据!")
        print("💡 可以开始开发完整的数据提取和转换功能")

if __name__ == "__main__":
    main()