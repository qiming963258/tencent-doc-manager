#!/usr/bin/env python3
"""
测试综合打分文件验证和错误报告
测试各种不符合规范的情况
"""

import json
import os
import sys
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')
from comprehensive_score_validator import ComprehensiveScoreValidator
from standard_columns_config import STANDARD_COLUMNS

def create_invalid_file_wrong_columns():
    """创建一个列名错误的文件"""
    data = {
        "metadata": {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "week": "W38",
            "generator": "test",
            "total_params": 5200,
            "processing_time": 1.0
        },
        "summary": {
            "total_tables": 3,
            "total_columns": 19,
            "total_modifications": 100,
            "overall_risk_score": 0.5,
            "processing_status": "complete"
        },
        "table_names": ["表1", "表2", "表3"],
        # 故意使用错误的列名
        "column_names": [
            "错误列1", "错误列2", "错误列3", "错误列4", "错误列5",
            "错误列6", "错误列7", "错误列8", "错误列9", "错误列10",
            "错误列11", "错误列12", "错误列13", "错误列14", "错误列15",
            "错误列16", "错误列17", "错误列18", "错误列19"
        ],
        "heatmap_data": {
            "matrix": [[0.1] * 19 for _ in range(3)]
        },
        "table_details": [],
        "hover_data": {"data": []},
        "statistics": {
            "table_modifications": [10, 20, 30],
            "table_row_counts": [100, 200, 300],
            "column_total_modifications": [5] * 19,
            "risk_distribution": {"high": 1, "medium": 2, "low": 3}
        }
    }

    filename = '/tmp/test_wrong_columns.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename

def create_invalid_file_wrong_column_count():
    """创建一个列数错误的文件"""
    data = {
        "metadata": {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "week": "W38",
            "generator": "test",
            "total_params": 5200,
            "processing_time": 1.0
        },
        "summary": {
            "total_tables": 3,
            "total_columns": 15,  # 错误的列数
            "total_modifications": 100,
            "overall_risk_score": 0.5,
            "processing_status": "complete"
        },
        "table_names": ["表1", "表2", "表3"],
        # 只有15个列名
        "column_names": STANDARD_COLUMNS[:15],
        "heatmap_data": {
            "matrix": [[0.1] * 15 for _ in range(3)]  # 错误的矩阵大小
        },
        "table_details": [],
        "hover_data": {"data": []},
        "statistics": {
            "table_modifications": [10, 20, 30],
            "table_row_counts": [100, 200, 300],
            "column_total_modifications": [5] * 15,  # 错误的长度
            "risk_distribution": {"high": 1, "medium": 2, "low": 3}
        }
    }

    filename = '/tmp/test_wrong_count.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename

def create_invalid_file_missing_fields():
    """创建一个缺少必需字段的文件"""
    data = {
        "metadata": {
            "version": "2.0",
            # 缺少timestamp
            "week": "W38",
            "generator": "test",
            # 缺少total_params
            "processing_time": 1.0
        },
        # 缺少summary
        "table_names": ["表1", "表2", "表3"],
        "column_names": STANDARD_COLUMNS,
        # 缺少heatmap_data
        "table_details": [],
        # 缺少hover_data
        # 缺少statistics
    }

    filename = '/tmp/test_missing_fields.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename

def test_validation():
    """测试各种验证情况"""
    print("=" * 60)
    print("🧪 综合打分文件验证测试")
    print("=" * 60)

    validator = ComprehensiveScoreValidator()

    # 测试1：列名错误
    print("\n📋 测试1：列名错误")
    print("-" * 40)
    file1 = create_invalid_file_wrong_columns()
    is_valid, errors, _ = validator.validate_file(file1)

    if not is_valid:
        print(f"❌ 验证失败（预期）")
        print("\n错误详情:")
        for i, error in enumerate(errors[:5], 1):
            print(f"  {i}. {error}")
    else:
        print("⚠️ 验证通过（不应该）")

    # 测试2：列数错误
    print("\n📋 测试2：列数错误")
    print("-" * 40)
    file2 = create_invalid_file_wrong_column_count()
    is_valid, errors, _ = validator.validate_file(file2)

    if not is_valid:
        print(f"❌ 验证失败（预期）")
        print("\n错误详情:")
        for i, error in enumerate(errors[:5], 1):
            print(f"  {i}. {error}")
    else:
        print("⚠️ 验证通过（不应该）")

    # 测试3：缺少必需字段
    print("\n📋 测试3：缺少必需字段")
    print("-" * 40)
    file3 = create_invalid_file_missing_fields()
    is_valid, errors, _ = validator.validate_file(file3)

    if not is_valid:
        print(f"❌ 验证失败（预期）")
        print("\n错误详情:")
        for i, error in enumerate(errors[:10], 1):
            print(f"  {i}. {error}")
    else:
        print("⚠️ 验证通过（不应该）")

    # 测试4：验证正确的文件
    print("\n📋 测试4：验证正确的文件")
    print("-" * 40)
    correct_file = '/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_clustered.json'

    if os.path.exists(correct_file):
        is_valid, errors, data = validator.validate_file(correct_file)

        if is_valid:
            print("✅ 验证通过（预期）")
            print(f"  - 版本: {data['metadata']['version']}")
            print(f"  - 表格数: {data['summary']['total_tables']}")
            print(f"  - 参数数: {data['metadata']['total_params']}")
        else:
            print("❌ 验证失败（不应该）")
            for error in errors[:5]:
                print(f"  - {error}")

    # 清理测试文件
    for f in [file1, file2, file3]:
        if os.path.exists(f):
            os.remove(f)

    print("\n" + "=" * 60)
    print("✅ 测试完成")

if __name__ == "__main__":
    test_validation()