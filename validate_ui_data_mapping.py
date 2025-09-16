#!/usr/bin/env python3
"""
UI数据映射规范验证脚本
验证综合打分系统生成的数据是否符合规范要求
基于《10-综合打分绝对规范》的UI数据映射关系
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

class UIDataMappingValidator:
    """UI数据映射验证器"""

    # 规范要求的UI数据映射关系
    UI_MAPPINGS = {
        'table_names': {'desc': '表名作为行名', 'ui': '热力图Y轴'},
        'column_names': {'desc': '列名', 'ui': '热力图X轴'},
        'heatmap_data.matrix': {'desc': '格子的列修改值', 'ui': '热力图数值'},
        'hover_data.data[].column_modifications': {'desc': '每表每列总修改行数', 'ui': '悬浮窗显示'},
        'statistics.table_modifications': {'desc': '每表总修改数', 'ui': '右侧统计'},
        'statistics.table_row_counts': {'desc': '每表总行数', 'ui': '一维图基础'},
        'table_details[].column_details[].modified_rows': {'desc': '每列修改行位置', 'ui': '一维图详细'},
        'table_details[].excel_url': {'desc': 'Excel URL', 'ui': '点击跳转'}
    }

    # 标准19列
    STANDARD_COLUMNS = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
        "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
    ]

    def __init__(self):
        self.base_dir = Path("/root/projects/tencent-doc-manager")
        self.validation_results = []
        self.errors = []
        self.warnings = []

    def validate_comprehensive_score_file(self, file_path: str) -> Tuple[bool, Dict]:
        """验证综合打分文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"\n📋 验证文件: {os.path.basename(file_path)}")
            print("=" * 60)

            # 1. 验证表名作为行名
            valid, msg = self._validate_table_names(data)
            self._log_result("table_names", valid, msg)

            # 2. 验证列名
            valid, msg = self._validate_column_names(data)
            self._log_result("column_names", valid, msg)

            # 3. 验证热力图矩阵
            valid, msg = self._validate_heatmap_matrix(data)
            self._log_result("heatmap_data.matrix", valid, msg)

            # 4. 验证悬浮数据
            valid, msg = self._validate_hover_data(data)
            self._log_result("hover_data", valid, msg)

            # 5. 验证统计信息
            valid, msg = self._validate_statistics(data)
            self._log_result("statistics", valid, msg)

            # 6. 验证表格详情
            valid, msg = self._validate_table_details(data)
            self._log_result("table_details", valid, msg)

            # 7. 验证数据一致性
            valid, msg = self._validate_data_consistency(data)
            self._log_result("data_consistency", valid, msg)

            # 生成验证报告
            return self._generate_report(data)

        except Exception as e:
            self.errors.append(f"文件读取失败: {e}")
            return False, {"success": False, "error": str(e)}

    def _validate_table_names(self, data: Dict) -> Tuple[bool, str]:
        """验证表名数组"""
        if 'table_names' not in data:
            return False, "❌ 缺少 table_names 字段"

        table_names = data['table_names']
        if not isinstance(table_names, list):
            return False, f"❌ table_names 应为数组，实际为 {type(table_names)}"

        if len(table_names) == 0:
            return False, "❌ table_names 数组为空"

        return True, f"✅ 包含 {len(table_names)} 个表名"

    def _validate_column_names(self, data: Dict) -> Tuple[bool, str]:
        """验证列名数组"""
        if 'column_names' not in data:
            return False, "❌ 缺少 column_names 字段"

        column_names = data['column_names']
        if not isinstance(column_names, list):
            return False, f"❌ column_names 应为数组，实际为 {type(column_names)}"

        if len(column_names) != 19:
            self.warnings.append(f"⚠️ 列数不是19，实际为 {len(column_names)}")

        # 检查是否符合标准列名
        if column_names != self.STANDARD_COLUMNS:
            missing = set(self.STANDARD_COLUMNS) - set(column_names)
            extra = set(column_names) - set(self.STANDARD_COLUMNS)
            if missing:
                self.warnings.append(f"⚠️ 缺少标准列: {missing}")
            if extra:
                self.warnings.append(f"⚠️ 额外的列: {extra}")

        return True, f"✅ 包含 {len(column_names)} 个列名"

    def _validate_heatmap_matrix(self, data: Dict) -> Tuple[bool, str]:
        """验证热力图矩阵"""
        # 检查直接的matrix字段
        if 'heatmap_data' in data and 'matrix' in data['heatmap_data']:
            matrix = data['heatmap_data']['matrix']
        else:
            return False, "❌ 缺少 heatmap_data.matrix 字段"

        if not isinstance(matrix, list):
            return False, f"❌ matrix 应为二维数组，实际为 {type(matrix)}"

        table_count = len(data.get('table_names', []))
        if len(matrix) != table_count:
            return False, f"❌ 矩阵行数({len(matrix)})与表格数({table_count})不匹配"

        # 检查每行的列数
        for i, row in enumerate(matrix):
            if len(row) != 19:
                self.warnings.append(f"⚠️ 第{i}行列数不是19，实际为{len(row)}")

        return True, f"✅ 矩阵大小 {len(matrix)}×{len(matrix[0]) if matrix else 0}"

    def _validate_hover_data(self, data: Dict) -> Tuple[bool, str]:
        """验证悬浮数据"""
        if 'hover_data' not in data:
            return False, "❌ 缺少 hover_data 字段"

        hover_data = data['hover_data']
        if 'data' not in hover_data:
            return False, "❌ hover_data 缺少 data 字段"

        hover_items = hover_data['data']
        table_count = len(data.get('table_names', []))

        if len(hover_items) != table_count:
            return False, f"❌ 悬浮数据数量({len(hover_items)})与表格数({table_count})不匹配"

        # 验证每个悬浮项的结构
        for item in hover_items:
            if 'column_modifications' not in item:
                return False, "❌ 悬浮数据项缺少 column_modifications"
            if len(item['column_modifications']) != 19:
                self.warnings.append(f"⚠️ 悬浮数据列数不是19")

        return True, f"✅ 包含 {len(hover_items)} 个悬浮数据项"

    def _validate_statistics(self, data: Dict) -> Tuple[bool, str]:
        """验证统计信息"""
        if 'statistics' not in data:
            return False, "❌ 缺少 statistics 字段"

        stats = data['statistics']
        required_fields = ['table_modifications', 'table_row_counts']

        for field in required_fields:
            if field not in stats:
                return False, f"❌ statistics 缺少 {field} 字段"

            if not isinstance(stats[field], list):
                return False, f"❌ statistics.{field} 应为数组"

            table_count = len(data.get('table_names', []))
            if len(stats[field]) != table_count:
                return False, f"❌ statistics.{field} 长度({len(stats[field])})与表格数({table_count})不匹配"

        return True, "✅ 统计信息完整"

    def _validate_table_details(self, data: Dict) -> Tuple[bool, str]:
        """验证表格详情"""
        if 'table_details' not in data:
            return False, "❌ 缺少 table_details 字段"

        details = data['table_details']
        if not isinstance(details, list):
            return False, f"❌ table_details 应为数组，实际为 {type(details)}"

        table_count = len(data.get('table_names', []))
        if len(details) != table_count:
            return False, f"❌ table_details 数量({len(details)})与表格数({table_count})不匹配"

        # 验证每个表格详情
        for i, detail in enumerate(details):
            # 检查必需字段
            if 'table_name' not in detail:
                return False, f"❌ table_details[{i}] 缺少 table_name"
            if 'excel_url' not in detail:
                self.warnings.append(f"⚠️ table_details[{i}] 缺少 excel_url")
            if 'column_details' not in detail:
                return False, f"❌ table_details[{i}] 缺少 column_details"

            # 验证列详情
            col_details = detail.get('column_details', [])
            if len(col_details) != 19:
                self.warnings.append(f"⚠️ table_details[{i}].column_details 列数不是19")

            for col_detail in col_details:
                if 'modified_rows' not in col_detail:
                    return False, f"❌ column_details 缺少 modified_rows"

        return True, f"✅ 包含 {len(details)} 个表格详情"

    def _validate_data_consistency(self, data: Dict) -> Tuple[bool, str]:
        """验证数据一致性"""
        issues = []

        # 1. 表名一致性
        table_names = data.get('table_names', [])
        table_details = data.get('table_details', [])

        if table_details:
            detail_names = [d.get('table_name', '') for d in table_details]
            if table_names != detail_names:
                issues.append("表名顺序不一致")

        # 2. 矩阵与统计数据一致性
        if 'heatmap_data' in data and 'matrix' in data['heatmap_data']:
            matrix = data['heatmap_data']['matrix']
            stats = data.get('statistics', {})

            # 验证修改数是否匹配
            if 'table_modifications' in stats:
                for i, row in enumerate(matrix):
                    calc_mods = sum(1 for v in row if v > 0.05)  # 大于背景值的格子
                    stat_mods = stats['table_modifications'][i] if i < len(stats['table_modifications']) else 0
                    # 允许一定误差
                    if abs(calc_mods - stat_mods) > 5:
                        issues.append(f"表{i}的修改数不一致: 矩阵计算={calc_mods}, 统计={stat_mods}")

        if issues:
            return False, f"❌ 发现一致性问题: {', '.join(issues[:3])}"

        return True, "✅ 数据一致性验证通过"

    def _log_result(self, field: str, valid: bool, message: str):
        """记录验证结果"""
        self.validation_results.append({
            'field': field,
            'valid': valid,
            'message': message
        })
        print(f"  {message}")

    def _generate_report(self, data: Dict) -> Tuple[bool, Dict]:
        """生成验证报告"""
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for r in self.validation_results if r['valid'])

        print("\n" + "=" * 60)
        print("📊 验证报告总结")
        print("=" * 60)

        # 统计信息
        print(f"✓ 通过检查: {passed_checks}/{total_checks}")
        print(f"✗ 失败检查: {total_checks - passed_checks}/{total_checks}")

        if self.warnings:
            print(f"\n⚠️ 警告 ({len(self.warnings)}):")
            for warning in self.warnings[:5]:
                print(f"  - {warning}")

        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)}):")
            for error in self.errors[:5]:
                print(f"  - {error}")

        # 判断整体是否通过
        overall_pass = passed_checks == total_checks and len(self.errors) == 0

        print(f"\n{'✅ 整体验证通过' if overall_pass else '❌ 整体验证失败'}")

        return overall_pass, {
            'success': overall_pass,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'warnings': self.warnings,
            'errors': self.errors,
            'validation_results': self.validation_results,
            'metadata': data.get('metadata', {})
        }

def main():
    """主函数"""
    validator = UIDataMappingValidator()

    # 查找最新的综合打分文件
    scoring_dir = Path("/root/projects/tencent-doc-manager/scoring_results/comprehensive")

    if scoring_dir.exists():
        files = list(scoring_dir.glob("comprehensive_score_*.json"))
        if files:
            latest_file = max(files, key=os.path.getmtime)
            print(f"🔍 找到最新综合打分文件: {latest_file.name}")

            # 执行验证
            success, report = validator.validate_comprehensive_score_file(str(latest_file))

            # 保存报告
            report_file = scoring_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📝 验证报告已保存: {report_file}")

            return 0 if success else 1
        else:
            print("❌ 未找到综合打分文件")
            return 1
    else:
        print(f"❌ 目录不存在: {scoring_dir}")
        return 1

if __name__ == "__main__":
    sys.exit(main())