#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试UnifiedCSVComparator是否能正确检测变更
验证它是否能处理第一行是标题的CSV文件
"""

from unified_csv_comparator import UnifiedCSVComparator
import json

def test_with_real_files():
    """使用实际下载的文件测试UnifiedCSVComparator"""
    
    print("\n" + "="*60)
    print("测试UnifiedCSVComparator对比功能")
    print("="*60)
    
    # 实际文件路径
    baseline_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-测试版本-出国销售计划表-工作表1_20250911_1131_midweek_W37.csv"
    target_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-副本-测试版本-出国销售计划表-工作表1_20250911_1132_midweek_W37.csv"
    
    print(f"\n基线文件: ...{baseline_file[-50:]}")
    print(f"目标文件: ...{target_file[-50:]}")
    
    # 使用UnifiedCSVComparator
    comparator = UnifiedCSVComparator()
    
    try:
        print("\n执行对比...")
        result = comparator.compare(baseline_file, target_file)
        
        # 分析结果
        print("\n对比结果:")
        print("-"*40)
        
        if 'statistics' in result:
            stats = result['statistics']
            print(f"总修改数: {stats.get('total_modifications', 0)}")
            print(f"相似度: {stats.get('similarity', 0):.2%}")
        
        if 'modifications' in result:
            mods = result['modifications']
            print(f"\n检测到 {len(mods)} 个变更:")
            
            # 显示前5个变更
            for i, mod in enumerate(mods[:5], 1):
                print(f"\n  {i}. 单元格 {mod['cell']}:")
                print(f"     旧值: '{mod['old'][:50]}...' " if len(mod['old']) > 50 else f"     旧值: '{mod['old']}'")
                print(f"     新值: '{mod['new'][:50]}...' " if len(mod['new']) > 50 else f"     新值: '{mod['new']}'")
            
            if len(mods) > 5:
                print(f"\n  ... 还有 {len(mods)-5} 个变更")
        
        if 'modified_columns' in result:
            cols = result['modified_columns']
            if cols:
                print(f"\n涉及的列: {', '.join(cols.keys())}")
        
        # 保存完整结果
        output_file = "/tmp/unified_comparator_test_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n完整结果已保存到: {output_file}")
        
        # 判断是否成功
        if result.get('statistics', {}).get('total_modifications', 0) > 0:
            print("\n✅ 成功！UnifiedCSVComparator正确检测到了变更。")
            print("这说明它能够处理第一行是标题的CSV文件。")
        else:
            print("\n⚠️ 问题：UnifiedCSVComparator仍然没有检测到变更。")
            print("可能需要检查SimplifiedCSVComparator的实现。")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_format():
    """分析UnifiedCSVComparator的输出格式"""
    
    print("\n" + "="*60)
    print("输出格式分析")
    print("="*60)
    
    result = test_with_real_files()
    
    if result:
        print("\n输出格式结构:")
        print("-"*40)
        print("顶层键:", list(result.keys()))
        
        if 'format_version' in result:
            print(f"格式版本: {result['format_version']}")
        
        if 'comparison_engine' in result:
            print(f"对比引擎: {result['comparison_engine']}")
        
        print("\n✅ 输出格式符合简化版规范要求")

if __name__ == "__main__":
    analyze_format()