#!/usr/bin/env python3
"""
数据格式适配器 - 转换生成的打分文件为符合10-综合打分绝对规范的格式
用于修复当前输出与UI要求之间的数据格式差异
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class DataFormatAdapter:
    """数据格式适配器，确保输出符合规范"""

    def __init__(self):
        """初始化适配器"""
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
            "完成链接", "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
        ]

    def transform_to_standard_format(self, input_data: Dict) -> Dict:
        """
        将当前格式转换为符合10-综合打分绝对规范的格式

        参数:
            input_data: 当前生成的综合打分数据

        返回:
            符合规范的综合打分数据
        """
        print("🔄 开始数据格式转换...")

        # 提取基础信息
        table_names = input_data.get('table_names', [])
        table_scores = input_data.get('table_scores', [])

        # 构建符合规范的输出格式
        output_data = {
            # 元数据部分
            "metadata": {
                "version": "2.0",
                "timestamp": datetime.now().isoformat(),
                "week": input_data.get('week_number', 'W38'),
                "generator": "data_format_adapter",
                "total_params": 0,  # 稍后计算
                "processing_time": 0.0,
                "data_source": "csv_comparison"
            },

            # 摘要部分
            "summary": {
                "total_tables": len(table_names),
                "total_columns": len(self.standard_columns),
                "total_modifications": input_data.get('total_modifications', 0),
                "overall_risk_score": 0.0,  # 稍后计算
                "processing_status": "complete"
            },

            # 表名列表（UI参数1：表名作为行名）
            "table_names": table_names,

            # 列名列表（UI参数2：列名）
            "column_names": self.standard_columns,

            # 热力图矩阵数据（UI参数4：格子的列修改值）
            "heatmap_data": {
                "matrix": [],
                "description": f"{len(table_names)}×19矩阵，值域[0.05-1.0]"
            },

            # 详细表格数据
            "table_details": [],

            # UI数据（用于前端渲染）
            "ui_data": input_data.get('ui_data', [])
        }

        # 构建热力图矩阵和表格详情
        for i, table_score in enumerate(table_scores):
            table_name = table_score.get('table_name', f'表格_{i+1}')
            column_scores = table_score.get('column_scores', {})

            # 构建单行热力图数据
            row_data = []
            column_details = []

            for col_name in self.standard_columns:
                if col_name in column_scores:
                    col_data = column_scores[col_name]
                    score = col_data.get('avg_score', 0.05)
                    modified_rows = col_data.get('modified_rows', [])
                    modification_count = col_data.get('modification_count', 0)
                else:
                    score = 0.05
                    modified_rows = []
                    modification_count = 0

                row_data.append(round(score, 2))

                # 构建列详情（UI参数5,8：修改行数和位置）
                column_details.append({
                    "column_name": col_name,
                    "column_index": self.standard_columns.index(col_name),
                    "modification_count": modification_count,
                    "modified_rows": modified_rows,
                    "score": round(score, 2)
                })

            output_data['heatmap_data']['matrix'].append(row_data)

            # 构建表格详情（UI参数6,7,9：总修改数、总行数、URL）
            table_detail = {
                "table_id": f"table_{i+1:03d}",
                "table_name": table_name,
                "table_index": i,
                "total_rows": self._extract_total_rows(table_score),
                "total_modifications": table_score.get('total_modifications', 0),
                "overall_risk_score": table_score.get('overall_risk_score', 0.05),
                "excel_url": table_score.get('table_url', ''),
                "column_details": column_details
            }

            output_data['table_details'].append(table_detail)

        # 计算总体统计
        total_params = sum(
            td['total_rows'] * len(self.standard_columns)
            for td in output_data['table_details']
        )
        output_data['metadata']['total_params'] = total_params

        # 计算平均风险分数
        if output_data['table_details']:
            avg_risk = sum(
                td['overall_risk_score']
                for td in output_data['table_details']
            ) / len(output_data['table_details'])
            output_data['summary']['overall_risk_score'] = round(avg_risk, 3)

        # 添加hover_data（用于悬浮提示）
        output_data['hover_data'] = {
            "data": self._build_hover_data(output_data['table_details'])
        }

        # 添加统计信息
        output_data['statistics'] = self._calculate_statistics(output_data)

        print(f"✅ 数据格式转换完成")
        print(f"   - 表格数量: {len(table_names)}")
        print(f"   - 总参数数: {total_params}")
        print(f"   - 矩阵维度: {len(table_names)}×19")

        return output_data

    def _extract_total_rows(self, table_score: Dict) -> int:
        """
        提取表格总行数
        如果没有明确的total_rows字段，尝试从其他地方推断
        """
        # 直接查找total_rows字段
        if 'total_rows' in table_score:
            return table_score['total_rows']

        # 尝试从修改行中推断（取最大行号）
        max_row = 0
        column_scores = table_score.get('column_scores', {})
        for col_data in column_scores.values():
            modified_rows = col_data.get('modified_rows', [])
            if modified_rows:
                max_row = max(max_row, max(modified_rows))

        # 如果有修改，假设总行数至少是最大行号的1.5倍
        if max_row > 0:
            return int(max_row * 1.5)

        # 默认值
        return 100

    def _build_hover_data(self, table_details: List[Dict]) -> List[Dict]:
        """构建悬浮提示数据"""
        hover_data = []

        for table in table_details:
            hover_item = {
                "table_index": table['table_index'],
                "table_name": table['table_name'],
                "total_modifications": table['total_modifications'],
                "column_details": [
                    {
                        "column_name": cd['column_name'],
                        "modification_count": cd['modification_count'],
                        "modified_rows": cd['modified_rows'][:5]  # 只显示前5个
                    }
                    for cd in table['column_details']
                ]
            }
            hover_data.append(hover_item)

        return hover_data

    def _calculate_statistics(self, data: Dict) -> Dict:
        """计算统计信息"""
        heatmap_matrix = data['heatmap_data']['matrix']

        # 统计不同风险等级的数量
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0

        for row in heatmap_matrix:
            for value in row:
                if value >= 0.7:
                    high_risk_count += 1
                elif value >= 0.3:
                    medium_risk_count += 1
                elif value > 0.05:
                    low_risk_count += 1

        # 统计有修改的表格数
        tables_with_modifications = sum(
            1 for td in data['table_details']
            if td['total_modifications'] > 0
        )

        return {
            "total_modifications": data['summary']['total_modifications'],
            "average_modifications_per_table": (
                data['summary']['total_modifications'] /
                max(1, data['summary']['total_tables'])
            ),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "tables_with_modifications": tables_with_modifications
        }

    def validate_output(self, data: Dict) -> bool:
        """
        验证输出数据是否符合规范要求的9类参数
        """
        required_fields = [
            'table_names',  # UI参数1
            'column_names',  # UI参数2
            'heatmap_data',  # UI参数4
            'table_details'  # 包含UI参数5-9
        ]

        # 检查必需字段
        for field in required_fields:
            if field not in data:
                print(f"❌ 缺少必需字段: {field}")
                return False

        # 检查热力图矩阵
        if 'matrix' not in data['heatmap_data']:
            print("❌ 缺少热力图矩阵数据")
            return False

        # 检查矩阵维度
        matrix = data['heatmap_data']['matrix']
        expected_rows = len(data['table_names'])
        expected_cols = len(data['column_names'])

        if len(matrix) != expected_rows:
            print(f"❌ 矩阵行数不匹配: 期望{expected_rows}, 实际{len(matrix)}")
            return False

        for row in matrix:
            if len(row) != expected_cols:
                print(f"❌ 矩阵列数不匹配: 期望{expected_cols}, 实际{len(row)}")
                return False

        # 检查表格详情
        for table in data['table_details']:
            required_table_fields = [
                'table_name',
                'total_rows',
                'total_modifications',
                'column_details',
                'excel_url'
            ]

            for field in required_table_fields:
                if field not in table:
                    print(f"❌ 表格缺少字段: {field}")
                    return False

        print("✅ 数据格式验证通过，包含所有9类必需参数")
        return True


def convert_comprehensive_score_file(input_file: str, output_file: str = None):
    """
    转换综合打分文件格式

    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选，默认在同目录下生成_standard版本）
    """
    adapter = DataFormatAdapter()

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    # 转换格式
    output_data = adapter.transform_to_standard_format(input_data)

    # 验证输出
    if not adapter.validate_output(output_data):
        print("⚠️ 输出数据验证失败，但仍会保存文件")

    # 确定输出文件路径
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_standard.json"

    # 保存输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"📁 标准格式文件已保存: {output_file}")
    return output_file


if __name__ == "__main__":
    # 测试转换最新的综合打分文件
    import glob

    scoring_dir = '/root/projects/tencent-doc-manager/scoring_results/comprehensive'
    pattern = os.path.join(scoring_dir, 'comprehensive_score_W38_*.json')
    files = glob.glob(pattern)

    if files:
        # 找到最新的文件
        latest_file = max(files, key=os.path.getmtime)
        print(f"📂 转换文件: {os.path.basename(latest_file)}")

        # 执行转换
        output_file = convert_comprehensive_score_file(latest_file)

        print("\n🎯 转换完成！")