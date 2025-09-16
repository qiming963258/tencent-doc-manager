#!/usr/bin/env python3
"""
综合评分热力图聚类优化模块
使用真正的聚类算法替代简单排序
"""

import numpy as np
from typing import List, Tuple
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform


class ComprehensiveHeatmapClustering:
    """综合评分热力图聚类算法"""

    def __init__(self):
        self.method = 'ward'  # 层次聚类方法
        self.metric = 'euclidean'  # 距离度量

    def cluster_columns(self, matrix: List[List[float]]) -> List[int]:
        """
        对列进行聚类，返回重排序的列索引
        使用层次聚类将相似的列聚集在一起
        """
        if not matrix or not matrix[0]:
            return list(range(len(matrix[0]) if matrix else 0))

        # 转换为numpy数组
        data = np.array(matrix)
        n_cols = data.shape[1]

        # 转置矩阵以便对列进行聚类
        col_data = data.T

        # 计算列之间的距离矩阵
        try:
            # 使用层次聚类
            linkage_matrix = linkage(col_data, method=self.method, metric=self.metric)

            # 获取聚类顺序
            col_order = self._get_cluster_order(linkage_matrix, n_cols)

            return col_order

        except Exception as e:
            print(f"⚠️ 列聚类失败: {e}，使用热度排序")
            # 失败时使用基于热度的排序
            col_scores = [sum(col) for col in col_data]
            return sorted(range(n_cols), key=lambda x: col_scores[x], reverse=True)

    def cluster_rows(self, matrix: List[List[float]]) -> List[int]:
        """
        对行进行聚类，返回重排序的行索引
        使用层次聚类将相似的行聚集在一起
        """
        if not matrix:
            return []

        # 转换为numpy数组
        data = np.array(matrix)
        n_rows = data.shape[0]

        try:
            # 使用层次聚类
            linkage_matrix = linkage(data, method=self.method, metric=self.metric)

            # 获取聚类顺序
            row_order = self._get_cluster_order(linkage_matrix, n_rows)

            return row_order

        except Exception as e:
            print(f"⚠️ 行聚类失败: {e}，使用密度排序")
            # 失败时使用基于密度的排序
            row_scores = [sum(row) for row in data]
            return sorted(range(n_rows), key=lambda x: row_scores[x], reverse=True)

    def _get_cluster_order(self, linkage_matrix: np.ndarray, n_items: int) -> List[int]:
        """
        从层次聚类链接矩阵中提取最优排序
        """
        # 初始化叶节点顺序
        order = []

        def get_leaves(node_id):
            """递归获取叶节点"""
            if node_id < n_items:
                return [node_id]
            else:
                # 内部节点
                idx = int(node_id - n_items)
                left = int(linkage_matrix[idx, 0])
                right = int(linkage_matrix[idx, 1])
                return get_leaves(left) + get_leaves(right)

        # 从根节点开始
        if len(linkage_matrix) > 0:
            root = int(linkage_matrix[-1, 0]), int(linkage_matrix[-1, 1])
            order = get_leaves(root[0]) + get_leaves(root[1])
        else:
            order = list(range(n_items))

        return order

    def biclustering(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        双向聚类：同时对行和列进行聚类
        返回：(行排序索引, 列排序索引)
        """
        # 先对列聚类
        col_order = self.cluster_columns(matrix)

        # 根据列顺序重排矩阵
        reordered_matrix = []
        for row in matrix:
            reordered_row = [row[i] for i in col_order]
            reordered_matrix.append(reordered_row)

        # 对重排后的矩阵进行行聚类
        row_order = self.cluster_rows(reordered_matrix)

        return row_order, col_order

    def optimize_block_diagonal(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        优化块对角结构，最大化热点聚集
        """
        # 使用双向聚类
        row_order, col_order = self.biclustering(matrix)

        # 进一步优化：将高热度块移到左上角
        data = np.array(matrix)

        # 计算重排后每个块的平均热度
        block_size = 3  # 块大小
        n_rows, n_cols = len(row_order), len(col_order)

        best_score = -1
        best_row_order = row_order
        best_col_order = col_order

        # 尝试不同的块排列
        for row_flip in [False, True]:
            for col_flip in [False, True]:
                test_row_order = row_order[::-1] if row_flip else row_order
                test_col_order = col_order[::-1] if col_flip else col_order

                # 计算左上角的热度得分
                score = 0
                for i in range(min(block_size, n_rows)):
                    for j in range(min(block_size, n_cols)):
                        r_idx = test_row_order[i]
                        c_idx = test_col_order[j]
                        # 左上角权重更高
                        weight = (block_size - i) * (block_size - j)
                        score += data[r_idx, c_idx] * weight

                if score > best_score:
                    best_score = score
                    best_row_order = test_row_order
                    best_col_order = test_col_order

        return best_row_order, best_col_order


def apply_comprehensive_clustering(heatmap_data: List[List[float]],
                                  table_names: List[str],
                                  column_names: List[str]) -> Tuple[List[List[float]], List[str], List[str], List[int], List[int]]:
    """
    应用综合聚类算法到热力图数据

    参数：
        heatmap_data: 原始热力图矩阵
        table_names: 表格名称列表
        column_names: 列名列表

    返回：
        (聚类后的矩阵, 重排的表格名, 重排的列名, 行顺序, 列顺序)
    """
    clustering = ComprehensiveHeatmapClustering()

    # 执行优化的块对角聚类
    row_order, col_order = clustering.optimize_block_diagonal(heatmap_data)

    # 应用重排序
    clustered_matrix = []
    reordered_table_names = []

    for row_idx in row_order:
        reordered_row = [heatmap_data[row_idx][col_idx] for col_idx in col_order]
        clustered_matrix.append(reordered_row)
        reordered_table_names.append(table_names[row_idx])

    reordered_column_names = [column_names[i] for i in col_order]

    # 打印聚类统计
    print(f"✅ 综合聚类完成:")
    print(f"  - 行重排序: {row_order[:5]}...")
    print(f"  - 列重排序: {col_order[:5]}...")

    # 计算聚类质量
    quality_score = calculate_clustering_quality(clustered_matrix)
    print(f"  - 聚类质量得分: {quality_score:.2f}")

    return clustered_matrix, reordered_table_names, reordered_column_names, row_order, col_order


def calculate_clustering_quality(matrix: List[List[float]]) -> float:
    """
    计算聚类质量得分（块对角性）
    得分越高，热点聚集效果越好
    """
    if not matrix or not matrix[0]:
        return 0.0

    data = np.array(matrix)
    n_rows, n_cols = data.shape

    # 计算块对角得分
    total_heat = np.sum(data)
    if total_heat == 0:
        return 0.0

    # 计算对角块的热度（左上角到右下角）
    diagonal_heat = 0
    block_size = min(n_rows, n_cols) // 3  # 分成3个块

    for i in range(3):
        start_row = i * block_size
        end_row = min((i + 1) * block_size, n_rows)
        start_col = i * block_size
        end_col = min((i + 1) * block_size, n_cols)

        if start_row < n_rows and start_col < n_cols:
            block = data[start_row:end_row, start_col:end_col]
            diagonal_heat += np.sum(block)

    # 质量得分 = 对角块热度 / 总热度
    quality = diagonal_heat / total_heat * 100

    return quality