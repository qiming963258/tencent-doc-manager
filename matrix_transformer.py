#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV对比结果到热力图矩阵转换器
将任意大小的CSV变更映射到30×19矩阵
"""

import json
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatrixTransformer:
    """将CSV对比结果转换为热力图矩阵"""
    
    def __init__(self, rows=30, cols=19):
        """
        初始化矩阵转换器
        
        Args:
            rows: 矩阵行数（默认30）
            cols: 矩阵列数（默认19）
        """
        self.rows = rows
        self.cols = cols
        self.matrix = [[0.0 for _ in range(cols)] for _ in range(rows)]
        
    def load_comparison_result(self, result_path: str) -> Dict:
        """
        加载对比结果JSON
        
        Args:
            result_path: 对比结果文件路径
            
        Returns:
            对比结果字典
        """
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载对比结果失败: {e}")
            return {}
    
    def map_differences_to_matrix(self, differences: List[Dict]) -> List[List[float]]:
        """
        将差异映射到矩阵
        
        Args:
            differences: 差异列表
            
        Returns:
            30×19的numpy数组
        """
        # 重置矩阵
        self.matrix = [[0.0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        if not differences:
            logger.info("没有发现差异，返回零矩阵")
            return self.matrix
        
        # 计算每个差异应该占据的矩阵空间
        total_cells = self.rows * self.cols
        cells_per_diff = max(1, total_cells // len(differences))
        
        # 映射差异到矩阵
        for idx, diff in enumerate(differences):
            # 计算风险值（0-1范围）
            risk_score = diff.get('risk_score', 0.5)
            
            # 计算起始位置
            start_pos = (idx * cells_per_diff) % total_cells
            row = start_pos // self.cols
            col = start_pos % self.cols
            
            # 根据风险等级设置强度
            risk_level = diff.get('risk_level', 'L3')
            if risk_level == 'L1':
                intensity = 0.9  # 高风险
            elif risk_level == 'L2':
                intensity = 0.6  # 中风险
            else:
                intensity = 0.3  # 低风险
            
            # 在矩阵中标记变化（使用高斯分布使变化更自然）
            self._apply_gaussian_spot(row, col, intensity, radius=2)
        
        return self.matrix
    
    def _apply_gaussian_spot(self, center_row: int, center_col: int, 
                            intensity: float, radius: int = 2):
        """
        在矩阵上应用高斯热点
        
        Args:
            center_row: 中心行
            center_col: 中心列
            intensity: 强度（0-1）
            radius: 影响半径
        """
        for r in range(max(0, center_row - radius), 
                      min(self.rows, center_row + radius + 1)):
            for c in range(max(0, center_col - radius), 
                          min(self.cols, center_col + radius + 1)):
                # 计算距离
                dist = math.sqrt((r - center_row)**2 + (c - center_col)**2)
                # 高斯衰减
                gaussian_value = intensity * math.exp(-(dist**2) / (2 * (radius/2)**2))
                # 更新矩阵值（取最大值避免覆盖）
                self.matrix[r][c] = max(self.matrix[r][c], gaussian_value)
    
    def generate_heatmap_data(self, comparison_result: Dict) -> Dict:
        """
        生成完整的热力图数据
        
        Args:
            comparison_result: 对比结果
            
        Returns:
            热力图数据字典
        """
        differences = comparison_result.get('differences', [])
        matrix = self.map_differences_to_matrix(differences)
        
        # 生成统计信息
        statistics = {
            'total_changes': len(differences),
            'risk_levels': {
                'L1': sum(1 for d in differences if d.get('risk_level') == 'L1'),
                'L2': sum(1 for d in differences if d.get('risk_level') == 'L2'),
                'L3': sum(1 for d in differences if d.get('risk_level') == 'L3'),
            },
            'security_score': comparison_result.get('security_score', 100),
            'overall_risk': comparison_result.get('risk_level', 'N/A'),
            'max_intensity': float(max(max(row) for row in matrix)),
            'mean_intensity': float(sum(sum(row) for row in matrix) / (self.rows * self.cols)),
            'affected_cells': sum(1 for row in matrix for cell in row if cell > 0)
        }
        
        # 构建热力图数据
        heatmap_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'matrix_size': {
                'rows': self.rows,
                'cols': self.cols
            },
            'matrix': matrix,  # 已经是列表格式
            'statistics': statistics,
            'source': 'matrix_transformer_v1.0',
            'comparison_metadata': {
                'total_differences': len(differences),
                'processing_time': comparison_result.get('processing_time', 0),
                'file_checksums': comparison_result.get('file_checksums', {})
            }
        }
        
        return heatmap_data
    
    def save_heatmap_data(self, heatmap_data: Dict, output_path: str):
        """
        保存热力图数据到JSON文件
        
        Args:
            heatmap_data: 热力图数据
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(heatmap_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 热力图数据已保存到: {output_path}")
        except Exception as e:
            logger.error(f"❌ 保存热力图数据失败: {e}")


def main():
    """测试矩阵转换器"""
    transformer = MatrixTransformer()
    
    # 加载对比结果
    comparison_file = '/root/projects/tencent-doc-manager/csv_versions/comparison/comparison_result.json'
    if Path(comparison_file).exists():
        result = transformer.load_comparison_result(comparison_file)
        
        # 生成热力图数据
        heatmap_data = transformer.generate_heatmap_data(result)
        
        # 显示统计信息
        stats = heatmap_data['statistics']
        print(f"📊 矩阵转换完成:")
        print(f"  • 变更数量: {stats['total_changes']}")
        print(f"  • 风险分布: L1={stats['risk_levels']['L1']}, L2={stats['risk_levels']['L2']}, L3={stats['risk_levels']['L3']}")
        print(f"  • 安全评分: {stats['security_score']}")
        print(f"  • 影响单元格: {stats['affected_cells']}/{30*19}")
        print(f"  • 最大强度: {stats['max_intensity']:.2f}")
        print(f"  • 平均强度: {stats['mean_intensity']:.4f}")
        
        # 保存热力图数据
        output_file = '/root/projects/tencent-doc-manager/production/servers/current_heatmap_data_new.json'
        transformer.save_heatmap_data(heatmap_data, output_file)
    else:
        print(f"❌ 对比结果文件不存在: {comparison_file}")


if __name__ == '__main__':
    main()