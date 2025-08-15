#!/usr/bin/env python3
"""
评分算法实现验证工具
验证评分算法的实现正确性和边界条件处理
"""

import math
from typing import Dict, List, Any, Tuple

class ScoringAlgorithmValidator:
    """评分算法验证器"""
    
    def __init__(self):
        # 文档中定义的权重
        self.documented_weights = {
            'modification_count': 0.3,
            'change_complexity': 0.25,
            'risk_level': 0.35,
            'time_recency': 0.1
        }
        
        # 风险等级分数映射
        self.risk_level_scores = {
            'L1': 1.0,    # L1修改影响最大
            'L2': 0.6,    # L2修改中等影响
            'L3': 0.2     # L3修改影响最小
        }
        
        # 分数范围定义
        self.score_ranges = {
            'L1': (0.9, 1.0),
            'L2': (0.3, 0.8),
            'L3': (0.1, 0.3)
        }
        
    def validate_scoring_formula(self) -> Dict[str, Any]:
        """验证评分公式的正确性"""
        print("🧮 验证评分公式实现...")
        print("=" * 50)
        
        issues = []
        test_results = []
        
        # 测试用例设计
        test_cases = [
            {
                "name": "高风险典型场景",
                "data": {
                    "modification_count": 1.0,  # 归一化到0-1
                    "change_complexity": 1.0,
                    "risk_level": "L1",
                    "time_recency": 1.0
                },
                "expected_range": (0.9, 1.0),
                "expected_level": "L1"
            },
            {
                "name": "中风险典型场景", 
                "data": {
                    "modification_count": 0.6,
                    "change_complexity": 0.6,
                    "risk_level": "L2",
                    "time_recency": 0.5
                },
                "expected_range": (0.3, 0.8),
                "expected_level": "L2"
            },
            {
                "name": "低风险典型场景",
                "data": {
                    "modification_count": 0.2,
                    "change_complexity": 0.2,
                    "risk_level": "L3",
                    "time_recency": 0.1
                },
                "expected_range": (0.1, 0.3),
                "expected_level": "L3"
            },
            {
                "name": "边界条件-全零值",
                "data": {
                    "modification_count": 0.0,
                    "change_complexity": 0.0,
                    "risk_level": "L3",
                    "time_recency": 0.0
                },
                "expected_range": (0.0, 0.3),
                "expected_level": "L3"
            },
            {
                "name": "边界条件-全最大值",
                "data": {
                    "modification_count": 1.0,
                    "change_complexity": 1.0,
                    "risk_level": "L1",
                    "time_recency": 1.0
                },
                "expected_range": (0.9, 1.0),
                "expected_level": "L1"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 测试: {test_case['name']}")
            
            # 计算分数
            calculated_score = self._calculate_risk_score(test_case['data'])
            expected_min, expected_max = test_case['expected_range']
            
            print(f"   输入数据: {test_case['data']}")
            print(f"   计算分数: {calculated_score:.3f}")
            print(f"   期望范围: {expected_min}-{expected_max}")
            
            # 检查分数是否在期望范围内
            in_range = expected_min <= calculated_score <= expected_max
            
            if in_range:
                print(f"   ✅ 分数在期望范围内")
            else:
                print(f"   ❌ 分数超出期望范围")
                issues.append({
                    "type": "score_out_of_range",
                    "test_case": test_case['name'],
                    "calculated": calculated_score,
                    "expected_range": test_case['expected_range'],
                    "severity": "high"
                })
            
            # 检查推导的风险等级
            derived_level = self._derive_risk_level_from_score(calculated_score)
            expected_level = test_case['expected_level']
            
            print(f"   推导等级: {derived_level}")
            print(f"   期望等级: {expected_level}")
            
            if derived_level == expected_level:
                print(f"   ✅ 风险等级推导正确")
            else:
                print(f"   ❌ 风险等级推导错误")
                issues.append({
                    "type": "risk_level_mismatch",
                    "test_case": test_case['name'],
                    "derived_level": derived_level,
                    "expected_level": expected_level,
                    "severity": "medium"
                })
            
            test_results.append({
                "test_case": test_case['name'],
                "calculated_score": calculated_score,
                "in_expected_range": in_range,
                "derived_level": derived_level,
                "level_correct": derived_level == expected_level
            })
        
        return {
            "issues": issues,
            "test_results": test_results,
            "total_tests": len(test_cases),
            "passed_tests": len([r for r in test_results if r["in_expected_range"] and r["level_correct"]]),
            "success_rate": len([r for r in test_results if r["in_expected_range"] and r["level_correct"]]) / len(test_cases)
        }
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """测试边界条件和异常值处理"""
        print(f"\n🔬 测试边界条件和异常值处理...")
        print("=" * 50)
        
        edge_cases = [
            {
                "name": "负数输入",
                "data": {
                    "modification_count": -0.5,
                    "change_complexity": 0.5,
                    "risk_level": "L2",
                    "time_recency": 0.3
                },
                "should_handle": True
            },
            {
                "name": "超大数值输入",
                "data": {
                    "modification_count": 100.0,
                    "change_complexity": 50.0,
                    "risk_level": "L1",
                    "time_recency": 10.0
                },
                "should_handle": True
            },
            {
                "name": "NaN输入",
                "data": {
                    "modification_count": float('nan'),
                    "change_complexity": 0.5,
                    "risk_level": "L2", 
                    "time_recency": 0.3
                },
                "should_handle": True
            },
            {
                "name": "无穷大输入",
                "data": {
                    "modification_count": float('inf'),
                    "change_complexity": 0.5,
                    "risk_level": "L2",
                    "time_recency": 0.3
                },
                "should_handle": True
            },
            {
                "name": "无效风险等级",
                "data": {
                    "modification_count": 0.5,
                    "change_complexity": 0.5,
                    "risk_level": "L4",  # 不存在的等级
                    "time_recency": 0.3
                },
                "should_handle": True
            }
        ]
        
        issues = []
        
        for edge_case in edge_cases:
            print(f"\n🧪 边界测试: {edge_case['name']}")
            
            try:
                score = self._calculate_risk_score(edge_case['data'])
                
                # 检查返回的分数是否合理
                if math.isnan(score) or math.isinf(score):
                    print(f"   ❌ 返回了无效分数: {score}")
                    issues.append({
                        "type": "invalid_score_returned",
                        "test_case": edge_case['name'],
                        "returned_score": str(score),
                        "severity": "high"
                    })
                elif score < 0 or score > 1:
                    print(f"   ❌ 分数超出有效范围[0,1]: {score}")
                    issues.append({
                        "type": "score_out_of_bounds",
                        "test_case": edge_case['name'],
                        "returned_score": score,
                        "severity": "high"
                    })
                else:
                    print(f"   ✅ 正确处理异常输入，返回分数: {score:.3f}")
                    
            except Exception as e:
                print(f"   ❌ 处理异常输入时发生错误: {e}")
                issues.append({
                    "type": "exception_on_edge_case",
                    "test_case": edge_case['name'],
                    "error": str(e),
                    "severity": "high"
                })
        
        return {
            "issues": issues,
            "edge_cases_tested": len(edge_cases),
            "edge_cases_passed": len(edge_cases) - len(issues)
        }
    
    def validate_score_consistency(self) -> Dict[str, Any]:
        """验证评分一致性"""
        print(f"\n🔄 验证评分一致性...")
        print("=" * 50)
        
        # 测试相同输入是否产生相同输出
        test_data = {
            "modification_count": 0.7,
            "change_complexity": 0.6,
            "risk_level": "L2",
            "time_recency": 0.4
        }
        
        scores = []
        for i in range(10):
            score = self._calculate_risk_score(test_data)
            scores.append(score)
        
        # 检查一致性
        all_same = all(abs(score - scores[0]) < 1e-10 for score in scores)
        
        print(f"   测试数据: {test_data}")
        print(f"   10次计算结果: {[f'{s:.6f}' for s in scores[:3]]}..." if len(scores) > 3 else scores)
        print(f"   一致性检查: {'✅ 通过' if all_same else '❌ 失败'}")
        
        return {
            "consistency_passed": all_same,
            "scores": scores,
            "variance": max(scores) - min(scores) if scores else 0
        }
    
    def _calculate_risk_score(self, data: Dict[str, Any]) -> float:
        """计算风险分数的参考实现"""
        try:
            # 处理异常输入
            mod_count = self._normalize_value(data.get('modification_count', 0))
            complexity = self._normalize_value(data.get('change_complexity', 0))
            time_recency = self._normalize_value(data.get('time_recency', 0))
            
            # 获取风险等级分数
            risk_level = data.get('risk_level', 'L3')
            risk_score = self.risk_level_scores.get(risk_level, 0.2)  # 默认L3
            
            # 计算加权分数
            weighted_score = (
                self.documented_weights['modification_count'] * mod_count +
                self.documented_weights['change_complexity'] * complexity +
                self.documented_weights['risk_level'] * risk_score +
                self.documented_weights['time_recency'] * time_recency
            )
            
            # 确保分数在[0,1]范围内
            return max(0.0, min(1.0, weighted_score))
            
        except Exception as e:
            # 出错时返回默认的中等风险分数
            return 0.5
    
    def _normalize_value(self, value: Any) -> float:
        """标准化数值到[0,1]范围"""
        try:
            val = float(value)
            if math.isnan(val) or math.isinf(val):
                return 0.5  # 默认中等值
            return max(0.0, min(1.0, val))  # 限制在[0,1]范围
        except (ValueError, TypeError):
            return 0.5  # 无法转换时返回默认值
    
    def _derive_risk_level_from_score(self, score: float) -> str:
        """从分数推导风险等级"""
        if 0.9 <= score <= 1.0:
            return "L1"
        elif 0.3 <= score <= 0.8:
            return "L2"
        elif 0.1 <= score <= 0.3:
            return "L3"
        else:
            # 分数在重叠区域或异常范围，根据最接近的区间判断
            if score > 0.8:
                return "L1"
            elif score > 0.3:
                return "L2"
            else:
                return "L3"
    
    def generate_validation_report(self, formula_results: Dict, edge_results: Dict, 
                                 consistency_results: Dict) -> str:
        """生成验证报告"""
        report = []
        report.append("# 评分算法验证报告")
        report.append("")
        
        # 公式验证结果
        report.append("## 📊 评分公式验证")
        success_rate = formula_results['success_rate']
        report.append(f"- **测试通过率**: {success_rate:.1%}")
        report.append(f"- **测试用例**: {formula_results['passed_tests']}/{formula_results['total_tests']}")
        
        if formula_results['issues']:
            report.append("\n### 发现的问题")
            for issue in formula_results['issues']:
                severity_icon = "🔴" if issue['severity'] == 'high' else "🟡"
                report.append(f"- {severity_icon} **{issue['type']}**: {issue.get('test_case', '')}")
        
        # 边界条件测试结果
        report.append("\n## 🔬 边界条件测试")
        edge_pass_rate = edge_results['edge_cases_passed'] / edge_results['edge_cases_tested']
        report.append(f"- **边界测试通过率**: {edge_pass_rate:.1%}")
        report.append(f"- **测试用例**: {edge_results['edge_cases_passed']}/{edge_results['edge_cases_tested']}")
        
        if edge_results['issues']:
            report.append("\n### 边界条件问题")
            for issue in edge_results['issues']:
                report.append(f"- 🔴 **{issue['type']}**: {issue.get('test_case', '')}")
        
        # 一致性测试结果
        report.append("\n## 🔄 一致性测试")
        consistency_status = "✅ 通过" if consistency_results['consistency_passed'] else "❌ 失败"
        report.append(f"- **一致性检查**: {consistency_status}")
        report.append(f"- **分数方差**: {consistency_results['variance']:.10f}")
        
        # 总体评价
        overall_issues = len(formula_results['issues']) + len(edge_results['issues'])
        if not consistency_results['consistency_passed']:
            overall_issues += 1
            
        report.append("\n## 🎯 总体评价")
        if overall_issues == 0:
            report.append("✅ **评分算法实现正确，无重大问题**")
        elif overall_issues <= 2:
            report.append("🟡 **评分算法基本正确，有少量问题需要修复**")
        else:
            report.append("❌ **评分算法存在多个问题，需要重点修复**")
        
        report.append(f"\n- **发现问题总数**: {overall_issues}")
        report.append(f"- **算法可靠性**: {'高' if overall_issues <= 1 else '中' if overall_issues <= 3 else '低'}")
        
        return "\n".join(report)

def main():
    """主函数"""
    validator = ScoringAlgorithmValidator()
    
    print("🚀 开始评分算法实现验证")
    print("=" * 60)
    
    # 验证评分公式
    formula_results = validator.validate_scoring_formula()
    
    # 测试边界条件
    edge_results = validator.test_edge_cases()
    
    # 验证一致性
    consistency_results = validator.validate_score_consistency()
    
    # 生成报告
    report = validator.generate_validation_report(
        formula_results, edge_results, consistency_results
    )
    
    # 保存报告
    report_filename = "scoring_algorithm_validation_report.md"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📊 算法验证完成!")
    print(f"📄 验证报告已保存: {report_filename}")
    
    # 汇总结果
    total_issues = len(formula_results['issues']) + len(edge_results['issues'])
    if not consistency_results['consistency_passed']:
        total_issues += 1
    
    print(f"\n🎯 验证汇总:")
    print(f"   公式测试通过率: {formula_results['success_rate']:.1%}")
    print(f"   边界测试通过率: {edge_results['edge_cases_passed']/edge_results['edge_cases_tested']:.1%}")
    print(f"   一致性测试: {'通过' if consistency_results['consistency_passed'] else '失败'}")
    print(f"   发现问题总数: {total_issues}")
    print(f"   算法状态: {'✅ 可靠' if total_issues <= 1 else '🟡 基本可用' if total_issues <= 3 else '❌ 需要修复'}")

if __name__ == "__main__":
    main()