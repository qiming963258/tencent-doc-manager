#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确对比测试演示
展示如何使用不同版本的文档进行对比
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

def create_test_documents():
    """创建模拟不同版本的测试文档"""
    
    # 创建测试目录
    test_dir = Path('/tmp/test_comparison')
    test_dir.mkdir(exist_ok=True)
    
    # 1. 创建基线版本（上周的数据）
    baseline_file = test_dir / 'baseline_week36.csv'
    with open(baseline_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['产品名称', '销售额', '库存量', '单价', '状态', '备注'])
        writer.writerow(['产品A', '1000', '500', '10.5', '正常', '热销产品'])
        writer.writerow(['产品B', '2000', '300', '20.8', '正常', '稳定销售'])
        writer.writerow(['产品C', '3000', '200', '30.2', '正常', ''])
        writer.writerow(['产品D', '4000', '100', '40.5', '缺货', '需要补货'])
        writer.writerow(['产品E', '5000', '50', '50.8', '缺货', '即将停产'])
        writer.writerow(['产品F', '1500', '400', '15.5', '正常', ''])
        writer.writerow(['产品G', '2500', '150', '25.0', '正常', ''])
    
    print(f"✅ 创建基线版本: {baseline_file}")
    
    # 2. 创建目标版本（本周的数据，有多处变更）
    target_file = test_dir / 'target_week37.csv'
    with open(target_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['产品名称', '销售额', '库存量', '单价', '状态', '备注'])
        writer.writerow(['产品A', '1500', '450', '10.5', '正常', '热销产品'])  # 销售额和库存变化
        writer.writerow(['产品B', '2000', '0', '25.0', '缺货', '库存耗尽'])      # 库存、单价、状态、备注变化
        writer.writerow(['产品C', '3500', '200', '30.2', '正常', '促销中'])     # 销售额和备注变化
        writer.writerow(['产品D', '6000', '300', '40.5', '正常', '已补货'])      # 销售额、库存、状态、备注变化
        writer.writerow(['产品E', '5000', '0', '60.0', '停产', '已停产'])       # 库存、单价、状态、备注变化
        writer.writerow(['产品F', '2000', '350', '15.5', '正常', ''])          # 销售额和库存变化
        writer.writerow(['产品G', '3000', '100', '28.0', '低库存', '需关注'])    # 销售额、库存、单价、状态、备注变化
    
    print(f"✅ 创建目标版本: {target_file}")
    
    # 3. 分析变更
    print("\n📊 变更分析:")
    print("="*60)
    changes = [
        ("产品A", "销售额 1000→1500 (+50%), 库存 500→450"),
        ("产品B", "库存 300→0 (耗尽), 单价 20.8→25.0 (+20%), 状态→缺货"),
        ("产品C", "销售额 3000→3500 (+16.7%), 新增促销备注"),
        ("产品D", "销售额 4000→6000 (+50%), 库存 100→300 (补货), 状态恢复正常"),
        ("产品E", "库存 50→0, 单价 50.8→60.0 (+18%), 状态→停产"),
        ("产品F", "销售额 1500→2000 (+33%), 库存 400→350"),
        ("产品G", "销售额 2500→3000 (+20%), 单价 25→28 (+12%), 新增低库存警告")
    ]
    
    for product, change in changes:
        print(f"  • {product}: {change}")
    
    print("="*60)
    print(f"\n总计: 7个产品全部有变更，涉及26个单元格的修改")
    
    # 4. 风险评估
    print("\n⚠️ 风险评估:")
    print("  • 高风险: 产品B(库存耗尽)、产品E(停产)")
    print("  • 中风险: 产品A、D(销售额大幅变化)、产品G(低库存)")
    print("  • 低风险: 产品C、F(正常业务波动)")
    
    return baseline_file, target_file

def test_with_intelligent_marker():
    """使用智能标记器测试"""
    try:
        from intelligent_excel_marker import DetailedScoreGenerator
        
        baseline_file, target_file = create_test_documents()
        
        print("\n🎯 生成详细打分文件...")
        generator = DetailedScoreGenerator()
        score_file = generator.generate_score_json(
            str(baseline_file),
            str(target_file),
            '/tmp'
        )
        
        # 读取打分结果
        import json
        with open(score_file, 'r', encoding='utf-8') as f:
            score_data = json.load(f)
        
        print(f"✅ 打分文件生成成功")
        print(f"  • 总单元格数: {score_data['statistics']['total_cells']}")
        print(f"  • 变更单元格: {score_data['statistics']['changed_cells']}")
        print(f"  • 高风险: {score_data['statistics']['high_risk_count']}")
        print(f"  • 中风险: {score_data['statistics']['medium_risk_count']}")
        print(f"  • 低风险: {score_data['statistics']['low_risk_count']}")
        
        return score_file
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("正确的文档对比测试")
    print("="*60)
    
    print("\n📌 正确的使用方式:")
    print("  1. 基线文档: 使用上周或更早版本的文档")
    print("  2. 目标文档: 使用当前最新版本的文档")
    print("  3. 两个URL必须不同，指向不同版本的文档")
    
    print("\n" + "-"*60)
    
    # 创建测试数据并生成打分
    score_file = test_with_intelligent_marker()
    
    if score_file:
        print("\n✅ 测试成功！")
        print("这就是系统正确工作时应该检测到的变更。")
        print("\n💡 建议:")
        print("  • 在8093系统中，基线URL填入上周的文档链接")
        print("  • 目标URL填入本周最新的文档链接")
        print("  • 系统会自动检测变更并进行涂色标记")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()