#!/usr/bin/env python3
"""
评分程序合理性与正确性审查工具
对腾讯文档智能监控系统的评分算法进行全面审查
"""

import json
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime

class ScoringSystemAuditor:
    """评分系统审查器"""
    
    def __init__(self):
        self.audit_results = {}
        self.issues = []
        self.recommendations = []
        
    def audit_weight_configuration(self) -> Dict[str, Any]:
        """审查权重配置的合理性"""
        print("🔍 审查权重配置合理性...")
        print("=" * 50)
        
        # 从文档中提取的权重配置
        documented_weights = {
            'modificationCount': 0.3,     # 修改次数权重
            'changeComplexity': 0.25,     # 变更复杂度权重  
            'riskLevel': 0.35,            # 风险等级权重
            'timeRecency': 0.1            # 时间新近度权重
        }
        
        # 业务优先级理论权重
        business_expected_weights = {
            'riskLevel': 0.4,             # 风险等级应该是最重要的
            'modificationCount': 0.25,    # 修改次数次重要
            'changeComplexity': 0.25,     # 变更复杂度
            'timeRecency': 0.1           # 时间新近度最低
        }
        
        issues = []
        
        # 1. 权重总和检查
        total_weight = sum(documented_weights.values())
        print(f"📊 权重总和检查: {total_weight}")
        if abs(total_weight - 1.0) > 0.001:
            issues.append({
                "type": "weight_sum_error",
                "severity": "high",
                "message": f"权重总和应为1.0，实际为{total_weight}",
                "expected": 1.0,
                "actual": total_weight
            })
            print(f"❌ 权重总和错误: {total_weight} ≠ 1.0")
        else:
            print(f"✅ 权重总和正确: {total_weight}")
        
        # 2. 业务优先级匹配度检查
        print(f"\n📋 业务优先级匹配度分析:")
        for factor, expected_weight in business_expected_weights.items():
            actual_weight = documented_weights.get(factor, 0)
            difference = abs(actual_weight - expected_weight)
            
            print(f"   {factor}:")
            print(f"     期望权重: {expected_weight}")
            print(f"     实际权重: {actual_weight}")
            print(f"     差异: {difference:.3f}")
            
            if difference > 0.1:  # 超过10%的差异认为是问题
                issues.append({
                    "type": "business_priority_mismatch",
                    "severity": "medium",
                    "factor": factor,
                    "message": f"{factor}权重与业务优先级不匹配",
                    "expected": expected_weight,
                    "actual": actual_weight,
                    "difference": difference
                })
                print(f"     ⚠️ 权重不匹配（差异>{10}%）")
            else:
                print(f"     ✅ 权重合理")
        
        # 3. 权重敏感性分析
        print(f"\n🔬 权重敏感性分析:")
        sensitivity_results = self._analyze_weight_sensitivity(documented_weights)
        
        # 4. 生成权重优化建议
        recommendations = self._generate_weight_recommendations(
            documented_weights, business_expected_weights, issues
        )
        
        result = {
            "documented_weights": documented_weights,
            "business_expected_weights": business_expected_weights,
            "total_weight": total_weight,
            "issues": issues,
            "sensitivity_analysis": sensitivity_results,
            "recommendations": recommendations,
            "audit_status": "completed"
        }
        
        self.audit_results["weight_configuration"] = result
        return result
    
    def audit_risk_classification(self) -> Dict[str, Any]:
        """审查风险分级体系的一致性"""
        print(f"\n🎯 审查风险分级体系一致性...")
        print("=" * 50)
        
        # 从风险规则文档提取的分类
        documented_classification = {
            "L1": {
                "score_range": "0.9-1.0",
                "description": "红色警戒区",
                "columns": [
                    "任务发起时间", "预计完成时间", "复盘时间",
                    "来源", "序号", 
                    "目标对齐", "关键KR对齐",
                    "完成进度", "重要程度"
                ]
            },
            "L2": {
                "score_range": "0.3-0.8", 
                "description": "黄色保护区",
                "columns": [
                    "具体计划内容",
                    "邓总指导登记",
                    "负责人", "协助人", "监督人",
                    "形成计划清单"
                ]
            },
            "L3": {
                "score_range": "0.1-0.3",
                "description": "绿色自由区", 
                "columns": [
                    "序号", "编号",  # 注意：序号在这里也出现了
                    "复盘时间",      # 注意：复盘时间在这里也出现了
                    "进度分析与总结", "周度分析总结",
                    "对上汇报", "应用情况"
                ]
            }
        }
        
        # 从测试代码提取的分类
        test_code_classification = {
            "L1": ["来源", "任务发起时间"],
            "L2": ["负责人", "协助人", "具体计划内容"],  # 大部分修改为L2
            "L3": ["序号"]
        }
        
        issues = []
        
        # 1. 检查重复列名
        print("🔍 检查列名重复问题:")
        all_columns = {}
        for level, config in documented_classification.items():
            for column in config["columns"]:
                if column in all_columns:
                    issues.append({
                        "type": "duplicate_column",
                        "severity": "high",
                        "column": column,
                        "levels": [all_columns[column], level],
                        "message": f"列'{column}'同时出现在{all_columns[column]}和{level}级别中"
                    })
                    print(f"❌ 重复列名: '{column}' 出现在 {all_columns[column]} 和 {level}")
                else:
                    all_columns[column] = level
        
        # 2. 检查测试代码与文档的一致性
        print(f"\n🔄 检查测试代码与文档一致性:")
        for level in ["L1", "L2", "L3"]:
            doc_columns = set(documented_classification[level]["columns"])
            test_columns = set(test_code_classification.get(level, []))
            
            print(f"   {level}级别:")
            print(f"     文档定义: {len(doc_columns)}个列")
            print(f"     测试代码: {len(test_columns)}个列")
            
            missing_in_test = doc_columns - test_columns
            extra_in_test = test_columns - doc_columns
            
            if missing_in_test:
                print(f"     ⚠️ 测试代码缺失: {missing_in_test}")
                issues.append({
                    "type": "test_missing_columns",
                    "severity": "medium",
                    "level": level,
                    "missing_columns": list(missing_in_test),
                    "message": f"{level}级别测试代码缺失列定义"
                })
            
            if extra_in_test:
                print(f"     ⚠️ 测试代码多余: {extra_in_test}")
                issues.append({
                    "type": "test_extra_columns", 
                    "severity": "low",
                    "level": level,
                    "extra_columns": list(extra_in_test),
                    "message": f"{level}级别测试代码有多余列定义"
                })
            
            if not missing_in_test and not extra_in_test:
                print(f"     ✅ 文档与测试代码一致")
        
        # 3. 检查分数范围重叠
        print(f"\n📊 检查分数范围重叠:")
        score_ranges = {}
        for level, config in documented_classification.items():
            range_str = config["score_range"]
            min_score, max_score = map(float, range_str.split('-'))
            score_ranges[level] = (min_score, max_score)
            print(f"   {level}: {min_score}-{max_score}")
        
        # 检查范围重叠
        overlap_found = False
        for level1, (min1, max1) in score_ranges.items():
            for level2, (min2, max2) in score_ranges.items():
                if level1 != level2:
                    if not (max1 < min2 or max2 < min1):  # 有重叠
                        issues.append({
                            "type": "score_range_overlap",
                            "severity": "high", 
                            "levels": [level1, level2],
                            "ranges": [f"{min1}-{max1}", f"{min2}-{max2}"],
                            "message": f"{level1}和{level2}的分数范围有重叠"
                        })
                        print(f"     ❌ {level1}({min1}-{max1}) 与 {level2}({min2}-{max2}) 重叠")
                        overlap_found = True
        
        if not overlap_found:
            print(f"     ✅ 分数范围无重叠")
        
        result = {
            "documented_classification": documented_classification,
            "test_code_classification": test_code_classification,
            "issues": issues,
            "total_columns": len(all_columns),
            "duplicate_columns": len([i for i in issues if i["type"] == "duplicate_column"]),
            "audit_status": "completed"
        }
        
        self.audit_results["risk_classification"] = result
        return result
    
    def _analyze_weight_sensitivity(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """分析权重敏感性"""
        sensitivity = {}
        
        # 计算每个权重变化10%对总分的影响
        for factor, weight in weights.items():
            # 模拟权重变化的影响
            original_score = self._calculate_mock_score(weights, 1.0, 1.0, 1.0, 1.0)
            
            # 增加10%权重
            modified_weights = weights.copy()
            modified_weights[factor] = weight * 1.1
            
            # 重新归一化
            total = sum(modified_weights.values())
            for k in modified_weights:
                modified_weights[k] /= total
            
            modified_score = self._calculate_mock_score(
                modified_weights, 1.0, 1.0, 1.0, 1.0
            )
            
            sensitivity[factor] = {
                "weight_change": 0.1,
                "score_impact": abs(modified_score - original_score),
                "sensitivity_ratio": abs(modified_score - original_score) / 0.1
            }
        
        return sensitivity
    
    def _calculate_mock_score(self, weights: Dict[str, float], 
                            mod_count: float, complexity: float, 
                            risk: float, recency: float) -> float:
        """计算模拟分数"""
        return (weights['modificationCount'] * mod_count +
                weights['changeComplexity'] * complexity +
                weights['riskLevel'] * risk +
                weights['timeRecency'] * recency)
    
    def _generate_weight_recommendations(self, current: Dict[str, float], 
                                       expected: Dict[str, float], 
                                       issues: List[Dict]) -> List[str]:
        """生成权重优化建议"""
        recommendations = []
        
        if any(i["type"] == "weight_sum_error" for i in issues):
            recommendations.append("将权重总和标准化为1.0")
        
        for factor, expected_weight in expected.items():
            current_weight = current.get(factor, 0)
            if abs(current_weight - expected_weight) > 0.05:
                recommendations.append(
                    f"调整{factor}权重从{current_weight}到{expected_weight}，更符合业务优先级"
                )
        
        if not recommendations:
            recommendations.append("当前权重配置基本合理，无需重大调整")
        
        return recommendations
    
    def generate_audit_report(self) -> str:
        """生成完整的审查报告"""
        report = []
        report.append("# 评分程序审查报告")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 权重配置审查结果
        if "weight_configuration" in self.audit_results:
            weight_result = self.audit_results["weight_configuration"]
            report.append("## 🏋️ 权重配置审查")
            report.append("")
            
            # 当前权重
            report.append("### 当前权重配置")
            for factor, weight in weight_result["documented_weights"].items():
                report.append(f"- **{factor}**: {weight} ({weight*100:.1f}%)")
            report.append("")
            
            # 问题汇总
            issues = weight_result["issues"]
            if issues:
                report.append("### 发现的问题")
                for issue in issues:
                    severity_icon = "🔴" if issue["severity"] == "high" else "🟡" if issue["severity"] == "medium" else "🟢"
                    report.append(f"- {severity_icon} **{issue['type']}**: {issue['message']}")
                report.append("")
            
            # 建议
            report.append("### 优化建议")
            for rec in weight_result["recommendations"]:
                report.append(f"- {rec}")
            report.append("")
        
        # 风险分级审查结果
        if "risk_classification" in self.audit_results:
            risk_result = self.audit_results["risk_classification"]
            report.append("## 🎯 风险分级体系审查")
            report.append("")
            
            # 问题汇总
            issues = risk_result["issues"]
            if issues:
                report.append("### 发现的问题")
                high_issues = [i for i in issues if i["severity"] == "high"]
                medium_issues = [i for i in issues if i["severity"] == "medium"]
                low_issues = [i for i in issues if i["severity"] == "low"]
                
                if high_issues:
                    report.append("#### 🔴 高优先级问题")
                    for issue in high_issues:
                        report.append(f"- **{issue['type']}**: {issue['message']}")
                    report.append("")
                
                if medium_issues:
                    report.append("#### 🟡 中优先级问题")
                    for issue in medium_issues:
                        report.append(f"- **{issue['type']}**: {issue['message']}")
                    report.append("")
                
                if low_issues:
                    report.append("#### 🟢 低优先级问题")
                    for issue in low_issues:
                        report.append(f"- **{issue['type']}**: {issue['message']}")
                    report.append("")
            else:
                report.append("### ✅ 未发现重大问题")
                report.append("")
        
        return "\n".join(report)

def main():
    """主函数"""
    auditor = ScoringSystemAuditor()
    
    print("🚀 开始评分程序合理性与正确性审查")
    print("=" * 60)
    
    # 审查权重配置
    weight_results = auditor.audit_weight_configuration()
    
    # 审查风险分级
    risk_results = auditor.audit_risk_classification()
    
    # 生成报告
    report = auditor.generate_audit_report()
    
    # 保存报告
    report_filename = f"scoring_system_audit_report_{int(datetime.now().timestamp())}.md"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📊 审查完成!")
    print(f"📄 详细报告已保存: {report_filename}")
    
    # 汇总统计
    total_issues = len(weight_results.get("issues", [])) + len(risk_results.get("issues", []))
    high_issues = sum(1 for issue in weight_results.get("issues", []) + risk_results.get("issues", [])
                     if issue.get("severity") == "high")
    
    print(f"\n🎯 审查汇总:")
    print(f"   发现问题总数: {total_issues}")
    print(f"   高优先级问题: {high_issues}")
    print(f"   审查状态: {'⚠️ 需要修复' if high_issues > 0 else '✅ 基本合格'}")
    
    return auditor

if __name__ == "__main__":
    auditor = main()