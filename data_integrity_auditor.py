#!/usr/bin/env python3
"""
数据流程完整性深度审计器
发现并分析数据传递过程中的丢失、割裂和不一致问题
"""

import json
import os
from typing import Dict, List, Any

class DataFlowIntegrityAuditor:
    """数据流程完整性审计器"""
    
    def __init__(self):
        self.base_dir = "/root/projects/tencent-doc-manager"
        self.audit_results = {
            "timestamp": "2025-08-20T20:30:00",
            "audit_type": "deep_data_integrity_check",
            "critical_issues": [],
            "data_loss_points": [],
            "inconsistencies": [],
            "recommendations": []
        }
    
    def perform_comprehensive_audit(self) -> Dict[str, Any]:
        """执行全面的数据流程审计"""
        
        print("🔍 开始数据流程完整性深度审计...")
        
        # 步骤1: 审计CSV对比数据
        csv_audit = self._audit_csv_comparison_stage()
        
        # 步骤2: 审计智能映射阶段  
        mapping_audit = self._audit_intelligent_mapping_stage()
        
        # 步骤3: 审计最终热力图数据
        heatmap_audit = self._audit_final_heatmap_stage()
        
        # 步骤4: 数据一致性交叉验证
        consistency_audit = self._perform_cross_stage_validation(
            csv_audit, mapping_audit, heatmap_audit
        )
        
        # 步骤5: 生成问题报告和修复建议
        self._generate_audit_report(csv_audit, mapping_audit, heatmap_audit, consistency_audit)
        
        return self.audit_results
    
    def _audit_csv_comparison_stage(self) -> Dict[str, Any]:
        """审计CSV对比阶段"""
        
        print("   📋 审计阶段1: CSV对比数据...")
        
        csv_file = os.path.join(self.base_dir, "csv_security_results/real_test_comparison.json")
        
        if not os.path.exists(csv_file):
            return {"error": "CSV对比结果文件不存在"}
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_data = json.load(f)
        
        audit_result = {
            "stage": "csv_comparison",
            "total_differences": len(csv_data.get("differences", [])),
            "column_info": csv_data.get("file_info", {}).get("metadata", {}).get("column_mapping", {}),
            "differences_detail": []
        }
        
        # 详细分析每个差异
        for i, diff in enumerate(csv_data.get("differences", [])):
            diff_info = {
                "index": i + 1,
                "location": f"行{diff['行号']}列{diff['列索引']}",
                "column_name": diff["列名"],
                "change": f"{diff['原值']} → {diff['新值']}",
                "risk_level": diff["risk_level"],
                "risk_score": diff["risk_score"],
                "mappable": self._check_column_mappability(diff["列名"])
            }
            audit_result["differences_detail"].append(diff_info)
        
        print(f"      ✓ 发现 {audit_result['total_differences']} 个差异")
        return audit_result
    
    def _audit_intelligent_mapping_stage(self) -> Dict[str, Any]:
        """审计智能映射阶段"""
        
        print("   🧠 审计阶段2: 智能映射处理...")
        
        mapping_file = os.path.join(self.base_dir, "intelligent_mapping_result.json")
        
        if not os.path.exists(mapping_file):
            return {"error": "智能映射结果文件不存在"}
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
        
        audit_result = {
            "stage": "intelligent_mapping",
            "claimed_source_differences": mapping_data["processing_info"]["source_differences"],
            "column_mapping": mapping_data["column_mapping"]["mappings"],
            "unmapped_columns": mapping_data["column_mapping"]["unmapped_columns"],
            "coverage_rate": mapping_data["column_mapping"]["coverage_rate"],
            "row_mapping": mapping_data["row_mapping"]["mappings"],
            "mapping_issues": []
        }
        
        # 检查映射问题
        for unmapped_col in audit_result["unmapped_columns"]:
            audit_result["mapping_issues"].append({
                "type": "unmapped_column",
                "column": unmapped_col,
                "impact": "该列的所有差异将被丢失",
                "severity": "HIGH"
            })
        
        print(f"      ✓ 列映射覆盖率: {audit_result['coverage_rate']:.1%}")
        print(f"      ⚠ 未映射列数: {len(audit_result['unmapped_columns'])}")
        
        return audit_result
    
    def _audit_final_heatmap_stage(self) -> Dict[str, Any]:
        """审计最终热力图阶段"""
        
        print("   🔥 审计阶段3: 最终热力图数据...")
        
        heatmap_file = os.path.join(self.base_dir, "production/servers/real_time_heatmap.json")
        
        if not os.path.exists(heatmap_file):
            return {"error": "热力图数据文件不存在"}
        
        with open(heatmap_file, 'r', encoding='utf-8') as f:
            heatmap_data = json.load(f)
        
        # 分析热力图矩阵
        matrix = heatmap_data["heatmap_data"]
        significant_hotspots = []
        
        for i, row in enumerate(matrix):
            for j, value in enumerate(row):
                if value > 0.1:  # 显著热点阈值
                    significant_hotspots.append({
                        "position": f"行{i}列{j}",
                        "intensity": round(value, 4)
                    })
        
        audit_result = {
            "stage": "final_heatmap",
            "claimed_changes_applied": heatmap_data["changes_applied"],
            "data_source": heatmap_data["data_source"],
            "matrix_size": f"{len(matrix)}x{len(matrix[0])}",
            "total_hotspots": len([v for row in matrix for v in row if v > 0.06]),
            "significant_hotspots": len(significant_hotspots),
            "max_intensity": max(max(row) for row in matrix),
            "hotspots_detail": significant_hotspots
        }
        
        print(f"      ✓ 声称应用变更: {audit_result['claimed_changes_applied']}个")
        print(f"      ✓ 显著热点数: {audit_result['significant_hotspots']}个")
        
        return audit_result
    
    def _perform_cross_stage_validation(self, csv_audit, mapping_audit, heatmap_audit) -> Dict[str, Any]:
        """执行跨阶段数据一致性验证"""
        
        print("   🔗 执行跨阶段一致性验证...")
        
        validation_result = {
            "data_quantity_consistency": {},
            "data_quality_consistency": {},
            "processing_chain_integrity": {}
        }
        
        # 验证1: 数据数量一致性
        csv_differences = csv_audit.get("total_differences", 0)
        mapping_claimed = mapping_audit.get("claimed_source_differences", 0)  
        heatmap_claimed = heatmap_audit.get("claimed_changes_applied", 0)
        
        validation_result["data_quantity_consistency"] = {
            "csv_differences": csv_differences,
            "mapping_claimed": mapping_claimed,
            "heatmap_claimed": heatmap_claimed,
            "consistent": csv_differences == mapping_claimed == heatmap_claimed,
            "discrepancy": abs(csv_differences - heatmap_claimed)
        }
        
        # 验证2: 实际处理效果
        unmapped_columns = mapping_audit.get("unmapped_columns", [])
        coverage_rate = mapping_audit.get("coverage_rate", 0)
        significant_hotspots = heatmap_audit.get("significant_hotspots", 0)
        
        # 计算预期可处理的差异数量
        processable_differences = 0
        for diff in csv_audit.get("differences_detail", []):
            if diff["column_name"] not in unmapped_columns:
                processable_differences += 1
        
        validation_result["data_quality_consistency"] = {
            "processable_differences": processable_differences,
            "actual_significant_hotspots": significant_hotspots,
            "expected_vs_actual_ratio": significant_hotspots / processable_differences if processable_differences > 0 else 0,
            "coverage_impact": len(unmapped_columns) / 5  # 假设总列数为5
        }
        
        # 验证3: 处理链路完整性
        data_loss_points = []
        
        if csv_differences != heatmap_claimed:
            data_loss_points.append("数量声明不一致")
        
        if len(unmapped_columns) > 0:
            data_loss_points.append(f"{len(unmapped_columns)}个列无法映射")
        
        if significant_hotspots < processable_differences:
            data_loss_points.append("热点生成不足")
        
        validation_result["processing_chain_integrity"] = {
            "integrity_status": "BROKEN" if data_loss_points else "INTACT",
            "data_loss_points": data_loss_points,
            "overall_efficiency": (significant_hotspots / csv_differences) if csv_differences > 0 else 0
        }
        
        return validation_result
    
    def _check_column_mappability(self, column_name: str) -> bool:
        """检查列名是否可以映射到19个标准列"""
        
        # 模拟智能映射算法的关键词匹配
        standard_keywords = [
            ["id", "序号", "编号"], ["负责人", "owner", "responsible"],
            ["状态", "status", "进度"], ["类型", "type", "category"],
            ["时间", "date", "time"], ["部门", "department", "dept"],
            # ... 其他标准列关键词
        ]
        
        column_lower = column_name.lower()
        
        for keywords in standard_keywords:
            for keyword in keywords:
                if keyword.lower() in column_lower or column_lower in keyword.lower():
                    return True
        
        return False
    
    def _generate_audit_report(self, csv_audit, mapping_audit, heatmap_audit, consistency_audit):
        """生成审计报告"""
        
        print("   📄 生成审计报告...")
        
        # 识别关键问题
        consistency = consistency_audit["data_quantity_consistency"]
        quality = consistency_audit["data_quality_consistency"]
        integrity = consistency_audit["processing_chain_integrity"]
        
        # 严重问题识别
        if not consistency["consistent"]:
            self.audit_results["critical_issues"].append({
                "type": "DATA_QUANTITY_INCONSISTENCY",
                "description": f"数据数量声明不一致: CSV({consistency['csv_differences']}) vs 热力图({consistency['heatmap_claimed']})",
                "severity": "CRITICAL",
                "impact": "数据完整性受损"
            })
        
        if len(mapping_audit["unmapped_columns"]) > 0:
            lost_differences = 0
            for diff in csv_audit.get("differences_detail", []):
                if diff["column_name"] in mapping_audit["unmapped_columns"]:
                    lost_differences += 1
            
            self.audit_results["critical_issues"].append({
                "type": "COLUMN_MAPPING_DATA_LOSS",
                "description": f"{len(mapping_audit['unmapped_columns'])}个列无法映射，导致{lost_differences}个差异丢失",
                "severity": "HIGH",
                "impact": f"数据丢失率: {lost_differences/csv_audit['total_differences']:.1%}",
                "lost_columns": mapping_audit["unmapped_columns"]
            })
        
        if quality["actual_significant_hotspots"] < quality["processable_differences"]:
            self.audit_results["critical_issues"].append({
                "type": "HEATMAP_GENERATION_INEFFICIENCY", 
                "description": f"可处理{quality['processable_differences']}个差异，但只生成{quality['actual_significant_hotspots']}个显著热点",
                "severity": "MEDIUM",
                "impact": "热力图效果不佳"
            })
        
        # 数据丢失点分析
        self.audit_results["data_loss_points"] = [
            {
                "stage": "intelligent_mapping",
                "type": "column_unmappable",
                "description": "部分列名无法映射到标准19列",
                "affected_data": mapping_audit["unmapped_columns"],
                "loss_rate": 1 - mapping_audit["coverage_rate"]
            },
            {
                "stage": "heatmap_generation", 
                "type": "insufficient_intensity",
                "description": "部分映射成功的差异未产生显著热点",
                "affected_data": "低强度热点",
                "loss_rate": 1 - quality["expected_vs_actual_ratio"]
            }
        ]
        
        # 修复建议
        self.audit_results["recommendations"] = [
            {
                "priority": "HIGH",
                "category": "算法改进",
                "action": "扩展智能映射算法的语义词典",
                "description": "为'工资'、'部门'等常见列名添加映射规则",
                "expected_impact": "提高列映射覆盖率到90%+"
            },
            {
                "priority": "HIGH", 
                "category": "数据完整性",
                "action": "实现数据守恒验证机制",
                "description": "确保每个阶段处理的数据量与输入一致",
                "expected_impact": "消除数据无声丢失问题"
            },
            {
                "priority": "MEDIUM",
                "category": "热力图算法",
                "action": "调整热力强度计算公式",
                "description": "确保所有有效差异都产生可见热点",
                "expected_impact": "提高热点生成效率"
            },
            {
                "priority": "MEDIUM",
                "category": "监控告警",
                "action": "添加实时数据流程监控",
                "description": "在每个处理阶段验证数据完整性",
                "expected_impact": "及时发现数据异常"
            }
        ]

def main():
    """主函数"""
    auditor = DataFlowIntegrityAuditor()
    
    print("🎯 数据流程完整性深度审计")
    print("=" * 60)
    
    audit_results = auditor.perform_comprehensive_audit()
    
    # 保存审计报告
    report_file = "/root/projects/tencent-doc-manager/data_integrity_audit_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("📊 审计结果摘要:")
    print(f"   关键问题数: {len(audit_results['critical_issues'])}")
    print(f"   数据丢失点: {len(audit_results['data_loss_points'])}")
    print(f"   修复建议: {len(audit_results['recommendations'])}")
    
    print("\n🚨 关键问题:")
    for issue in audit_results["critical_issues"]:
        print(f"   ❌ {issue['type']}: {issue['description']}")
    
    print("\n💡 优先修复建议:")
    for rec in audit_results["recommendations"][:3]:
        print(f"   🔧 {rec['priority']}: {rec['action']}")
    
    print(f"\n📄 完整审计报告已保存至: {report_file}")
    
    return audit_results

if __name__ == "__main__":
    main()