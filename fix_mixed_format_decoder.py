#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复混合格式解码器 - 正确分离CSV中的文本和二进制数据
"""

import csv
import re
import struct
from pathlib import Path
from datetime import datetime

def decode_mixed_csv_ejs(file_path):
    """解码混合了二进制数据的CSV格式EJS"""
    print(f"\n{'='*60}")
    print(f"解码混合格式文档: {Path(file_path).name}")
    print(f"{'='*60}")
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # 解析CSV
    import io
    csv_reader = csv.reader(io.StringIO(content))
    rows = list(csv_reader)
    
    print(f"CSV行数: {len(rows)}")
    
    # 分离文本和二进制数据
    text_cells = []
    binary_cells = []
    real_chinese = []
    
    for row_idx, row in enumerate(rows):
        for col_idx, cell in enumerate(row):
            cell = cell.strip()
            
            if not cell:
                continue
            
            # 检查是否包含不可打印字符（二进制数据标志）
            has_binary = any(ord(c) < 32 or ord(c) > 126 
                           for c in cell 
                           if ord(c) not in [9, 10, 13] and not (0x4e00 <= ord(c) <= 0x9fff))
            
            if has_binary:
                # 包含二进制数据，尝试提取可读部分
                readable_parts = extract_readable_parts(cell)
                if readable_parts:
                    text_cells.extend(readable_parts)
                binary_cells.append({
                    'row': row_idx,
                    'col': col_idx,
                    'length': len(cell)
                })
            else:
                # 纯文本内容
                # 检查是否是真正的中文（不是乱码）
                chinese_chars = re.findall(r'[\u4e00-\u9fff]+', cell)
                if chinese_chars:
                    for ch in chinese_chars:
                        # 过滤掉单个中文字符的乱码
                        if len(ch) >= 2 and is_meaningful_chinese(ch):
                            real_chinese.append(ch)
                            text_cells.append({
                                'row': row_idx,
                                'col': col_idx,
                                'content': ch,
                                'type': 'chinese'
                            })
                
                # 检查是否是有意义的英文/数字
                if is_meaningful_text(cell):
                    text_cells.append({
                        'row': row_idx,
                        'col': col_idx,
                        'content': cell,
                        'type': 'text'
                    })
    
    print(f"\n分析结果:")
    print(f"   文本单元格: {len(text_cells)}个")
    print(f"   二进制单元格: {len(binary_cells)}个")
    print(f"   真实中文内容: {len(real_chinese)}个")
    
    # 查找可能的表头
    headers = find_table_headers(text_cells)
    if headers:
        print(f"\n找到可能的表头:")
        for h in headers:
            print(f"   - {h}")
    
    # 查找业务数据
    business_data = find_business_data(text_cells, real_chinese)
    
    return {
        'text_cells': text_cells,
        'chinese_content': real_chinese,
        'headers': headers,
        'business_data': business_data
    }

def extract_readable_parts(mixed_string):
    """从混合字符串中提取可读部分"""
    readable = []
    current = []
    
    for char in mixed_string:
        # 检查是否是可读字符
        if (32 <= ord(char) <= 126 or  # ASCII可打印
            0x4e00 <= ord(char) <= 0x9fff):  # 中文
            current.append(char)
        else:
            # 遇到不可读字符，保存当前累积的可读部分
            if len(current) > 2:  # 至少3个字符才认为有意义
                text = ''.join(current)
                if is_meaningful_text(text):
                    readable.append({'content': text, 'type': 'extracted'})
            current = []
    
    # 保存最后的部分
    if len(current) > 2:
        text = ''.join(current)
        if is_meaningful_text(text):
            readable.append({'content': text, 'type': 'extracted'})
    
    return readable

def is_meaningful_chinese(text):
    """判断是否是有意义的中文（不是乱码）"""
    # 常见的中文词汇
    common_words = [
        '工作', '表格', '数据', '文档', '项目', '计划', '管理', '时间',
        '名称', '编号', '类型', '状态', '备注', '说明', '内容', '信息',
        '年', '月', '日', '周', '季度', '部门', '人员', '负责',
        '销售', '采购', '库存', '订单', '客户', '产品', '价格', '数量',
        '合计', '总计', '小计', '统计', '分析', '报表', '清单', '明细'
    ]
    
    # 如果包含常见词汇，很可能是真实内容
    for word in common_words:
        if word in text:
            return True
    
    # 如果是纯中文且长度合理，可能是真实内容
    if re.match(r'^[\u4e00-\u9fff]+$', text) and 2 <= len(text) <= 20:
        # 检查是否是重复字符（乱码特征）
        if len(set(text)) > 1:  # 不是重复字符
            return True
    
    return False

def is_meaningful_text(text):
    """判断是否是有意义的文本"""
    # 排除系统关键词
    system_keywords = [
        'font', 'color', 'style', 'calibri', 'arial', 'microsoft',
        '000000', 'ffffff', 'jpan', 'hans', 'hant', 'arab', 'hebr'
    ]
    
    text_lower = text.lower()
    
    # 如果是系统关键词，不是业务数据
    if any(k in text_lower for k in system_keywords):
        return False
    
    # 如果太短或只是标点符号
    if len(text) <= 1 or text in ['*', ':', 'J', 'B', 'R', '(', ')', '"', ',', '.', '-']:
        return False
    
    # 如果是版本号格式
    if re.match(r'^\d+\.\d+\.\d+', text):
        return True  # 版本号是有意义的
    
    # 如果是日期格式
    if re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text):
        return True
    
    # 如果是数字且长度合理
    if text.replace('.', '').replace('-', '').isdigit() and 2 <= len(text) <= 10:
        return True
    
    # 如果是英文单词或短语
    if re.match(r'^[A-Za-z][A-Za-z\s]+$', text) and len(text) >= 3:
        return True
    
    # 如果是代码/ID格式
    if re.match(r'^[A-Z0-9]{4,}$', text) and text not in ['FFFFFF', 'E8E8E8']:
        return True
    
    return False

def find_table_headers(text_cells):
    """查找可能的表头"""
    headers = []
    
    # 常见的表头关键词
    header_keywords = [
        '序号', '编号', 'ID', 'No', '名称', 'Name', '类型', 'Type',
        '日期', 'Date', '时间', 'Time', '状态', 'Status', '备注', 'Remark',
        '数量', 'Qty', '价格', 'Price', '金额', 'Amount', '合计', 'Total',
        '部门', 'Dept', '负责人', 'Owner', '客户', 'Customer', '产品', 'Product'
    ]
    
    for cell in text_cells:
        if cell.get('type') == 'chinese':
            content = cell['content']
            if any(k in content for k in header_keywords):
                headers.append(content)
        elif cell.get('type') == 'text':
            content = cell['content']
            if any(k.lower() in content.lower() for k in header_keywords):
                headers.append(content)
    
    return list(set(headers))  # 去重

def find_business_data(text_cells, chinese_content):
    """查找业务数据"""
    business_data = []
    
    # 查找日期
    for cell in text_cells:
        content = cell.get('content', '')
        # 日期格式
        if re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', content):
            business_data.append({'type': 'date', 'value': content})
        # 金额格式
        elif re.match(r'^\d+\.?\d*$', content) and len(content) >= 3:
            business_data.append({'type': 'number', 'value': content})
    
    # 查找有意义的中文
    for ch in chinese_content:
        if is_meaningful_chinese(ch):
            business_data.append({'type': 'chinese', 'value': ch})
    
    return business_data

def generate_clean_csv(decode_result, original_file):
    """生成清理后的CSV"""
    print(f"\n生成清理后的CSV...")
    
    text_cells = decode_result.get('text_cells', [])
    
    if not text_cells:
        print("   没有找到有意义的文本内容")
        return None
    
    # 按行组织数据
    rows_dict = {}
    for cell in text_cells:
        if 'row' in cell and 'col' in cell:
            row_idx = cell['row']
            col_idx = cell['col']
            
            if row_idx not in rows_dict:
                rows_dict[row_idx] = {}
            rows_dict[row_idx][col_idx] = cell.get('content', '')
    
    # 转换为行列表
    if not rows_dict:
        print("   没有可组织的行数据")
        return None
    
    max_col = max(max(row.keys()) for row in rows_dict.values() if row)
    
    clean_rows = []
    for row_idx in sorted(rows_dict.keys()):
        row_data = []
        for col_idx in range(max_col + 1):
            row_data.append(rows_dict[row_idx].get(col_idx, ''))
        
        # 只保留有内容的行
        if any(cell for cell in row_data):
            clean_rows.append(row_data)
    
    # 生成CSV文件
    timestamp = datetime.now().strftime('%H%M%S')
    output_file = Path(original_file).parent / f"{Path(original_file).stem}_clean_{timestamp}.csv"
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(clean_rows)
    
    print(f"   ✅ 已保存: {output_file.name}")
    print(f"   包含 {len(clean_rows)} 行数据")
    
    return str(output_file)

def main():
    """主函数"""
    print("🔧 修复混合格式文档解码")
    print("="*60)
    
    # 处理所有EJS文件
    test_dir = Path('/root/projects/tencent-doc-manager/real_test_results')
    ejs_files = list(test_dir.glob('*.ejs'))
    
    results = []
    
    for ejs_file in ejs_files[:1]:  # 先测试一个文件
        print(f"\n处理文件: {ejs_file.name}")
        
        result = decode_mixed_csv_ejs(str(ejs_file))
        
        # 显示业务数据
        if result.get('business_data'):
            print(f"\n找到的业务数据:")
            for i, data in enumerate(result['business_data'][:10], 1):
                print(f"   {i}. [{data['type']}] {data['value']}")
        
        # 生成清理后的CSV
        clean_csv = generate_clean_csv(result, str(ejs_file))
        
        results.append({
            'file': ejs_file.name,
            'success': clean_csv is not None,
            'output': clean_csv,
            'business_data_count': len(result.get('business_data', []))
        })
    
    # 总结
    print(f"\n" + "="*60)
    print("处理结果总结")
    print("="*60)
    
    for result in results:
        if result['success']:
            print(f"✅ {result['file']}")
            print(f"   业务数据: {result['business_data_count']}个")
            print(f"   输出文件: {Path(result['output']).name if result['output'] else 'N/A'}")
        else:
            print(f"❌ {result['file']} - 未找到有意义的数据")

if __name__ == "__main__":
    main()