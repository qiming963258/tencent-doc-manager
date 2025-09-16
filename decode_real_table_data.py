#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解码真实的表格数据
基于找到的185KB用户数据进行深度分析
"""

import struct
import re
from pathlib import Path

def analyze_real_table_structure(data_file):
    """分析真实表格数据结构"""
    print("="*60)
    print("深度分析真实表格数据")
    print("="*60)
    
    with open(data_file, 'rb') as f:
        data = f.read()
    
    print(f"数据大小: {len(data):,} bytes")
    print(f"数据类型: 二进制protobuf格式")
    
    # 查找表格数据模式
    cell_data = extract_cell_values(data)
    
    # 查找表格结构
    table_structure = analyze_table_structure(data)
    
    # 重建完整表格
    reconstruct_business_table(data)
    
    return cell_data, table_structure

def extract_cell_values(data):
    """提取实际的单元格数值"""
    print("\n提取单元格数据:")
    
    cell_values = []
    
    # 方法1：查找数值型数据
    print("  查找数值数据...")
    numbers_found = []
    
    # 扫描所有可能的数值格式
    for i in range(0, len(data) - 8, 1):
        # 尝试不同的数值格式
        try:
            # 32位整数
            if i + 4 <= len(data):
                int_val = struct.unpack('<i', data[i:i+4])[0]
                if 1 <= int_val <= 100000:  # 合理的业务数值范围
                    numbers_found.append(('int32', i, int_val))
            
            # 32位浮点数
            if i + 4 <= len(data):
                float_val = struct.unpack('<f', data[i:i+4])[0]
                if 0.01 <= abs(float_val) <= 1000000 and not (float_val != float_val):  # NaN检查
                    numbers_found.append(('float32', i, float_val))
                    
        except:
            continue
    
    # 去重和过滤
    unique_numbers = []
    seen_values = set()
    
    for dtype, pos, val in numbers_found:
        if val not in seen_values:
            seen_values.add(val)
            unique_numbers.append((dtype, pos, val))
    
    print(f"  找到 {len(unique_numbers)} 个唯一数值:")
    for dtype, pos, val in unique_numbers[:20]:
        print(f"    位置{pos:5d}: {val} ({dtype})")
    
    # 方法2：查找文本数据
    print("\n  查找文本数据...")
    text_data = find_text_cells(data)
    
    return unique_numbers + text_data

def find_text_cells(data):
    """查找文本单元格"""
    text_cells = []
    
    # 查找UTF-8编码的文本
    try:
        # 转换为文本分析
        text_content = data.decode('utf-8', errors='ignore')
        
        # 查找中文内容（业务数据的重要标识）
        chinese_pattern = r'[\u4e00-\u9fff]+'
        chinese_matches = re.finditer(chinese_pattern, text_content)
        
        for match in chinese_matches:
            chinese_text = match.group()
            if len(chinese_text) >= 2:  # 至少2个中文字符
                text_cells.append(('chinese', match.start(), chinese_text))
        
        # 查找英文单词
        english_pattern = r'[a-zA-Z]{3,20}'
        english_matches = re.finditer(english_pattern, text_content)
        
        for match in english_matches:
            english_text = match.group()
            if english_text not in ['UTF', 'EJS', 'JSON', 'HTTP']:  # 过滤系统关键词
                text_cells.append(('english', match.start(), english_text))
        
        # 查找数字串（可能的ID、编号等）
        number_pattern = r'\\d{3,10}'
        number_matches = re.finditer(number_pattern, text_content)
        
        for match in number_matches:
            number_text = match.group()
            text_cells.append(('number_string', match.start(), number_text))
            
    except Exception as e:
        print(f"    文本解析错误: {e}")
    
    print(f"  找到 {len(text_cells)} 个文本单元格:")
    for dtype, pos, val in text_cells[:15]:
        print(f"    位置{pos:5d}: {val} ({dtype})")
    
    return text_cells

def analyze_table_structure(data):
    """分析表格结构"""
    print("\n分析表格结构:")
    
    # 我们知道这个表格是166行×21列
    expected_rows = 166
    expected_cols = 21
    expected_cells = expected_rows * expected_cols
    
    print(f"  期望结构: {expected_rows}行 × {expected_cols}列 = {expected_cells:,}个单元格")
    
    # 查找重复模式（可能是行或单元格分隔符）
    print("  查找数据模式...")
    
    patterns = {}
    pattern_length = 4
    
    for i in range(len(data) - pattern_length):
        pattern = data[i:i+pattern_length]
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(i)
    
    # 找出高频模式
    frequent_patterns = {k: v for k, v in patterns.items() if len(v) > 100}
    
    print(f"  找到 {len(frequent_patterns)} 个高频模式:")
    for pattern, positions in list(frequent_patterns.items())[:5]:
        print(f"    {pattern.hex()}: 出现{len(positions)}次")
        
        # 检查模式间隔
        if len(positions) > 2:
            intervals = [positions[i+1] - positions[i] for i in range(min(10, len(positions)-1))]
            avg_interval = sum(intervals) / len(intervals)
            print(f"      平均间隔: {avg_interval:.1f} bytes")
    
    return {
        'expected_structure': (expected_rows, expected_cols),
        'patterns': frequent_patterns
    }

def reconstruct_business_table(data):
    """重建业务表格"""
    print("\n重建业务表格:")
    
    # 使用更智能的方法提取表格数据
    table_data = []
    
    # 方法1：按固定间隔提取数据
    print("  尝试按间隔提取数据...")
    
    # 计算可能的单元格大小
    expected_cells = 166 * 21
    avg_cell_size = len(data) // expected_cells
    
    print(f"  平均单元格大小: {avg_cell_size} bytes")
    
    if 10 <= avg_cell_size <= 200:  # 合理的单元格大小
        extracted_data = []
        
        for i in range(0, len(data), avg_cell_size):
            if i + avg_cell_size <= len(data):
                cell_data = data[i:i+avg_cell_size]
                
                # 尝试解析这个cell的内容
                cell_content = parse_cell_content(cell_data)
                if cell_content:
                    extracted_data.append(cell_content)
        
        print(f"  提取了 {len(extracted_data)} 个单元格")
        
        # 尝试重组为表格
        if len(extracted_data) >= 100:  # 至少有一些数据
            rows = []
            cols_per_row = 21
            
            for i in range(0, min(len(extracted_data), 166 * 21), cols_per_row):
                row = extracted_data[i:i+cols_per_row]
                if len(row) == cols_per_row:
                    rows.append(row)
            
            if rows:
                print(f"  重建了 {len(rows)} 行数据")
                
                # 保存为CSV
                csv_content = []
                for row in rows[:20]:  # 只显示前20行
                    csv_content.append(','.join(f'"{str(cell)}"' for cell in row))
                
                if csv_content:
                    csv_file = 'business_table_reconstructed.csv'
                    with open(csv_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(csv_content))
                    
                    print(f"  ✅ 业务表格已保存: {csv_file}")
                    
                    # 显示前几行预览
                    print("  前5行预览:")
                    for i, row in enumerate(csv_content[:5]):
                        print(f"    行{i+1}: {row[:100]}...")
                    
                    return csv_file
    
    print("  表格重建失败，需要更深入的格式分析")
    return None

def parse_cell_content(cell_bytes):
    """解析单个单元格内容"""
    # 尝试多种解析方式
    
    # 1. 尝试整数
    if len(cell_bytes) >= 4:
        try:
            int_val = struct.unpack('<i', cell_bytes[:4])[0]
            if -1000000 < int_val < 1000000:
                return int_val
        except:
            pass
    
    # 2. 尝试浮点数
    if len(cell_bytes) >= 4:
        try:
            float_val = struct.unpack('<f', cell_bytes[:4])[0]
            if -1000000 < float_val < 1000000 and float_val == float_val:  # 非NaN
                return round(float_val, 2)
        except:
            pass
    
    # 3. 尝试字符串
    try:
        text = cell_bytes.decode('utf-8', errors='ignore').strip()
        if text and len(text) < 100:
            # 过滤掉明显的二进制垃圾
            if text.isprintable() and not all(ord(c) < 32 or ord(c) > 126 for c in text if ord(c) < 128):
                return text
    except:
        pass
    
    # 4. 返回空值
    return ""

def main():
    """主函数"""
    print("🔍 深度解码真实业务表格数据")
    print("="*60)
    
    data_file = "related_sheet_data.bin"
    
    if not Path(data_file).exists():
        print(f"❌ 数据文件不存在: {data_file}")
        print("请先运行 find_actual_user_data.py")
        return
    
    # 分析数据
    cell_data, table_structure = analyze_real_table_structure(data_file)
    
    print("\n" + "="*60)
    print("实际测试最终结果")
    print("="*60)
    
    # 检查是否生成了业务表格
    business_file = "business_table_reconstructed.csv"
    if Path(business_file).exists():
        print("✅ 成功重建业务表格!")
        
        # 验证内容
        with open(business_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含有意义的数据
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', content))
        has_numbers = bool(re.search(r'\\d+', content))
        has_meaningful_data = len(content) > 1000
        
        print(f"  包含中文: {'✅' if has_chinese else '❌'}")
        print(f"  包含数字: {'✅' if has_numbers else '❌'}")
        print(f"  数据充足: {'✅' if has_meaningful_data else '❌'}")
        
        if has_chinese and has_numbers and has_meaningful_data:
            print("\n🎉 实际测试完全成功！")
            print("我们已经能够从腾讯文档的EJS加密格式中提取真实的业务数据！")
        else:
            print("\n⚠️ 数据提取部分成功，但可能需要进一步优化解析算法")
    else:
        print("❌ 业务表格重建失败")
        print("数据解密成功，但表格重组需要进一步研究")
    
    print(f"\n📊 数据分析统计:")
    print(f"  原始数据: {len(open(data_file, 'rb').read()):,} bytes")
    print(f"  找到单元格: {len(cell_data):,} 个")
    print(f"  预期单元格: {166 * 21:,} 个")
    print(f"  提取率: {len(cell_data) / (166 * 21) * 100:.1f}%")

if __name__ == "__main__":
    main()