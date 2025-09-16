#!/usr/bin/env python3
"""
终极块对角化热力图算法
基于最新的双聚类理论实现真正的块对角结构
"""

from typing import List, Tuple, Optional
import math
import random

class UltimateBlockDiagonalClustering:
    """
    终极块对角化算法
    目标：创建清晰的块对角结构，最大化热团聚集
    """

    def __init__(self, n_clusters: int = 5):
        """
        初始化
        n_clusters: 期望的块数量
        """
        self.n_clusters = n_clusters
        self.high_threshold = 0.6  # 高值阈值
        self.medium_threshold = 0.3  # 中值阈值

    def block_diagonal_reorder(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        块对角化重排序

        核心算法：
        1. 谱双聚类 (Spectral Co-clustering)
        2. 块内优化
        3. 块间排序
        """
        if not matrix or not matrix[0]:
            return list(range(len(matrix))), list(range(len(matrix[0]) if matrix else 0))

        rows, cols = len(matrix), len(matrix[0])

        # Step 1: 计算行列的双聚类分配
        print("🔄 Step 1: 执行谱双聚类...")
        row_clusters, col_clusters = self._spectral_coclustering(matrix)

        # Step 2: 创建块结构
        print("🔄 Step 2: 构建块对角结构...")
        blocks = self._create_blocks(matrix, row_clusters, col_clusters)

        # Step 3: 按块密度排序
        print("🔄 Step 3: 优化块排序...")
        sorted_blocks = self._sort_blocks_by_density(blocks)

        # Step 4: 构建最终顺序
        print("🔄 Step 4: 生成最终排序...")
        row_order, col_order = self._build_final_order(sorted_blocks)

        # Step 5: 块内局部优化
        print("🔄 Step 5: 块内精细优化...")
        row_order, col_order = self._optimize_within_blocks(
            matrix, row_order, col_order, sorted_blocks
        )

        return row_order, col_order

    def _spectral_coclustering(self, matrix: List[List[float]]) -> Tuple[List[List[int]], List[List[int]]]:
        """
        谱双聚类实现
        基于SVD分解找到双聚类结构
        """
        rows, cols = len(matrix), len(matrix[0])

        # 计算归一化矩阵 (类似于SpectralCoclustering)
        # An = D_r^(-1/2) * A * D_c^(-1/2)
        row_sums = [sum(row) for row in matrix]
        col_sums = [sum(matrix[i][j] for i in range(rows)) for j in range(cols)]

        # 归一化
        normalized = [[0.0] * cols for _ in range(rows)]
        for i in range(rows):
            for j in range(cols):
                if row_sums[i] > 0 and col_sums[j] > 0:
                    normalized[i][j] = matrix[i][j] / math.sqrt(row_sums[i] * col_sums[j])
                else:
                    normalized[i][j] = 0.0

        # 简化的谱聚类：基于相似性分组
        row_clusters = self._cluster_by_similarity(normalized, 'row')
        col_clusters = self._cluster_by_similarity(normalized, 'col')

        return row_clusters, col_clusters

    def _cluster_by_similarity(self, matrix: List[List[float]], axis: str) -> List[List[int]]:
        """
        基于相似性进行聚类
        """
        if axis == 'row':
            n_items = len(matrix)
            get_vector = lambda i: matrix[i]
        else:
            n_items = len(matrix[0])
            get_vector = lambda j: [matrix[i][j] for i in range(len(matrix))]

        # 计算相似性矩阵
        similarities = [[0.0] * n_items for _ in range(n_items)]
        for i in range(n_items):
            vec_i = get_vector(i)
            for j in range(i, n_items):
                vec_j = get_vector(j)
                sim = self._cosine_similarity(vec_i, vec_j)
                similarities[i][j] = sim
                similarities[j][i] = sim

        # K-means风格的聚类
        clusters = self._kmeans_clustering(similarities, self.n_clusters)

        return clusters

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _kmeans_clustering(self, similarity_matrix: List[List[float]], k: int) -> List[List[int]]:
        """
        简化的K-means聚类
        """
        n = len(similarity_matrix)

        # 随机初始化中心点
        centers = random.sample(range(n), min(k, n))

        # 迭代分配
        max_iterations = 20
        for _ in range(max_iterations):
            clusters = [[] for _ in range(k)]

            # 分配到最近的中心
            for i in range(n):
                best_cluster = 0
                best_sim = similarity_matrix[i][centers[0]]

                for c in range(1, k):
                    sim = similarity_matrix[i][centers[c]]
                    if sim > best_sim:
                        best_sim = sim
                        best_cluster = c

                clusters[best_cluster].append(i)

            # 更新中心点
            new_centers = []
            for cluster in clusters:
                if cluster:
                    # 选择与其他点相似度总和最大的点作为新中心
                    best_center = cluster[0]
                    best_score = sum(similarity_matrix[cluster[0]][j] for j in cluster)

                    for i in cluster[1:]:
                        score = sum(similarity_matrix[i][j] for j in cluster)
                        if score > best_score:
                            best_score = score
                            best_center = i

                    new_centers.append(best_center)
                else:
                    # 空簇，随机选择一个点
                    new_centers.append(random.randint(0, n-1))

            centers = new_centers

        # 移除空簇
        clusters = [c for c in clusters if c]

        return clusters

    def _create_blocks(self, matrix: List[List[float]],
                      row_clusters: List[List[int]],
                      col_clusters: List[List[int]]) -> List[dict]:
        """
        创建块结构
        """
        blocks = []

        for r_idx, row_cluster in enumerate(row_clusters):
            for c_idx, col_cluster in enumerate(col_clusters):
                if not row_cluster or not col_cluster:
                    continue

                # 计算块的平均密度
                block_sum = 0
                count = 0
                for r in row_cluster:
                    for c in col_cluster:
                        block_sum += matrix[r][c]
                        count += 1

                density = block_sum / count if count > 0 else 0

                blocks.append({
                    'row_cluster': row_cluster,
                    'col_cluster': col_cluster,
                    'density': density,
                    'row_idx': r_idx,
                    'col_idx': c_idx
                })

        return blocks

    def _sort_blocks_by_density(self, blocks: List[dict]) -> List[dict]:
        """
        按密度排序块，高密度块放在对角线上
        """
        # 按密度降序排序
        sorted_blocks = sorted(blocks, key=lambda x: x['density'], reverse=True)

        # 重新分配对角线位置
        diagonal_blocks = []
        off_diagonal_blocks = []

        # 选择前n个高密度块作为对角块
        n_diagonal = min(self.n_clusters, len(sorted_blocks))

        for i, block in enumerate(sorted_blocks[:n_diagonal]):
            block['diagonal_position'] = i
            diagonal_blocks.append(block)

        for block in sorted_blocks[n_diagonal:]:
            block['diagonal_position'] = -1
            off_diagonal_blocks.append(block)

        return diagonal_blocks + off_diagonal_blocks

    def _build_final_order(self, sorted_blocks: List[dict]) -> Tuple[List[int], List[int]]:
        """
        构建最终的行列顺序
        """
        row_order = []
        col_order = []
        used_rows = set()
        used_cols = set()

        # 首先放置对角块
        for block in sorted_blocks:
            if block.get('diagonal_position', -1) >= 0:
                # 添加未使用的行
                for r in block['row_cluster']:
                    if r not in used_rows:
                        row_order.append(r)
                        used_rows.add(r)

                # 添加未使用的列
                for c in block['col_cluster']:
                    if c not in used_cols:
                        col_order.append(c)
                        used_cols.add(c)

        # 添加剩余的行列
        all_rows = set(range(len(sorted_blocks[0]['row_cluster']) if sorted_blocks else 0))
        all_cols = set(range(len(sorted_blocks[0]['col_cluster']) if sorted_blocks else 0))

        # 这里需要获取矩阵的实际大小
        if sorted_blocks:
            all_rows = set()
            all_cols = set()
            for block in sorted_blocks:
                all_rows.update(block['row_cluster'])
                all_cols.update(block['col_cluster'])

        for r in range(max(all_rows) + 1 if all_rows else 0):
            if r not in used_rows:
                row_order.append(r)

        for c in range(max(all_cols) + 1 if all_cols else 0):
            if c not in used_cols:
                col_order.append(c)

        return row_order, col_order

    def _optimize_within_blocks(self, matrix: List[List[float]],
                               row_order: List[int],
                               col_order: List[int],
                               blocks: List[dict]) -> Tuple[List[int], List[int]]:
        """
        在每个块内部进行局部优化
        """
        # 对每个对角块进行内部优化
        for block in blocks:
            if block.get('diagonal_position', -1) >= 0:
                # 获取块的行列索引
                block_rows = block['row_cluster']
                block_cols = block['col_cluster']

                if len(block_rows) > 1 and len(block_cols) > 1:
                    # 在块内部按值排序
                    # 计算每行在块内的平均值
                    row_scores = []
                    for r in block_rows:
                        score = sum(matrix[r][c] for c in block_cols) / len(block_cols)
                        row_scores.append((r, score))

                    # 按分数降序排序
                    row_scores.sort(key=lambda x: x[1], reverse=True)

                    # 更新row_order中的顺序
                    block_row_positions = [row_order.index(r) for r in block_rows]
                    block_row_positions.sort()

                    for i, (r, _) in enumerate(row_scores):
                        if i < len(block_row_positions):
                            row_order[block_row_positions[i]] = r

                    # 对列做类似处理
                    col_scores = []
                    for c in block_cols:
                        score = sum(matrix[r][c] for r in block_rows) / len(block_rows)
                        col_scores.append((c, score))

                    col_scores.sort(key=lambda x: x[1], reverse=True)

                    block_col_positions = [col_order.index(c) for c in block_cols]
                    block_col_positions.sort()

                    for i, (c, _) in enumerate(col_scores):
                        if i < len(block_col_positions):
                            col_order[block_col_positions[i]] = c

        return row_order, col_order


# 测试代码
if __name__ == "__main__":
    # 创建测试矩阵 - 有明显块结构但被打乱
    test_matrix = []
    random.seed(42)

    # 创建30x19的矩阵
    for i in range(30):
        row = []
        for j in range(19):
            # 创建几个高密度块（但位置打乱）
            if (i % 7 < 3) and (j % 6 < 3):  # 块模式
                value = 0.7 + random.random() * 0.3
            elif (i % 5 == 0) and (j % 4 == 0):  # 稀疏高值
                value = 0.6 + random.random() * 0.3
            else:
                value = random.random() * 0.3
            row.append(value)
        test_matrix.append(row)

    print("🧪 测试终极块对角化算法")
    print(f"矩阵尺寸: {len(test_matrix)}x{len(test_matrix[0])}")

    # 应用算法
    algo = UltimateBlockDiagonalClustering(n_clusters=4)
    row_order, col_order = algo.block_diagonal_reorder(test_matrix)

    print(f"\n✅ 算法完成!")
    print(f"行顺序前10: {row_order[:10]}")
    print(f"列顺序前10: {col_order[:10]}")

    # 计算改进度
    def calculate_block_diagonal_score(matrix, row_order, col_order):
        """计算块对角化得分"""
        score = 0.0
        n = min(len(row_order), len(col_order))

        # 对角块得分
        block_size = n // 4  # 假设4个块
        for b in range(4):
            start = b * block_size
            end = min(start + block_size, n)

            for i in range(start, end):
                for j in range(start, end):
                    if i < len(row_order) and j < len(col_order):
                        score += matrix[row_order[i]][col_order[j]]

        return score

    original_score = calculate_block_diagonal_score(
        test_matrix,
        list(range(len(test_matrix))),
        list(range(len(test_matrix[0])))
    )

    optimized_score = calculate_block_diagonal_score(
        test_matrix, row_order, col_order
    )

    improvement = ((optimized_score - original_score) / original_score) * 100
    print(f"\n📊 块对角化得分提升: {improvement:.1f}%")