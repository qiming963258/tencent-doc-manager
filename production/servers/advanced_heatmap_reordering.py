#!/usr/bin/env python3
"""
高级热力图重排序算法
使用更先进的技术实现最大化热团聚集
"""

from typing import List, Tuple, Optional
import math
import random

class AdvancedHeatmapReordering:
    """
    高级热力图重排序算法集合
    包含多种先进算法实现最大化热团聚集
    """

    def __init__(self):
        self.max_iterations = 1000
        self.temperature = 1.0
        self.cooling_rate = 0.995

    def reorder_matrix_advanced(self, matrix: List[List[float]],
                               method: str = 'spectral_biclustering') -> Tuple[List[int], List[int]]:
        """
        使用高级算法进行矩阵重排序

        方法选项:
        - spectral_biclustering: 谱双聚类（最推荐）
        - simulated_annealing: 模拟退火
        - block_diagonal: 块对角化
        - cross_association: 交叉关联
        - barycenter: 重心法
        """
        if not matrix or not matrix[0]:
            return list(range(len(matrix))), list(range(len(matrix[0]) if matrix else 0))

        if method == 'spectral_biclustering':
            return self._spectral_biclustering(matrix)
        elif method == 'simulated_annealing':
            return self._simulated_annealing(matrix)
        elif method == 'block_diagonal':
            return self._block_diagonal_form(matrix)
        elif method == 'cross_association':
            return self._cross_association(matrix)
        elif method == 'barycenter':
            return self._barycenter_heuristic(matrix)
        else:
            # 默认使用谱双聚类
            return self._spectral_biclustering(matrix)

    def _spectral_biclustering(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        谱双聚类算法 - 最有效的热团聚集方法
        基于图的拉普拉斯矩阵特征向量
        """
        print("🎯 使用谱双聚类算法（最优热团聚集）...")

        rows, cols = len(matrix), len(matrix[0])

        # 步骤1: 构建二分图的邻接矩阵
        # 将热力图转换为二分图表示
        bipartite_matrix = self._create_bipartite_matrix(matrix)

        # 步骤2: 计算归一化的拉普拉斯矩阵
        laplacian = self._compute_normalized_laplacian(bipartite_matrix)

        # 步骤3: 使用幂迭代法计算第二小特征值对应的特征向量
        eigenvector = self._power_iteration(laplacian, 2)

        # 步骤4: 基于特征向量值对行列重新排序
        row_scores = eigenvector[:rows]
        col_scores = eigenvector[rows:rows+cols]

        # 排序索引
        row_order = sorted(range(rows), key=lambda i: row_scores[i])
        col_order = sorted(range(cols), key=lambda j: col_scores[j])

        # 步骤5: 局部优化 - 在谱排序基础上微调
        row_order = self._local_search_optimization(matrix, row_order, axis='row')
        col_order = self._local_search_optimization(matrix, col_order, axis='col')

        return row_order, col_order

    def _simulated_annealing(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        模拟退火算法 - 全局优化方法
        通过随机搜索和概率接受找到全局最优解
        """
        print("🔥 使用模拟退火算法进行全局优化...")

        rows, cols = len(matrix), len(matrix[0])

        # 初始随机排序
        row_order = list(range(rows))
        col_order = list(range(cols))
        random.shuffle(row_order)
        random.shuffle(col_order)

        # 当前最佳解
        best_row_order = row_order[:]
        best_col_order = col_order[:]
        best_score = self._calculate_clustering_score(matrix, row_order, col_order)

        temperature = self.temperature

        for iteration in range(self.max_iterations):
            # 生成邻域解（随机交换两个位置）
            new_row_order = row_order[:]
            new_col_order = col_order[:]

            # 50%概率交换行，50%概率交换列
            if random.random() < 0.5 and rows > 1:
                i, j = random.sample(range(rows), 2)
                new_row_order[i], new_row_order[j] = new_row_order[j], new_row_order[i]
            elif cols > 1:
                i, j = random.sample(range(cols), 2)
                new_col_order[i], new_col_order[j] = new_col_order[j], new_col_order[i]

            # 计算新解的得分
            new_score = self._calculate_clustering_score(matrix, new_row_order, new_col_order)

            # 决定是否接受新解
            delta = new_score - best_score
            if delta > 0 or random.random() < math.exp(delta / temperature):
                row_order = new_row_order
                col_order = new_col_order

                if new_score > best_score:
                    best_score = new_score
                    best_row_order = new_row_order[:]
                    best_col_order = new_col_order[:]

            # 降温
            temperature *= self.cooling_rate

            if iteration % 100 == 0:
                print(f"  迭代 {iteration}: 最佳得分 = {best_score:.3f}, 温度 = {temperature:.3f}")

        return best_row_order, best_col_order

    def _block_diagonal_form(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        块对角化算法 - 将矩阵重排成块对角形式
        适合具有明显块结构的热力图
        """
        print("⬛ 使用块对角化算法...")

        rows, cols = len(matrix), len(matrix[0])

        # 步骤1: 识别块结构
        blocks = self._identify_blocks(matrix)

        # 步骤2: 对每个块内部进行优化排序
        row_order = []
        col_order = []

        for block in blocks:
            block_rows, block_cols = block
            # 对块内元素按热度值排序
            block_rows.sort(key=lambda r: sum(matrix[r][c] for c in block_cols), reverse=True)
            block_cols.sort(key=lambda c: sum(matrix[r][c] for r in block_rows), reverse=True)
            row_order.extend(block_rows)
            col_order.extend(block_cols)

        # 添加未分配的行列
        for i in range(rows):
            if i not in row_order:
                row_order.append(i)
        for j in range(cols):
            if j not in col_order:
                col_order.append(j)

        return row_order, col_order

    def _cross_association(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        交叉关联算法 - 信息论方法
        最小化交叉熵来找到最佳聚类
        """
        print("🔗 使用交叉关联算法...")

        rows, cols = len(matrix), len(matrix[0])

        # 计算行列的信息熵
        row_entropy = [self._calculate_entropy([matrix[i][j] for j in range(cols)]) for i in range(rows)]
        col_entropy = [self._calculate_entropy([matrix[i][j] for i in range(rows)]) for j in range(cols)]

        # 按熵值排序（低熵表示更集中的分布）
        row_order = sorted(range(rows), key=lambda i: row_entropy[i])
        col_order = sorted(range(cols), key=lambda j: col_entropy[j])

        # 进一步优化：将高相关的行列聚在一起
        row_order = self._group_by_correlation(matrix, row_order, axis='row')
        col_order = self._group_by_correlation(matrix, col_order, axis='col')

        return row_order, col_order

    def _barycenter_heuristic(self, matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
        """
        重心启发式算法 - 基于加权位置的快速算法
        计算每个元素的"重心"位置并据此排序
        """
        print("⚖️ 使用重心启发式算法...")

        rows, cols = len(matrix), len(matrix[0])

        # 计算每行的重心
        row_barycenters = []
        for i in range(rows):
            total_weight = sum(matrix[i])
            if total_weight > 0:
                barycenter = sum(j * matrix[i][j] for j in range(cols)) / total_weight
            else:
                barycenter = cols / 2
            row_barycenters.append(barycenter)

        # 计算每列的重心
        col_barycenters = []
        for j in range(cols):
            total_weight = sum(matrix[i][j] for i in range(rows))
            if total_weight > 0:
                barycenter = sum(i * matrix[i][j] for i in range(rows)) / total_weight
            else:
                barycenter = rows / 2
            col_barycenters.append(barycenter)

        # 基于重心排序
        row_order = sorted(range(rows), key=lambda i: row_barycenters[i])
        col_order = sorted(range(cols), key=lambda j: col_barycenters[j])

        # 迭代优化（通常3-5次迭代就足够）
        for _ in range(5):
            # 固定列顺序，优化行顺序
            row_barycenters = []
            for i in range(rows):
                total_weight = sum(matrix[i])
                if total_weight > 0:
                    barycenter = sum(col_order.index(j) * matrix[i][j] for j in range(cols)) / total_weight
                else:
                    barycenter = cols / 2
                row_barycenters.append(barycenter)
            row_order = sorted(range(rows), key=lambda i: row_barycenters[i])

            # 固定行顺序，优化列顺序
            col_barycenters = []
            for j in range(cols):
                total_weight = sum(matrix[i][j] for i in range(rows))
                if total_weight > 0:
                    barycenter = sum(row_order.index(i) * matrix[i][j] for i in range(rows)) / total_weight
                else:
                    barycenter = rows / 2
                col_barycenters.append(barycenter)
            col_order = sorted(range(cols), key=lambda j: col_barycenters[j])

        return row_order, col_order

    # ========== 辅助函数 ==========

    def _create_bipartite_matrix(self, matrix: List[List[float]]) -> List[List[float]]:
        """创建二分图的邻接矩阵"""
        rows, cols = len(matrix), len(matrix[0])
        n = rows + cols
        bipartite = [[0.0] * n for _ in range(n)]

        # 填充二分图
        for i in range(rows):
            for j in range(cols):
                bipartite[i][rows + j] = matrix[i][j]
                bipartite[rows + j][i] = matrix[i][j]

        return bipartite

    def _compute_normalized_laplacian(self, adj_matrix: List[List[float]]) -> List[List[float]]:
        """计算归一化拉普拉斯矩阵"""
        n = len(adj_matrix)
        degree = [sum(row) for row in adj_matrix]
        laplacian = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j and degree[i] > 0:
                    laplacian[i][j] = 1.0
                elif adj_matrix[i][j] > 0 and degree[i] > 0 and degree[j] > 0:
                    laplacian[i][j] = -adj_matrix[i][j] / math.sqrt(degree[i] * degree[j])

        return laplacian

    def _power_iteration(self, matrix: List[List[float]], k: int = 2) -> List[float]:
        """幂迭代法计算特征向量"""
        n = len(matrix)
        vector = [random.random() for _ in range(n)]

        for _ in range(50):  # 通常50次迭代足够收敛
            new_vector = [0.0] * n
            for i in range(n):
                for j in range(n):
                    new_vector[i] += matrix[i][j] * vector[j]

            # 归一化
            norm = math.sqrt(sum(v * v for v in new_vector))
            if norm > 0:
                vector = [v / norm for v in new_vector]
            else:
                break

        return vector

    def _local_search_optimization(self, matrix: List[List[float]], order: List[int], axis: str) -> List[int]:
        """局部搜索优化"""
        improved = True
        while improved:
            improved = False
            for i in range(len(order) - 1):
                # 尝试交换相邻元素
                new_order = order[:]
                new_order[i], new_order[i + 1] = new_order[i + 1], new_order[i]

                if axis == 'row':
                    old_score = self._row_clustering_score(matrix, order, i, i + 1)
                    new_score = self._row_clustering_score(matrix, new_order, i, i + 1)
                else:
                    old_score = self._col_clustering_score(matrix, order, i, i + 1)
                    new_score = self._col_clustering_score(matrix, new_order, i, i + 1)

                if new_score > old_score:
                    order = new_order
                    improved = True

        return order

    def _calculate_clustering_score(self, matrix: List[List[float]], row_order: List[int], col_order: List[int]) -> float:
        """计算聚类得分 - 相邻高值元素越多得分越高"""
        score = 0.0
        rows, cols = len(matrix), len(matrix[0])

        for i in range(rows - 1):
            for j in range(cols - 1):
                r1, r2 = row_order[i], row_order[i + 1]
                c1, c2 = col_order[j], col_order[j + 1]
                # 计算2x2子矩阵的平均值
                submatrix_sum = (matrix[r1][c1] + matrix[r1][c2] +
                               matrix[r2][c1] + matrix[r2][c2])
                score += submatrix_sum * submatrix_sum  # 平方以强调高值区域

        return score

    def _row_clustering_score(self, matrix: List[List[float]], row_order: List[int], i1: int, i2: int) -> float:
        """计算特定行对的聚类得分"""
        score = 0.0
        cols = len(matrix[0])
        r1, r2 = row_order[i1], row_order[i2]

        for j in range(cols):
            score += matrix[r1][j] * matrix[r2][j]

        return score

    def _col_clustering_score(self, matrix: List[List[float]], col_order: List[int], j1: int, j2: int) -> float:
        """计算特定列对的聚类得分"""
        score = 0.0
        rows = len(matrix)
        c1, c2 = col_order[j1], col_order[j2]

        for i in range(rows):
            score += matrix[i][c1] * matrix[i][c2]

        return score

    def _identify_blocks(self, matrix: List[List[float]], threshold: float = 0.5) -> List[Tuple[List[int], List[int]]]:
        """识别矩阵中的块结构"""
        rows, cols = len(matrix), len(matrix[0])
        blocks = []
        used_rows = set()
        used_cols = set()

        # 贪心地寻找高密度块
        for _ in range(min(rows, cols) // 2):  # 最多寻找一半的块
            best_block = None
            best_density = 0

            for r in range(rows):
                if r in used_rows:
                    continue
                for c in range(cols):
                    if c in used_cols:
                        continue

                    # 尝试扩展块
                    block_rows = [r]
                    block_cols = [c]

                    # 贪心扩展
                    for r2 in range(rows):
                        if r2 not in used_rows and r2 != r:
                            avg_val = sum(matrix[r2][cc] for cc in block_cols) / len(block_cols)
                            if avg_val >= threshold:
                                block_rows.append(r2)

                    for c2 in range(cols):
                        if c2 not in used_cols and c2 != c:
                            avg_val = sum(matrix[rr][c2] for rr in block_rows) / len(block_rows)
                            if avg_val >= threshold:
                                block_cols.append(c2)

                    # 计算块密度
                    density = sum(matrix[rr][cc] for rr in block_rows for cc in block_cols)
                    density /= (len(block_rows) * len(block_cols))

                    if density > best_density:
                        best_density = density
                        best_block = (block_rows, block_cols)

            if best_block and best_density >= threshold:
                blocks.append(best_block)
                used_rows.update(best_block[0])
                used_cols.update(best_block[1])
            else:
                break

        return blocks

    def _calculate_entropy(self, values: List[float]) -> float:
        """计算信息熵"""
        total = sum(values)
        if total == 0:
            return 0

        entropy = 0
        for v in values:
            if v > 0:
                p = v / total
                entropy -= p * math.log(p)

        return entropy

    def _group_by_correlation(self, matrix: List[List[float]], order: List[int], axis: str) -> List[int]:
        """基于相关性分组"""
        if axis == 'row':
            # 计算行之间的相关性并分组
            size = len(matrix)
            groups = []
            used = set()

            for i in order:
                if i in used:
                    continue
                group = [i]
                used.add(i)

                for j in order:
                    if j not in used:
                        correlation = self._calculate_correlation(
                            [matrix[i][k] for k in range(len(matrix[0]))],
                            [matrix[j][k] for k in range(len(matrix[0]))]
                        )
                        if correlation > 0.7:  # 高相关性阈值
                            group.append(j)
                            used.add(j)

                groups.append(group)

            # 展平分组
            new_order = []
            for group in groups:
                new_order.extend(group)
            return new_order
        else:
            # 类似地处理列
            cols = len(matrix[0])
            groups = []
            used = set()

            for j in order:
                if j in used:
                    continue
                group = [j]
                used.add(j)

                for k in order:
                    if k not in used:
                        correlation = self._calculate_correlation(
                            [matrix[i][j] for i in range(len(matrix))],
                            [matrix[i][k] for i in range(len(matrix))]
                        )
                        if correlation > 0.7:
                            group.append(k)
                            used.add(k)

                groups.append(group)

            new_order = []
            for group in groups:
                new_order.extend(group)
            return new_order

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """计算皮尔逊相关系数"""
        n = len(x)
        if n == 0:
            return 0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        std_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
        std_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))

        if std_x == 0 or std_y == 0:
            return 0

        return cov / (std_x * std_y)


# 测试函数
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

    # 测试各种算法
    algo = AdvancedHeatmapReordering()

    methods = ['spectral_biclustering', 'simulated_annealing', 'block_diagonal',
               'cross_association', 'barycenter']

    for method in methods:
        print(f"\n{'='*50}")
        print(f"测试方法: {method}")
        row_order, col_order = algo.reorder_matrix_advanced(test_matrix, method=method)

        print(f"行顺序: {row_order}")
        print(f"列顺序: {col_order}")

        # 显示重排序后的矩阵
        print("重排序后:")
        for i in row_order:
            row = [test_matrix[i][j] for j in col_order]
            print([f"{x:.1f}" for x in row])