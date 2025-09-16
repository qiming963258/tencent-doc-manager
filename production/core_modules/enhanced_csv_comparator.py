#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版CSV对比器 - 支持所有列的对比，不限于标准列
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedCSVComparator:
    """
    增强版CSV对比器
    - 对比所有列，不仅限于标准列
    - 保留原有的风险评分机制
    - 支持对角线模式检测
    """

    def __init__(self):
        # 标准列配置（用于风险评分，但不限制对比范围）
        self.standard_columns = {
            "序号": "L3",
            "项目管理ID": "L3",
            "项目类型": "L2",
            "来源": "L1",
            "任务发起时间": "L1",
            "目标对齐": "L1",
            "关键KR对齐": "L1",
            "具体计划内容": "L2",
            "邓总指导登记": "L2",
            "负责人": "L2",
            "协助人": "L2",
            "监督人": "L2",
            "重要程度": "L1",
            "预计完成时间": "L1",
            "完成进度": "L1",
            "完成链接": "L2",
            "经理分析复盘": "L3",
            "最新复盘时间": "L3",
            "对上汇报": "L3",
            "应用情况": "L3"
        }

        # 列号到名称的映射
        self.column_letter_mapping = {
            0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E',
            5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J',
            10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O',
            15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T'
        }

    def _load_csv(self, file_path: str) -> List[List[str]]:
        """加载CSV文件"""
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    reader = csv.reader(f)
                    data = list(reader)
                    logger.info(f"✅ 成功使用 {encoding} 编码加载文件")
                    return data
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(f"无法加载文件: {file_path}")

    def _get_column_name(self, headers: List[str], col_idx: int) -> str:
        """获取列名（优先使用标题行，否则使用列字母）"""
        if col_idx < len(headers) and headers[col_idx].strip():
            return headers[col_idx].strip()
        else:
            return f"列{self.column_letter_mapping.get(col_idx, col_idx+1)}"

    def compare_all_columns(self, file1_path: str, file2_path: str) -> Dict:
        """
        对比所有列的修改，不限于标准列

        返回:
            包含所有差异的字典，包括对角线模式检测
        """
        try:
            logger.info(f"🔍 开始增强版CSV对比")
            logger.info(f"  基准文件: {Path(file1_path).name}")
            logger.info(f"  当前文件: {Path(file2_path).name}")

            # 加载文件
            data1 = self._load_csv(file1_path)
            data2 = self._load_csv(file2_path)

            if not data1 or not data2:
                raise ValueError("文件数据为空")

            # 获取标题行（假设第一行是标题）
            headers1 = data1[0] if data1 else []
            headers2 = data2[0] if data2 else []

            # 准备差异列表
            differences = []
            diagonal_pattern = []  # 对角线模式检测
            column_modifications = {}  # 每列的修改统计

            # 确定对比范围
            max_cols = max(len(headers1), len(headers2))
            max_rows = min(len(data1), len(data2))

            logger.info(f"  对比范围: {max_rows}行 × {max_cols}列")

            # 逐行逐列对比（从第二行开始，跳过标题）
            for row_idx in range(1, max_rows):
                row1 = data1[row_idx] if row_idx < len(data1) else []
                row2 = data2[row_idx] if row_idx < len(data2) else []

                # 对比每一列
                for col_idx in range(max_cols):
                    val1 = row1[col_idx] if col_idx < len(row1) else ""
                    val2 = row2[col_idx] if col_idx < len(row2) else ""

                    # 清理值
                    val1 = str(val1).strip()
                    val2 = str(val2).strip()

                    # 检测差异
                    if val1 != val2:
                        col_name = self._get_column_name(headers1, col_idx)
                        col_letter = self.column_letter_mapping.get(col_idx, str(col_idx+1))

                        # 记录差异
                        diff = {
                            "序号": len(differences) + 1,
                            "行号": row_idx + 1,  # Excel行号（从1开始）
                            "列号": col_idx + 1,  # Excel列号（从1开始）
                            "列字母": col_letter,
                            "列名": col_name,
                            "原值": val1,
                            "新值": val2,
                            "位置": f"{col_letter}{row_idx+1}",
                            "风险等级": self.standard_columns.get(col_name, "L3")
                        }
                        differences.append(diff)

                        # 统计列修改
                        if col_name not in column_modifications:
                            column_modifications[col_name] = []
                        column_modifications[col_name].append(row_idx + 1)

                        # 检测对角线模式
                        if col_idx == row_idx - 3:  # B4, C5, D6...的模式
                            diagonal_pattern.append(diff)

            # 分析结果
            logger.info(f"✅ 对比完成:")
            logger.info(f"  总差异数: {len(differences)}")
            logger.info(f"  修改的列数: {len(column_modifications)}")
            logger.info(f"  对角线模式: {len(diagonal_pattern)}个")

            # 如果检测到对角线模式，记录详情
            if diagonal_pattern:
                logger.info("  📐 检测到对角线修改模式:")
                for d in diagonal_pattern[:5]:  # 显示前5个
                    logger.info(f"    {d['位置']}: {d['列名']}")
                if len(diagonal_pattern) > 5:
                    logger.info(f"    ... 还有{len(diagonal_pattern)-5}个")

            # 构建结果
            result = {
                "success": True,
                "total_differences": len(differences),
                "differences": differences,
                "column_modifications": column_modifications,
                "diagonal_pattern": {
                    "detected": len(diagonal_pattern) > 0,
                    "count": len(diagonal_pattern),
                    "pattern": diagonal_pattern
                },
                "metadata": {
                    "file1_rows": len(data1),
                    "file1_cols": len(headers1),
                    "file2_rows": len(data2),
                    "file2_cols": len(headers2),
                    "compared_rows": max_rows - 1,
                    "compared_cols": max_cols,
                    "timestamp": datetime.now().isoformat()
                }
            }

            return result

        except Exception as e:
            logger.error(f"❌ 增强版CSV对比失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_differences": 0,
                "differences": []
            }

    def save_comparison_result(self, result: Dict, output_path: str):
        """保存对比结果"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 结果已保存到: {output_path}")

        except Exception as e:
            logger.error(f"保存失败: {e}")


def test_diagonal_pattern():
    """测试对角线模式检测"""
    comparator = EnhancedCSVComparator()

    # 查找最新的CSV文件
    csv_dir = Path('/root/projects/tencent-doc-manager/csv_versions/2025_W38')
    baseline_dir = csv_dir / 'baseline'
    midweek_dir = csv_dir / 'midweek'

    # 查找文件
    baseline_files = list(baseline_dir.glob('*出国*.csv')) if baseline_dir.exists() else []
    midweek_files = list(midweek_dir.glob('*出国*.csv')) if midweek_dir.exists() else []

    if not baseline_files or not midweek_files:
        logger.error("找不到测试文件")
        return

    # 执行对比
    result = comparator.compare_all_columns(
        str(baseline_files[0]),
        str(midweek_files[0])
    )

    # 保存结果
    output_path = '/root/projects/tencent-doc-manager/comparison_results/enhanced_comparison_result.json'
    comparator.save_comparison_result(result, output_path)

    return result


if __name__ == "__main__":
    # 执行测试
    result = test_diagonal_pattern()

    if result and result['success']:
        print(f"\n📊 增强版对比结果总结:")
        print(f"  总修改数: {result['total_differences']}")
        print(f"  对角线模式: {result['diagonal_pattern']['detected']}")

        if result['diagonal_pattern']['detected']:
            print(f"  对角线修改数: {result['diagonal_pattern']['count']}")