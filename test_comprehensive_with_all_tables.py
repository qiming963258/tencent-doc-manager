#!/usr/bin/env python3
"""
测试综合打分聚合器包含所有表格的功能
"""

import sys
import os
import json
from datetime import datetime

# 添加路径
sys.path.append('/root/projects/tencent-doc-manager/production')
sys.path.append('/root/projects/tencent-doc-manager/production/scoring_engine')

from scoring_engine.comprehensive_aggregator import ComprehensiveAggregator

def test_comprehensive_with_all_tables():
    """测试包含所有表格的综合打分"""
    
    print("🧪 测试综合打分聚合器（包含所有表格）")
    print("=" * 60)
    
    # 创建聚合器
    aggregator = ComprehensiveAggregator()
    
    # 模拟一些详细打分文件（实际环境中这些文件已存在）
    # 这里我们假设没有详细打分文件，所有表格都是未修改的
    detailed_files = []
    
    # 生成综合报告
    report = aggregator.aggregate_files(detailed_files, week='W37_TEST')
    
    # 显示结果
    print(f"\n📊 综合报告统计:")
    print(f"- 总表格数: {report['metadata']['total_tables']}")
    print(f"- 总修改数: {report['metadata']['total_modifications']}")
    print(f"- 生成时间: {report['metadata']['generation_time']}")
    
    print(f"\n📋 表格详情:")
    for table in report['table_scores']:
        status_icon = "✏️" if table['modifications_count'] > 0 else "✅"
        risk_level = table['table_summary']['risk_level']
        risk_score = table['table_summary']['overall_risk_score']
        
        print(f"{status_icon} {table['table_name'][:30]:30} | "
              f"修改: {table['modifications_count']:3} | "
              f"风险: {risk_level:10} | "
              f"分数: {risk_score:.3f}")
    
    # 保存报告
    output_file = f"/root/projects/tencent-doc-manager/scoring_results/test_comprehensive_all_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 测试报告已保存: {output_file}")
    
    # 验证结果
    print(f"\n✅ 验证结果:")
    if report['metadata']['total_tables'] == 3:
        print("  ✓ 成功包含所有3个配置表格")
    else:
        print(f"  ✗ 表格数量不正确: {report['metadata']['total_tables']} != 3")
    
    # 检查是否所有表格都有正确的URL
    all_have_urls = all(t.get('table_url') for t in report['table_scores'])
    if all_have_urls:
        print("  ✓ 所有表格都有正确的URL")
    else:
        print("  ✗ 某些表格缺少URL")
    
    # 检查未修改表格的分数是否为0
    unmodified_correct = all(
        t['table_summary']['overall_risk_score'] == 0.0 
        for t in report['table_scores'] 
        if t['modifications_count'] == 0
    )
    if unmodified_correct:
        print("  ✓ 未修改表格的风险分数正确设置为0")
    else:
        print("  ✗ 未修改表格的风险分数设置错误")
    
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    
    return report

if __name__ == '__main__':
    test_comprehensive_with_all_tables()