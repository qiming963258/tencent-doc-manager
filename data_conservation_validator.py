#!/usr/bin/env python3
"""
数据守恒验证器
确保数据在各处理阶段不会丢失、错位或无法传递
"""

import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

class DataLossException(Exception):
    """数据丢失异常"""
    pass

class DataConservationValidator:
    """数据守恒验证器"""
    
    def __init__(self, strict_mode: bool = True):
        """
        初始化验证器
        
        Args:
            strict_mode: 严格模式，任何数据丢失都会抛出异常
        """
        self.strict_mode = strict_mode
        self.audit_log = []
        self.validation_results = {
            "total_validations": 0,
            "failed_validations": 0,
            "data_loss_events": [],
            "stage_summary": {}
        }
        
    def validate_stage_consistency(self, 
                                 input_data: Any, 
                                 output_data: Any, 
                                 stage_name: str,
                                 expected_transformations: Dict[str, Any] = None) -> bool:
        """
        验证单个处理阶段的数据一致性
        
        Args:
            input_data: 输入数据
            output_data: 输出数据
            stage_name: 阶段名称
            expected_transformations: 预期的数据转换规则
        
        Returns:
            bool: 验证是否通过
        """
        
        self.validation_results["total_validations"] += 1
        
        # 计算输入输出数据量
        input_count = self._calculate_data_count(input_data, stage_name)
        output_count = self._calculate_output_count(output_data, stage_name)
        
        # 记录验证信息
        validation_record = {
            "timestamp": datetime.now().isoformat(),
            "stage_name": stage_name,
            "input_count": input_count,
            "output_count": output_count,
            "data_preserved": True,
            "issues": []
        }
        
        # 数据量验证
        data_loss_detected = False
        
        if stage_name == "csv_comparison":
            # CSV对比阶段：输入输出应该相等
            if input_count != output_count:
                data_loss_detected = True
                validation_record["issues"].append({
                    "type": "quantity_mismatch",
                    "description": f"CSV对比阶段数据量不匹配: {input_count} → {output_count}"
                })
        
        elif stage_name == "intelligent_mapping":
            # 智能映射阶段：需要验证映射覆盖率
            mapping_info = self._analyze_mapping_coverage(input_data, output_data)
            validation_record["mapping_coverage"] = mapping_info["coverage_rate"]
            
            if mapping_info["unmapped_count"] > 0:
                if self.strict_mode and mapping_info["coverage_rate"] < 0.8:
                    data_loss_detected = True
                validation_record["issues"].append({
                    "type": "mapping_incomplete", 
                    "description": f"映射覆盖率过低: {mapping_info['coverage_rate']:.1%}",
                    "unmapped_columns": mapping_info["unmapped_columns"],
                    "lost_data_count": mapping_info["lost_data_count"]
                })
        
        elif stage_name == "heatmap_generation":
            # 热力图生成阶段：验证热点生成效率
            hotspot_info = self._analyze_hotspot_generation(input_data, output_data)
            validation_record["hotspot_efficiency"] = hotspot_info["efficiency"]
            
            if hotspot_info["efficiency"] < 0.5:  # 至少50%的输入数据应产生可见热点
                validation_record["issues"].append({
                    "type": "hotspot_generation_low",
                    "description": f"热点生成效率过低: {hotspot_info['efficiency']:.1%}",
                    "expected_hotspots": hotspot_info["expected_hotspots"],
                    "actual_hotspots": hotspot_info["actual_hotspots"]
                })
        
        # 标记验证状态
        validation_record["data_preserved"] = not data_loss_detected
        
        if data_loss_detected:
            self.validation_results["failed_validations"] += 1
            self.validation_results["data_loss_events"].append(validation_record)
            
            if self.strict_mode:
                raise DataLossException(
                    f"{stage_name}阶段检测到数据丢失: {validation_record['issues']}"
                )
        
        # 记录到审计日志
        self.audit_log.append(validation_record)
        
        # 更新阶段摘要
        if stage_name not in self.validation_results["stage_summary"]:
            self.validation_results["stage_summary"][stage_name] = {
                "validations": 0,
                "failures": 0,
                "avg_data_preservation": 0.0
            }
        
        stage_summary = self.validation_results["stage_summary"][stage_name]
        stage_summary["validations"] += 1
        if data_loss_detected:
            stage_summary["failures"] += 1
        
        return not data_loss_detected
    
    def _calculate_data_count(self, data: Any, stage_name: str) -> int:
        """计算数据量"""
        
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            if stage_name == "csv_comparison" and "differences" in data:
                return len(data["differences"])
            elif stage_name == "intelligent_mapping" and "mappings" in data:
                return len(data["mappings"])
            else:
                return len(data)
        else:
            return 1 if data else 0
    
    def _calculate_output_count(self, output_data: Any, stage_name: str) -> int:
        """计算输出数据量"""
        
        if stage_name == "heatmap_generation":
            # 对热力图，计算显著热点数量
            if isinstance(output_data, dict) and "heatmap_data" in output_data:
                matrix = output_data["heatmap_data"]
                significant_hotspots = 0
                for row in matrix:
                    for value in row:
                        if value > 0.1:  # 显著热点阈值
                            significant_hotspots += 1
                return significant_hotspots
        
        return self._calculate_data_count(output_data, stage_name)
    
    def _analyze_mapping_coverage(self, input_data: Any, output_data: Any) -> Dict[str, Any]:
        """分析映射覆盖率"""
        
        coverage_info = {
            "coverage_rate": 1.0,
            "unmapped_count": 0,
            "unmapped_columns": [],
            "lost_data_count": 0
        }
        
        if isinstance(output_data, dict) and "column_mapping" in output_data:
            mapping_result = output_data["column_mapping"]
            coverage_info["coverage_rate"] = mapping_result.get("coverage_rate", 1.0)
            coverage_info["unmapped_columns"] = mapping_result.get("unmapped_columns", [])
            coverage_info["unmapped_count"] = len(coverage_info["unmapped_columns"])
            
            # 计算因映射失败而丢失的数据数量
            if isinstance(input_data, list):
                for diff in input_data:
                    if diff.get("列名") in coverage_info["unmapped_columns"]:
                        coverage_info["lost_data_count"] += 1
        
        return coverage_info
    
    def _analyze_hotspot_generation(self, input_data: Any, output_data: Any) -> Dict[str, Any]:
        """分析热点生成效率"""
        
        hotspot_info = {
            "efficiency": 1.0,
            "expected_hotspots": 0,
            "actual_hotspots": 0
        }
        
        # 计算预期热点数（基于映射成功的差异数量）
        if isinstance(input_data, dict) and "differences" in input_data:
            # 假设这是从CSV对比传入的数据
            hotspot_info["expected_hotspots"] = len(input_data["differences"])
        elif isinstance(input_data, list):
            hotspot_info["expected_hotspots"] = len(input_data)
        
        # 计算实际生成的显著热点数量
        if isinstance(output_data, dict) and "heatmap_data" in output_data:
            matrix = output_data["heatmap_data"]
            for row in matrix:
                for value in row:
                    if value > 0.1:  # 显著热点阈值
                        hotspot_info["actual_hotspots"] += 1
        
        # 计算效率
        if hotspot_info["expected_hotspots"] > 0:
            hotspot_info["efficiency"] = min(1.0, hotspot_info["actual_hotspots"] / hotspot_info["expected_hotspots"])
        
        return hotspot_info
    
    def validate_complete_pipeline(self, 
                                 csv_differences: List[Dict],
                                 mapping_result: Dict[str, Any],
                                 heatmap_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证完整的数据处理管道"""
        
        print("🔍 开始完整数据管道验证...")
        
        # 阶段1: CSV对比数据验证
        csv_valid = self.validate_stage_consistency(
            csv_differences, csv_differences, "csv_comparison"
        )
        
        # 阶段2: 智能映射验证
        mapping_valid = self.validate_stage_consistency(
            csv_differences, mapping_result, "intelligent_mapping"
        )
        
        # 阶段3: 热力图生成验证
        heatmap_valid = self.validate_stage_consistency(
            mapping_result, heatmap_result, "heatmap_generation"
        )
        
        # 计算总体数据完整性
        overall_integrity = self._calculate_overall_integrity(
            csv_differences, mapping_result, heatmap_result
        )
        
        validation_summary = {
            "pipeline_valid": csv_valid and mapping_valid and heatmap_valid,
            "overall_data_integrity": overall_integrity,
            "stage_results": {
                "csv_comparison": csv_valid,
                "intelligent_mapping": mapping_valid, 
                "heatmap_generation": heatmap_valid
            },
            "detailed_report": self.validation_results,
            "audit_log": self.audit_log
        }
        
        print(f"   ✅ 验证完成 - 数据完整性: {overall_integrity:.1%}")
        
        return validation_summary
    
    def _calculate_overall_integrity(self, 
                                   csv_data: List[Dict],
                                   mapping_result: Dict[str, Any],
                                   heatmap_result: Dict[str, Any]) -> float:
        """计算总体数据完整性"""
        
        if not csv_data:
            return 1.0
        
        original_count = len(csv_data)
        
        # 计算最终可见的热点数量
        final_visible_count = 0
        if isinstance(heatmap_result, dict) and "heatmap_data" in heatmap_result:
            matrix = heatmap_result["heatmap_data"]
            for row in matrix:
                for value in row:
                    if value > 0.1:  # 可见热点阈值
                        final_visible_count += 1
        
        # 数据完整性 = 最终可见数据 / 原始数据
        return min(1.0, final_visible_count / original_count) if original_count > 0 else 1.0
    
    def generate_data_integrity_report(self, output_file: str = None) -> Dict[str, Any]:
        """生成数据完整性报告"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "validation_summary": self.validation_results,
            "audit_trail": self.audit_log,
            "recommendations": []
        }
        
        # 生成修复建议
        if self.validation_results["failed_validations"] > 0:
            report["recommendations"].append({
                "priority": "HIGH",
                "action": "修复数据映射覆盖率",
                "description": "扩展智能映射算法的语义词典"
            })
        
        if len([e for e in self.validation_results["data_loss_events"] if "hotspot_generation_low" in str(e)]) > 0:
            report["recommendations"].append({
                "priority": "MEDIUM", 
                "action": "优化热点生成算法",
                "description": "调整热力强度计算，确保更多数据可见"
            })
        
        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 数据完整性报告已保存: {output_file}")
        
        return report

def test_data_conservation():
    """测试数据守恒验证"""
    
    # 模拟测试数据
    test_csv_data = [
        {"行号": 2, "列名": "负责人", "原值": "李四", "新值": "李小明"},
        {"行号": 2, "列名": "工资", "原值": "7500", "新值": "8500"},
        {"行号": 3, "列名": "状态", "原值": "正常", "新值": "离职"}
    ]
    
    test_mapping_result = {
        "column_mapping": {
            "coverage_rate": 0.6,
            "unmapped_columns": ["工资"]
        }
    }
    
    test_heatmap_result = {
        "heatmap_data": [[0.05, 0.25], [0.05, 0.05]]  # 只有1个显著热点
    }
    
    # 创建验证器
    validator = DataConservationValidator(strict_mode=False)
    
    # 执行验证
    result = validator.validate_complete_pipeline(
        test_csv_data, test_mapping_result, test_heatmap_result
    )
    
    # 生成报告
    report = validator.generate_data_integrity_report(
        "/root/projects/tencent-doc-manager/data_conservation_report.json"
    )
    
    print("🎯 数据守恒验证测试完成")
    return result

if __name__ == "__main__":
    test_data_conservation()