#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合打分到热力图映射桥接器
将列级综合打分数据转换为30×19热力图矩阵
"""

import json
import os
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScoringHeatmapMapper:
    """综合打分到热力图的智能映射器（支持动态矩阵大小）"""

    def __init__(self):
        self.base_path = Path('/root/projects/tencent-doc-manager')
        self.scoring_path = self.base_path / 'csv_security_results'
        # 动态设置矩阵行数（根据实际文档数量）
        self.matrix_rows = None  # 将由实际数据决定
        self.matrix_cols = 19  # 固定19列
        
        # L1/L2/L3风险等级基础热力值
        self.risk_base_heat = {
            'L1': 0.8,  # 高风险基础值
            'L2': 0.5,  # 中风险基础值  
            'L3': 0.2   # 低风险基础值
        }
        
        # AI决策对热力值的影响系数
        self.ai_decision_factors = {
            'APPROVE': 0.6,      # 批准：降低热力
            'CONDITIONAL': 0.8,  # 有条件批准：轻微降低
            'REVIEW': 1.2,       # 需要复审：增强热力
            'REJECT': 1.5        # 拒绝：显著增强
        }
        
        # 标准列名（与热力图系统一致）
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
        
    def load_comprehensive_scoring(self, week: str = None) -> Optional[Dict]:
        """加载综合打分数据"""
        try:
            # 查找最新的综合打分文件
            pattern = f"comprehensive_score_W{week}_*.json" if week else "comprehensive_score_*.json"
            scoring_files = list(self.scoring_path.glob(pattern))
            
            if not scoring_files:
                logger.warning(f"未找到综合打分文件: {pattern}")
                return None
                
            # 使用最新的文件
            latest_file = sorted(scoring_files)[-1]
            logger.info(f"加载综合打分文件: {latest_file}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"加载综合打分失败: {e}")
            return None
    
    def calculate_heat_value(self, column_data: Dict, column_name: str) -> float:
        """
        计算单个列的热力值
        
        Args:
            column_data: 列的评分数据
            column_name: 列名
            
        Returns:
            计算后的热力值 (0-1)
        """
        # 获取基础参数
        column_level = column_data.get('column_level', 'L3')
        aggregated_score = column_data.get('aggregated_score', 0.1)
        modifications = column_data.get('modifications', 0)
        ai_decisions = column_data.get('ai_decisions', {})
        
        # 计算基础热力值
        base_heat = self.risk_base_heat.get(column_level, 0.2)
        
        # 计算修改权重（5次修改达到最大权重）
        modification_weight = min(1.0, modifications / 5) if modifications > 0 else 0.5
        
        # 基础热力值计算
        heat_value = base_heat * aggregated_score * modification_weight
        
        # AI决策调整（仅L2列）
        if column_level == 'L2' and ai_decisions:
            # 计算AI决策的综合影响
            total_decisions = sum(ai_decisions.values())
            if total_decisions > 0:
                ai_factor = 0
                for decision, count in ai_decisions.items():
                    factor = self.ai_decision_factors.get(decision, 1.0)
                    ai_factor += factor * count
                ai_factor /= total_decisions
                heat_value *= ai_factor
        
        # L1列特殊处理：确保最小热力值
        if column_level == 'L1':
            heat_value = max(0.4, heat_value * 1.2)  # L1列增强并确保最小值
        
        # 确保热力值在合理范围内
        return max(0.05, min(0.95, heat_value))
    
    def expand_to_matrix_rows(self, table_scores: List[Dict]) -> List[List[float]]:
        """
        将表格评分动态扩展到N行矩阵（N=文档数量）

        Args:
            table_scores: 表格评分列表

        Returns:
            N×19的热力图矩阵
        """
        # 动态设置矩阵行数
        self.matrix_rows = len(table_scores) if table_scores else 1

        # 初始化矩阵
        matrix = [[0.05 for _ in range(self.matrix_cols)] for _ in range(self.matrix_rows)]

        # 每个表格占用一行
        for table_idx, table_data in enumerate(table_scores):
            # 获取列评分
            column_scores = table_data.get('column_scores', {})

            # 处理每一列
            for col_idx, col_name in enumerate(self.standard_columns):
                if col_name in column_scores:
                    col_data = column_scores[col_name]

                    # 计算该列的热力值
                    base_heat = self.calculate_heat_value(col_data, col_name)

                    # 将热力值赋给对应的单元格
                    matrix[table_idx][col_idx] = base_heat
                else:
                    # 无数据列使用默认值
                    matrix[table_idx][col_idx] = 0.05

        # 不再需要虚拟行填充，矩阵大小完全由实际数据决定
        
        return matrix
    
    def _fill_virtual_rows(self, matrix: List[List[float]], start_row: int, table_scores: List[Dict]):
        """填充虚拟数据行"""
        if not table_scores:
            return
            
        # 基于真实数据的统计特征生成虚拟数据
        for row_idx in range(start_row, self.matrix_rows):
            # 选择一个真实行作为模板
            template_row_idx = row_idx % start_row if start_row > 0 else 0
            
            for col_idx in range(self.matrix_cols):
                if start_row > 0:
                    template_value = matrix[template_row_idx][col_idx]
                else:
                    template_value = 0.05
                
                # 添加变异（±20%振幅变化 + 5%噪声）
                variation = 1.0 + (random.random() - 0.5) * 0.4  # ±20%
                noise = random.gauss(0, 0.05)  # 5%高斯噪声
                
                new_value = template_value * variation + noise
                matrix[row_idx][col_idx] = max(0.05, min(0.95, new_value))
    
    def apply_gaussian_smoothing(self, matrix: List[List[float]], radius: float = 0.3) -> List[List[float]]:
        """
        应用自适应高斯平滑
        
        Args:
            matrix: 输入矩阵
            radius: 高斯半径
            
        Returns:
            平滑后的矩阵
        """
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        
        # 深拷贝矩阵
        smoothed = [row[:] for row in matrix]
        
        # 构建高斯核
        kernel_size = int(radius * 2) + 1
        kernel = [[0.0 for _ in range(kernel_size)] for _ in range(kernel_size)]
        center = kernel_size // 2
        
        kernel_sum = 0.0
        for i in range(kernel_size):
            for j in range(kernel_size):
                x = i - center
                y = j - center
                dist_sq = x*x + y*y
                kernel[i][j] = math.exp(-dist_sq / (2 * radius * radius))
                kernel_sum += kernel[i][j]
        
        # 归一化核
        for i in range(kernel_size):
            for j in range(kernel_size):
                kernel[i][j] /= kernel_sum
        
        # 应用卷积（仅对非热点区域）
        for i in range(rows):
            for j in range(cols):
                # 如果是高热点（>0.7），保持不变
                if matrix[i][j] > 0.7:
                    continue
                    
                total_weight = 0
                weighted_sum = 0
                
                for ki in range(kernel_size):
                    for kj in range(kernel_size):
                        ni = i + ki - center
                        nj = j + kj - center
                        
                        if 0 <= ni < rows and 0 <= nj < cols:
                            # 如果邻居是热点，降低其权重
                            weight = kernel[ki][kj]
                            if matrix[ni][nj] > 0.7:
                                weight *= 0.3  # 降低热点的扩散影响
                            
                            weighted_sum += matrix[ni][nj] * weight
                            total_weight += weight
                
                if total_weight > 0:
                    smoothed[i][j] = weighted_sum / total_weight
        
        return smoothed
    
    def generate_heatmap_data(self, comprehensive_data: Dict) -> Dict:
        """
        生成热力图数据
        
        Args:
            comprehensive_data: 综合打分数据
            
        Returns:
            热力图API所需的数据格式
        """
        # 提取表格评分
        table_scores = comprehensive_data.get('table_scores', [])
        
        # 第一层：列级映射 + 第二层：行扩展
        matrix = self.expand_to_matrix_rows(table_scores)
        
        # 第三层：智能平滑
        smoothed_matrix = self.apply_gaussian_smoothing(matrix)
        
        # 已经是列表格式，直接使用
        heatmap_data = smoothed_matrix
        
        # 生成表格名称（基于真实文档 + 虚拟填充）
        table_names = self._generate_table_names(table_scores)
        
        # 生成行列顺序（可以后续添加聚类算法）
        row_order = list(range(self.matrix_rows))
        col_order = list(range(self.matrix_cols))
        
        # 计算统计信息
        statistics = self._calculate_statistics(smoothed_matrix, table_scores)
        
        return {
            "heatmap_data": heatmap_data,
            "table_names": table_names,
            "column_names": self.standard_columns,
            "row_order": row_order,
            "col_order": col_order,
            "statistics": statistics,
            "metadata": {
                "source": "comprehensive_scoring",
                "generation_time": datetime.now().isoformat(),
                "mapper_version": "v1.0"
            }
        }
    
    def _generate_table_names(self, table_scores: List[Dict]) -> List[str]:
        """动态生成表格名称（根据实际文档数量）"""
        names = []

        # 只添加真实文档名称，不再生成虚拟名称
        for table in table_scores:
            # 简化表格名称
            full_name = table.get('table_name', '未知表格')
            # 提取关键部分（例如"出国销售计划表"）
            if '销售计划表' in full_name:
                if '出国' in full_name:
                    short_name = "出国销售计划表"
                elif '回国' in full_name:
                    short_name = "回国销售计划表"
                else:
                    short_name = "销售计划表"
            elif '小红书' in full_name:
                short_name = "小红书部门表"
            else:
                short_name = full_name[:20] if len(full_name) > 20 else full_name

            names.append(short_name)

        # 如果没有数据，至少返回一个默认名称
        if not names:
            names.append("无数据")

        return names
    
    def _calculate_statistics(self, matrix: List[List[float]], table_scores: List[Dict]) -> Dict:
        """计算统计信息"""
        high_risk_threshold = 0.7
        medium_risk_threshold = 0.4
        
        # 计算风险统计
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        total_sum = 0
        max_value = 0
        min_value = 1
        total_cells = 0
        
        for row in matrix:
            for value in row:
                total_cells += 1
                total_sum += value
                max_value = max(max_value, value)
                min_value = min(min_value, value)
                
                if value > high_risk_threshold:
                    high_risk_count += 1
                elif value > medium_risk_threshold:
                    medium_risk_count += 1
                else:
                    low_risk_count += 1
        
        # 计算实际的修改数量
        total_modifications = sum(
            sum(col_data.get('modifications', 0) 
                for col_data in table.get('column_scores', {}).values())
            for table in table_scores
        )
        
        average_score = total_sum / total_cells if total_cells > 0 else 0
        
        return {
            "total_changes_detected": total_modifications,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "average_risk_score": average_score,
            "max_risk_score": max_value,
            "min_risk_score": min_value,
            "risk_distribution": {
                "high": high_risk_count / total_cells if total_cells > 0 else 0,
                "medium": medium_risk_count / total_cells if total_cells > 0 else 0,
                "low": low_risk_count / total_cells if total_cells > 0 else 0
            }
        }
    
    def map_scoring_to_heatmap(self, week: str = None) -> Optional[Dict]:
        """
        执行完整的映射流程
        
        Args:
            week: 周数（如W36），不指定则使用最新
            
        Returns:
            热力图数据或None
        """
        try:
            logger.info("开始综合打分到热力图映射...")
            
            # 加载综合打分数据
            comprehensive_data = self.load_comprehensive_scoring(week)
            if not comprehensive_data:
                logger.error("无法加载综合打分数据")
                return None
            
            # 生成热力图数据
            heatmap_data = self.generate_heatmap_data(comprehensive_data)
            
            logger.info(f"映射完成: 生成{self.matrix_rows}×{self.matrix_cols}热力图矩阵")
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"映射过程出错: {e}")
            return None


def main():
    """测试映射器"""
    mapper = ScoringHeatmapMapper()
    
    # 测试使用现有的comprehensive文件
    # 先尝试读取real_test_comprehensive.json
    test_file = Path('/root/projects/tencent-doc-manager/csv_security_results/real_test_comprehensive.json')
    
    if test_file.exists():
        print(f"使用测试文件: {test_file}")
        with open(test_file, 'r', encoding='utf-8') as f:
            comprehensive_data = json.load(f)
        
        # 生成热力图数据
        result = mapper.generate_heatmap_data(comprehensive_data)
        
        print(f"✅ 映射成功!")
        print(f"矩阵尺寸: {len(result['heatmap_data'])}×{len(result['heatmap_data'][0])}")
        print(f"统计信息: {result['statistics']}")
        
        # 保存结果用于测试
        output_path = Path('/root/projects/tencent-doc-manager/scoring_heatmap_test.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"测试结果已保存到: {output_path}")
    else:
        # 尝试自动查找
        result = mapper.map_scoring_to_heatmap()
        if result:
            print(f"✅ 映射成功!")
            print(f"矩阵尺寸: {len(result['heatmap_data'])}×{len(result['heatmap_data'][0])}")
            print(f"统计信息: {result['statistics']}")
        else:
            print("❌ 映射失败")


if __name__ == '__main__':
    main()