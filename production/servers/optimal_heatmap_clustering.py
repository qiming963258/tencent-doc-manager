#!/usr/bin/env python3
"""
终极热力图聚类算法
专门为最大化热团聚集而设计
"""

from typing import List, Tuple
import math
import random

class OptimalHeatmapClustering:
    """
    最优热力图聚类算法
    综合多种技术实现最佳热团聚集
    """

    def __init__(self):
        self.threshold = 0.5  # 判定为"高值"的阈值

    def optimal_reorder(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        最优重排序算法 - 专为热团聚集设计

        核心思想：
        1. 识别高值区域
        2. 计算行列的"热度签名"
        3. 使用多级排序策略
        4. 局部优化调整
        """
        if not matrix or not matrix[0]:
            return list(range(len(matrix))), list(range(len(matrix[0]) if matrix else 0))

        rows, cols = len(matrix), len(matrix[0])

        # 步骤1: 计算每行每列的热度签名
        row_signatures = self._compute_row_signatures(matrix)
        col_signatures = self._compute_col_signatures(matrix)

        # 步骤2: 聚类相似的行和列
        row_clusters = self._cluster_by_signature(row_signatures)
        col_clusters = self._cluster_by_signature(col_signatures)

        # 步骤3: 对每个聚类内部进行优化排序
        row_order = self._optimize_cluster_order(matrix, row_clusters, 'row')
        col_order = self._optimize_cluster_order(matrix, col_clusters, 'col')

        # 步骤4: 块对角化优化
        row_order, col_order = self._block_diagonal_optimization(matrix, row_order, col_order)

        # 步骤5: 最终的局部搜索优化
        row_order = self._final_local_search(matrix, row_order, 'row')
        col_order = self._final_local_search(matrix, col_order, 'col')

        return row_order, col_order

    def _compute_row_signatures(self, matrix: List[List[float]]) -> List[Tuple]:
        """计算每行的热度签名"""
        signatures = []
        for i, row in enumerate(matrix):
            # 多维签名：(平均值, 最大值, 高值数量, 热度模式)
            avg_val = sum(row) / len(row)
            max_val = max(row)
            high_count = sum(1 for v in row if v >= self.threshold)

            # 热度模式：将行分成几段，记录每段的平均值
            segments = 4
            seg_size = len(row) // segments
            pattern = []
            for s in range(segments):
                start = s * seg_size
                end = start + seg_size if s < segments - 1 else len(row)
                seg_avg = sum(row[start:end]) / (end - start) if end > start else 0
                pattern.append(seg_avg)

            signatures.append((i, avg_val, max_val, high_count, tuple(pattern)))

        return signatures

    def _compute_col_signatures(self, matrix: List[List[float]]) -> List[Tuple]:
        """计算每列的热度签名"""
        signatures = []
        cols = len(matrix[0])

        for j in range(cols):
            col = [matrix[i][j] for i in range(len(matrix))]
            avg_val = sum(col) / len(col)
            max_val = max(col)
            high_count = sum(1 for v in col if v >= self.threshold)

            # 热度模式
            segments = 4
            seg_size = len(col) // segments
            pattern = []
            for s in range(segments):
                start = s * seg_size
                end = start + seg_size if s < segments - 1 else len(col)
                seg_avg = sum(col[start:end]) / (end - start) if end > start else 0
                pattern.append(seg_avg)

            signatures.append((j, avg_val, max_val, high_count, tuple(pattern)))

        return signatures

    def _cluster_by_signature(self, signatures: List[Tuple]) -> List[List[int]]:
        """基于签名进行聚类"""
        # 按照多级标准排序：先按高值数量，再按平均值，最后按模式相似性
        sorted_sigs = sorted(signatures, key=lambda x: (x[3], x[1], x[2]), reverse=True)

        clusters = []
        used = set()

        for sig in sorted_sigs:
            idx = sig[0]
            if idx in used:
                continue

            # 创建新聚类
            cluster = [idx]
            used.add(idx)

            # 寻找相似的项加入聚类
            for other_sig in sorted_sigs:
                other_idx = other_sig[0]
                if other_idx not in used:
                    # 计算相似度
                    similarity = self._signature_similarity(sig, other_sig)
                    if similarity > 0.7:  # 相似度阈值
                        cluster.append(other_idx)
                        used.add(other_idx)

            clusters.append(cluster)

        # 添加未聚类的项
        for sig in signatures:
            if sig[0] not in used:
                clusters.append([sig[0]])

        return clusters

    def _signature_similarity(self, sig1: Tuple, sig2: Tuple) -> float:
        """计算两个签名的相似度"""
        # 基于多个维度计算相似度
        avg_sim = 1 - abs(sig1[1] - sig2[1])
        max_sim = 1 - abs(sig1[2] - sig2[2])
        count_sim = 1 - abs(sig1[3] - sig2[3]) / max(sig1[3], sig2[3], 1)

        # 模式相似度（余弦相似度）
        pattern1, pattern2 = sig1[4], sig2[4]
        dot_product = sum(p1 * p2 for p1, p2 in zip(pattern1, pattern2))
        norm1 = math.sqrt(sum(p * p for p in pattern1))
        norm2 = math.sqrt(sum(p * p for p in pattern2))
        pattern_sim = dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0

        # 加权平均
        similarity = 0.2 * avg_sim + 0.2 * max_sim + 0.3 * count_sim + 0.3 * pattern_sim
        return similarity

    def _optimize_cluster_order(self, matrix: List[List[float]], clusters: List[List[int]], axis: str) -> List[int]:
        """优化每个聚类内部的顺序"""
        optimized_order = []

        for cluster in clusters:
            if len(cluster) <= 1:
                optimized_order.extend(cluster)
                continue

            # 在聚类内部，按照与其他成员的相似度排序
            if axis == 'row':
                # 计算行之间的相似度矩阵
                similarity_scores = []
                for i in cluster:
                    score = 0
                    for j in cluster:
                        if i != j:
                            score += self._row_similarity(matrix, i, j)
                    similarity_scores.append((i, score))

                # 按相似度总分排序
                similarity_scores.sort(key=lambda x: x[1], reverse=True)
                cluster_order = [x[0] for x in similarity_scores]
            else:
                # 列的处理类似
                similarity_scores = []
                for i in cluster:
                    score = 0
                    for j in cluster:
                        if i != j:
                            score += self._col_similarity(matrix, i, j)
                    similarity_scores.append((i, score))

                similarity_scores.sort(key=lambda x: x[1], reverse=True)
                cluster_order = [x[0] for x in similarity_scores]

            optimized_order.extend(cluster_order)

        return optimized_order

    def _row_similarity(self, matrix: List[List[float]], i: int, j: int) -> float:
        """计算两行的相似度"""
        row1 = matrix[i]
        row2 = matrix[j]

        # 使用多种相似度度量
        # 1. 点积（强调共同的高值位置）
        dot_product = sum(a * b for a, b in zip(row1, row2))

        # 2. 重叠度（高值位置的重叠）
        overlap = sum(1 for a, b in zip(row1, row2)
                     if a >= self.threshold and b >= self.threshold)

        # 3. 距离的倒数
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(row1, row2)))
        distance_sim = 1 / (1 + distance)

        # 综合相似度
        similarity = dot_product + 0.5 * overlap + 0.3 * distance_sim
        return similarity

    def _col_similarity(self, matrix: List[List[float]], i: int, j: int) -> float:
        """计算两列的相似度"""
        col1 = [matrix[row][i] for row in range(len(matrix))]
        col2 = [matrix[row][j] for row in range(len(matrix))]

        dot_product = sum(a * b for a, b in zip(col1, col2))
        overlap = sum(1 for a, b in zip(col1, col2)
                     if a >= self.threshold and b >= self.threshold)
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(col1, col2)))
        distance_sim = 1 / (1 + distance)

        similarity = dot_product + 0.5 * overlap + 0.3 * distance_sim
        return similarity

    def _block_diagonal_optimization(self, matrix: List[List[float]],
                                    row_order: List[int], col_order: List[int]) -> Tuple[List[int], List[int]]:
        """块对角化优化 - 识别并强化块结构"""
        rows, cols = len(matrix), len(matrix[0])

        # 识别高密度块
        blocks = []
        block_size = 5  # 尝试找5x5的块

        for r_start in range(0, rows - block_size + 1, block_size // 2):
            for c_start in range(0, cols - block_size + 1, block_size // 2):
                # 计算块的平均密度
                block_sum = 0
                block_rows = row_order[r_start:r_start + block_size]
                block_cols = col_order[c_start:c_start + block_size]

                for r in block_rows:
                    for c in block_cols:
                        block_sum += matrix[r][c]

                block_density = block_sum / (block_size * block_size)

                if block_density >= self.threshold:
                    blocks.append((block_density, r_start, c_start, block_rows, block_cols))

        # 按密度排序块
        blocks.sort(reverse=True)

        # 重新排列以强化块结构
        if blocks:
            new_row_order = []
            new_col_order = []
            used_rows = set()
            used_cols = set()

            for _, _, _, block_rows, block_cols in blocks:
                for r in block_rows:
                    if r not in used_rows:
                        new_row_order.append(r)
                        used_rows.add(r)

                for c in block_cols:
                    if c not in used_cols:
                        new_col_order.append(c)
                        used_cols.add(c)

            # 添加未使用的行列
            for r in row_order:
                if r not in used_rows:
                    new_row_order.append(r)

            for c in col_order:
                if c not in used_cols:
                    new_col_order.append(c)

            return new_row_order, new_col_order

        return row_order, col_order

    def _final_local_search(self, matrix: List[List[float]], order: List[int], axis: str) -> List[int]:
        """最终的局部搜索优化"""
        improved = True
        iterations = 0
        max_iterations = 100

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            # 尝试交换相邻元素
            for i in range(len(order) - 1):
                # 计算当前配置的得分
                current_score = self._local_score(matrix, order, i, i + 1, axis)

                # 尝试交换
                order[i], order[i + 1] = order[i + 1], order[i]
                new_score = self._local_score(matrix, order, i, i + 1, axis)

                if new_score > current_score:
                    # 保持交换
                    improved = True
                else:
                    # 撤销交换
                    order[i], order[i + 1] = order[i + 1], order[i]

            # 也尝试较远的交换
            if not improved and iterations < max_iterations // 2:
                for _ in range(5):  # 尝试5次随机交换
                    if len(order) > 3:
                        i = random.randint(0, len(order) - 3)
                        j = random.randint(i + 2, len(order) - 1)

                        current_score = self._global_score(matrix, order, axis)
                        order[i], order[j] = order[j], order[i]
                        new_score = self._global_score(matrix, order, axis)

                        if new_score > current_score:
                            improved = True
                            break
                        else:
                            order[i], order[j] = order[j], order[i]

        return order

    def _local_score(self, matrix: List[List[float]], order: List[int], i: int, j: int, axis: str) -> float:
        """计算局部区域的聚类得分"""
        score = 0.0

        if axis == 'row':
            r1, r2 = order[i], order[j]
            for c in range(len(matrix[0])):
                # 相邻行的高值应该在相同列
                score += matrix[r1][c] * matrix[r2][c]
        else:
            c1, c2 = order[i], order[j]
            for r in range(len(matrix)):
                score += matrix[r][c1] * matrix[r][c2]

        return score

    def _global_score(self, matrix: List[List[float]], order: List[int], axis: str) -> float:
        """计算全局聚类得分"""
        score = 0.0

        if axis == 'row':
            for i in range(len(order) - 1):
                r1, r2 = order[i], order[i + 1]
                for c in range(len(matrix[0])):
                    score += matrix[r1][c] * matrix[r2][c]
        else:
            for j in range(len(order) - 1):
                c1, c2 = order[j], order[j + 1]
                for r in range(len(matrix)):
                    score += matrix[r][c1] * matrix[r][c2]

        return score


# 测试
if __name__ == "__main__":
    # 创建测试矩阵
    test_matrix = [
        [0.1, 0.2, 0.9, 0.8, 0.1],
        [0.2, 0.1, 0.8, 0.9, 0.2],
        [0.9, 0.8, 0.1, 0.2, 0.1],
        [0.8, 0.9, 0.2, 0.1, 0.2],
        [0.1, 0.2, 0.1, 0.2, 0.9]
    ]

    print("原始矩阵:")
    for row in test_matrix:
        print([f"{x:.1f}" for x in row])

    algo = OptimalHeatmapClustering()
    row_order, col_order = algo.optimal_reorder(test_matrix)

    print(f"\n优化后的排序:")
    print(f"行顺序: {row_order}")
    print(f"列顺序: {col_order}")

    print("\n重排序后的矩阵:")
    for i in row_order:
        row = [test_matrix[i][j] for j in col_order]
        print([f"{x:.1f}" for x in row])