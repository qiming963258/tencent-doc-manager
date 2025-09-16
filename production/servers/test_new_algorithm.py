#!/usr/bin/env python3
"""
测试新的热力图排序算法是否正确集成
"""

import sys
import os

# 添加路径
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/servers')
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')

# 设置环境变量避免Flask警告
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

# 创建测试矩阵
test_matrix = [
    [0.1, 0.2, 0.9, 0.1, 0.1],
    [0.2, 0.8, 0.9, 0.2, 0.1],
    [0.1, 0.7, 0.8, 0.1, 0.2],
    [0.3, 0.1, 0.2, 0.9, 0.8],
    [0.2, 0.2, 0.1, 0.8, 0.9]
]

print("🧪 测试新的热力图排序算法...")
print(f"原始矩阵 (5x5):")
for row in test_matrix:
    print("  ", [f"{x:.1f}" for x in row])

# 导入并测试算法
try:
    from heatmap_reordering_algorithm import HeatmapReorderingAlgorithm

    algo = HeatmapReorderingAlgorithm()
    print(f"\n✅ 算法模块加载成功")
    print(f"   使用NumPy: {algo.use_numpy}")

    # 测试排序
    reordered_matrix, row_order, col_order, row_names, col_names = algo.reorder_matrix(test_matrix, method='hybrid')

    print(f"\n📊 排序结果:")
    print(f"   行顺序: {row_order}")
    print(f"   列顺序: {col_order}")

    # 计算聚类得分（如果可用）
    # score = algo.calculate_clustering_score(test_matrix, row_order, col_order)
    # print(f"   聚类得分: {score:.3f}")

    # 显示重排序后的矩阵
    print(f"\n重排序后的矩阵:")
    for i in row_order:
        reordered_row = [test_matrix[i][j] for j in col_order]
        print("  ", [f"{x:.1f}" for x in reordered_row])

    print("\n✅ 测试成功！新算法正常工作")

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()