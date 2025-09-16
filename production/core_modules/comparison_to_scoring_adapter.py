#!/usr/bin/env python3
"""
CSV对比结果到综合打分的数据适配器
负责将CSV对比结果转换为综合打分生成器所需的格式
严格遵循06-详细分表打分方法规范和07-综合集成打分算法规范
"""

import json
import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime
import logging

sys.path.append('/root/projects/tencent-doc-manager')
from standard_columns_config import STANDARD_COLUMNS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComparisonToScoringAdapter:
    """CSV对比结果到综合打分的适配器"""

    # L1/L2/L3列分类定义（严格遵循规范06）
    L1_COLUMNS = [
        "来源", "任务发起时间", "目标对齐", "关键KR对齐",
        "重要程度", "预计完成时间", "完成进度"
    ]

    L2_COLUMNS = [
        "项目类型", "具体计划内容", "邓总指导登记",
        "负责人", "协助人", "监督人", "形成计划清单"
    ]

    L3_COLUMNS = [
        "序号", "最新复盘时间", "对上汇报", "应用情况",
        "经理分析复盘",  # 注意：规范中写的是"进度分析总结"，但实际列名是"经理分析复盘"
        "完成链接"  # 添加完成链接到L3分类（参考性信息）
    ]

    # 列权重定义（来自规范06）
    COLUMN_WEIGHTS = {
        # L1列权重
        "重要程度": 1.4,
        "任务发起时间": 1.3,
        "预计完成时间": 1.3,
        "完成进度": 1.1,
        # L2列权重
        "负责人": 1.2,
        "邓总指导登记": 1.15,
        "项目类型": 1.1
    }

    def __init__(self):
        self.standard_columns = STANDARD_COLUMNS
        self.base_dir = Path("/root/projects/tencent-doc-manager")

    def load_comparison_result(self, comparison_file: str) -> Dict:
        """加载CSV对比结果文件"""
        with open(comparison_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_table_data(self, comparison_result: Dict) -> Dict:
        """
        从CSV对比结果提取表格数据

        返回格式:
        {
            "table_name": str,
            "total_rows": int,
            "modifications": List[Dict],
            "column_modifications": Dict[str, List[int]]
        }
        """
        # 从文件信息提取
        file_info = comparison_result.get('file_info', {})
        metadata = file_info.get('metadata', {})
        file2_info = metadata.get('file2_info', {})

        # 获取表格基本信息
        total_rows = file2_info.get('rows', 0)

        # 提取所有修改
        differences = comparison_result.get('differences', [])
        modifications = []
        column_modifications = defaultdict(list)

        for diff in differences:
            modification = {
                'row': diff.get('行号', 0),
                'column': diff.get('列名', ''),
                'column_index': diff.get('列索引', 0),
                'old_value': diff.get('原值', ''),
                'new_value': diff.get('新值', ''),
                'risk_level': diff.get('risk_level', 'L3'),
                'risk_score': diff.get('risk_score', 0.2)
            }
            modifications.append(modification)

            # 按列收集修改行号
            column = modification['column']
            if column and modification['row'] > 0:
                column_modifications[column].append(modification['row'])

        # 转换为标准列名并填充
        standardized_column_mods = self._standardize_column_modifications(column_modifications)

        return {
            'table_name': self._extract_table_name(comparison_result),
            'total_rows': total_rows,
            'total_modifications': len(modifications),
            'modifications': modifications,
            'column_modifications': standardized_column_mods
        }

    def _extract_table_name(self, comparison_result: Dict) -> str:
        """从对比结果中提取表名"""
        # 尝试从审计日志中提取文件名
        audit_log = comparison_result.get('audit_log', [])
        if audit_log:
            details = audit_log[0].get('details', {})
            file2_path = details.get('file2', '')
            if file2_path:
                # 从路径中提取文件名
                filename = os.path.basename(file2_path)
                # 移除.csv扩展名
                table_name = filename.replace('.csv', '')
                return table_name

        # 默认表名
        return "数据表"

    def _standardize_column_modifications(self, column_mods: Dict[str, List[int]]) -> Dict[str, List[int]]:
        """将列修改映射到标准19列"""
        standardized = {}

        # 为每个标准列初始化
        for std_col in self.standard_columns:
            standardized[std_col] = []

        # 映射实际列到标准列
        column_mapping = self._create_column_mapping()

        for actual_col, row_list in column_mods.items():
            # 尝试找到匹配的标准列
            std_col = column_mapping.get(actual_col)
            if std_col and std_col in standardized:
                standardized[std_col] = row_list
            else:
                # 如果无法映射，尝试模糊匹配
                for std in self.standard_columns:
                    if actual_col in std or std in actual_col:
                        standardized[std] = row_list
                        break

        return standardized

    def _create_column_mapping(self) -> Dict[str, str]:
        """创建实际列名到标准列名的映射"""
        # 常见的映射关系
        mapping = {
            'id': '序号',
            'type': '项目类型',
            'source': '来源',
            'start_time': '任务发起时间',
            'target': '目标对齐',
            'kr': '关键KR对齐',
            'content': '具体计划内容',
            'guidance': '邓总指导登记',
            'owner': '负责人',
            'assistant': '协助人',
            'supervisor': '监督人',
            'importance': '重要程度',
            'deadline': '预计完成时间',
            'progress': '完成进度',
            'link': '完成链接',
            'review': '经理分析复盘',
            'review_time': '最新复盘时间',
            'report': '对上汇报',
            'application': '应用情况'
        }

        # 添加一些中文变体
        mapping.update({
            '负责人': '负责人',
            '状态': '完成进度',
            'status': '完成进度',
            'name': '项目类型',
            'department': '来源'
        })

        return mapping

    def calculate_heatmap_matrix(self, table_data_list: List[Dict]) -> List[List[float]]:
        """
        基于真实修改数据计算热力图矩阵

        Args:
            table_data_list: 多个表格的数据列表

        Returns:
            N×19的热力图矩阵
        """
        matrix = []

        for table_data in table_data_list:
            row_scores = []
            total_rows = table_data.get('total_rows', 1)
            column_mods = table_data.get('column_modifications', {})

            # 为每个标准列计算分数
            for std_col in self.standard_columns:
                mod_rows = column_mods.get(std_col, [])
                modification_count = len(mod_rows)

                # 基于修改比例和列级别计算分数
                score = self._calculate_column_score(modification_count, total_rows, std_col)
                row_scores.append(score)

            matrix.append(row_scores)

        return matrix

    def _get_column_level(self, column_name: str) -> str:
        """获取列的风险级别"""
        if column_name in self.L1_COLUMNS:
            return "L1"
        elif column_name in self.L2_COLUMNS:
            return "L2"
        elif column_name in self.L3_COLUMNS:
            return "L3"
        else:
            # 未分类的列默认为L3
            logger.warning(f"列 '{column_name}' 未在L1/L2/L3分类中，默认为L3")
            return "L3"

    def _calculate_column_score(self, modification_count: int, total_rows: int, column_name: str = None) -> float:
        """
        基于修改数量、总行数和列级别计算列的风险分数
        严格遵循规范06的打分策略
        """
        if total_rows == 0 or modification_count == 0:
            return 0.05  # 默认背景值

        # 获取列级别
        column_level = self._get_column_level(column_name) if column_name else "L3"

        # 根据列级别设置基础分
        if column_level == "L1":
            base_score = 0.8  # L1基础分
        elif column_level == "L2":
            base_score = 0.5  # L2基础分
        else:
            base_score = 0.2  # L3基础分

        # 计算变更系数
        ratio = modification_count / total_rows
        if ratio > 0.5:
            change_factor = 1.3  # 大量修改
        elif ratio > 0.3:
            change_factor = 1.2  # 中等修改
        elif ratio > 0.1:
            change_factor = 1.1  # 少量修改
        else:
            change_factor = 1.0  # 极少修改

        # 获取列权重
        column_weight = self.COLUMN_WEIGHTS.get(column_name, 1.0)

        # 计算最终分数
        score = base_score * change_factor * column_weight

        # 强制阈值实施（规范06要求）
        if column_level == "L1" and score > 0:
            score = max(0.8, score)  # L1强制最低0.8分（红色）
        elif column_level == "L2" and score > 0:
            score = max(0.6, score)  # L2强制最低0.6分（橙色）

        # 确保分数在有效范围内
        score = min(1.0, score)

        return round(score, 2)

    def generate_statistics(self, table_data_list: List[Dict]) -> Dict:
        """生成统计信息"""
        table_modifications = []
        table_row_counts = []
        column_total_modifications = [0] * 19  # 初始化19列

        for table_data in table_data_list:
            # 每表总修改数
            table_modifications.append(table_data.get('total_modifications', 0))
            # 每表总行数
            table_row_counts.append(table_data.get('total_rows', 0))

            # 累加每列的修改数
            column_mods = table_data.get('column_modifications', {})
            for i, std_col in enumerate(self.standard_columns):
                mod_rows = column_mods.get(std_col, [])
                column_total_modifications[i] += len(mod_rows)

        # 计算风险分布
        risk_distribution = self._calculate_risk_distribution(table_data_list)

        # 添加列级别统计
        column_level_stats = self._calculate_column_level_stats(table_data_list)

        return {
            'table_modifications': table_modifications,
            'table_row_counts': table_row_counts,
            'column_total_modifications': column_total_modifications,
            'risk_distribution': risk_distribution,
            'column_level_stats': column_level_stats  # 新增列级别统计
        }

    def _calculate_risk_distribution(self, table_data_list: List[Dict]) -> Dict:
        """计算风险等级分布"""
        high_risk = 0
        medium_risk = 0
        low_risk = 0

        for table_data in table_data_list:
            for mod in table_data.get('modifications', []):
                risk_level = mod.get('risk_level', 'L3')
                if risk_level == 'L1':
                    high_risk += 1
                elif risk_level == 'L2':
                    medium_risk += 1
                else:
                    low_risk += 1

        return {
            'high': high_risk,
            'medium': medium_risk,
            'low': low_risk
        }

    def _calculate_column_level_stats(self, table_data_list: List[Dict]) -> Dict:
        """计算列级别的统计信息"""
        l1_mods = 0
        l2_mods = 0
        l3_mods = 0

        for table_data in table_data_list:
            column_mods = table_data.get('column_modifications', {})
            for col_name, mod_rows in column_mods.items():
                if not mod_rows:
                    continue
                level = self._get_column_level(col_name)
                mod_count = len(mod_rows)
                if level == "L1":
                    l1_mods += mod_count
                elif level == "L2":
                    l2_mods += mod_count
                else:
                    l3_mods += mod_count

        return {
            'L1': {
                'count': l1_mods,
                'columns': self.L1_COLUMNS,
                'risk_level': 'EXTREME_HIGH'
            },
            'L2': {
                'count': l2_mods,
                'columns': self.L2_COLUMNS,
                'risk_level': 'HIGH',
                'requires_ai': True
            },
            'L3': {
                'count': l3_mods,
                'columns': self.L3_COLUMNS,
                'risk_level': 'LOW'
            }
        }

    def generate_table_details(self, table_data_list: List[Dict], excel_urls: Dict[str, str]) -> List[Dict]:
        """生成表格详细信息"""
        table_details = []

        for idx, table_data in enumerate(table_data_list):
            table_name = table_data.get('table_name', f'表格{idx+1}')

            table_detail = {
                'table_id': f'table_{idx+1:03d}',
                'table_name': table_name,
                'table_index': idx,
                'total_rows': table_data.get('total_rows', 0),
                'total_modifications': table_data.get('total_modifications', 0),
                'overall_risk_score': self._calculate_overall_risk(table_data),
                'excel_url': excel_urls.get(table_name, ''),
                'column_details': self._generate_column_details(table_data)
            }

            table_details.append(table_detail)

        return table_details

    def _generate_column_details(self, table_data: Dict) -> List[Dict]:
        """生成列详细信息"""
        column_details = []
        column_mods = table_data.get('column_modifications', {})
        total_rows = table_data.get('total_rows', 1)

        for col_idx, col_name in enumerate(self.standard_columns):
            modified_rows = column_mods.get(col_name, [])
            modification_count = len(modified_rows)

            column_detail = {
                'column_name': col_name,
                'column_index': col_idx,
                'column_level': self._get_column_level(col_name),  # 添加列级别
                'modification_count': modification_count,
                'modified_rows': sorted(modified_rows),  # 确保行号排序
                'score': self._calculate_column_score(modification_count, total_rows, col_name)
            }

            column_details.append(column_detail)

        return column_details

    def _calculate_overall_risk(self, table_data: Dict) -> float:
        """计算表格的整体风险分数"""
        total_mods = table_data.get('total_modifications', 0)
        total_rows = table_data.get('total_rows', 1)

        if total_rows == 0 or total_mods == 0:
            return 0.0

        # 收集所有列的风险分数
        risk_scores = []
        column_mods = table_data.get('column_modifications', {})

        for col_name in self.standard_columns:
            mod_count = len(column_mods.get(col_name, []))
            if mod_count > 0:
                score = self._calculate_column_score(mod_count, total_rows, col_name)
                # 根据列级别加权
                level = self._get_column_level(col_name)
                if level == "L1":
                    score *= 1.5  # L1列风险权重更高
                elif level == "L2":
                    score *= 1.2  # L2列中等权重
                risk_scores.append(score)

        if not risk_scores:
            return 0.0

        # 计算加权平均
        overall_score = sum(risk_scores) / len(risk_scores)

        # 确保分数在有效范围内
        overall_score = min(1.0, overall_score)

        return round(overall_score, 2)

    def convert_to_scoring_format(self, comparison_files: List[str], excel_urls: Dict[str, str]) -> Dict:
        """
        将多个CSV对比结果转换为综合打分所需格式

        Args:
            comparison_files: CSV对比结果文件路径列表
            excel_urls: 表名到Excel URL的映射

        Returns:
            综合打分生成器所需的数据格式
        """
        table_data_list = []

        # 处理每个对比文件
        for comp_file in comparison_files:
            if not os.path.exists(comp_file):
                print(f"⚠️ 文件不存在: {comp_file}")
                continue

            comparison_result = self.load_comparison_result(comp_file)
            table_data = self.extract_table_data(comparison_result)
            table_data_list.append(table_data)

        # 提取表名列表
        table_names = [td['table_name'] for td in table_data_list]

        # 生成热力图矩阵
        heatmap_matrix = self.calculate_heatmap_matrix(table_data_list)

        # 生成统计信息
        statistics = self.generate_statistics(table_data_list)

        # 生成表格详情
        table_details = self.generate_table_details(table_data_list, excel_urls)

        # 生成悬浮数据
        hover_data = self._generate_hover_data(table_data_list)

        return {
            'table_names': table_names,
            'heatmap_matrix': heatmap_matrix,
            'statistics': statistics,
            'table_details': table_details,
            'hover_data': hover_data,
            'total_modifications': sum(td['total_modifications'] for td in table_data_list)
        }

    def _generate_hover_data(self, table_data_list: List[Dict]) -> Dict:
        """生成鼠标悬浮数据"""
        hover_data = {
            'description': '鼠标悬浮显示数据',
            'data': []
        }

        for idx, table_data in enumerate(table_data_list):
            column_mods = table_data.get('column_modifications', {})
            column_modifications = []

            for std_col in self.standard_columns:
                mod_count = len(column_mods.get(std_col, []))
                column_modifications.append(mod_count)

            hover_data['data'].append({
                'table_index': idx,
                'column_modifications': column_modifications,
                'column_levels': [self._get_column_level(col) for col in self.standard_columns]  # 添加列级别信息
            })

        return hover_data


# 测试函数
def test_adapter():
    """测试适配器功能"""
    adapter = ComparisonToScoringAdapter()

    # 测试文件
    test_file = "/root/projects/tencent-doc-manager/csv_security_results/test_comparison_comparison.json"

    if os.path.exists(test_file):
        # 加载并转换
        comparison_result = adapter.load_comparison_result(test_file)
        table_data = adapter.extract_table_data(comparison_result)

        print("📊 提取的表格数据:")
        print(f"  表名: {table_data['table_name']}")
        print(f"  总行数: {table_data['total_rows']}")
        print(f"  总修改数: {table_data['total_modifications']}")
        print(f"  列修改分布: {list(table_data['column_modifications'].keys())[:5]}...")

        # 测试完整转换
        excel_urls = {"test_comparison": "https://docs.qq.com/sheet/test"}
        scoring_data = adapter.convert_to_scoring_format([test_file], excel_urls)

        print("\n✅ 转换后的数据:")
        print(f"  表格数: {len(scoring_data['table_names'])}")
        print(f"  矩阵维度: {len(scoring_data['heatmap_matrix'])}×19")
        print(f"  总修改数: {scoring_data['total_modifications']}")


if __name__ == "__main__":
    test_adapter()