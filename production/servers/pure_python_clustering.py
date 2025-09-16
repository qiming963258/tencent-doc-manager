#!/usr/bin/env python3
"""
纯Python实现的热力图聚类算法
不依赖numpy/scipy，使用标准库实现
"""

from typing import List, Tuple
import math
import random


class PurePythonClustering:
    """纯Python实现的聚类算法"""

    def __init__(self):
        self.distance_cache = {}

    def euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算欧氏距离"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))

    def correlation_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算相关性距离（1 - 相关系数）"""
        n = len(vec1)
        if n == 0:
            return 1.0

        # 计算均值
        mean1 = sum(vec1) / n
        mean2 = sum(vec2) / n

        # 计算相关系数
        numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(vec1, vec2))
        denominator1 = math.sqrt(sum((v - mean1) ** 2 for v in vec1))
        denominator2 = math.sqrt(sum((v - mean2) ** 2 for v in vec2))

        if denominator1 == 0 or denominator2 == 0:
            return 1.0

        correlation = numerator / (denominator1 * denominator2)
        # 转换为距离（0表示完全相关，2表示完全负相关）
        return 1 - correlation

    def find_similar_pairs(self, vectors: List[List[float]], use_correlation: bool = True) -> List[Tuple[int, int, float]]:
        """找到最相似的向量对"""
        pairs = []
        n = len(vectors)

        for i in range(n):
            for j in range(i + 1, n):
                if use_correlation:
                    dist = self.correlation_distance(vectors[i], vectors[j])
                else:
                    dist = self.euclidean_distance(vectors[i], vectors[j])
                pairs.append((i, j, dist))

        # 按距离排序
        pairs.sort(key=lambda x: x[2])
        return pairs

    def hierarchical_clustering(self, vectors: List[List[float]]) -> List[int]:
        """
        简化的层次聚类
        返回重排序的索引
        """
        n = len(vectors)
        if n <= 1:
            return list(range(n))

        # 初始化：每个向量是一个簇
        clusters = [[i] for i in range(n)]
        cluster_vectors = [vectors[i][:] for i in range(n)]

        # 聚类过程
        while len(clusters) > 1:
            # 找到最相似的两个簇
            min_dist = float('inf')
            merge_i, merge_j = 0, 1

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    dist = self.correlation_distance(cluster_vectors[i], cluster_vectors[j])
                    if dist < min_dist:
                        min_dist = dist
                        merge_i, merge_j = i, j

            # 合并簇
            new_cluster = clusters[merge_i] + clusters[merge_j]

            # 计算新簇的中心（平均向量）
            new_vector = []
            for k in range(len(cluster_vectors[0])):
                avg = (cluster_vectors[merge_i][k] * len(clusters[merge_i]) +
                       cluster_vectors[merge_j][k] * len(clusters[merge_j])) / len(new_cluster)
                new_vector.append(avg)

            # 更新簇列表（删除旧的，添加新的）
            clusters = [c for idx, c in enumerate(clusters) if idx not in (merge_i, merge_j)]
            clusters.append(new_cluster)

            cluster_vectors = [v for idx, v in enumerate(cluster_vectors) if idx not in (merge_i, merge_j)]
            cluster_vectors.append(new_vector)

        # 返回最终的顺序
        return clusters[0] if clusters else list(range(n))

    def smooth_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算平滑距离，考虑值的连续性"""
        # 组合相关性和欧氏距离，更重视平滑过渡
        corr_dist = self.correlation_distance(vec1, vec2)

        # 计算值变化的平滑度（相邻值的差异）
        smoothness = 0
        for i in range(len(vec1) - 1):
            smoothness += abs((vec1[i+1] - vec1[i]) - (vec2[i+1] - vec2[i]))
        smoothness = smoothness / (len(vec1) - 1) if len(vec1) > 1 else 0

        # 组合距离，更重视相关性
        return corr_dist * 0.7 + smoothness * 0.3

    def calculate_continuity_score(self, vectors: List[List[float]], order: List[int]) -> float:
        """计算排序的连续性得分（越低越好）"""
        if len(order) <= 1:
            return 0.0

        total_distance = 0
        for i in range(len(order) - 1):
            dist = self.smooth_distance(vectors[order[i]], vectors[order[i+1]])
            total_distance += dist

        return total_distance

    def two_opt_improve(self, vectors: List[List[float]], order: List[int]) -> List[int]:
        """使用2-opt算法改善排序，增强连续性"""
        improved = order[:]
        n = len(improved)
        improvement = True

        while improvement:
            improvement = False
            best_score = self.calculate_continuity_score(vectors, improved)

            for i in range(n - 1):
                for j in range(i + 2, min(i + 10, n)):  # 限制搜索范围提高效率
                    # 尝试反转i到j之间的顺序
                    new_order = improved[:i] + improved[i:j][::-1] + improved[j:]
                    new_score = self.calculate_continuity_score(vectors, new_order)

                    if new_score < best_score:
                        improved = new_order
                        best_score = new_score
                        improvement = True
                        break
                if improvement:
                    break

        return improved

    def simulated_annealing_order(self, vectors: List[List[float]], initial_order: List[int] = None, iterations: int = 1000) -> List[int]:
        """使用模拟退火算法优化排序，创建更平滑的过渡"""
        n = len(vectors)
        if n <= 1:
            return list(range(n))

        # 初始化
        if initial_order is None:
            # 使用贪心算法的结果作为初始解
            initial_order = self.reorder_by_similarity_greedy(vectors)

        current_order = initial_order[:]
        best_order = current_order[:]
        current_score = self.calculate_continuity_score(vectors, current_order)
        best_score = current_score

        # 温度参数
        temperature = 1.0
        cooling_rate = 0.995
        min_temperature = 0.01

        for iteration in range(iterations):
            if temperature < min_temperature:
                break

            # 生成邻域解（交换两个位置或反转一小段）
            new_order = current_order[:]

            if random.random() < 0.5:
                # 交换两个随机位置
                i, j = random.sample(range(n), 2)
                new_order[i], new_order[j] = new_order[j], new_order[i]
            else:
                # 反转一小段
                i = random.randint(0, n - 2)
                j = min(i + random.randint(2, 5), n)
                new_order[i:j] = new_order[i:j][::-1]

            # 计算新解的得分
            new_score = self.calculate_continuity_score(vectors, new_order)

            # 决定是否接受新解
            delta = new_score - current_score
            if delta < 0 or random.random() < math.exp(-delta / temperature):
                current_order = new_order
                current_score = new_score

                if new_score < best_score:
                    best_order = new_order[:]
                    best_score = new_score

            # 降温
            temperature *= cooling_rate

        # 最后用2-opt进一步优化
        best_order = self.two_opt_improve(vectors, best_order)

        return best_order

    def reorder_by_similarity_greedy(self, vectors: List[List[float]]) -> List[int]:
        """原始的贪心重排序算法（作为初始解）"""
        n = len(vectors)
        if n <= 1:
            return list(range(n))

        # 计算每个向量的总热度
        heat_scores = [sum(v) for v in vectors]

        # 从热度最高的开始
        remaining = set(range(n))
        ordered = []

        # 选择起始点（热度最高）
        start_idx = max(remaining, key=lambda i: heat_scores[i])
        ordered.append(start_idx)
        remaining.remove(start_idx)

        # 贪心添加最相似的向量
        while remaining:
            last_vec = vectors[ordered[-1]]
            best_idx = None
            best_dist = float('inf')

            for idx in remaining:
                dist = self.smooth_distance(last_vec, vectors[idx])
                if dist < best_dist:
                    best_dist = dist
                    best_idx = idx

            ordered.append(best_idx)
            remaining.remove(best_idx)

        return ordered

    def reorder_by_similarity(self, vectors: List[List[float]]) -> List[int]:
        """
        增强的重排序算法，使用模拟退火优化连续性
        """
        # 先用贪心算法获得初始解
        initial_order = self.reorder_by_similarity_greedy(vectors)

        # 使用模拟退火优化
        optimized_order = self.simulated_annealing_order(vectors, initial_order, iterations=500)

        return optimized_order

    def cluster_heatmap(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        对热力图矩阵进行双向聚类
        返回：(行顺序, 列顺序)
        """
        if not matrix or not matrix[0]:
            return [], []

        n_rows = len(matrix)
        n_cols = len(matrix[0])

        # 1. 对列进行聚类（转置矩阵）
        col_vectors = []
        for j in range(n_cols):
            col_vec = [matrix[i][j] for i in range(n_rows)]
            col_vectors.append(col_vec)

        col_order = self.reorder_by_similarity(col_vectors)

        # 2. 根据列顺序重排矩阵
        reordered_matrix = []
        for row in matrix:
            reordered_row = [row[j] for j in col_order]
            reordered_matrix.append(reordered_row)

        # 3. 对行进行聚类
        row_order = self.reorder_by_similarity(reordered_matrix)

        return row_order, col_order

    def group_by_heat_level(self, vectors: List[List[float]]) -> List[List[int]]:
        """按热度级别分组 - 使用自适应阈值"""
        n = len(vectors)
        if n <= 1:
            return [list(range(n))]

        # 计算每个向量的平均热度
        heat_levels = [(i, sum(v) / len(v)) for i, v in enumerate(vectors)]

        # 按热度排序
        heat_levels.sort(key=lambda x: x[1], reverse=True)

        # 计算热度差异，找到自然断点
        diffs = []
        for i in range(1, len(heat_levels)):
            diff = heat_levels[i-1][1] - heat_levels[i][1]
            diffs.append((i, diff))

        # 找到最大的几个差异作为分组边界
        diffs.sort(key=lambda x: x[1], reverse=True)

        # 使用前2-3个最大差异作为分组边界（最多分4组）
        split_points = []
        avg_diff = sum(d[1] for d in diffs) / len(diffs) if diffs else 0

        for idx, diff in diffs[:3]:  # 最多取3个分割点
            if diff > avg_diff * 1.5:  # 差异要显著大于平均值
                split_points.append(idx)

        split_points.sort()

        # 根据分割点创建组
        groups = []
        start = 0

        for split in split_points:
            group = [heat_levels[i][0] for i in range(start, split)]
            if group:
                groups.append(group)
            start = split

        # 添加最后一组
        if start < len(heat_levels):
            group = [heat_levels[i][0] for i in range(start, len(heat_levels))]
            if group:
                groups.append(group)

        # 如果没有找到明显的分组，至少分成高中低三组
        if len(groups) <= 1:
            third = len(heat_levels) // 3
            groups = []
            groups.append([heat_levels[i][0] for i in range(third)])
            groups.append([heat_levels[i][0] for i in range(third, 2*third)])
            groups.append([heat_levels[i][0] for i in range(2*third, len(heat_levels))])
            groups = [g for g in groups if g]  # 移除空组

        return groups

    def hierarchical_reorder(self, vectors: List[List[float]]) -> List[int]:
        """分层重排序：先分组，再组内优化"""
        # 1. 按热度级别分组
        groups = self.group_by_heat_level(vectors)

        print(f"  - 检测到 {len(groups)} 个热度层级")
        for i, group in enumerate(groups):
            avg_heat = sum(sum(vectors[idx]) / len(vectors[idx]) for idx in group) / len(group)
            print(f"    层级{i+1}: {len(group)}个项目, 平均热度{avg_heat:.2f}")

        # 2. 对每个组内的向量进行相似性优化
        ordered = []
        for group in groups:
            if len(group) <= 1:
                ordered.extend(group)
            else:
                # 获取组内向量
                group_vectors = [vectors[i] for i in group]

                # 组内优化排序
                group_order = self.simulated_annealing_order(group_vectors, iterations=200)

                # 映射回原始索引
                ordered.extend([group[i] for i in group_order])

        return ordered

    def optimize_block_diagonal(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        优化块对角结构 - 使用分层聚类
        确保相似热度的块聚集在一起
        """
        n_rows = len(matrix)
        n_cols = len(matrix[0]) if matrix else 0

        # 1. 对列进行分层聚类
        col_vectors = []
        for j in range(n_cols):
            col_vec = [matrix[i][j] for i in range(n_rows)]
            col_vectors.append(col_vec)

        print("📊 列聚类分析:")
        col_order = self.hierarchical_reorder(col_vectors)

        # 2. 根据列顺序重排矩阵
        reordered_matrix = []
        for row in matrix:
            reordered_row = [row[j] for j in col_order]
            reordered_matrix.append(reordered_row)

        # 3. 对行进行分层聚类
        print("📊 行聚类分析:")
        row_order = self.hierarchical_reorder(reordered_matrix)

        # 4. 检查不同方向，选择最优
        configurations = [
            (row_order, col_order),
            (row_order[::-1], col_order),
            (row_order, col_order[::-1]),
            (row_order[::-1], col_order[::-1])
        ]

        best_score = -1
        best_config = configurations[0]

        for r_order, c_order in configurations:
            # 计算热块聚集度
            score = 0

            # 检查高热度区域的聚集程度
            for i in range(min(n_rows // 2, len(r_order))):
                for j in range(min(n_cols // 2, len(c_order))):
                    value = matrix[r_order[i]][c_order[j]]
                    # 高热度值权重更高
                    if value > 0.7:
                        score += value * 3
                    elif value > 0.5:
                        score += value * 2
                    else:
                        score += value

            if score > best_score:
                best_score = score
                best_config = (r_order, c_order)

        return best_config


def apply_pure_clustering(heatmap_data: List[List[float]],
                         table_names: List[str],
                         column_names: List[str]) -> Tuple[List[List[float]], List[str], List[str], List[int], List[int]]:
    """
    应用纯Python聚类算法

    参数：
        heatmap_data: 热力图矩阵
        table_names: 表格名称列表
        column_names: 列名列表

    返回：
        (聚类后的矩阵, 重排的表格名, 重排的列名, 行顺序, 列顺序)
    """
    clustering = PurePythonClustering()

    # 执行聚类
    row_order, col_order = clustering.optimize_block_diagonal(heatmap_data)

    # 应用重排序
    clustered_matrix = []
    reordered_table_names = []

    for row_idx in row_order:
        reordered_row = [heatmap_data[row_idx][col_idx] for col_idx in col_order]
        clustered_matrix.append(reordered_row)
        reordered_table_names.append(table_names[row_idx])

    reordered_column_names = [column_names[i] for i in col_order]

    print(f"✅ 纯Python增强聚类完成:")
    print(f"  - 使用模拟退火算法优化连续性")
    print(f"  - 行顺序: {row_order[:5]}... -> {row_order[-5:]}")
    print(f"  - 列顺序: {col_order[:5]}... -> {col_order[-5:]}")

    # 计算聚类改善度
    improvement = calculate_improvement(heatmap_data, clustered_matrix)
    continuity_improvement = calculate_continuity_improvement(heatmap_data, clustered_matrix)
    print(f"  - 块对角性改善: {improvement:.1f}%")
    print(f"  - 连续性改善: {continuity_improvement:.1f}%")

    return clustered_matrix, reordered_table_names, reordered_column_names, row_order, col_order


def calculate_improvement(original: List[List[float]], clustered: List[List[float]]) -> float:
    """计算聚类改善程度"""
    if not original or not original[0]:
        return 0.0

    def diagonal_score(matrix):
        score = 0
        min_dim = min(len(matrix), len(matrix[0]))
        for i in range(min_dim):
            for j in range(min_dim):
                if abs(i - j) <= 1:  # 对角线附近
                    score += matrix[i][j] * (2 - abs(i - j))
        return score

    original_score = diagonal_score(original)
    clustered_score = diagonal_score(clustered)

    if original_score == 0:
        return 0.0

    return (clustered_score - original_score) / original_score * 100


def calculate_continuity_improvement(original: List[List[float]], clustered: List[List[float]]) -> float:
    """计算连续性改善程度（相邻行/列的相似度）"""
    if not original or not original[0] or len(original) < 2:
        return 0.0

    def continuity_score(matrix):
        """计算矩阵的连续性得分（越低越好）"""
        score = 0
        n_rows = len(matrix)
        n_cols = len(matrix[0]) if matrix else 0

        # 计算相邻行的差异
        for i in range(n_rows - 1):
            for j in range(n_cols):
                score += abs(matrix[i][j] - matrix[i+1][j])

        # 计算相邻列的差异
        for i in range(n_rows):
            for j in range(n_cols - 1):
                score += abs(matrix[i][j] - matrix[i][j+1])

        return score

    original_score = continuity_score(original)
    clustered_score = continuity_score(clustered)

    if original_score == 0:
        return 0.0

    # 连续性得分越低越好，所以改善是负向的
    return (original_score - clustered_score) / original_score * 100