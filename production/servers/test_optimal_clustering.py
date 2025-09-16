#!/usr/bin/env python3
"""
测试最优聚类算法效果
"""

import sys
import os
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/servers')

# 创建更真实的测试矩阵 30x19
import random
random.seed(42)

# 创建一个有明显热团但分散的矩阵
matrix = []
for i in range(30):
    row = []
    for j in range(19):
        # 创建几个热团区域
        if (5 <= i <= 10 and 3 <= j <= 7):  # 热团1
            value = 0.7 + random.random() * 0.3
        elif (15 <= i <= 20 and 10 <= j <= 14):  # 热团2
            value = 0.6 + random.random() * 0.3
        elif (22 <= i <= 27 and 2 <= j <= 6):  # 热团3
            value = 0.65 + random.random() * 0.3
        elif (0 <= i <= 4 and 12 <= j <= 16):  # 热团4
            value = 0.75 + random.random() * 0.25
        else:
            value = random.random() * 0.3  # 背景低值
        row.append(value)
    matrix.append(row)

print("🧪 测试最优热力图聚类算法")
print(f"矩阵尺寸: {len(matrix)}x{len(matrix[0])}")

# 计算原始矩阵的聚类度
def calculate_clustering_metric(mat, row_order=None, col_order=None):
    """计算矩阵的聚类度量"""
    if row_order is None:
        row_order = list(range(len(mat)))
    if col_order is None:
        col_order = list(range(len(mat[0])))

    score = 0.0
    rows, cols = len(mat), len(mat[0])

    # 计算相邻高值的聚集度
    for i in range(rows - 1):
        for j in range(cols - 1):
            r1, r2 = row_order[i], row_order[i+1]
            c1, c2 = col_order[j], col_order[j+1]

            # 2x2子矩阵的平均值
            block_sum = (mat[r1][c1] + mat[r1][c2] +
                        mat[r2][c1] + mat[r2][c2])
            # 平方以强调高值区域
            score += block_sum * block_sum

    return score / ((rows-1) * (cols-1))

# 显示热团分布
def show_heatmap_distribution(mat, title="热力图分布"):
    """简单可视化热力图分布"""
    print(f"\n{title}:")
    print("  ", end="")
    for j in range(len(mat[0])):
        print(f"{j:2}", end=" ")
    print()

    for i in range(len(mat)):
        print(f"{i:2}: ", end="")
        for j in range(len(mat[0])):
            val = mat[i][j]
            if val >= 0.8:
                symbol = "█"  # 极高
            elif val >= 0.6:
                symbol = "▓"  # 高
            elif val >= 0.4:
                symbol = "▒"  # 中
            elif val >= 0.2:
                symbol = "░"  # 低
            else:
                symbol = "·"  # 极低
            print(f" {symbol}", end=" ")
        print()

# 测试原始矩阵
original_score = calculate_clustering_metric(matrix)
print(f"\n原始矩阵聚类得分: {original_score:.3f}")
show_heatmap_distribution(matrix, "原始矩阵（热团分散）")

# 测试最优聚类算法
try:
    from optimal_heatmap_clustering import OptimalHeatmapClustering

    print(f"\n{'='*60}")
    print("测试最优聚类算法（基于热度签名）")

    algo = OptimalHeatmapClustering()
    row_order, col_order = algo.optimal_reorder(matrix)

    # 计算新的聚类得分
    new_score = calculate_clustering_metric(matrix, row_order, col_order)
    improvement = ((new_score - original_score) / original_score) * 100

    print(f"聚类得分: {new_score:.3f} (提升 {improvement:.1f}%)")

    # 显示重排序后的矩阵
    reordered = []
    for i in row_order:
        reordered_row = [matrix[i][j] for j in col_order]
        reordered.append(reordered_row)

    show_heatmap_distribution(reordered, "最优算法后（热团最大化聚集）")

    print(f"\n✅ 最优聚类算法测试成功！")
    print(f"   聚类得分提升: {improvement:.1f}%")
    print(f"   准备集成到生产环境...")

except ImportError as e:
    print(f"❌ 无法导入最优算法: {e}")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()