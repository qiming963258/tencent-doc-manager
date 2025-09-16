#!/usr/bin/env python3
"""
热力图双维度重排序算法 - 最大化热团聚集
基于层次聚类、TSP和贪心算法的混合方法
"""

from typing import List, Tuple, Optional
import json
import math

# 尝试导入numpy，如果不可用则使用纯Python实现
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

class HeatmapReorderingAlgorithm:
    """
    热力图矩阵双维度重排序算法
    目标：最大化热团聚集，使高值单元格尽可能聚在一起
    """

    def __init__(self):
        self.use_numpy = NUMPY_AVAILABLE
        if not self.use_numpy:
            print("⚠️ NumPy不可用，使用纯Python实现")

    def reorder_matrix(self, matrix: List[List[float]],
                      row_names: Optional[List[str]] = None,
                      col_names: Optional[List[str]] = None,
                      method: str = 'hybrid') -> Tuple:
        """
        对热力图矩阵进行双维度重排序

        参数:
            matrix: 热力图数据矩阵
            row_names: 行名称列表
            col_names: 列名称列表
            method: 排序方法 ('hybrid', 'hierarchical', 'tsp', 'greedy', 'weighted')

        返回:
            (重排序后的矩阵, 行顺序索引, 列顺序索引, 重排序后的行名, 重排序后的列名)
        """
        if not matrix or not matrix[0]:
            return matrix, list(range(len(matrix))), list(range(len(matrix[0]) if matrix else 0)), row_names, col_names

        rows, cols = len(matrix), len(matrix[0])

        # 根据方法选择算法
        if method == 'hybrid':
            row_order, col_order = self._hybrid_reordering(matrix)
        elif method == 'hierarchical':
            row_order, col_order = self._hierarchical_clustering_reorder(matrix)
        elif method == 'tsp':
            row_order, col_order = self._tsp_seriation_reorder(matrix)
        elif method == 'greedy':
            row_order, col_order = self._greedy_reorder(matrix)
        elif method == 'weighted':
            row_order, col_order = self._weighted_score_reorder(matrix)
        else:
            # 默认使用加权评分方法
            row_order, col_order = self._weighted_score_reorder(matrix)

        # 应用重排序
        reordered_matrix = self._apply_reordering(matrix, row_order, col_order)

        # 重排序名称
        reordered_row_names = [row_names[i] for i in row_order] if row_names else None
        reordered_col_names = [col_names[j] for j in col_order] if col_names else None

        return reordered_matrix, row_order, col_order, reordered_row_names, reordered_col_names

    def _hybrid_reordering(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        混合算法：结合多种方法的优点
        1. 首先使用层次聚类获得初始分组
        2. 然后在每个组内使用TSP优化
        3. 最后用贪心算法微调
        """
        print("🔄 使用混合算法进行矩阵重排序...")

        # 步骤1: 层次聚类获得初始分组
        row_clusters, col_clusters = self._get_hierarchical_clusters(matrix)

        # 步骤2: 在每个聚类内部使用TSP优化
        row_order = self._optimize_within_clusters(matrix, row_clusters, axis=0)
        col_order = self._optimize_within_clusters(matrix, col_clusters, axis=1)

        # 步骤3: 贪心算法微调
        row_order = self._greedy_refinement(matrix, row_order, axis=0)
        col_order = self._greedy_refinement(matrix, col_order, axis=1)

        return row_order, col_order

    def _hierarchical_clustering_reorder(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        基于层次聚类的重排序（带最优叶序）
        这是scipy.cluster.hierarchy.optimal_leaf_ordering的简化实现
        """
        print("🔄 使用层次聚类算法...")

        if self.use_numpy:
            try:
                import numpy as np
                from scipy.cluster import hierarchy
                from scipy.spatial.distance import pdist, squareform

                # 计算行距离矩阵并进行层次聚类
                mat = np.array(matrix)
                row_dists = pdist(mat, metric='euclidean')
                row_linkage = hierarchy.linkage(row_dists, method='ward')
                row_order = hierarchy.leaves_list(hierarchy.optimal_leaf_ordering(row_linkage, row_dists))

                # 计算列距离矩阵并进行层次聚类
                col_dists = pdist(mat.T, metric='euclidean')
                col_linkage = hierarchy.linkage(col_dists, method='ward')
                col_order = hierarchy.leaves_list(hierarchy.optimal_leaf_ordering(col_linkage, col_dists))

                return row_order.tolist(), col_order.tolist()

            except ImportError:
                print("⚠️ SciPy不可用，回退到简化实现")

        # 简化的层次聚类实现
        return self._simple_hierarchical_clustering(matrix)

    def _tsp_seriation_reorder(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        基于TSP（旅行商问题）的序列化重排序
        目标：最小化相邻行/列之间的距离总和
        """
        print("🔄 使用TSP序列化算法...")

        rows, cols = len(matrix), len(matrix[0])

        # 行排序 - 最小化相邻行的距离
        row_order = self._tsp_solve_1d(matrix, axis=0)

        # 列排序 - 最小化相邻列的距离
        col_order = self._tsp_solve_1d(matrix, axis=1)

        return row_order, col_order

    def _greedy_reorder(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        贪心算法：每次选择与当前聚类最相似的行/列
        """
        print("🔄 使用贪心算法...")

        rows, cols = len(matrix), len(matrix[0])

        # 行排序 - 从热度最高的行开始
        row_order = self._greedy_ordering(matrix, axis=0)

        # 列排序 - 从热度最高的列开始
        col_order = self._greedy_ordering(matrix, axis=1)

        return row_order, col_order

    def _weighted_score_reorder(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        加权评分排序：结合多个指标进行排序
        - 总热度值
        - 高值单元格数量
        - 值的方差（聚集程度）
        - 与高热度邻居的相似度
        """
        print("🔄 使用加权评分算法...")

        rows, cols = len(matrix), len(matrix[0])

        # 计算行评分
        row_scores = []
        for i in range(rows):
            row = matrix[i]
            total_heat = sum(row)
            high_values = sum(1 for v in row if v > 0.6)
            variance = self._calculate_variance(row)

            # 加权评分：总热度40%，高值数量40%，方差20%
            score = total_heat * 0.4 + high_values * 0.4 + variance * 0.2
            row_scores.append((i, score))

        # 计算列评分
        col_scores = []
        for j in range(cols):
            col = [matrix[i][j] for i in range(rows)]
            total_heat = sum(col)
            high_values = sum(1 for v in col if v > 0.6)
            variance = self._calculate_variance(col)

            # 加权评分
            score = total_heat * 0.4 + high_values * 0.4 + variance * 0.2
            col_scores.append((j, score))

        # 排序并提取索引
        row_scores.sort(key=lambda x: x[1], reverse=True)
        col_scores.sort(key=lambda x: x[1], reverse=True)

        row_order = [x[0] for x in row_scores]
        col_order = [x[0] for x in col_scores]

        # 应用块聚类优化
        row_order = self._block_clustering_optimization(matrix, row_order, axis=0)
        col_order = self._block_clustering_optimization(matrix, col_order, axis=1)

        return row_order, col_order

    # ========== 辅助方法 ==========

    def _simple_hierarchical_clustering(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """简化的层次聚类实现（不依赖scipy）"""
        rows, cols = len(matrix), len(matrix[0])

        # 基于相似度的简单聚类
        row_similarities = self._calculate_similarities(matrix, axis=0)
        col_similarities = self._calculate_similarities(matrix, axis=1)

        # 使用相似度进行排序
        row_order = self._similarity_based_ordering(row_similarities)
        col_order = self._similarity_based_ordering(col_similarities)

        return row_order, col_order

    def _calculate_similarities(self, matrix: List[List[float]], axis: int) -> List[List[float]]:
        """计算行或列之间的相似度"""
        if axis == 0:  # 行相似度
            n = len(matrix)
            similarities = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    similarities[i][j] = self._cosine_similarity(matrix[i], matrix[j])
        else:  # 列相似度
            n = len(matrix[0])
            similarities = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    col_i = [matrix[row][i] for row in range(len(matrix))]
                    col_j = [matrix[row][j] for row in range(len(matrix))]
                    similarities[i][j] = self._cosine_similarity(col_i, col_j)

        return similarities

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _similarity_based_ordering(self, similarities: List[List[float]]) -> List[int]:
        """基于相似度矩阵进行排序"""
        n = len(similarities)
        visited = [False] * n
        order = []

        # 从相似度总和最高的元素开始
        total_sims = [sum(similarities[i]) for i in range(n)]
        start = total_sims.index(max(total_sims))

        order.append(start)
        visited[start] = True

        # 贪心地添加最相似的未访问元素
        while len(order) < n:
            last = order[-1]
            best_next = -1
            best_sim = -1

            for i in range(n):
                if not visited[i] and similarities[last][i] > best_sim:
                    best_sim = similarities[last][i]
                    best_next = i

            if best_next == -1:
                # 如果没有找到，选择剩余的第一个
                for i in range(n):
                    if not visited[i]:
                        best_next = i
                        break

            order.append(best_next)
            visited[best_next] = True

        return order

    def _tsp_solve_1d(self, matrix: List[List[float]], axis: int) -> List[int]:
        """解决一维TSP问题"""
        if axis == 0:  # 行
            n = len(matrix)
            distances = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    distances[i][j] = self._euclidean_distance(matrix[i], matrix[j])
        else:  # 列
            n = len(matrix[0])
            distances = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    col_i = [matrix[row][i] for row in range(len(matrix))]
                    col_j = [matrix[row][j] for row in range(len(matrix))]
                    distances[i][j] = self._euclidean_distance(col_i, col_j)

        # 使用最近邻算法解决TSP
        return self._nearest_neighbor_tsp(distances)

    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算欧氏距离"""
        return sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5

    def _nearest_neighbor_tsp(self, distances: List[List[float]]) -> List[int]:
        """最近邻TSP算法"""
        n = len(distances)
        visited = [False] * n
        path = []

        # 从第一个节点开始
        current = 0
        path.append(current)
        visited[current] = True

        while len(path) < n:
            next_node = -1
            min_dist = float('inf')

            for i in range(n):
                if not visited[i] and distances[current][i] < min_dist:
                    min_dist = distances[current][i]
                    next_node = i

            if next_node == -1:
                # 如果没有找到，选择第一个未访问的
                for i in range(n):
                    if not visited[i]:
                        next_node = i
                        break

            path.append(next_node)
            visited[next_node] = True
            current = next_node

        return path

    def _greedy_ordering(self, matrix: List[List[float]], axis: int) -> List[int]:
        """贪心排序算法"""
        if axis == 0:  # 行
            n = len(matrix)
            # 计算每行的热度
            heats = [(i, sum(matrix[i])) for i in range(n)]
        else:  # 列
            n = len(matrix[0])
            # 计算每列的热度
            heats = [(j, sum(matrix[i][j] for i in range(len(matrix)))) for j in range(n)]

        # 按热度排序
        heats.sort(key=lambda x: x[1], reverse=True)

        # 从最热的开始，贪心地构建序列
        order = []
        remaining = [x[0] for x in heats]

        if remaining:
            order.append(remaining.pop(0))

        while remaining:
            last = order[-1]
            best_next = None
            best_score = -float('inf')

            for idx in remaining:
                if axis == 0:  # 行
                    score = self._cosine_similarity(matrix[last], matrix[idx])
                else:  # 列
                    col_last = [matrix[i][last] for i in range(len(matrix))]
                    col_idx = [matrix[i][idx] for i in range(len(matrix))]
                    score = self._cosine_similarity(col_last, col_idx)

                if score > best_score:
                    best_score = score
                    best_next = idx

            if best_next is not None:
                order.append(best_next)
                remaining.remove(best_next)

        return order

    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _block_clustering_optimization(self, matrix: List[List[float]], order: List[int], axis: int) -> List[int]:
        """块聚类优化：将相似的元素聚成块"""
        # 识别高热度块
        threshold = 0.5
        blocks = []
        current_block = []

        for idx in order:
            if axis == 0:  # 行
                heat = sum(matrix[idx]) / len(matrix[idx])
            else:  # 列
                heat = sum(matrix[i][idx] for i in range(len(matrix))) / len(matrix)

            if heat > threshold:
                current_block.append(idx)
            else:
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                blocks.append([idx])

        if current_block:
            blocks.append(current_block)

        # 重组块
        optimized_order = []
        for block in blocks:
            optimized_order.extend(block)

        return optimized_order

    def _get_hierarchical_clusters(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """获取层次聚类的聚类标签"""
        rows, cols = len(matrix), len(matrix[0])

        # 简单的基于阈值的聚类
        row_clusters = []
        for i in range(rows):
            avg_heat = sum(matrix[i]) / cols
            if avg_heat > 0.6:
                row_clusters.append(0)  # 高热度聚类
            elif avg_heat > 0.3:
                row_clusters.append(1)  # 中热度聚类
            else:
                row_clusters.append(2)  # 低热度聚类

        col_clusters = []
        for j in range(cols):
            avg_heat = sum(matrix[i][j] for i in range(rows)) / rows
            if avg_heat > 0.6:
                col_clusters.append(0)
            elif avg_heat > 0.3:
                col_clusters.append(1)
            else:
                col_clusters.append(2)

        return row_clusters, col_clusters

    def _optimize_within_clusters(self, matrix: List[List[float]], clusters: List[int], axis: int) -> List[int]:
        """在每个聚类内部优化顺序"""
        # 按聚类分组
        cluster_groups = {}
        for i, cluster in enumerate(clusters):
            if cluster not in cluster_groups:
                cluster_groups[cluster] = []
            cluster_groups[cluster].append(i)

        # 对每个聚类内部进行TSP优化
        optimized_order = []
        for cluster in sorted(cluster_groups.keys()):
            group = cluster_groups[cluster]
            if len(group) > 1:
                # 在组内进行TSP优化
                group_order = self._tsp_within_group(matrix, group, axis)
                optimized_order.extend(group_order)
            else:
                optimized_order.extend(group)

        return optimized_order

    def _tsp_within_group(self, matrix: List[List[float]], group: List[int], axis: int) -> List[int]:
        """在组内进行TSP优化"""
        n = len(group)
        distances = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if axis == 0:  # 行
                    distances[i][j] = self._euclidean_distance(matrix[group[i]], matrix[group[j]])
                else:  # 列
                    col_i = [matrix[row][group[i]] for row in range(len(matrix))]
                    col_j = [matrix[row][group[j]] for row in range(len(matrix))]
                    distances[i][j] = self._euclidean_distance(col_i, col_j)

        # 解决TSP
        local_order = self._nearest_neighbor_tsp(distances)

        # 映射回原始索引
        return [group[i] for i in local_order]

    def _greedy_refinement(self, matrix: List[List[float]], order: List[int], axis: int) -> List[int]:
        """贪心算法微调"""
        # 尝试交换相邻元素以改善目标函数
        improved = True
        iterations = 0
        max_iterations = 10

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            for i in range(len(order) - 1):
                # 计算当前配置的代价
                current_cost = self._calculate_local_cost(matrix, order, i, i+1, axis)

                # 尝试交换
                order[i], order[i+1] = order[i+1], order[i]
                new_cost = self._calculate_local_cost(matrix, order, i, i+1, axis)

                if new_cost < current_cost:
                    # 保持交换
                    improved = True
                else:
                    # 撤销交换
                    order[i], order[i+1] = order[i+1], order[i]

        return order

    def _calculate_local_cost(self, matrix: List[List[float]], order: List[int], i: int, j: int, axis: int) -> float:
        """计算局部代价"""
        if axis == 0:  # 行
            return self._euclidean_distance(matrix[order[i]], matrix[order[j]])
        else:  # 列
            col_i = [matrix[row][order[i]] for row in range(len(matrix))]
            col_j = [matrix[row][order[j]] for row in range(len(matrix))]
            return self._euclidean_distance(col_i, col_j)

    def _apply_reordering(self, matrix: List[List[float]], row_order: List[int], col_order: List[int]) -> List[List[float]]:
        """应用重排序到矩阵"""
        # 首先应用行重排序
        row_reordered = [matrix[i] for i in row_order]

        # 然后应用列重排序
        final_matrix = []
        for row in row_reordered:
            reordered_row = [row[j] for j in col_order]
            final_matrix.append(reordered_row)

        return final_matrix


def test_algorithm():
    """测试算法效果"""
    # 创建测试矩阵（模拟热力图数据）
    import random

    # 创建一个有明显热团的测试矩阵
    size = 20
    matrix = [[random.random() * 0.2 for _ in range(size)] for _ in range(size)]

    # 添加几个热团
    # 热团1: (0-5, 0-5)
    for i in range(5):
        for j in range(5):
            matrix[i][j] = 0.8 + random.random() * 0.2

    # 热团2: (10-15, 10-15)
    for i in range(10, 15):
        for j in range(10, 15):
            matrix[i][j] = 0.7 + random.random() * 0.3

    # 热团3: (15-20, 5-10)
    for i in range(15, 20):
        for j in range(5, 10):
            matrix[i][j] = 0.6 + random.random() * 0.3

    print("🧪 测试热力图重排序算法")
    print(f"原始矩阵大小: {len(matrix)}x{len(matrix[0])}")

    # 测试不同方法
    reorderer = HeatmapReorderingAlgorithm()

    methods = ['weighted', 'greedy', 'tsp', 'hybrid']
    for method in methods:
        print(f"\n📊 测试方法: {method}")
        reordered, row_order, col_order, _, _ = reorderer.reorder_matrix(matrix, method=method)

        # 计算聚集度指标
        clustering_score = calculate_clustering_score(reordered)
        print(f"  聚集度评分: {clustering_score:.3f}")
        print(f"  行顺序前10: {row_order[:10]}")
        print(f"  列顺序前10: {col_order[:10]}")


def calculate_clustering_score(matrix: List[List[float]]) -> float:
    """
    计算矩阵的聚集度评分
    评分越高，热团聚集效果越好
    """
    if not matrix or not matrix[0]:
        return 0.0

    rows, cols = len(matrix), len(matrix[0])
    score = 0.0

    # 计算相邻单元格的相似度
    for i in range(rows):
        for j in range(cols):
            # 检查右邻居
            if j < cols - 1:
                score += 1.0 - abs(matrix[i][j] - matrix[i][j+1])
            # 检查下邻居
            if i < rows - 1:
                score += 1.0 - abs(matrix[i][j] - matrix[i+1][j])

    # 归一化
    max_score = (rows * (cols - 1) + cols * (rows - 1))
    return score / max_score if max_score > 0 else 0.0


if __name__ == "__main__":
    test_algorithm()