#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试列名标准化处理流程
"""

import json
import asyncio
from column_standardization_processor import ColumnStandardizationProcessor

def create_test_comparison_result():
    """创建测试用的CSV对比结果"""
    return {
        "metadata": {
            "original_file": "test_comparison.csv",
            "baseline_file": "baseline.csv",
            "target_file": "target.csv",
            "comparison_time": "2025-09-05T12:00:00"
        },
        "differences": [
            {
                "row_number": 1,
                "序列号": {
                    "baseline_value": "001",
                    "target_value": "001",
                    "changed": False
                },
                "项目类别": {
                    "baseline_value": "类型A",
                    "target_value": "类型B",
                    "changed": True
                },
                "来源地": {
                    "baseline_value": "北京",
                    "target_value": "上海",
                    "changed": True
                },
                "发起时间": {
                    "baseline_value": "2025-01-01",
                    "target_value": "2025-01-02",
                    "changed": True
                },
                "目标": {
                    "baseline_value": "目标1",
                    "target_value": "目标1",
                    "changed": False
                },
                "KR": {
                    "baseline_value": "KR1",
                    "target_value": "KR2",
                    "changed": True
                },
                "额外列1": {
                    "baseline_value": "数据1",
                    "target_value": "数据2",
                    "changed": True
                },
                "额外列2": {
                    "baseline_value": "信息1",
                    "target_value": "信息2",
                    "changed": True
                }
            },
            {
                "row_number": 2,
                "序列号": {
                    "baseline_value": "002",
                    "target_value": "002",
                    "changed": False
                },
                "项目类别": {
                    "baseline_value": "类型C",
                    "target_value": "类型D",
                    "changed": True
                },
                "来源地": {
                    "baseline_value": "深圳",
                    "target_value": "广州",
                    "changed": True
                },
                "发起时间": {
                    "baseline_value": "2025-02-01",
                    "target_value": "2025-02-01",
                    "changed": False
                }
            }
        ]
    }

async def test_standardization():
    """测试标准化流程"""
    print("\n" + "="*60)
    print("📊 CSV列名标准化测试")
    print("="*60)
    
    # 创建处理器
    api_key = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
    processor = ColumnStandardizationProcessor(api_key)
    
    # 创建测试数据
    test_data = create_test_comparison_result()
    
    # 保存测试数据到文件
    test_file = "/tmp/test_comparison.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 测试文件已创建: {test_file}")
    
    # 步骤1：提取有修改的列
    print("\n📋 步骤1：提取有修改的列")
    modified_columns, column_data = processor.extract_modified_columns(test_data)
    
    print(f"  原始列名: {list(test_data['differences'][0].keys())}")
    print(f"  有修改的列: {modified_columns}")
    print(f"  过滤掉的列: {set(test_data['differences'][0].keys()) - set(modified_columns) - {'row_number'}}")
    
    # 步骤2：生成序号标签
    print("\n🔤 步骤2：生成序号标签")
    labels = processor.generate_column_labels(len(modified_columns))
    labeled_columns = {labels[i]: modified_columns[i] for i in range(len(modified_columns))}
    
    for label, col in labeled_columns.items():
        print(f"  {label}: {col}")
    
    # 步骤3：调用AI标准化
    print("\n🤖 步骤3：调用AI进行标准化")
    print("  正在调用DeepSeek V3...")
    
    try:
        standardization_result = await processor.standardize_columns(modified_columns)
        
        if standardization_result.get("success"):
            result = standardization_result["result"]
            print("\n✅ AI标准化成功！")
            
            # 显示映射结果
            if "numbered_mapping" in result:
                print("\n  序号映射结果:")
                for label, standard in result["numbered_mapping"].items():
                    original = labeled_columns.get(label, "未知")
                    print(f"    {label}: {original} → {standard}")
            
            # 显示统计信息
            if "statistics" in result:
                stats = result["statistics"]
                print(f"\n  统计信息:")
                print(f"    总输入列数: {stats.get('total_input', 0)}")
                print(f"    成功映射: {stats.get('mapped_count', 0)}")
                print(f"    丢弃列数: {stats.get('discarded_count', 0)}")
                print(f"    缺失标准列: {stats.get('missing_standard_count', 0)}")
            
            # 步骤4：应用标准化
            print("\n📝 步骤4：应用标准化到原始数据")
            standardized_result = processor.apply_standardization(test_data, standardization_result)
            
            # 保存结果
            output_file = "/tmp/test_standardized.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(standardized_result, f, ensure_ascii=False, indent=2)
            
            print(f"  标准化结果已保存到: {output_file}")
            
            # 显示标准化后的列
            if standardized_result.get("differences"):
                standardized_columns = list(standardized_result["differences"][0].keys())
                standardized_columns.remove("row_number")
                print(f"\n  标准化后的列名 ({len(standardized_columns)}个):")
                for i, col in enumerate(standardized_columns, 1):
                    print(f"    {i}. {col}")
            
        else:
            print(f"\n❌ AI标准化失败: {standardization_result.get('error', '未知错误')}")
    
    except Exception as e:
        print(f"\n❌ 处理过程出错: {e}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_standardization())