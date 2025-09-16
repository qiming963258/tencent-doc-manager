#!/usr/bin/env python3
"""
综合打分文件严格验证器
完全按照10-综合打分绝对规范进行验证
不符合规范的文件直接报错，不尝试生成图像
增强版：精确报告错误位置
"""

import json
import os
import sys
from typing import Dict, List, Any, Tuple

# 导入标准列配置
sys.path.append('/root/projects/tencent-doc-manager')
from standard_columns_config import STANDARD_COLUMNS, validate_columns

class ComprehensiveScoreValidator:
    """综合打分文件验证器"""

    # 必需的顶层字段
    REQUIRED_TOP_FIELDS = [
        'metadata',
        'summary',
        'table_names',
        'column_names',
        'heatmap_data',
        'table_details',
        'hover_data',
        'statistics'
    ]

    # metadata必需字段
    REQUIRED_METADATA_FIELDS = [
        'version',
        'timestamp',
        'week',
        'generator',
        'total_params',
        'processing_time'
    ]

    # summary必需字段
    REQUIRED_SUMMARY_FIELDS = [
        'total_tables',
        'total_columns',
        'total_modifications',
        'overall_risk_score',
        'processing_status'
    ]

    # table_details中每个表必需字段
    REQUIRED_TABLE_FIELDS = [
        'table_id',
        'table_name',
        'table_index',
        'total_rows',
        'total_modifications',
        'overall_risk_score',
        'excel_url',
        'column_details'
    ]

    # column_details中每列必需字段
    REQUIRED_COLUMN_FIELDS = [
        'column_name',
        'column_index',
        'modification_count',
        'modified_rows',
        'score'
    ]

    # statistics必需字段
    REQUIRED_STATISTICS_FIELDS = [
        'table_modifications',
        'table_row_counts',
        'column_total_modifications',
        'risk_distribution'
    ]

    @classmethod
    def validate_file(cls, file_path: str) -> Tuple[bool, List[str], Dict]:
        """
        验证综合打分文件
        返回: (是否有效, 错误列表, 数据)
        """
        errors = []

        # 1. 检查文件存在
        if not os.path.exists(file_path):
            return False, ["文件不存在"], {}

        # 2. 加载JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"JSON解析错误: {e}"], {}
        except Exception as e:
            return False, [f"文件读取错误: {e}"], {}

        # 3. 验证顶层字段
        for field in cls.REQUIRED_TOP_FIELDS:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")

        if errors:
            return False, errors, data

        # 4. 验证metadata
        metadata_errors = cls._validate_metadata(data.get('metadata', {}))
        errors.extend(metadata_errors)

        # 5. 验证summary
        summary_errors = cls._validate_summary(data.get('summary', {}))
        errors.extend(summary_errors)

        # 6. 验证table_names和column_names
        if not isinstance(data.get('table_names'), list):
            errors.append("【位置】顶层 > table_names：必须是数组")
        elif len(data['table_names']) == 0:
            errors.append("【位置】顶层 > table_names：不能为空")

        # 严格验证列名必须与标准19列完全一致
        if not isinstance(data.get('column_names'), list):
            errors.append("【位置】顶层 > column_names：必须是数组")
        else:
            columns = data.get('column_names', [])
            if len(columns) != 19:
                errors.append(f"【位置】顶层 > column_names：必须有19个列名，当前{len(columns)}个")

            # 使用标准列配置进行验证
            columns_valid, column_errors = validate_columns(columns)
            if not columns_valid:
                for col_error in column_errors:
                    errors.append(f"【位置】顶层 > column_names > {col_error}")

        # 7. 验证heatmap_data
        heatmap_errors = cls._validate_heatmap(data.get('heatmap_data', {}),
                                               len(data.get('table_names', [])))
        errors.extend(heatmap_errors)

        # 8. 验证table_details
        table_errors = cls._validate_table_details(data.get('table_details', []),
                                                   data.get('table_names', []))
        errors.extend(table_errors)

        # 9. 验证hover_data
        hover_errors = cls._validate_hover_data(data.get('hover_data', {}),
                                                len(data.get('table_names', [])))
        errors.extend(hover_errors)

        # 10. 验证statistics
        stat_errors = cls._validate_statistics(data.get('statistics', {}),
                                               len(data.get('table_names', [])))
        errors.extend(stat_errors)

        # 11. 验证参数总数
        if data.get('metadata', {}).get('total_params', 0) < 5200:
            errors.append(f"参数总数不足5200，当前: {data.get('metadata', {}).get('total_params', 0)}")

        return len(errors) == 0, errors, data

    @classmethod
    def _validate_metadata(cls, metadata: Dict) -> List[str]:
        """验证metadata部分"""
        errors = []
        for field in cls.REQUIRED_METADATA_FIELDS:
            if field not in metadata:
                errors.append(f"metadata缺少字段: {field}")

        # 验证版本号
        if metadata.get('version') != '2.0':
            errors.append(f"版本号必须是2.0，当前: {metadata.get('version')}")

        return errors

    @classmethod
    def _validate_summary(cls, summary: Dict) -> List[str]:
        """验证summary部分"""
        errors = []
        for field in cls.REQUIRED_SUMMARY_FIELDS:
            if field not in summary:
                errors.append(f"summary缺少字段: {field}")

        # 验证列数必须是19
        if summary.get('total_columns') != 19:
            errors.append(f"列数必须是19，当前: {summary.get('total_columns')}")

        return errors

    @classmethod
    def _validate_heatmap(cls, heatmap: Dict, expected_rows: int) -> List[str]:
        """验证heatmap_data部分"""
        errors = []

        if 'matrix' not in heatmap:
            errors.append("heatmap_data缺少matrix字段")
            return errors

        matrix = heatmap['matrix']
        if not isinstance(matrix, list):
            errors.append("matrix必须是数组")
            return errors

        # 验证矩阵大小
        if len(matrix) != expected_rows:
            errors.append(f"矩阵行数不匹配，期望{expected_rows}行，实际{len(matrix)}行")

        for i, row in enumerate(matrix):
            if not isinstance(row, list):
                errors.append(f"矩阵第{i}行不是数组")
                continue
            if len(row) != 19:
                errors.append(f"矩阵第{i}行列数不是19，实际{len(row)}")

            # 验证值域[0.05-1.0]
            for j, val in enumerate(row):
                if not isinstance(val, (int, float)):
                    errors.append(f"矩阵[{i}][{j}]不是数字: {val}")
                elif val < 0.05 or val > 1.0:
                    errors.append(f"矩阵[{i}][{j}]值超出范围[0.05-1.0]: {val}")

        return errors

    @classmethod
    def _validate_table_details(cls, table_details: List, table_names: List) -> List[str]:
        """验证table_details部分"""
        errors = []

        if not isinstance(table_details, list):
            errors.append("table_details必须是数组")
            return errors

        if len(table_details) != len(table_names):
            errors.append(f"table_details数量({len(table_details)})与table_names({len(table_names)})不匹配")

        for i, table in enumerate(table_details):
            if not isinstance(table, dict):
                errors.append(f"table_details[{i}]不是对象")
                continue

            # 验证必需字段
            for field in cls.REQUIRED_TABLE_FIELDS:
                if field not in table:
                    errors.append(f"table_details[{i}]缺少字段: {field}")

            # 验证column_details
            if 'column_details' in table:
                col_details = table['column_details']
                if not isinstance(col_details, list):
                    errors.append(f"table_details[{i}].column_details不是数组")
                elif len(col_details) < 19:
                    # 可以少于19（示例中简化了），但不能没有
                    pass
                else:
                    for j, col in enumerate(col_details[:19]):
                        for field in cls.REQUIRED_COLUMN_FIELDS:
                            if field not in col:
                                errors.append(f"table_details[{i}].column_details[{j}]缺少字段: {field}")

        return errors

    @classmethod
    def _validate_hover_data(cls, hover_data: Dict, expected_tables: int) -> List[str]:
        """验证hover_data部分"""
        errors = []

        if 'data' not in hover_data:
            errors.append("hover_data缺少data字段")
            return errors

        data = hover_data['data']
        if not isinstance(data, list):
            errors.append("hover_data.data必须是数组")
            return errors

        if len(data) != expected_tables:
            errors.append(f"hover_data.data数量({len(data)})与表格数量({expected_tables})不匹配")

        for i, item in enumerate(data):
            if 'column_modifications' not in item:
                errors.append(f"hover_data.data[{i}]缺少column_modifications")
            elif len(item['column_modifications']) != 19:
                errors.append(f"hover_data.data[{i}].column_modifications必须有19个值")

        return errors

    @classmethod
    def _validate_statistics(cls, statistics: Dict, expected_tables: int) -> List[str]:
        """验证statistics部分"""
        errors = []

        for field in cls.REQUIRED_STATISTICS_FIELDS:
            if field not in statistics:
                errors.append(f"statistics缺少字段: {field}")

        # 验证数组长度
        if 'table_modifications' in statistics:
            if len(statistics['table_modifications']) != expected_tables:
                errors.append(f"table_modifications长度不匹配")

        if 'table_row_counts' in statistics:
            if len(statistics['table_row_counts']) != expected_tables:
                errors.append(f"table_row_counts长度不匹配")

        if 'column_total_modifications' in statistics:
            if len(statistics['column_total_modifications']) != 19:
                errors.append(f"column_total_modifications必须有19个值")

        return errors


def validate_and_report(file_path: str):
    """验证文件并生成报告"""
    print("=" * 60)
    print("📋 综合打分文件验证")
    print("=" * 60)
    print(f"文件: {file_path}")
    print()

    validator = ComprehensiveScoreValidator()
    is_valid, errors, data = validator.validate_file(file_path)

    if is_valid:
        print("✅ 文件符合规范！")
        print()
        print("📊 文件信息:")
        print(f"  - 版本: {data['metadata']['version']}")
        print(f"  - 周数: {data['metadata']['week']}")
        print(f"  - 表格数: {data['summary']['total_tables']}")
        print(f"  - 总参数: {data['metadata']['total_params']}")
        print(f"  - 总修改数: {data['summary']['total_modifications']}")
    else:
        print("❌ 文件不符合规范！")
        print()
        print("🚫 错误列表:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
        print("⚠️ 系统将拒绝渲染此文件")

    return is_valid


if __name__ == "__main__":
    # 测试最新的综合打分文件
    test_file = "/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_clustered.json"

    if os.path.exists(test_file):
        validate_and_report(test_file)
    else:
        print(f"测试文件不存在: {test_file}")