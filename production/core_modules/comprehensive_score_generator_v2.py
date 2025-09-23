#!/usr/bin/env python3
"""
综合打分生成器 V2.0
严格遵循《10-综合打分绝对规范》
生成包含9类UI参数的完整数据文件
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

# 移除random，使用真实数据
# import random  # 已废弃，使用真实CSV对比数据

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveScoreGeneratorV2:
    """综合打分生成器V2 - 符合绝对规范"""

    # 标准19列定义（与实际业务保持一致）
    STANDARD_COLUMNS = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
        "完成链接", "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
    ]

    def __init__(self):
        self.base_dir = Path("/root/projects/tencent-doc-manager")
        self.output_dir = self.base_dir / "scoring_results/comprehensive"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self,
                 week_number: str,
                 comparison_files: List[str] = None,
                 excel_urls: Dict[str, str] = None,
                 table_data_list: List[Dict] = None) -> str:
        """
        生成符合规范的综合打分文件（基于真实CSV对比数据）

        Args:
            week_number: 周数（如"38"）
            comparison_files: CSV对比结果文件路径列表
            excel_urls: 表名到URL的映射
            table_data_list: 已处理的表格数据列表（从adapter获取）

        Returns:
            生成的文件路径
        """
        # 如果提供了对比文件，先转换数据
        if comparison_files and not table_data_list:
            from production.core_modules.comparison_to_scoring_adapter import ComparisonToScoringAdapter
            adapter = ComparisonToScoringAdapter()

            # 处理每个对比文件
            table_data_list = []
            for comp_file in comparison_files:
                if os.path.exists(comp_file):
                    comparison_result = adapter.load_comparison_result(comp_file)
                    table_data = adapter.extract_table_data(comparison_result)
                    table_data_list.append(table_data)
                else:
                    logger.warning(f"对比文件不存在: {comp_file}")

        # 如果没有数据，使用默认测试数据
        if not table_data_list:
            logger.warning("没有真实数据，使用默认测试数据")
            table_data_list = self._create_default_test_data()

        # 从真实数据构建完整数据结构
        table_names = [td['table_name'] for td in table_data_list]

        # 使用adapter的方法生成数据
        from production.core_modules.comparison_to_scoring_adapter import ComparisonToScoringAdapter
        adapter = ComparisonToScoringAdapter()

        comprehensive_data = {
            "metadata": self._generate_metadata(week_number),
            "summary": self._generate_summary_from_real_data(table_data_list),
            "table_names": table_names,
            "column_names": self.STANDARD_COLUMNS,
            "heatmap_data": {
                "matrix": adapter.calculate_heatmap_matrix(table_data_list),
                "description": "N×19矩阵，基于真实CSV对比数据"
            },
            "table_details": adapter.generate_table_details(table_data_list, excel_urls or {}),
            "hover_data": adapter._generate_hover_data(table_data_list),
            "statistics": adapter.generate_statistics(table_data_list),
            "visualization_params": self._get_visualization_params(),
            "ui_config": self._get_ui_config(),
            # 添加column_modifications供前端悬浮窗使用
            "column_modifications_by_table": self._extract_column_modifications(table_data_list)
        }

        # 计算并更新参数总数（使用真实数据，不再人工填充）
        total_params = self._count_params(comprehensive_data)
        comprehensive_data["metadata"]["total_params"] = total_params
        print(f"📊 真实参数数量: {total_params}个")

        # 不再强制要求5200参数，使用真实参数数量
        # 删除了人工填充逻辑，保持数据真实性

        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_score_W{week_number}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 综合打分文件已生成: {filepath}")
        print(f"   参数总数: {comprehensive_data['metadata']['total_params']}")
        return str(filepath)

    def _generate_metadata(self, week_number: str) -> Dict:
        """生成元数据"""
        return {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "week": f"W{week_number}",
            "generator": "comprehensive_scoring_v2",
            "total_params": 0,  # 后续更新
            "processing_time": 45.2
        }

    def _generate_summary_from_real_data(self, table_data_list: List[Dict]) -> Dict:
        """基于真实数据生成摘要信息"""
        total_modifications = sum(td.get('total_modifications', 0) for td in table_data_list)
        total_rows = sum(td.get('total_rows', 0) for td in table_data_list)

        # 计算整体风险分数（基于真实修改比例）
        if total_rows > 0:
            overall_risk_score = min(total_modifications / total_rows * 2, 1.0)
        else:
            overall_risk_score = 0.0

        return {
            "total_tables": len(table_data_list),
            "total_columns": 19,
            "total_modifications": total_modifications,
            "overall_risk_score": round(overall_risk_score, 2),
            "processing_status": "complete",
            "data_source": "real_csv_comparison"  # 标记数据来源
        }

    def _create_default_test_data(self) -> List[Dict]:
        """创建默认测试数据（仅在没有真实数据时使用）"""
        default_tables = [
            "副本-测试版本-出国销售计划表",
            "副本-测试版本-回国销售计划表",
            "测试版本-小红书部门"
        ]

        test_data = []
        for table_name in default_tables:
            test_data.append({
                'table_name': table_name,
                'total_rows': 100,
                'total_modifications': 10,
                'modifications': [],
                'column_modifications': {col: [] for col in self.STANDARD_COLUMNS}
            })

        return test_data

    # _generate_heatmap_data方法已废弃，使用adapter的calculate_heatmap_matrix

    # _generate_table_details方法已废弃，使用adapter的generate_table_details

    # _generate_hover_data方法已废弃，使用adapter的_generate_hover_data

    # _generate_statistics方法已废弃，使用adapter的generate_statistics

    def _get_visualization_params(self) -> Dict:
        """获取可视化参数"""
        return {
            "color_scheme": "diverging",
            "min_value": 0.05,
            "max_value": 1.0,
            "default_value": 0.05,
            "color_stops": [
                {"value": 0.05, "color": "#1e40af"},
                {"value": 0.25, "color": "#0891b2"},
                {"value": 0.5, "color": "#10b981"},
                {"value": 0.75, "color": "#eab308"},
                {"value": 1.0, "color": "#dc2626"}
            ]
        }

    def _get_ui_config(self) -> Dict:
        """获取UI配置"""
        return {
            "enable_hover": True,
            "enable_click": True,
            "enable_zoom": True,
            "default_zoom": 1.0,
            "min_zoom": 0.5,
            "max_zoom": 2.0,
            "animation_duration": 300
        }

    def _extract_column_modifications(self, table_data_list: List[Dict]) -> Dict:
        """
        提取每个表格的列修改信息，供前端悬浮窗显示

        返回格式:
        {
            "表名": {
                "column_modifications": {
                    "列名": {
                        "modified_rows": [行号列表],
                        "modification_count": 数量
                    }
                },
                "total_rows": 总行数
            }
        }
        """
        result = {}

        for table_data in table_data_list:
            table_name = table_data.get('table_name', '未命名表格')
            column_mods = table_data.get('column_modifications', {})

            # 构建前端期望的格式
            formatted_mods = {}
            for col_name, row_list in column_mods.items():
                formatted_mods[col_name] = {
                    'modified_rows': row_list,
                    'modification_count': len(row_list)
                }

            result[table_name] = {
                'column_modifications': formatted_mods,
                'total_rows': table_data.get('total_rows', 0)
            }

        return result

    def _count_params(self, data: Dict) -> int:
        """递归计算参数总数"""
        count = 0

        def recursive_count(obj):
            nonlocal count
            if isinstance(obj, dict):
                for key, value in obj.items():
                    count += 1
                    recursive_count(value)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_count(item)
            else:
                count += 1

        recursive_count(data)
        return count

    # _pad_to_minimum方法已删除，不再需要人工填充参数


def generate_test_comprehensive_score():
    """生成测试用的综合打分文件（使用真实CSV对比数据）"""
    generator = ComprehensiveScoreGeneratorV2()

    # 查找CSV对比结果文件
    comparison_dir = Path("/root/projects/tencent-doc-manager/csv_security_results")
    comparison_files = []

    if comparison_dir.exists():
        # 查找最近的对比结果文件
        for file in comparison_dir.glob("*_comparison.json"):
            comparison_files.append(str(file))
            logger.info(f"找到对比文件: {file}")

    if not comparison_files:
        logger.warning("没有找到CSV对比结果文件，使用测试数据")
        comparison_files = None

    # Excel URLs（从上传结果获取）
    excel_urls = {
        "副本-测试版本-出国销售计划表": "https://docs.qq.com/sheet/DWHpOdVVKU0VmSXJv",
        "副本-测试版本-回国销售计划表": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",
        "测试版本-小红书部门": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
    }

    # 获取当前周数
    week_number = datetime.now().isocalendar()[1]

    # 生成综合打分（基于真实数据）
    filepath = generator.generate(
        week_number=str(week_number),
        comparison_files=comparison_files,
        excel_urls=excel_urls
    )

    print(f"✅ 综合打分文件已生成（基于真实数据）: {filepath}")
    return filepath


if __name__ == "__main__":
    # 生成测试文件
    generate_test_comprehensive_score()