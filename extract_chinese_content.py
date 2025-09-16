#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取CSV文件中的中文内容
"""

import re
from pathlib import Path

def extract_chinese_from_csv(csv_file):
    """从CSV文件提取中文内容"""
    print(f"\n提取中文内容: {Path(csv_file).name}")
    print("="*50)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找中文
    chinese_pattern = r'[\u4e00-\u9fff]+'
    chinese_matches = re.findall(chinese_pattern, content)
    
    # 去重
    unique_chinese = []
    for match in chinese_matches:
        if match not in unique_chinese and len(match) >= 1:
            unique_chinese.append(match)
    
    print(f"找到 {len(unique_chinese)} 个中文内容:")
    
    # 按长度排序，长的更可能是业务数据
    unique_chinese.sort(key=len, reverse=True)
    
    for i, text in enumerate(unique_chinese[:30], 1):  # 显示前30个
        print(f"  {i:2d}. {text}")
    
    return unique_chinese

def main():
    """主函数"""
    csv_files = [
        "/root/projects/tencent-doc-manager/real_test_results/DWEVjZndkR2xVSWJN_CSV_20250828_102625_business_data_102829.csv",
        "/root/projects/tencent-doc-manager/real_test_results/DRFppYm15RGZ2WExN_CSV_20250828_102627_business_data_102829.csv", 
        "/root/projects/tencent-doc-manager/real_test_results/DRHZrS1hOS3pwRGZB_CSV_20250828_102630_business_data_102829.csv"
    ]
    
    all_chinese = []
    
    for csv_file in csv_files:
        if Path(csv_file).exists():
            chinese_content = extract_chinese_from_csv(csv_file)
            all_chinese.extend(chinese_content)
    
    # 总结
    print(f"\n" + "="*60)
    print(f"所有文件中文内容总结")
    print(f"="*60)
    print(f"总中文内容数: {len(all_chinese)}个")
    
    # 查找可能的业务关键词
    business_keywords = [
        '销售', '计划', '客户', '产品', '订单', '目标', '业绩', '市场', '营销', 
        '项目', '任务', '完成', '进度', '负责', '部门', '团队', '管理', '汇报',
        '年', '月', '日', '时间', '地点', '人员', '数据', '分析', '统计'
    ]
    
    found_business = []
    for text in all_chinese:
        if any(keyword in text for keyword in business_keywords):
            found_business.append(text)
    
    if found_business:
        print(f"\n找到可能的业务关键词:")
        for keyword in found_business:
            print(f"  - {keyword}")
    else:
        print(f"\n这些文档可能是系统配置表，而不是业务数据表")

if __name__ == "__main__":
    main()