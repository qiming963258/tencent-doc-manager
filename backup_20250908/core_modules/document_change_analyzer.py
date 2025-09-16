#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档变更对比分析程序
用于检测CSV表格的修改内容并生成风险评估报告
"""

import pandas as pd
import difflib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import re
import sys
import os

# 导入自适应表格对比器
try:
    from adaptive_table_comparator import AdaptiveTableComparator, IntelligentColumnMatcher
except ImportError:
    # 如果导入失败，添加当前目录到路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from adaptive_table_comparator import AdaptiveTableComparator, IntelligentColumnMatcher

class DocumentChangeAnalyzer:
    """文档变更分析器 - 增强版本，集成自适应表格对比功能"""
    
    def __init__(self):
        # 列风险等级配置（基于规格说明书）
        self.column_risk_levels = {
            "序号": "L3",                    # 可自由编辑
            "项目类型": "L2",                # 需要语义审核  
            "来源": "L1",                    # 绝对不能修改
            "任务发起时间": "L1",            # 绝对不能修改
            "目标对齐": "L1",                # 绝对不能修改 - 用户特别强调
            "关键KR对齐": "L1",              # 绝对不能修改
            "具体计划内容": "L2",            # 需要语义审核
            "邓总指导登记": "L2",            # 需要语义审核
            "负责人": "L2",                  # 需要语义审核
            "协助人": "L2",                  # 需要语义审核
            "监督人": "L2",                  # 需要语义审核
            "重要程度": "L1",                # 绝对不能修改
            "预计完成时间": "L1",            # 绝对不能修改
            "完成进度": "L1",                # 绝对不能修改
            "形成计划清单,完成附件、链接、截图上传": "L2",  # 需要语义审核
            "复盘周期": "L3",                # 可自由编辑
            "复盘时间": "L3",                # 可自由编辑
            "对上汇报": "L3",                # 可自由编辑
            "应用情况": "L3",                # 可自由编辑
            "进度分析与总结": "L3"           # 可自由编辑
        }
        
        # 风险评分配置
        self.risk_scores = {
            "L1": 1.0,    # 最高风险
            "L2": 0.6,    # 中等风险
            "L3": 0.2     # 最低风险
        }
        
        # 集成自适应表格对比器
        self.adaptive_comparator = AdaptiveTableComparator()
        self.column_matcher = IntelligentColumnMatcher()
        
        # 处理模式：'legacy' 传统模式 | 'adaptive' 自适应模式 | 'hybrid' 混合模式
        self.processing_mode = 'hybrid'

    def adaptive_compare_tables(self, current_file: str, reference_file: str = None) -> Dict[str, Any]:
        """
        自适应表格对比分析 - 新增方法
        支持不同格式表格的智能对比和分析
        
        Args:
            current_file: 当前表格文件路径
            reference_file: 参考表格文件路径（可选）
            
        Returns:
            完整的对比分析结果，包括智能匹配和风险评估
        """
        print(f"🔍 启动自适应表格对比分析")
        print(f"当前文件: {current_file}")
        if reference_file:
            print(f"参考文件: {reference_file}")
        
        try:
            # 加载当前表格数据
            current_df = self.load_csv_data(current_file)
            if current_df.empty:
                return {"error": f"无法加载当前文件: {current_file}"}
            
            # 转换为自适应对比器需要的格式
            current_table_data = {
                "name": os.path.basename(current_file),
                "data": [current_df.columns.tolist()] + current_df.values.tolist()
            }
            
            tables_to_compare = [current_table_data]
            reference_tables = None
            
            # 如果有参考文件，加载参考数据
            if reference_file:
                reference_df = self.load_csv_data(reference_file)
                if not reference_df.empty:
                    reference_table_data = {
                        "name": os.path.basename(reference_file),
                        "data": [reference_df.columns.tolist()] + reference_df.values.tolist()
                    }
                    reference_tables = [reference_table_data]
                    print(f"✅ 参考数据加载成功: {len(reference_df)}行 × {len(reference_df.columns)}列")
            
            print(f"✅ 当前数据加载成功: {len(current_df)}行 × {len(current_df.columns)}列")
            
            # 执行自适应对比分析
            adaptive_result = self.adaptive_comparator.adaptive_compare_tables(
                tables_to_compare, reference_tables
            )
            
            # 如果是混合模式，还要执行传统对比（用于兼容性）
            legacy_result = None
            if self.processing_mode in ['legacy', 'hybrid'] and reference_file and not reference_df.empty:
                legacy_result = self.compare_dataframes(reference_df, current_df)
                print("✅ 传统对比分析完成")
            
            # 合并和增强结果
            enhanced_result = self._merge_analysis_results(
                adaptive_result, legacy_result, current_df.columns.tolist()
            )
            
            print(f"✅ 自适应对比分析完成")
            return enhanced_result
            
        except Exception as e:
            error_msg = f"自适应对比分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "traceback": str(e)}
    
    def _merge_analysis_results(self, adaptive_result: Dict[str, Any], 
                               legacy_result: Dict[str, Any] = None,
                               current_columns: List[str] = None) -> Dict[str, Any]:
        """
        合并自适应分析结果和传统分析结果
        
        Args:
            adaptive_result: 自适应对比器的结果
            legacy_result: 传统对比器的结果（可选）
            current_columns: 当前表格的列名
            
        Returns:
            合并后的增强结果
        """
        
        enhanced_result = {
            "analysis_mode": self.processing_mode,
            "analysis_timestamp": datetime.now().isoformat(),
            "adaptive_analysis": adaptive_result,
            "legacy_analysis": legacy_result,
            "enhanced_summary": {},
            "column_intelligence": {},
            "recommendations": []
        }
        
        # 提取自适应分析的关键信息
        if adaptive_result and "comparison_results" in adaptive_result:
            first_table_result = adaptive_result["comparison_results"][0] if adaptive_result["comparison_results"] else {}
            
            # 列匹配智能分析
            if "matching_result" in first_table_result:
                matching_result = first_table_result["matching_result"]
                enhanced_result["column_intelligence"] = {
                    "total_input_columns": len(current_columns) if current_columns else 0,
                    "successfully_matched": len(matching_result.get("mapping", {})),
                    "match_confidence": {
                        col: conf for col, conf in matching_result.get("confidence_scores", {}).items()
                    },
                    "unmatched_columns": matching_result.get("unmatched_columns", []),
                    "missing_standard_columns": matching_result.get("missing_columns", []),
                    "matching_report": matching_result.get("matching_report", "")
                }
                
                # 生成列匹配建议
                if matching_result.get("unmatched_columns"):
                    enhanced_result["recommendations"].append({
                        "type": "column_matching",
                        "priority": "high",
                        "message": f"发现 {len(matching_result['unmatched_columns'])} 个未匹配的列，建议检查列名规范",
                        "details": matching_result["unmatched_columns"]
                    })
                
                # 低置信度匹配警告
                low_confidence_matches = [
                    col for col, conf in matching_result.get("confidence_scores", {}).items()
                    if conf < 0.7
                ]
                if low_confidence_matches:
                    enhanced_result["recommendations"].append({
                        "type": "low_confidence_matching",
                        "priority": "medium", 
                        "message": f"发现 {len(low_confidence_matches)} 个低置信度匹配，建议人工确认",
                        "details": low_confidence_matches
                    })
            
            # 数据质量分析
            if "standardization_result" in first_table_result:
                std_result = first_table_result["standardization_result"]
                quality_score = std_result.get("data_quality_score", 0.0)
                
                enhanced_result["enhanced_summary"]["data_quality_score"] = quality_score
                enhanced_result["enhanced_summary"]["standardization_issues"] = len(std_result.get("issues", []))
                
                if quality_score < 0.7:
                    enhanced_result["recommendations"].append({
                        "type": "data_quality",
                        "priority": "high",
                        "message": f"数据质量较低 ({quality_score:.2f})，建议检查原始数据",
                        "details": std_result.get("issues", [])[:5]  # 只显示前5个问题
                    })
        
        # 合并传统分析结果（如果有）
        if legacy_result:
            enhanced_result["enhanced_summary"].update({
                "legacy_total_changes": legacy_result["summary"]["total_changes"],
                "legacy_l1_violations": legacy_result["summary"]["l1_violations"],
                "legacy_l2_modifications": legacy_result["summary"]["l2_modifications"],
                "legacy_l3_modifications": legacy_result["summary"]["l3_modifications"],
                "legacy_risk_score": legacy_result["summary"]["risk_score"]
            })
            
            # L1违规严重警告
            if legacy_result["summary"]["l1_violations"] > 0:
                enhanced_result["recommendations"].append({
                    "type": "l1_violations",
                    "priority": "critical",
                    "message": f"检测到 {legacy_result['summary']['l1_violations']} 个L1级严重违规修改",
                    "details": [
                        change for change in legacy_result["detailed_changes"] 
                        if change["risk_level"] == "L1"
                    ][:3]  # 只显示前3个
                })
        
        # 处理统计汇总
        processing_stats = adaptive_result.get("processing_stats", {})
        enhanced_result["enhanced_summary"].update({
            "tables_processed": processing_stats.get("tables_processed", 0),
            "average_match_confidence": processing_stats.get("average_match_confidence", 0.0),
            "total_processing_time": processing_stats.get("total_processing_time", 0.0)
        })
        
        # 整体风险评估
        overall_risk = self._assess_overall_risk(enhanced_result)
        enhanced_result["enhanced_summary"]["overall_risk_level"] = overall_risk
        
        return enhanced_result
    
    def _assess_overall_risk(self, enhanced_result: Dict[str, Any]) -> str:
        """评估整体风险等级"""
        
        # 检查L1违规
        l1_violations = enhanced_result["enhanced_summary"].get("legacy_l1_violations", 0)
        if l1_violations > 0:
            return "CRITICAL"  # 有L1违规就是严重风险
        
        # 检查数据质量
        data_quality = enhanced_result["enhanced_summary"].get("data_quality_score", 1.0)
        if data_quality < 0.6:
            return "HIGH"  # 数据质量太低
        
        # 检查匹配质量
        column_intel = enhanced_result.get("column_intelligence", {})
        match_rate = 0
        if column_intel.get("total_input_columns", 0) > 0:
            match_rate = column_intel.get("successfully_matched", 0) / column_intel["total_input_columns"]
        
        if match_rate < 0.7:
            return "HIGH"  # 匹配率太低
        
        # 检查L2修改数量
        l2_modifications = enhanced_result["enhanced_summary"].get("legacy_l2_modifications", 0)
        if l2_modifications > 5:
            return "MEDIUM"  # L2修改较多
        
        return "LOW"  # 其他情况认为是低风险
    
    def load_csv_data(self, file_path: str) -> pd.DataFrame:
        """加载CSV数据"""
        try:
            # 使用UTF-8编码读取，跳过BOM，跳过第一行标题
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=1)
            return df
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return pd.DataFrame()

    def compare_dataframes(self, df_original: pd.DataFrame, df_modified: pd.DataFrame) -> Dict[str, Any]:
        """对比两个DataFrame，检测变更"""
        changes = {
            "summary": {
                "total_changes": 0,
                "l1_violations": 0,
                "l2_modifications": 0, 
                "l3_modifications": 0,
                "risk_score": 0.0
            },
            "detailed_changes": [],
            "risk_matrix": {}
        }
        
        # 确保两个DataFrame有相同的形状进行对比
        max_rows = max(len(df_original), len(df_modified))
        max_cols = max(len(df_original.columns) if not df_original.empty else 0, 
                      len(df_modified.columns) if not df_modified.empty else 0)
        
        # 重新索引以确保对齐
        if not df_original.empty:
            df_original = df_original.reindex(range(max_rows))
        if not df_modified.empty:
            df_modified = df_modified.reindex(range(max_rows))
        
        # 逐列对比
        for col_idx, col_name in enumerate(df_modified.columns if not df_modified.empty else []):
            if col_name in df_original.columns:
                original_col = df_original[col_name].fillna("")
                modified_col = df_modified[col_name].fillna("")
                
                # 逐行对比该列
                for row_idx in range(max_rows):
                    original_value = str(original_col.iloc[row_idx]) if row_idx < len(original_col) else ""
                    modified_value = str(modified_col.iloc[row_idx]) if row_idx < len(modified_col) else ""
                    
                    if original_value != modified_value:
                        change = self._analyze_change(
                            row_idx, col_name, original_value, modified_value
                        )
                        changes["detailed_changes"].append(change)
                        changes["summary"]["total_changes"] += 1
                        
                        # 统计不同风险等级的修改
                        risk_level = change["risk_level"]
                        if risk_level == "L1":
                            changes["summary"]["l1_violations"] += 1
                        elif risk_level == "L2":
                            changes["summary"]["l2_modifications"] += 1
                        elif risk_level == "L3":
                            changes["summary"]["l3_modifications"] += 1
                        
                        # 累计风险分数
                        changes["summary"]["risk_score"] += change["risk_score"]
        
        # 生成风险矩阵（用于热力图）
        changes["risk_matrix"] = self._generate_risk_matrix(df_modified, changes["detailed_changes"])
        
        return changes

    def _analyze_change(self, row_idx: int, col_name: str, original: str, modified: str) -> Dict[str, Any]:
        """分析单个变更的详细信息"""
        # 获取列的风险等级
        risk_level = self.column_risk_levels.get(col_name, "L2")
        risk_score = self.risk_scores[risk_level]
        
        # 检测修改类型
        change_type = "content_update"
        if "【修改】" in modified:
            change_type = "explicit_modification"
            risk_score *= 1.2  # 明确标记的修改增加风险分数
        elif "【新增】" in modified:
            change_type = "content_addition"
            risk_score *= 1.1
        elif original and not modified:
            change_type = "deletion"
            risk_score *= 1.3
        elif not original and modified:
            change_type = "insertion"
            risk_score *= 1.1
            
        # 计算修改强度（基于文本差异程度）
        similarity = self._calculate_similarity(original, modified)
        modification_intensity = 1.0 - similarity
        
        return {
            "row": row_idx,
            "column": col_name,
            "original_value": original[:100] + "..." if len(original) > 100 else original,
            "modified_value": modified[:100] + "..." if len(modified) > 100 else modified,
            "change_type": change_type,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "modification_intensity": modification_intensity,
            "severity": self._assess_severity(risk_level, modification_intensity),
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
            
        # 使用SequenceMatcher计算相似度
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()

    def _assess_severity(self, risk_level: str, modification_intensity: float) -> str:
        """评估修改严重程度"""
        if risk_level == "L1":
            return "critical"  # L1列的任何修改都是严重的
        elif risk_level == "L2":
            if modification_intensity > 0.7:
                return "high"
            elif modification_intensity > 0.4:
                return "medium"
            else:
                return "low"
        else:  # L3
            if modification_intensity > 0.8:
                return "medium"
            else:
                return "low"

    def _generate_risk_matrix(self, df: pd.DataFrame, changes: List[Dict]) -> Dict[str, Any]:
        """生成用于热力图的风险矩阵"""
        if df.empty:
            return {}
            
        matrix = {}
        rows, cols = df.shape
        
        # 初始化矩阵
        for col_name in df.columns:
            matrix[col_name] = [0.0] * rows
        
        # 填入风险分数
        for change in changes:
            col_name = change["column"]
            row_idx = change["row"]
            if col_name in matrix and row_idx < len(matrix[col_name]):
                matrix[col_name][row_idx] = change["modification_intensity"] * change["risk_score"]
        
        return matrix

    def generate_report(self, changes: Dict[str, Any]) -> str:
        """生成变更分析报告"""
        report = []
        report.append("=" * 60)
        report.append("腾讯文档变更检测报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 概要统计
        summary = changes["summary"]
        report.append("📊 变更概要:")
        report.append(f"  总变更数量: {summary['total_changes']}")
        report.append(f"  🔴 L1级严重违规: {summary['l1_violations']} (绝对不能修改)")
        report.append(f"  🟡 L2级异常修改: {summary['l2_modifications']} (需要语义审核)")
        report.append(f"  🟢 L3级常规修改: {summary['l3_modifications']} (可自由编辑)")
        report.append(f"  综合风险评分: {summary['risk_score']:.2f}")
        
        # 风险等级评估
        if summary['l1_violations'] > 0:
            report.append(f"  ⚠️  风险等级: 🔴 严重 (发现L1级别违规)")
        elif summary['l2_modifications'] > 3:
            report.append(f"  ⚠️  风险等级: 🟡 中等 (L2修改较多)")
        else:
            report.append(f"  ⚠️  风险等级: 🟢 正常")
        
        report.append("")
        
        # 详细变更列表
        if changes["detailed_changes"]:
            report.append("📋 详细变更记录:")
            for i, change in enumerate(changes["detailed_changes"][:10], 1):  # 只显示前10个
                report.append(f"\n  [{i}] 第{change['row'] + 1}行 - {change['column']}")
                report.append(f"      风险等级: {change['risk_level']} | 严重程度: {change['severity']}")
                report.append(f"      修改强度: {change['modification_intensity']:.2f} | 风险分数: {change['risk_score']:.2f}")
                report.append(f"      原内容: {change['original_value']}")
                report.append(f"      新内容: {change['modified_value']}")
                report.append(f"      修改类型: {change['change_type']}")
                
            if len(changes["detailed_changes"]) > 10:
                report.append(f"\n  ... 还有 {len(changes['detailed_changes']) - 10} 个变更未显示")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    """主函数：执行对比分析测试 - 增强版本，支持自适应和传统两种模式"""
    print("🔍 启动腾讯文档变更检测系统 - 增强版本")
    print("支持自适应表格对比和传统对比两种模式")
    
    analyzer = DocumentChangeAnalyzer()
    
    # 文件路径
    original_file = "/root/projects/tencent-doc-manager/refer/测试版本-小红书部门-工作表2.csv"
    modified_file = "/root/projects/tencent-doc-manager/测试版本-小红书部门-工作表2-修改版.csv"
    
    print(f"\n=== 模式选择 ===")
    print(f"当前处理模式: {analyzer.processing_mode}")
    print("模式说明:")
    print("  - hybrid: 混合模式（推荐）- 同时运行自适应和传统对比")
    print("  - adaptive: 仅自适应模式 - 智能列匹配和标准化")
    print("  - legacy: 仅传统模式 - 原有的逐列对比")
    
    # 执行自适应对比分析
    print(f"\n🚀 执行自适应对比分析...")
    adaptive_result = analyzer.adaptive_compare_tables(modified_file, original_file)
    
    if "error" in adaptive_result:
        print(f"❌ 自适应分析失败: {adaptive_result['error']}")
        return
    
    # 显示增强分析结果
    print("\n" + "="*80)
    print("📊 自适应表格对比分析报告")
    print("="*80)
    
    enhanced_summary = adaptive_result.get("enhanced_summary", {})
    column_intelligence = adaptive_result.get("column_intelligence", {})
    recommendations = adaptive_result.get("recommendations", [])
    
    # 基本信息
    print(f"分析模式: {adaptive_result.get('analysis_mode', 'unknown')}")
    print(f"分析时间: {adaptive_result.get('analysis_timestamp', 'unknown')}")
    print(f"处理耗时: {enhanced_summary.get('total_processing_time', 0):.2f}秒")
    
    # 列匹配智能分析
    print(f"\n📋 列匹配智能分析:")
    print(f"  输入列数: {column_intelligence.get('total_input_columns', 0)}")
    print(f"  成功匹配: {column_intelligence.get('successfully_matched', 0)}")
    print(f"  匹配成功率: {column_intelligence.get('successfully_matched', 0) / max(1, column_intelligence.get('total_input_columns', 1)) * 100:.1f}%")
    print(f"  平均匹配置信度: {enhanced_summary.get('average_match_confidence', 0):.3f}")
    
    if column_intelligence.get("unmatched_columns"):
        print(f"  未匹配列: {column_intelligence['unmatched_columns']}")
    
    if column_intelligence.get("missing_standard_columns"):
        print(f"  缺失标准列: {column_intelligence['missing_standard_columns']}")
    
    # 数据质量分析
    print(f"\n📈 数据质量分析:")
    data_quality = enhanced_summary.get("data_quality_score")
    if data_quality is not None:
        print(f"  数据质量分数: {data_quality:.3f}")
        quality_status = "优秀" if data_quality >= 0.9 else "良好" if data_quality >= 0.7 else "待改进"
        print(f"  质量等级: {quality_status}")
        
    standardization_issues = enhanced_summary.get("standardization_issues", 0)
    if standardization_issues > 0:
        print(f"  标准化问题数: {standardization_issues}")
    
    # 传统对比结果（如果有）
    if "legacy_analysis" in adaptive_result and adaptive_result["legacy_analysis"]:
        print(f"\n🔍 传统对比分析结果:")
        print(f"  总变更数: {enhanced_summary.get('legacy_total_changes', 0)}")
        print(f"  🔴 L1级严重违规: {enhanced_summary.get('legacy_l1_violations', 0)}")
        print(f"  🟡 L2级异常修改: {enhanced_summary.get('legacy_l2_modifications', 0)}")
        print(f"  🟢 L3级常规修改: {enhanced_summary.get('legacy_l3_modifications', 0)}")
        print(f"  综合风险评分: {enhanced_summary.get('legacy_risk_score', 0):.2f}")
    
    # 整体风险评估
    overall_risk = enhanced_summary.get("overall_risk_level", "UNKNOWN")
    risk_icons = {
        "CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"
    }
    print(f"\n⚠️  整体风险等级: {risk_icons.get(overall_risk, '❓')} {overall_risk}")
    
    # 建议和推荐
    if recommendations:
        print(f"\n💡 系统建议 ({len(recommendations)}条):")
        for i, rec in enumerate(recommendations, 1):
            priority_icons = {
                "critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"
            }
            icon = priority_icons.get(rec.get("priority", "medium"), "💡")
            print(f"  [{i}] {icon} {rec.get('message', '')}")
            if rec.get("details") and len(rec["details"]) <= 3:
                for detail in rec["details"]:
                    if isinstance(detail, dict):
                        print(f"      - {detail.get('column', 'unknown')}: {detail.get('change_type', 'unknown')}")
                    else:
                        print(f"      - {detail}")
    
    # 保存详细结果到JSON文件
    output_file = "/root/projects/tencent-doc-manager/自适应分析结果.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(adaptive_result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 详细分析结果已保存至: {output_file}")
    
    # 显示详细匹配报告（如果有）
    if column_intelligence.get("matching_report"):
        print(f"\n📋 详细匹配报告:")
        print(column_intelligence["matching_report"])
    
    # 传统模式的验证检测（兼容性保持）
    if enhanced_summary.get("legacy_total_changes", 0) > 0:
        print(f"\n🔍 传统模式验证检测准确性:")
        detected_l1 = enhanced_summary.get("legacy_l1_violations", 0)
        detected_l2 = enhanced_summary.get("legacy_l2_modifications", 0) 
        detected_l3 = enhanced_summary.get("legacy_l3_modifications", 0)
        
        print(f"  预期L1违规: 4个, 检测到: {detected_l1}个")
        print(f"  预期L2修改: 1个, 检测到: {detected_l2}个")
        print(f"  预期L3修改: 1个, 检测到: {detected_l3}个")
        
        if detected_l1 >= 4 and detected_l2 >= 1:
            print("✅ 传统检测准确性良好: 成功识别关键风险修改")
        else:
            print("⚠️  传统检测结果需要进一步优化")
    
    print(f"\n✅ 自适应表格对比分析完成")
    print("="*80)

if __name__ == "__main__":
    main()