#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接解压zlib压缩的文件
"""

import zlib
import gzip
from pathlib import Path

def decompress_file(file_path):
    """尝试解压文件"""
    print(f"\n解压文件: {Path(file_path).name}")
    print("="*60)
    
    with open(file_path, 'rb') as f:
        compressed_data = f.read()
    
    print(f"文件大小: {len(compressed_data)} bytes")
    print(f"前16字节(hex): {compressed_data[:16].hex()}")
    
    # 检查文件头
    if compressed_data[:2] == b'\x78\x01':
        print("✅ 检测到zlib压缩 (78 01)")
    elif compressed_data[:2] == b'\x78\x9c':
        print("✅ 检测到zlib压缩 (78 9c)")
    elif compressed_data[:2] == b'\x78\xda':
        print("✅ 检测到zlib压缩 (78 da)")
    elif compressed_data[:2] == b'\x1f\x8b':
        print("✅ 检测到gzip压缩 (1f 8b)")
    else:
        print(f"❓ 未知压缩格式: {compressed_data[:2].hex()}")
    
    # 尝试多种解压方法
    methods = [
        ("zlib.decompress (默认)", lambda d: zlib.decompress(d)),
        ("zlib.decompress (-15)", lambda d: zlib.decompress(d, -15)),  # raw deflate
        ("zlib.decompress (15)", lambda d: zlib.decompress(d, 15)),    # with header
        ("zlib.decompress (31)", lambda d: zlib.decompress(d, 31)),    # auto detect
        ("gzip.decompress", lambda d: gzip.decompress(d)),
    ]
    
    for method_name, decompress_func in methods:
        try:
            print(f"\n尝试 {method_name}...")
            decompressed = decompress_func(compressed_data)
            print(f"✅ 成功! 解压后大小: {len(decompressed)} bytes")
            
            # 分析解压后的数据
            try:
                # 尝试UTF-8解码
                text = decompressed.decode('utf-8')
                print(f"UTF-8解码成功, 长度: {len(text)} 字符")
                
                # 检查内容
                if ',' in text[:1000] or '\t' in text[:1000]:
                    print("📊 看起来是表格数据（CSV格式）")
                    lines = text.split('\n')[:5]
                    for i, line in enumerate(lines, 1):
                        print(f"  第{i}行: {line[:100]}{'...' if len(line) > 100 else ''}")
                    
                    # 保存解压后的文件
                    output_file = file_path.replace('.xlsx', '_decompressed.csv').replace('_extracted.csv', '_final.csv')
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"\n💾 已保存到: {output_file}")
                    
                elif text.startswith('<?xml') or '<html' in text[:1000]:
                    print("📄 看起来是XML/HTML数据")
                    print(f"预览: {text[:500]}...")
                    
                elif text.startswith('{') or text.startswith('['):
                    print("📊 看起来是JSON数据")
                    import json
                    data = json.loads(text)
                    print(f"JSON类型: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())[:10]}")
                    
                    # 保存JSON文件
                    output_file = file_path.replace('.xlsx', '_decompressed.json').replace('_extracted.csv', '_final.json')
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"\n💾 已保存到: {output_file}")
                else:
                    print("📝 文本数据")
                    print(f"预览: {text[:500]}...")
                    
                return True
                
            except UnicodeDecodeError:
                print("❌ UTF-8解码失败，尝试其他编码...")
                
                # 尝试其他编码
                for encoding in ['gbk', 'utf-16', 'latin1']:
                    try:
                        text = decompressed.decode(encoding)
                        print(f"✅ {encoding}解码成功")
                        print(f"预览: {text[:200]}...")
                        
                        output_file = file_path.replace('.xlsx', f'_decompressed_{encoding}.txt').replace('_extracted.csv', f'_final_{encoding}.txt')
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(text)
                        print(f"💾 已保存到: {output_file}")
                        return True
                    except:
                        continue
                
                # 如果所有编码都失败，保存为二进制
                print("保存为二进制文件...")
                output_file = file_path.replace('.xlsx', '_decompressed.bin').replace('_extracted.csv', '_final.bin')
                with open(output_file, 'wb') as f:
                    f.write(decompressed)
                print(f"💾 已保存到: {output_file}")
                return True
                
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    return False

def main():
    """主函数"""
    # 测试文件列表
    test_files = [
        "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718_extracted.csv",
        "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_Excel格式_20250827_231720.xlsx"
    ]
    
    success_count = 0
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        if decompress_file(file_path):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"处理完成: {success_count}/{len(test_files)} 文件成功解压")
    
    if success_count > 0:
        print("✅ 成功解压文件!")
        print("💡 现在可以查看解压后的数据")

if __name__ == "__main__":
    main()