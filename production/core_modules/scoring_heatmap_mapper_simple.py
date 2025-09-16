#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版综合打分到热力图映射器
直接使用aggregated_score作为唯一数据源，无需额外计算
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

class SimpleScoringHeatmapMapper:
    """简化版映射器：直接使用综合打分数据"""
    
    def __init__(self):
        self.base_path = Path('/root/projects/tencent-doc-manager')
        self.scoring_path = self.base_path / 'csv_security_results'
        self.matrix_rows = 30  # 热力图行数
        self.matrix_cols = 19  # 热力图列数
        
        # 标准列名（与热力图系统一致）
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
        
        # 表格名到行区间的映射（固定映射关系）
        self.table_row_mapping = {
            "副本-测试版本-出国销售计划表": (0, 10),
            "副本-测试版本-回国销售计划表": (10, 20),
            "测试版本-小红书部门": (20, 30),
            # 简化名称也支持
            "出国销售": (0, 10),
            "回国销售": (10, 20),
            "小红书": (20, 30)
        }
        
    def load_comprehensive_scoring(self, week: str = None) -> Optional[Dict]:
        """加载综合打分数据"""
        try:
            # 查找综合打分文件
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
    
    def simple_map_to_matrix(self, comprehensive_data: Dict) -> List[List[float]]:
        """
        简化映射：直接使用aggregated_score填充矩阵
        
        核心理念：
        1. 表格名决定行位置
        2. 列名决定列位置
        3. aggregated_score直接作为热力值
        """
        # 初始化矩阵，默认值0.05（低热力）
        matrix = [[0.05 for _ in range(self.matrix_cols)] for _ in range(self.matrix_rows)]
        
        # 提取表格评分数据
        table_scores = comprehensive_data.get('table_scores', [])
        
        for table_data in table_scores:
            table_name = table_data.get('table_name', '')
            
            # 查找表格对应的行区间
            row_range = None
            for key, value in self.table_row_mapping.items():
                if key in table_name:
                    row_range = value
                    break
            
            if not row_range:
                # 如果找不到匹配，尝试分配到未使用的区域
                logger.warning(f"未找到表格'{table_name}'的行映射，跳过")
                continue
            
            start_row, end_row = row_range
            logger.info(f"表格'{table_name}'映射到行{start_row}-{end_row}")
            
            # 获取列评分数据
            column_scores = table_data.get('column_scores', {})
            
            # 遍历每一列的评分
            for col_name, col_data in column_scores.items():
                # 查找列名对应的索引
                if col_name not in self.standard_columns:
                    logger.warning(f"列名'{col_name}'不在标准列中，跳过")
                    continue
                    
                col_idx = self.standard_columns.index(col_name)
                
                # 直接使用aggregated_score作为热力值
                aggregated_score = col_data.get('aggregated_score', 0.05)
                
                # 获取详细分数列表（如果有的话）
                scores = col_data.get('scores', [])
                
                # 填充矩阵
                if scores and len(scores) > 0:
                    # 如果有详细分数，分配到不同行
                    rows_to_fill = end_row - start_row
                    for i in range(rows_to_fill):
                        if i < len(scores):
                            # 使用详细分数
                            matrix[start_row + i][col_idx] = scores[i]
                        else:
                            # 超出详细分数范围，使用汇总分数
                            matrix[start_row + i][col_idx] = aggregated_score
                else:
                    # 没有详细分数，所有行使用相同的汇总分数
                    for row_idx in range(start_row, end_row):
                        matrix[row_idx][col_idx] = aggregated_score
                
                logger.debug(f"  列'{col_name}'(索引{col_idx})填充分数{aggregated_score:.3f}")
        
        return matrix
    
    def apply_gaussian_smoothing(self, matrix: List[List[float]], radius: float = 0.3) -> List[List[float]]:
        """
        应用高斯平滑（保留原有功能）
        仅用于视觉优化，不改变数据本质
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
        
        # 应用卷积（保护高热点）
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
        生成热力图数据（简化版）
        """
        # 简单映射：直接使用aggregated_score
        matrix = self.simple_map_to_matrix(comprehensive_data)
        
        # 可选：应用轻微的高斯平滑以改善视觉效果
        smoothed_matrix = self.apply_gaussian_smoothing(matrix)
        
        # 生成表格名称列表
        table_names = self._generate_table_names(comprehensive_data.get('table_scores', []))
        
        # 生成行列顺序（初始为自然顺序，可由聚类算法重排）
        row_order = list(range(self.matrix_rows))
        col_order = list(range(self.matrix_cols))
        
        # 计算统计信息
        statistics = self._calculate_statistics(smoothed_matrix, comprehensive_data)
        
        return {
            "heatmap_data": smoothed_matrix,
            "table_names": table_names,
            "column_names": self.standard_columns,
            "row_order": row_order,
            "col_order": col_order,
            "statistics": statistics,
            "metadata": {
                "source": "comprehensive_scoring_simple",
                "generation_time": datetime.now().isoformat(),
                "mapper_version": "v2.0-simple"
            }
        }
    
    def _generate_table_names(self, table_scores: List[Dict]) -> List[str]:
        """生成30个表格名称"""
        names = []
        
        # 为每个真实表格生成10个名称
        for table in table_scores[:3]:
            full_name = table.get('table_name', '未知表格')
            
            # 简化表格名称
            if '出国销售' in full_name:
                short_name = "出国销售计划表"
            elif '回国销售' in full_name:
                short_name = "回国销售计划表"
            elif '小红书' in full_name:
                short_name = "小红书部门表"
            else:
                short_name = full_name[:15] if len(full_name) > 15 else full_name
            
            # 生成10个变体
            for i in range(10):
                if i == 0:
                    names.append(short_name)
                else:
                    names.append(f"{short_name}_R{i}")
        
        # 如果不足30个，填充默认名称
        while len(names) < 30:
            names.append(f"表格_{len(names)+1}")
        
        return names[:30]
    
    def _calculate_statistics(self, matrix: List[List[float]], comprehensive_data: Dict) -> Dict:
        """计算统计信息"""
        # 风险阈值
        high_threshold = 0.7
        medium_threshold = 0.4
        
        # 统计各风险等级数量
        high_count = 0
        medium_count = 0
        low_count = 0
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
                
                if value > high_threshold:
                    high_count += 1
                elif value > medium_threshold:
                    medium_count += 1
                else:
                    low_count += 1
        
        # 从综合打分获取实际修改数
        total_modifications = 0
        for table in comprehensive_data.get('table_scores', []):
            total_modifications += table.get('modifications_count', 0)
        
        average = total_sum / total_cells if total_cells > 0 else 0
        
        return {
            "total_changes_detected": total_modifications,
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "low_risk_count": low_count,
            "average_risk_score": average,
            "max_risk_score": max_value,
            "min_risk_score": min_value,
            "risk_distribution": {
                "high": high_count / total_cells if total_cells > 0 else 0,
                "medium": medium_count / total_cells if total_cells > 0 else 0,
                "low": low_count / total_cells if total_cells > 0 else 0
            }
        }
    
    def map_scoring_to_heatmap(self, week: str = None) -> Optional[Dict]:
        """
        执行简化的映射流程
        """
        try:
            logger.info("开始简化版综合打分到热力图映射...")
            
            # 加载综合打分数据
            comprehensive_data = self.load_comprehensive_scoring(week)
            if not comprehensive_data:
                logger.error("无法加载综合打分数据")
                return None
            
            # 生成热力图数据
            heatmap_data = self.generate_heatmap_data(comprehensive_data)
            
            logger.info(f"映射完成: 生成{self.matrix_rows}×{self.matrix_cols}热力图矩阵")
            
            # 输出一些统计信息
            stats = heatmap_data['statistics']
            logger.info(f"统计: 高风险{stats['high_risk_count']}个, "
                       f"中风险{stats['medium_risk_count']}个, "
                       f"低风险{stats['low_risk_count']}个")
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"映射过程出错: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """测试简化版映射器"""
    mapper = SimpleScoringHeatmapMapper()
    
    # 测试W36数据
    result = mapper.map_scoring_to_heatmap('36')
    
    if result:
        print(f"✅ 简化版映射成功!")
        print(f"矩阵尺寸: {len(result['heatmap_data'])}×{len(result['heatmap_data'][0])}")
        print(f"统计信息: {result['statistics']}")
        
        # 显示部分热力值
        print(f"\n热力值示例（前3行，前5列）:")
        for i in range(min(3, len(result['heatmap_data']))):
            row_str = " ".join(f"{result['heatmap_data'][i][j]:.2f}" 
                              for j in range(min(5, len(result['heatmap_data'][0]))))
            print(f"  行{i}: {row_str}")
        
        # 保存结果
        output_path = Path('/root/projects/tencent-doc-manager/scoring_heatmap_simple_test.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: {output_path}")
    else:
        print("❌ 映射失败")


if __name__ == '__main__':
    main()