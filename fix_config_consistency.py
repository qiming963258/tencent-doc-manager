#!/usr/bin/env python3
"""
配置统一化修复脚本
用于检查和修复系统配置一致性问题
创建日期：2025-09-20
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

# 导入配置中心
from production.config import (
    STANDARD_COLUMNS,
    L1_COLUMNS,
    L2_COLUMNS,
    L3_COLUMNS,
    get_column_risk_level
)

class ConfigConsistencyChecker:
    """配置一致性检查器"""

    def __init__(self):
        self.project_root = Path('/root/projects/tencent-doc-manager')
        self.issues = []
        self.modules_to_fix = []

    def check_module_config(self, module_path):
        """检查单个模块的配置"""
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # 检查是否使用配置中心
        uses_config_center = 'from production.config import' in content

        # 检查是否定义了自己的STANDARD_COLUMNS
        has_own_columns = 'STANDARD_COLUMNS = [' in content or 'STANDARD_COLUMNS = (' in content

        # 检查错误的列名
        wrong_column_names = [
            ('形成计划清单', '完成链接'),
            ('进度分析总结', '经理分析复盘'),
            ('复盘时间', '最新复盘时间')
        ]

        for wrong, correct in wrong_column_names:
            if wrong in content:
                issues.append({
                    'type': 'wrong_column_name',
                    'wrong': wrong,
                    'correct': correct,
                    'line': self._find_line_number(content, wrong)
                })

        # 检查L1/L2/L3定义
        has_own_risk_levels = any([
            'L1_COLUMNS = [' in content,
            'L2_COLUMNS = [' in content,
            'L3_COLUMNS = [' in content
        ])

        return {
            'path': str(module_path),
            'uses_config_center': uses_config_center,
            'has_own_columns': has_own_columns,
            'has_own_risk_levels': has_own_risk_levels,
            'issues': issues
        }

    def _find_line_number(self, content, search_str):
        """查找字符串所在行号"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_str in line:
                return i
        return -1

    def check_all_modules(self):
        """检查所有Python模块"""
        print("\n" + "="*60)
        print("🔍 开始配置一致性检查")
        print("="*60)

        # 要检查的关键模块
        key_modules = [
            'intelligent_excel_marker_solid.py',
            'production_integrated_test_system_8093.py',
            'production/core_modules/comprehensive_score_generator_v2.py',
            'production/core_modules/comparison_to_scoring_adapter.py',
            'production/generate_comprehensive_score.py'
        ]

        results = []

        for module in key_modules:
            module_path = self.project_root / module
            if module_path.exists():
                result = self.check_module_config(module_path)
                results.append(result)

                # 分析结果
                if not result['uses_config_center'] and (result['has_own_columns'] or result['has_own_risk_levels']):
                    self.modules_to_fix.append(module)
                    print(f"\n❌ {module}")
                    print(f"   - 使用配置中心: {'✅' if result['uses_config_center'] else '❌'}")
                    print(f"   - 自定义列: {'❌ 有' if result['has_own_columns'] else '✅ 无'}")
                    print(f"   - 自定义风险级别: {'❌ 有' if result['has_own_risk_levels'] else '✅ 无'}")

                    if result['issues']:
                        print(f"   - 问题：")
                        for issue in result['issues']:
                            print(f"     • 行{issue['line']}: '{issue['wrong']}' 应改为 '{issue['correct']}'")
                else:
                    print(f"\n✅ {module} - 配置正确")

        return results

    def generate_fix_report(self, results):
        """生成修复报告"""
        print("\n" + "="*60)
        print("📊 配置一致性报告")
        print("="*60)

        total = len(results)
        using_config = sum(1 for r in results if r['uses_config_center'])
        has_issues = sum(1 for r in results if r['issues'])

        print(f"\n📈 统计：")
        print(f"  - 总模块数: {total}")
        print(f"  - 使用配置中心: {using_config}/{total} ({using_config/total*100:.1f}%)")
        print(f"  - 存在问题: {has_issues}/{total}")

        if self.modules_to_fix:
            print(f"\n🔧 需要修复的模块：")
            for module in self.modules_to_fix:
                print(f"  - {module}")

        # 保存报告
        report = {
            'check_time': datetime.now().isoformat(),
            'summary': {
                'total_modules': total,
                'using_config_center': using_config,
                'has_issues': has_issues,
                'config_center_usage_rate': f"{using_config/total*100:.1f}%"
            },
            'modules_to_fix': self.modules_to_fix,
            'detailed_results': results
        }

        report_file = self.project_root / 'config_consistency_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📁 报告已保存到: {report_file}")

        return report

    def show_correct_config(self):
        """显示正确的配置"""
        print("\n" + "="*60)
        print("✅ 正确的配置（来自配置中心）")
        print("="*60)

        print("\n📋 标准19列：")
        for i, col in enumerate(STANDARD_COLUMNS):
            risk_level = get_column_risk_level(col)
            print(f"  {i:2d}. {col:15s} - {risk_level}")

        print(f"\n🎯 风险分级：")
        print(f"  - L1列（高风险）: {len(L1_COLUMNS)}个")
        print(f"    {', '.join(L1_COLUMNS)}")
        print(f"  - L2列（中风险）: {len(L2_COLUMNS)}个")
        print(f"    {', '.join(L2_COLUMNS)}")
        print(f"  - L3列（低风险）: {len(L3_COLUMNS)}个")
        print(f"    {', '.join(L3_COLUMNS)}")

    def suggest_fixes(self):
        """建议修复方案"""
        print("\n" + "="*60)
        print("🔧 建议修复方案")
        print("="*60)

        print("""
1. 对于每个需要修复的模块，添加配置中心导入：
   ```python
   from production.config import (
       STANDARD_COLUMNS,
       L1_COLUMNS,
       L2_COLUMNS,
       L3_COLUMNS,
       get_column_risk_level
   )
   ```

2. 删除模块内的独立定义：
   - 删除 STANDARD_COLUMNS = [...]
   - 删除 L1_COLUMNS = [...]
   - 删除 L2_COLUMNS = [...]
   - 删除 L3_COLUMNS = [...]

3. 更新错误的列名引用：
   - "形成计划清单" → "完成链接"
   - "进度分析总结" → "经理分析复盘"
   - "复盘时间" → "最新复盘时间"

4. 测试修复后的模块：
   - 运行单元测试
   - 验证CSV对比功能
   - 检查热力图显示
        """)

def main():
    """主函数"""
    checker = ConfigConsistencyChecker()

    # 显示正确配置
    checker.show_correct_config()

    # 检查所有模块
    results = checker.check_all_modules()

    # 生成报告
    report = checker.generate_fix_report(results)

    # 建议修复方案
    checker.suggest_fixes()

    print("\n" + "="*60)
    print("✅ 配置一致性检查完成！")
    print("="*60)

    return report

if __name__ == "__main__":
    main()