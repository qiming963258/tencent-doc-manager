#!/usr/bin/env python3
"""测试使用真实基线文件对比最新文档"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')
sys.path.append('/root/projects/tencent-doc-manager')

from production.core_modules.real_doc_loader import RealDocumentLoader
import json
from datetime import datetime

def test_comparison():
    """测试对比9月15日基线与最新文档"""

    # 初始化文档加载器
    loader = RealDocumentLoader()
    documents = loader.get_documents()

    print("=" * 60)
    print("🔍 开始对比测试")
    print("=" * 60)

    results = []

    for doc in documents:
        doc_name = doc['name'].replace('副本-测试版本-', '').replace('测试版本-', '')
        print(f"\n📄 处理文档: {doc_name}")

        # 基线文件路径
        baseline_path = None
        target_path = None

        # 查找对应的基线文件（使用9月15日的）
        if '出国销售' in doc_name:
            baseline_path = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline/tencent_出国销售计划表_20250915_0145_baseline_W39.csv'
            target_path = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_出国销售计划表_20250925_1956_midweek_W39.csv'
        elif '小红书' in doc_name:
            baseline_path = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline/tencent_小红书部门_20250915_0146_baseline_W39.csv'
            target_path = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_小红书部门_20250925_1959_midweek_W39.csv'
        elif '回国销售' in doc_name:
            # 回国销售没有9月15日的基线，跳过
            print("  ⚠️ 没有9月15日的基线文件，跳过")
            continue

        if baseline_path and target_path:
            if os.path.exists(baseline_path) and os.path.exists(target_path):
                # 简单对比文件大小和行数
                baseline_size = os.path.getsize(baseline_path)
                target_size = os.path.getsize(target_path)

                with open(baseline_path, 'r', encoding='utf-8') as f:
                    baseline_lines = len(f.readlines())

                with open(target_path, 'r', encoding='utf-8') as f:
                    target_lines = len(f.readlines())

                size_diff = target_size - baseline_size
                line_diff = target_lines - baseline_lines

                print(f"  📊 基线文件: {os.path.basename(baseline_path)}")
                print(f"  📊 目标文件: {os.path.basename(target_path)}")
                print(f"  📏 文件大小差异: {size_diff:+d} 字节")
                print(f"  📝 行数差异: {line_diff:+d} 行")

                if line_diff != 0 or size_diff != 0:
                    print(f"  ✅ 检测到实际差异！")
                    results.append({
                        'document': doc_name,
                        'has_changes': True,
                        'line_diff': line_diff,
                        'size_diff': size_diff
                    })
                else:
                    print(f"  ⚠️ 文件完全相同")
                    results.append({
                        'document': doc_name,
                        'has_changes': False
                    })
            else:
                print(f"  ❌ 文件不存在")

    print("\n" + "=" * 60)
    print("📊 对比结果总结:")
    print("=" * 60)

    for result in results:
        if result['has_changes']:
            print(f"✅ {result['document']}: 有变化 (行数差异: {result['line_diff']:+d})")
        else:
            print(f"⚠️ {result['document']}: 无变化")

    # 如果有差异，运行完整的对比流程
    if any(r['has_changes'] for r in results):
        print("\n🚀 检测到文档有实际差异，建议运行完整的批处理流程生成热力图")
        print("   运行命令: python3 run_batch_with_old_baseline.py")

if __name__ == "__main__":
    test_comparison()