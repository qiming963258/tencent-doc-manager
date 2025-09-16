#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强CSV对比算法集成
"""

from simple_comparison_handler import simple_csv_compare
import json

def test_integration():
    """测试集成后的对比功能"""
    baseline = "/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_副本-测试版本-出国销售计划表-工作表1_csv_20250905_0033_midweek_W36.csv"
    target = "/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_副本-副本-测试版本-出国销售计划表-工作表1_csv_20250905_0034_midweek_W36.csv"
    
    print("📊 测试增强CSV对比算法集成:")
    print("-" * 50)
    
    result = simple_csv_compare(baseline, target)
    
    print(f"✅ 相似度: {result['similarity_score']*100:.1f}%")
    print(f"📈 总变更: {result['total_changes']}")
    print(f"➕ 新增行: {result['added_rows']}")
    print(f"➖ 删除行: {result['deleted_rows']}")  
    print(f"✏️ 修改行: {result['modified_rows']}")
    
    if 'details' in result:
        details = result['details']
        print(f"\n📋 详细信息:")
        print(f"  - 基线行数: {details.get('baseline_total_rows', 'N/A')}")
        print(f"  - 目标行数: {details.get('target_total_rows', 'N/A')}")
        print(f"  - 基线列数: {details.get('baseline_columns', 'N/A')}")
        print(f"  - 目标列数: {details.get('target_columns', 'N/A')}")
        print(f"  - 共同列数: {details.get('common_columns', 'N/A')}")
        print(f"  - 对比单元格数: {details.get('total_cells_compared', 'N/A')}")
        print(f"  - 相同单元格数: {details.get('identical_cells', 'N/A')}")
        print(f"  - 修改单元格数: {details.get('modified_cells', 'N/A')}")
    
    if 'warning' in result:
        print(f"\n⚠️ 警告: {result['warning']}")
    
    if 'error' in result:
        print(f"\n❌ 错误: {result['error']}")
    
    # 验证结果
    assert result['similarity_score'] > 0.9, f"相似度太低: {result['similarity_score']}"
    assert result['similarity_score'] < 0.95, f"相似度太高: {result['similarity_score']}"
    print(f"\n✅ 测试通过! 算法正确识别了文件间的差异")
    
    return result

if __name__ == "__main__":
    test_integration()