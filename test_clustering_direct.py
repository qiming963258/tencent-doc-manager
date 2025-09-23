#!/usr/bin/env python3
"""
测试聚类功能是否正常工作
"""

import json
import sys

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def test_clustering():
    """测试聚类功能"""

    # 加载测试数据
    with open('/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W39_latest.json', 'r') as f:
        data = json.load(f)

    # 提取数据
    heatmap_matrix = data['heatmap_data']['matrix']
    table_names = data['table_names']
    column_names = data['column_names']

    print(f"📊 原始数据：")
    print(f"   表格数量: {len(table_names)}")
    print(f"   列数: {len(column_names)}")
    print(f"   热力图矩阵: {len(heatmap_matrix)}x{len(heatmap_matrix[0]) if heatmap_matrix else 0}")
    print(f"   原始列顺序前5个: {column_names[:5]}")

    # 测试纯Python聚类
    try:
        from production.servers.pure_python_clustering import apply_pure_clustering

        print("\n🔄 应用纯Python聚类算法...")
        reordered_heatmap, reordered_tables, reordered_columns, row_order, col_order = \
            apply_pure_clustering(heatmap_matrix, table_names, column_names)

        print("✅ 聚类成功！")
        print(f"   重排后列顺序前5个: {reordered_columns[:5]}")
        print(f"   列重排序索引: {col_order}")

        # 比较前后顺序
        if column_names[:5] != reordered_columns[:5]:
            print("🎯 列顺序已改变 - 聚类功能正常工作！")
        else:
            print("⚠️ 列顺序未改变 - 可能数据不够复杂或聚类效果不明显")

    except Exception as e:
        print(f"❌ 聚类失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clustering()