#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从protobuf数据中提取有意义的表格内容
基于深度分析的发现
"""

from pathlib import Path
import struct
import re

def extract_colors_and_fonts(data):
    """提取颜色和字体信息"""
    print("="*60)
    print("提取样式信息")
    print("="*60)
    
    # 已知的颜色代码和字体
    colors_found = []
    fonts_found = []
    
    # 搜索颜色代码
    color_patterns = [
        r'[0-9A-F]{6}',  # 6位十六进制颜色
        r'#[0-9A-F]{6}', # 带#的颜色
        r'rgb\(\d+,\d+,\d+\)'  # RGB格式
    ]
    
    try:
        text = data.decode('utf-8', errors='ignore')
        
        # 查找颜色
        for pattern in color_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            colors_found.extend(matches)
        
        # 查找字体名
        font_keywords = ['Calibri', 'Arial', 'Times', '宋体', '微软雅黑', 'SimSun', 'SimHei']
        for font in font_keywords:
            if font in text:
                fonts_found.append(font)
    
    except Exception as e:
        print(f"文本解析错误: {e}")
    
    # 从已知位置提取颜色
    known_colors = ['000000', 'FFFFFF', '0E2841', 'E8E8E8', '5071BE', 'DD8344', 'A5A5A5', 'F4C243', '6C9AD0']
    
    print(f"找到的颜色:")
    for color in known_colors:
        if color in data.decode('utf-8', errors='ignore'):
            colors_found.append(color)
            print(f"  #{color}")
    
    print(f"找到的字体:")
    for font in fonts_found:
        print(f"  {font}")
    
    return colors_found, fonts_found

def search_table_content(data):
    """搜索实际的表格内容"""
    print("\n" + "="*60)
    print("搜索表格内容")
    print("="*60)
    
    # 根据深度分析，我们知道有129个可能的单元格内容
    # 让我们更仔细地提取它们
    
    cell_candidates = []
    
    # 方法1：查找可打印字符串
    current_string = []
    start_pos = 0
    
    for i, byte in enumerate(data):
        if 32 <= byte <= 126 or byte in [9, 10, 13]:  # 可打印字符 + 制表符换行符
            if not current_string:
                start_pos = i
            current_string.append(chr(byte))
        else:
            if len(current_string) > 1:
                text = ''.join(current_string).strip()
                if text and not text.isspace():
                    # 过滤掉明显的系统信息
                    if not any(sys_word in text.lower() for sys_word in ['calibri', 'times', 'arial', '000000', 'ffffff']):
                        if len(text) < 100:  # 合理的单元格长度
                            cell_candidates.append({
                                'position': start_pos,
                                'content': text,
                                'length': len(text)
                            })
            current_string = []
    
    print(f"找到 {len(cell_candidates)} 个单元格候选:")
    for i, candidate in enumerate(cell_candidates[:20]):  # 显示前20个
        print(f"  {i+1:2d}. 位置{candidate['position']:4d}: {candidate['content']}")
    
    # 方法2：基于数据模式分割
    print(f"\n分析数据模式...")
    
    # 查找重复的分隔符
    separators = {}
    for i in range(len(data) - 3):
        pattern = data[i:i+4]
        if pattern not in separators:
            separators[pattern] = []
        separators[pattern].append(i)
    
    # 找出可能的分隔符（出现频率高的4字节模式）
    frequent_seps = {k: v for k, v in separators.items() if len(v) > 10}
    
    if frequent_seps:
        print("可能的分隔符:")
        for sep, positions in list(frequent_seps.items())[:5]:
            print(f"  {sep.hex()}: 出现{len(positions)}次")
            
            # 尝试用这个分隔符分割数据
            if len(positions) > 20:  # 如果出现次数很多
                segments = []
                last_pos = 0
                
                for pos in positions[:10]:  # 只检查前10个位置
                    if pos - last_pos > 5:  # 段落足够长
                        segment = data[last_pos:pos]
                        try:
                            text = segment.decode('utf-8', errors='ignore').strip()
                            if text and len(text) > 2 and len(text) < 50:
                                segments.append(text)
                        except:
                            pass
                    last_pos = pos + 4
                
                if segments:
                    print(f"    用此分隔符得到的段落: {segments[:5]}")
    
    return cell_candidates

def reconstruct_table_structure(cell_candidates):
    """尝试重建表格结构"""
    print("\n" + "="*60)
    print("重建表格结构")  
    print("="*60)
    
    # 我们知道表格是166行×21列
    expected_rows = 166
    expected_cols = 21
    total_cells = expected_rows * expected_cols
    
    print(f"期望的表格结构: {expected_rows}行 × {expected_cols}列 = {total_cells}个单元格")
    print(f"找到的候选单元格: {len(cell_candidates)}个")
    
    if len(cell_candidates) > 0:
        # 尝试按位置排列单元格
        sorted_candidates = sorted(cell_candidates, key=lambda x: x['position'])
        
        print(f"\n按位置排序的前20个单元格:")
        for i, candidate in enumerate(sorted_candidates[:20]):
            row = i // expected_cols if len(sorted_candidates) >= expected_cols else 0
            col = i % expected_cols
            print(f"  [{row:2d},{col:2d}] {candidate['content']}")
        
        # 尝试检测是否有规律
        if len(sorted_candidates) >= expected_cols:
            print(f"\n可能的第一行数据:")
            first_row = sorted_candidates[:expected_cols]
            for i, cell in enumerate(first_row):
                print(f"  列{i+1}: {cell['content']}")
            
            # 保存为CSV
            csv_content = []
            for row in range(min(expected_rows, len(sorted_candidates) // expected_cols)):
                row_data = []
                for col in range(expected_cols):
                    idx = row * expected_cols + col
                    if idx < len(sorted_candidates):
                        row_data.append(sorted_candidates[idx]['content'])
                    else:
                        row_data.append('')
                csv_content.append(','.join(f'"{cell}"' for cell in row_data))
            
            if csv_content:
                csv_file = 'reconstructed_table.csv'
                with open(csv_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(csv_content))
                print(f"\n✅ 重建的表格已保存: {csv_file}")
                print(f"   包含 {len(csv_content)} 行数据")
                
                # 预览前5行
                print(f"\n前5行预览:")
                for i, row in enumerate(csv_content[:5]):
                    print(f"  行{i+1}: {row[:100]}...")
                
                return csv_file
    
    return None

def find_chinese_content(data):
    """查找中文内容"""
    print("\n" + "="*60)
    print("搜索中文内容")
    print("="*60)
    
    try:
        text = data.decode('utf-8', errors='ignore')
        
        # 使用正则表达式查找中文
        chinese_pattern = r'[\u4e00-\u9fff]+'
        chinese_matches = re.findall(chinese_pattern, text)
        
        if chinese_matches:
            print(f"找到 {len(chinese_matches)} 个中文片段:")
            for i, match in enumerate(chinese_matches):
                if len(match) > 1:  # 至少2个中文字符
                    print(f"  {i+1}. {match}")
        else:
            print("未找到中文内容")
            
        # 查找可能的单元格中文内容
        chinese_cells = []
        for match in chinese_matches:
            if 2 <= len(match) <= 20:  # 合理的单元格长度
                chinese_cells.append(match)
        
        return chinese_cells
        
    except Exception as e:
        print(f"中文搜索失败: {e}")
        return []

def main():
    """主函数"""
    protobuf_file = "/root/projects/tencent-doc-manager/test_DWEVjZndkR2xVSWJN_CSV格式_20250827_231718_nodejs_decoded.bin"
    
    if not Path(protobuf_file).exists():
        print(f"文件不存在: {protobuf_file}")
        return
    
    with open(protobuf_file, 'rb') as f:
        data = f.read()
    
    print(f"分析文件: {protobuf_file}")
    print(f"数据大小: {len(data)} bytes")
    
    # 1. 提取样式信息
    colors, fonts = extract_colors_and_fonts(data)
    
    # 2. 搜索表格内容
    cell_candidates = search_table_content(data)
    
    # 3. 查找中文内容
    chinese_content = find_chinese_content(data)
    
    # 4. 重建表格结构
    csv_file = reconstruct_table_structure(cell_candidates)
    
    print("\n" + "="*60)
    print("提取结果总结")
    print("="*60)
    
    print(f"✅ 颜色信息: {len(colors)}个")
    print(f"✅ 字体信息: {len(fonts)}个")  
    print(f"✅ 单元格候选: {len(cell_candidates)}个")
    print(f"✅ 中文内容: {len(chinese_content)}个")
    
    if csv_file:
        print(f"✅ 重建表格: {csv_file}")
        print("\n🎉 成功从protobuf中提取了表格数据!")
    else:
        print("需要进一步分析数据结构")
    
    print("\n建议:")
    if len(cell_candidates) > 100:
        print("1. 单元格数据足够多，继续优化重建算法")
    else:
        print("1. 需要改进单元格提取方法")
    
    if chinese_content:
        print("2. 中文内容提取成功，这是真实的表格数据")
    else:
        print("2. 可能需要处理编码问题")

if __name__ == "__main__":
    main()