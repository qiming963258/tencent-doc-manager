#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析解压后的数据，看起来是protobuf格式
"""

import struct
from pathlib import Path

def analyze_protobuf_like_data(file_path):
    """分析类protobuf格式的数据"""
    print(f"\n分析文件: {Path(file_path).name}")
    print("="*60)
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"文件大小: {len(data)} bytes")
    print(f"前32字节(hex): {data[:32].hex()}")
    
    # 查找文本字符串
    print("\n找到的文本字符串:")
    
    # 提取所有可读的ASCII/UTF-8字符串
    current_string = []
    strings_found = []
    
    for i, byte in enumerate(data):
        # 检查是否是可打印字符
        if 32 <= byte <= 126 or byte in [10, 13, 9]:  # ASCII可打印字符 + 换行/制表符
            current_string.append(chr(byte))
        else:
            # 如果当前字符串长度超过3，认为是有意义的字符串
            if len(current_string) > 3:
                s = ''.join(current_string)
                if not s.isspace():  # 排除纯空白
                    strings_found.append((i - len(current_string), s))
            current_string = []
    
    # 检查最后的字符串
    if len(current_string) > 3:
        s = ''.join(current_string)
        if not s.isspace():
            strings_found.append((len(data) - len(current_string), s))
    
    # 显示找到的字符串
    for pos, string in strings_found[:50]:  # 只显示前50个
        # 过滤掉乱码
        if any(c in string for c in ['000000', 'FFFFFF', 'Calibri', '工作表', 'Times']):
            print(f"  位置 {pos:5d}: {string[:100]}")
    
    # 查找中文字符串
    print("\n找到的中文内容:")
    chinese_found = False
    
    try:
        # 尝试UTF-8解码
        text = data.decode('utf-8', errors='ignore')
        import re
        
        # 查找中文字符
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        chinese_matches = chinese_pattern.findall(text)
        
        for match in chinese_matches[:30]:  # 显示前30个
            if len(match) > 1:  # 至少2个中文字符
                print(f"  {match}")
                chinese_found = True
                
    except Exception as e:
        print(f"  解码错误: {e}")
    
    if not chinese_found:
        print("  未找到明显的中文内容")
    
    # 分析protobuf结构
    print("\n可能的protobuf字段:")
    
    # protobuf通常使用varint编码
    # 字段格式: (field_number << 3) | wire_type
    # wire_type: 0=varint, 1=64bit, 2=length-delimited, 5=32bit
    
    i = 0
    field_count = 0
    while i < min(len(data), 500) and field_count < 20:  # 分析前500字节或前20个字段
        if i >= len(data):
            break
            
        try:
            # 读取字段标签
            tag = data[i]
            if tag == 0:
                i += 1
                continue
                
            field_number = tag >> 3
            wire_type = tag & 0x07
            
            wire_type_names = {
                0: "varint",
                1: "64-bit",
                2: "length-delimited",
                3: "start-group",
                4: "end-group", 
                5: "32-bit"
            }
            
            if wire_type in wire_type_names:
                print(f"  偏移 {i:3d}: 字段{field_number:3d}, 类型={wire_type_names[wire_type]}")
                field_count += 1
                
                # 根据类型跳过相应的字节
                if wire_type == 0:  # varint
                    i += 1
                    while i < len(data) and data[i] & 0x80:
                        i += 1
                    i += 1
                elif wire_type == 1:  # 64-bit
                    i += 9
                elif wire_type == 2:  # length-delimited
                    i += 1
                    length = 0
                    shift = 0
                    while i < len(data):
                        b = data[i]
                        length |= (b & 0x7F) << shift
                        i += 1
                        if not (b & 0x80):
                            break
                        shift += 7
                    
                    if length < 1000:  # 合理的长度
                        # 检查是否是字符串
                        if i + length <= len(data):
                            content = data[i:i+length]
                            try:
                                text = content.decode('utf-8')
                                if text.isprintable() or '工作表' in text:
                                    print(f"    -> 字符串: {text[:50]}")
                            except:
                                pass
                    i += length
                elif wire_type == 5:  # 32-bit
                    i += 5
                else:
                    i += 1
            else:
                i += 1
                
        except Exception as e:
            i += 1
    
    # 查找表格数据标记
    print("\n查找表格相关内容:")
    
    # 查找可能的单元格引用 (A1, B2等)
    cell_refs = []
    for i in range(len(data) - 2):
        if 65 <= data[i] <= 90:  # A-Z
            if 48 <= data[i+1] <= 57:  # 0-9
                cell_ref = chr(data[i]) + chr(data[i+1])
                if data[i+2] == 0 or data[i+2] > 127:  # 后面是分隔符
                    cell_refs.append((i, cell_ref))
    
    if cell_refs:
        print(f"  找到{len(cell_refs)}个可能的单元格引用:")
        for pos, ref in cell_refs[:10]:
            print(f"    位置{pos}: {ref}")
    
    # 生成更易读的输出
    print("\n尝试提取表格数据...")
    
    # 查找数字序列（可能是表格数据）
    numbers = []
    for i in range(0, len(data) - 8, 4):
        try:
            # 尝试读取float
            f = struct.unpack('<f', data[i:i+4])[0]
            if -1000000 < f < 1000000 and f != 0:
                numbers.append((i, f))
        except:
            pass
    
    if numbers:
        print(f"  找到{len(numbers)}个可能的数值:")
        for pos, num in numbers[:10]:
            print(f"    位置{pos}: {num:.2f}")
    
    return data

def main():
    """主函数"""
    decoded_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718_nodejs_decoded.txt"
    
    if Path(decoded_file).exists():
        data = analyze_protobuf_like_data(decoded_file)
        
        # 保存为二进制文件以便进一步分析
        bin_file = decoded_file.replace('.txt', '.bin')
        with open(bin_file, 'wb') as f:
            f.write(data)
        print(f"\n二进制数据已保存到: {bin_file}")
        
        print("\n" + "="*60)
        print("分析结论:")
        print("="*60)
        print("1. 数据是protobuf或类似的二进制格式")
        print("2. 包含版本号(3.0.0)和工作表信息")
        print("3. 包含颜色定义(000000, FFFFFF等)")
        print("4. 包含字体信息(Calibri, 宋体等)")
        print("5. 需要protobuf定义文件(.proto)才能完全解析")
        print("\n建议: 使用浏览器自动化方案获取真实Excel文件")
    else:
        print(f"文件不存在: {decoded_file}")

if __name__ == "__main__":
    main()