# -*- coding: utf-8 -*-
"""
自适应表格对比器 - 增强版本
基于document_change_analyzer.py扩展，支持30个异构表格的智能对比分析
"""

import pandas as pd
import numpy as np
import json
import hashlib
import time
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
import asyncio
import functools

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentColumnMatcher:
    """智能列匹配引擎"""
    
    def __init__(self):
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
        
        # 列名变异映射表（基于历史数据学习）
        self.column_variations = {
            "项目类型": ["项目分类", "类型", "项目", "分类", "project_type"],
            "来源": ["数据来源", "来源部门", "源头", "起源", "source"],
            "任务发起时间": ["发起时间", "开始时间", "任务时间", "发起日期", "start_time"],
            "目标对齐": ["对齐目标", "目标", "对齐情况", "目标匹配", "goal_alignment"],
            "关键KR对齐": ["KR对齐", "关键结果", "KR匹配", "关键指标对齐", "kr_alignment"],
            "具体计划内容": ["计划内容", "计划详情", "具体计划", "内容", "plan_content"],
            "负责人": ["责任人", "主负责人", "项目负责人", "负责", "owner", "responsible"],
            "协助人": ["协助", "协助者", "协助人员", "辅助人", "assistant"],
            "监督人": ["监督", "监督者", "监督人员", "督导", "supervisor"],
            "重要程度": ["重要性", "优先级", "重要等级", "程度", "priority", "importance"],
            "预计完成时间": ["完成时间", "计划完成", "预期完成", "截止时间", "deadline"],
            "完成进度": ["进度", "完成度", "完成状态", "进展", "progress"],
            "形成计划清单": ["计划清单", "清单", "任务清单", "计划列表", "checklist"],
            "复盘时间": ["复盘", "复盘日期", "回顾时间", "总结时间", "review_time"],
            "对上汇报": ["汇报", "上报", "汇报情况", "汇报状态", "report"],
            "应用情况": ["应用", "应用状态", "使用情况", "执行情况", "application"],
            "进度分析总结": ["分析总结", "总结", "进度总结", "分析报告", "summary"]
        }
        
        # 语义相似度计算器
        self.similarity_calculator = SemanticSimilarityCalculator()
        
        # 匹配历史记录（用于学习和改进）
        self.matching_history = []
        
    def match_columns(self, actual_columns: List[str], table_name: str = None, 
                     confidence_threshold: float = 0.6) -> Dict[str, Any]:
        """
        智能列匹配主函数
        
        Args:
            actual_columns: 实际表格的列名列表
            table_name: 表格名称（用于上下文分析）
            confidence_threshold: 匹配置信度阈值
            
        Returns:
            {
                "mapping": {"实际列名": "标准列名"},
                "confidence_scores": {"实际列名": 置信度分数},
                "unmatched_columns": ["未匹配的列名"],
                "missing_columns": ["缺失的标准列名"],
                "matching_report": "详细匹配报告"
            }
        """
        
        matching_result = {
            "mapping": {},
            "confidence_scores": {},
            "unmatched_columns": [],
            "missing_columns": [],
            "matching_report": ""
        }
        
        logger.info(f"开始匹配表格列名: {table_name}, 输入列数: {len(actual_columns)}")
        
        # 步骤1: 精确匹配
        exact_matches = self._find_exact_matches(actual_columns)
        for actual_col, standard_col in exact_matches.items():
            matching_result["mapping"][actual_col] = standard_col
            matching_result["confidence_scores"][actual_col] = 1.0
            
        logger.info(f"精确匹配结果: {len(exact_matches)}个")
        
        # 步骤2: 变异匹配
        remaining_columns = [col for col in actual_columns if col not in exact_matches]
        variation_matches = self._find_variation_matches(remaining_columns)
        for actual_col, (standard_col, confidence) in variation_matches.items():
            if confidence >= confidence_threshold:
                matching_result["mapping"][actual_col] = standard_col
                matching_result["confidence_scores"][actual_col] = confidence
                remaining_columns.remove(actual_col)
                
        logger.info(f"变异匹配结果: {len(variation_matches)}个")
        
        # 步骤3: 语义相似度匹配
        semantic_matches = self._find_semantic_matches(
            remaining_columns, table_name, confidence_threshold
        )
        for actual_col, (standard_col, confidence) in semantic_matches.items():
            matching_result["mapping"][actual_col] = standard_col
            matching_result["confidence_scores"][actual_col] = confidence
            remaining_columns.remove(actual_col)
            
        logger.info(f"语义匹配结果: {len(semantic_matches)}个")
        
        # 步骤4: 位置启发式匹配
        position_matches = self._find_position_based_matches(
            remaining_columns, actual_columns, confidence_threshold
        )
        for actual_col, (standard_col, confidence) in position_matches.items():
            matching_result["mapping"][actual_col] = standard_col
            matching_result["confidence_scores"][actual_col] = confidence
            remaining_columns.remove(actual_col)
            
        logger.info(f"位置匹配结果: {len(position_matches)}个")
        
        # 确定未匹配和缺失的列
        matching_result["unmatched_columns"] = remaining_columns
        matched_standard_columns = set(matching_result["mapping"].values())
        matching_result["missing_columns"] = [
            col for col in self.standard_columns 
            if col not in matched_standard_columns
        ]
        
        # 生成匹配报告
        matching_result["matching_report"] = self._generate_matching_report(
            matching_result, actual_columns, table_name
        )
        
        # 记录匹配历史用于学习
        self._record_matching_history(actual_columns, matching_result, table_name)
        
        return matching_result
    
    def _find_exact_matches(self, actual_columns: List[str]) -> Dict[str, str]:
        """精确匹配：完全相同的列名"""
        exact_matches = {}
        for actual_col in actual_columns:
            if actual_col in self.standard_columns:
                exact_matches[actual_col] = actual_col
        return exact_matches
    
    def _find_variation_matches(self, remaining_columns: List[str]) -> Dict[str, Tuple[str, float]]:
        """变异匹配：已知变异形式的列名"""
        variation_matches = {}
        
        for actual_col in remaining_columns:
            best_match = None
            best_confidence = 0.0
            
            for standard_col, variations in self.column_variations.items():
                for variation in variations:
                    # 计算文本相似度
                    similarity = self._calculate_text_similarity(actual_col, variation)
                    if similarity > best_confidence:
                        best_match = standard_col
                        best_confidence = similarity
            
            if best_match and best_confidence > 0.7:  # 变异匹配需要较高置信度
                variation_matches[actual_col] = (best_match, best_confidence)
        
        return variation_matches
    
    def _find_semantic_matches(self, remaining_columns: List[str], table_name: str, 
                             threshold: float) -> Dict[str, Tuple[str, float]]:
        """语义匹配：基于语义相似度的匹配"""
        semantic_matches = {}
        
        for actual_col in remaining_columns:
            # 为每个剩余列计算与所有标准列的语义相似度
            similarities = []
            for standard_col in self.standard_columns:
                semantic_score = self.similarity_calculator.calculate_semantic_similarity(
                    actual_col, standard_col, context=table_name
                )
                similarities.append((standard_col, semantic_score))
            
            # 选择最高相似度的匹配
            best_match = max(similarities, key=lambda x: x[1])
            if best_match[1] >= threshold:
                semantic_matches[actual_col] = best_match
        
        return semantic_matches
    
    def _find_position_based_matches(self, remaining_columns: List[str], 
                                   all_columns: List[str], threshold: float) -> Dict[str, Tuple[str, float]]:
        """位置启发式匹配：基于列的位置信息进行匹配"""
        position_matches = {}
        
        for i, actual_col in enumerate(all_columns):
            if actual_col in remaining_columns:
                # 基于位置推测可能的标准列
                if i < len(self.standard_columns):
                    expected_standard_col = self.standard_columns[i]
                    
                    # 计算位置匹配置信度
                    position_confidence = self._calculate_position_confidence(
                        actual_col, expected_standard_col, i
                    )
                    
                    if position_confidence >= threshold:
                        position_matches[actual_col] = (expected_standard_col, position_confidence)
        
        return position_matches
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（基于编辑距离和字符相似度）"""
        # Levenshtein距离
        edit_distance = self._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 1.0
        
        # 基于编辑距离的相似度
        edit_similarity = 1 - (edit_distance / max_len)
        
        # 字符重叠相似度
        set1 = set(text1)
        set2 = set(text2)
        overlap_similarity = len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0
        
        # 综合相似度
        final_similarity = 0.7 * edit_similarity + 0.3 * overlap_similarity
        
        return final_similarity
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算Levenshtein编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _calculate_position_confidence(self, actual_col: str, expected_col: str, position: int) -> float:
        """计算位置匹配置信度"""
        # 基于位置的基础置信度
        base_confidence = max(0.3, 1.0 - position * 0.05)  # 位置越后置信度越低
        
        # 基于文本相似度的调整
        text_similarity = self._calculate_text_similarity(actual_col, expected_col)
        
        # 综合置信度
        return base_confidence * 0.4 + text_similarity * 0.6
    
    def _generate_matching_report(self, result: Dict[str, Any], 
                                actual_columns: List[str], table_name: str) -> str:
        """生成匹配报告"""
        total_matched = len(result["mapping"])
        total_columns = len(actual_columns)
        match_rate = (total_matched / total_columns) * 100 if total_columns > 0 else 0
        
        report = f"""
=== 列匹配分析报告 ===
表格名称: {table_name or '未知'}
输入列数: {total_columns}
匹配成功: {total_matched} ({match_rate:.1f}%)
平均置信度: {np.mean(list(result["confidence_scores"].values())):.3f}

=== 匹配详情 ===
"""
        
        for actual_col, standard_col in result["mapping"].items():
            confidence = result["confidence_scores"][actual_col]
            report += f"• {actual_col} → {standard_col} (置信度: {confidence:.3f})\n"
        
        if result["unmatched_columns"]:
            report += f"\n=== 未匹配列 ({len(result['unmatched_columns'])}个) ===\n"
            for col in result["unmatched_columns"]:
                report += f"• {col}\n"
        
        if result["missing_columns"]:
            report += f"\n=== 缺失标准列 ({len(result['missing_columns'])}个) ===\n"
            for col in result["missing_columns"]:
                report += f"• {col}\n"
        
        return report.strip()
    
    def _record_matching_history(self, actual_columns: List[str], 
                               result: Dict[str, Any], table_name: str):
        """记录匹配历史用于学习"""
        history_record = {
            "timestamp": datetime.now().isoformat(),
            "table_name": table_name,
            "input_columns": actual_columns,
            "matching_result": result,
            "success_rate": len(result["mapping"]) / len(actual_columns) if actual_columns else 0
        }
        
        self.matching_history.append(history_record)
        
        # 保持历史记录在合理范围内
        if len(self.matching_history) > 100:
            self.matching_history = self.matching_history[-100:]


class SemanticSimilarityCalculator:
    """语义相似度计算器"""
    
    def __init__(self):
        # 业务领域词汇映射
        self.domain_vocabulary = {
            "时间": ["时间", "日期", "期限", "截止", "开始", "结束", "time", "date"],
            "人员": ["人", "员", "者", "负责", "主管", "经理", "owner", "responsible"],
            "进度": ["进度", "完成", "状态", "情况", "程度", "progress", "status"],
            "内容": ["内容", "详情", "描述", "说明", "计划", "content", "description"],
            "重要": ["重要", "优先", "关键", "核心", "主要", "priority", "important"]
        }
        
        # 上下文关键词
        self.context_keywords = {
            "项目管理": ["项目", "管理", "计划", "执行", "监控"],
            "任务追踪": ["任务", "跟踪", "追踪", "监督", "检查"],
            "绩效评估": ["绩效", "评估", "考核", "评价", "分析"]
        }
    
    def calculate_semantic_similarity(self, actual_column: str, standard_column: str, 
                                    context: str = None) -> float:
        """
        计算语义相似度
        
        Args:
            actual_column: 实际列名
            standard_column: 标准列名
            context: 上下文信息（如表格名称）
        
        Returns:
            float: 语义相似度分数 (0-1)
        """
        
        # 基础词汇匹配分数
        word_similarity = self._calculate_word_similarity(actual_column, standard_column)
        
        # 领域语义分数
        domain_similarity = self._calculate_domain_similarity(actual_column, standard_column)
        
        # 上下文增强分数
        context_boost = self._calculate_context_boost(
            actual_column, standard_column, context
        ) if context else 0
        
        # 综合语义相似度
        semantic_score = (
            0.4 * word_similarity + 
            0.4 * domain_similarity + 
            0.2 * context_boost
        )
        
        return min(1.0, semantic_score)
    
    def _calculate_word_similarity(self, actual: str, standard: str) -> float:
        """计算词汇级别的相似度"""
        actual_words = self._extract_meaningful_words(actual)
        standard_words = self._extract_meaningful_words(standard)
        
        if not actual_words or not standard_words:
            return 0.0
        
        # 计算词汇重叠度
        overlap = len(set(actual_words) & set(standard_words))
        total = len(set(actual_words) | set(standard_words))
        
        return overlap / total if total > 0 else 0.0
    
    def _extract_meaningful_words(self, text: str) -> List[str]:
        """提取有意义的词汇"""
        # 简单的中英文词汇分割
        import re
        
        # 提取中文词汇和英文单词
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        
        return chinese_words + english_words
    
    def _calculate_domain_similarity(self, actual: str, standard: str) -> float:
        """计算领域语义相似度"""
        actual_domains = self._identify_domains(actual)
        standard_domains = self._identify_domains(standard)
        
        if not actual_domains or not standard_domains:
            return 0.0
        
        # 领域重叠度
        domain_overlap = len(actual_domains & standard_domains)
        domain_total = len(actual_domains | standard_domains)
        
        return domain_overlap / domain_total if domain_total > 0 else 0.0
    
    def _identify_domains(self, column_name: str) -> set:
        """识别列名所属的业务领域"""
        identified_domains = set()
        
        for domain, keywords in self.domain_vocabulary.items():
            for keyword in keywords:
                if keyword in column_name:
                    identified_domains.add(domain)
        
        return identified_domains
    
    def _calculate_context_boost(self, actual: str, standard: str, context: str) -> float:
        """计算上下文增强分数"""
        if not context:
            return 0.0
        
        context_boost = 0.0
        for context_type, keywords in self.context_keywords.items():
            for keyword in keywords:
                if keyword in context:
                    # 如果上下文匹配，给相关字段加分
                    if self._is_context_relevant(actual, standard, context_type):
                        context_boost += 0.1
        
        return min(1.0, context_boost)
    
    def _is_context_relevant(self, actual: str, standard: str, context_type: str) -> bool:
        """判断是否与上下文相关"""
        # 简单的关联性判断
        relevant_mappings = {
            "项目管理": ["负责人", "计划", "进度", "内容"],
            "任务追踪": ["状态", "完成", "进度"],
            "绩效评估": ["重要", "评估", "分析"]
        }
        
        if context_type in relevant_mappings:
            for term in relevant_mappings[context_type]:
                if term in actual or term in standard:
                    return True
        
        return False


class AdaptiveDataStandardizer:
    """自适应数据标准化器"""
    
    def __init__(self):
        self.standard_data_types = {
            "序号": int,
            "项目类型": str,
            "来源": str,
            "任务发起时间": "datetime",
            "目标对齐": str,
            "关键KR对齐": str,
            "具体计划内容": str,
            "邓总指导登记": str,
            "负责人": str,
            "协助人": str,
            "监督人": str,
            "重要程度": str,  # 可能是数值或文本
            "预计完成时间": "datetime",
            "完成进度": "percentage",  # 0-1或0-100%
            "形成计划清单": str,
            "复盘时间": "datetime",
            "对上汇报": str,
            "应用情况": str,
            "进度分析总结": str
        }
        
        self.standardization_rules = {
            "datetime": self._standardize_datetime,
            "percentage": self._standardize_percentage,
            int: self._standardize_integer,
            str: self._standardize_string
        }
        
    def standardize_table_data(self, raw_data: List[List], column_mapping: Dict[str, str], 
                             table_metadata: Dict = None) -> Dict[str, Any]:
        """
        标准化表格数据
        
        Args:
            raw_data: 原始表格数据 (list of lists)
            column_mapping: 列名映射 {"实际列名": "标准列名"}
            table_metadata: 表格元数据
            
        Returns:
            {
                "standardized_data": 标准化后的数据,
                "standardization_report": 标准化报告,
                "data_quality_score": 数据质量分数,
                "issues": 发现的问题列表
            }
        """
        
        if not raw_data:
            return self._empty_standardization_result()
        
        logger.info(f"开始数据标准化，原始数据行数: {len(raw_data)}")
        
        # 提取标题行和数据行
        headers = raw_data[0] if raw_data else []
        data_rows = raw_data[1:] if len(raw_data) > 1 else []
        
        # 创建标准化后的数据结构
        standardized_data = []
        standardization_issues = []
        
        # 处理每一行数据
        for row_index, row in enumerate(data_rows):
            try:
                standardized_row = self._standardize_single_row(
                    row, headers, column_mapping, row_index, standardization_issues
                )
                standardized_data.append(standardized_row)
            except Exception as e:
                logger.error(f"第{row_index + 1}行数据标准化失败: {e}")
                standardization_issues.append({
                    "type": "row_processing_error",
                    "row": row_index,
                    "error": str(e),
                    "raw_data": row
                })
        
        # 填充缺失列
        standardized_data = self._fill_missing_columns(
            standardized_data, column_mapping, standardization_issues
        )
        
        # 计算数据质量分数
        quality_score = self._calculate_data_quality_score(
            standardized_data, standardization_issues, len(data_rows)
        )
        
        logger.info(f"数据标准化完成，质量分数: {quality_score:.3f}")
        
        return {
            "standardized_data": standardized_data,
            "standardization_report": self._generate_standardization_report(
                standardization_issues, quality_score
            ),
            "data_quality_score": quality_score,
            "issues": standardization_issues
        }
    
    def _standardize_single_row(self, row: List, headers: List[str], 
                              column_mapping: Dict[str, str], row_index: int, 
                              issues: List[Dict]) -> Dict[str, Any]:
        """标准化单行数据"""
        standardized_row = {}
        
        # 处理每个标准列
        for standard_column in self.standard_data_types.keys():
            value = None
            
            # 查找对应的实际列值
            for actual_column, mapped_standard in column_mapping.items():
                if mapped_standard == standard_column:
                    try:
                        actual_column_index = headers.index(actual_column) if actual_column in headers else -1
                        if actual_column_index != -1 and actual_column_index < len(row):
                            raw_value = row[actual_column_index]
                            
                            # 应用标准化规则
                            value = self._apply_standardization_rule(
                                raw_value, standard_column, row_index, actual_column
                            )
                    except Exception as e:
                        issues.append({
                            "type": "standardization_error",
                            "row": row_index,
                            "column": standard_column,
                            "raw_value": row[actual_column_index] if actual_column_index < len(row) else None,
                            "error": str(e)
                        })
                        value = self._get_default_value(standard_column)
                    break
            
            # 如果没有找到对应值，使用默认值
            if value is None:
                value = self._get_default_value(standard_column)
                issues.append({
                    "type": "missing_value",
                    "row": row_index,
                    "column": standard_column,
                    "default_used": value
                })
            
            standardized_row[standard_column] = value
        
        return standardized_row
    
    def _apply_standardization_rule(self, raw_value: Any, standard_column: str, 
                                  row_index: int, actual_column: str) -> Any:
        """应用标准化规则"""
        expected_type = self.standard_data_types.get(standard_column, str)
        
        if expected_type in self.standardization_rules:
            return self.standardization_rules[expected_type](raw_value, standard_column)
        else:
            return str(raw_value) if raw_value is not None else ""
    
    def _standardize_datetime(self, value: Any, column_name: str) -> Optional[str]:
        """标准化日期时间"""
        if not value or pd.isna(value):
            return None
        
        # 尝试多种日期格式
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d", 
            "%Y年%m月%d日",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%m/%d/%Y",
            "%d/%m/%Y"
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(value).strip(), fmt)
                return parsed_date.isoformat()
            except ValueError:
                continue
        
        # 如果所有格式都失败，返回原值
        return str(value)
    
    def _standardize_percentage(self, value: Any, column_name: str) -> float:
        """标准化百分比"""
        if not value or pd.isna(value):
            return 0.0
        
        str_value = str(value).strip()
        
        # 处理百分号格式
        if '%' in str_value:
            numeric_part = str_value.replace('%', '').strip()
            try:
                return float(numeric_part) / 100.0
            except ValueError:
                return 0.0
        
        # 处理小数格式
        try:
            numeric_value = float(str_value)
            if numeric_value > 1.0:
                return numeric_value / 100.0  # 假设是百分数形式
            return numeric_value
        except ValueError:
            return 0.0
    
    def _standardize_integer(self, value: Any, column_name: str) -> int:
        """标准化整数"""
        if not value or pd.isna(value):
            return 0
        
        try:
            return int(float(str(value)))
        except ValueError:
            return 0
    
    def _standardize_string(self, value: Any, column_name: str) -> str:
        """标准化字符串"""
        if not value or pd.isna(value):
            return ""
        
        # 清理字符串
        cleaned = str(value).strip()
        
        # 移除多余的空白字符
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _get_default_value(self, standard_column: str) -> Any:
        """获取默认值"""
        expected_type = self.standard_data_types.get(standard_column, str)
        
        if expected_type == int:
            return 0
        elif expected_type == "datetime":
            return None
        elif expected_type == "percentage":
            return 0.0
        else:
            return ""
    
    def _fill_missing_columns(self, standardized_data: List[Dict], 
                            column_mapping: Dict[str, str], issues: List[Dict]) -> List[Dict]:
        """填充缺失列"""
        if not standardized_data:
            return standardized_data
        
        # 确保所有行都有所有标准列
        for row_index, row in enumerate(standardized_data):
            for standard_column in self.standard_data_types.keys():
                if standard_column not in row:
                    default_value = self._get_default_value(standard_column)
                    row[standard_column] = default_value
                    
                    issues.append({
                        "type": "column_filled",
                        "row": row_index,
                        "column": standard_column,
                        "default_value": default_value
                    })
        
        return standardized_data
    
    def _calculate_data_quality_score(self, standardized_data: List[Dict], 
                                    issues: List[Dict], original_row_count: int) -> float:
        """计算数据质量分数"""
        if not standardized_data or original_row_count == 0:
            return 0.0
        
        # 统计问题类型
        error_types = Counter(issue["type"] for issue in issues)
        
        # 基础分数
        base_score = 1.0
        
        # 根据不同问题类型扣分
        if error_types.get("standardization_error", 0) > 0:
            base_score -= 0.3 * (error_types["standardization_error"] / (original_row_count * 19))
        
        if error_types.get("missing_value", 0) > 0:
            base_score -= 0.2 * (error_types["missing_value"] / (original_row_count * 19))
        
        if error_types.get("row_processing_error", 0) > 0:
            base_score -= 0.4 * (error_types["row_processing_error"] / original_row_count)
        
        return max(0.0, base_score)
    
    def _generate_standardization_report(self, issues: List[Dict], quality_score: float) -> str:
        """生成标准化报告"""
        issue_summary = Counter(issue["type"] for issue in issues)
        
        report = f"""
=== 数据标准化报告 ===
数据质量分数: {quality_score:.3f}
处理问题总数: {len(issues)}

=== 问题统计 ===
"""
        
        for issue_type, count in issue_summary.items():
            report += f"• {issue_type}: {count}个\n"
        
        if quality_score < 0.7:
            report += f"\n⚠️ 数据质量较低 (< 0.7)，建议检查原始数据\n"
        elif quality_score < 0.9:
            report += f"\n⚠️ 数据质量一般 (< 0.9)，存在部分问题\n"
        else:
            report += f"\n✅ 数据质量良好 (≥ 0.9)\n"
        
        return report.strip()
    
    def _empty_standardization_result(self) -> Dict[str, Any]:
        """空数据的标准化结果"""
        return {
            "standardized_data": [],
            "standardization_report": "输入数据为空",
            "data_quality_score": 0.0,
            "issues": []
        }


class AdaptiveTableComparator:
    """自适应表格对比器 - 主类"""
    
    def __init__(self):
        self.column_matcher = IntelligentColumnMatcher()
        self.data_standardizer = AdaptiveDataStandardizer()
        
        # 风险等级定义
        self.column_risk_levels = {
            "目标对齐": "L1",        # 绝对不能修改
            "关键KR对齐": "L1",      # 绝对不能修改  
            "重要程度": "L1",        # 绝对不能修改
            "负责人": "L2",          # 需要语义审核
            "具体计划内容": "L2",    # 需要语义审核
            "协助人": "L2",          # 需要语义审核
            "监督人": "L2",          # 需要语义审核
            "预计完成时间": "L2",    # 需要语义审核
            # 其他列默认为L3
        }
        
        self.processing_stats = {
            "tables_processed": 0,
            "total_columns_matched": 0,
            "total_processing_time": 0,
            "average_match_confidence": 0.0
        }
    
    def adaptive_compare_tables(self, current_tables: List[Dict], 
                              reference_tables: List[Dict] = None) -> Dict[str, Any]:
        """
        自适应表格对比主函数
        
        Args:
            current_tables: 当前表格列表 [{"name": "表格名", "data": [[行数据]]}, ...]
            reference_tables: 参考表格列表（可选）
            
        Returns:
            {
                "comparison_results": [...],
                "standardized_matrix": 30×19标准矩阵,
                "processing_report": "处理报告",
                "quality_summary": 质量汇总
            }
        """
        
        start_time = time.time()
        logger.info(f"开始自适应表格对比分析，输入表格数: {len(current_tables)}")
        
        comparison_results = []
        standardized_matrix = []
        total_match_confidence = 0.0
        processed_count = 0
        
        # 处理每个表格
        for table_index, table_info in enumerate(current_tables):
            try:
                table_name = table_info.get("name", f"表格_{table_index + 1}")
                table_data = table_info.get("data", [])
                
                logger.info(f"处理表格 {table_index + 1}/{len(current_tables)}: {table_name}")
                
                # 步骤1: 智能列匹配
                if not table_data:
                    logger.warning(f"表格 {table_name} 数据为空，跳过处理")
                    continue
                
                actual_columns = table_data[0] if table_data else []
                matching_result = self.column_matcher.match_columns(
                    actual_columns, table_name, confidence_threshold=0.6
                )
                
                # 步骤2: 数据标准化
                standardization_result = self.data_standardizer.standardize_table_data(
                    table_data, matching_result["mapping"], {"table_name": table_name}
                )
                
                # 步骤3: 变更检测（如果有参考数据）
                change_detection_result = None
                if reference_tables and table_index < len(reference_tables):
                    reference_data = reference_tables[table_index].get("data", [])
                    change_detection_result = self._detect_changes(
                        standardization_result["standardized_data"],
                        reference_data,
                        matching_result["mapping"]
                    )
                
                # 合并结果
                table_result = {
                    "table_id": f"table_{table_index}",
                    "table_name": table_name,
                    "matching_result": matching_result,
                    "standardization_result": standardization_result,
                    "change_detection_result": change_detection_result,
                    "processing_timestamp": datetime.now().isoformat()
                }
                
                comparison_results.append(table_result)
                
                # 构建标准化矩阵行
                matrix_row = self._build_matrix_row(standardization_result["standardized_data"])
                standardized_matrix.append(matrix_row)
                
                # 更新统计信息
                avg_confidence = np.mean(list(matching_result["confidence_scores"].values())) \
                    if matching_result["confidence_scores"] else 0.0
                total_match_confidence += avg_confidence
                processed_count += 1
                
            except Exception as e:
                logger.error(f"表格 {table_index + 1} 处理失败: {e}")
                comparison_results.append({
                    "table_id": f"table_{table_index}",
                    "table_name": table_info.get("name", f"表格_{table_index + 1}"),
                    "error": str(e),
                    "processing_timestamp": datetime.now().isoformat()
                })
        
        # 填充矩阵到30行
        while len(standardized_matrix) < 30:
            standardized_matrix.append([0] * 19)
        
        # 截取到30行（如果超过）
        standardized_matrix = standardized_matrix[:30]
        
        # 更新处理统计
        processing_time = time.time() - start_time
        self.processing_stats.update({
            "tables_processed": processed_count,
            "total_processing_time": processing_time,
            "average_match_confidence": total_match_confidence / processed_count if processed_count > 0 else 0.0
        })
        
        # 生成处理报告
        processing_report = self._generate_processing_report(comparison_results, processing_time)
        
        # 质量汇总
        quality_summary = self._generate_quality_summary(comparison_results)
        
        logger.info(f"自适应表格对比完成，处理时间: {processing_time:.2f}秒")
        
        return {
            "comparison_results": comparison_results,
            "standardized_matrix": standardized_matrix,
            "processing_report": processing_report,
            "quality_summary": quality_summary,
            "processing_stats": self.processing_stats
        }
    
    def _detect_changes(self, current_data: List[Dict], reference_data: List[List], 
                       column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """检测数据变更"""
        if not reference_data or len(reference_data) < 2:
            return {"changes": [], "summary": "无参考数据"}
        
        changes = []
        reference_headers = reference_data[0]
        reference_rows = reference_data[1:]
        
        # 简化的变更检测逻辑
        for row_index, current_row in enumerate(current_data[:len(reference_rows)]):
            if row_index < len(reference_rows):
                reference_row = reference_rows[row_index]
                
                for standard_col, current_value in current_row.items():
                    # 找到对应的参考列
                    reference_value = None
                    for actual_col, mapped_standard in column_mapping.items():
                        if mapped_standard == standard_col and actual_col in reference_headers:
                            ref_col_index = reference_headers.index(actual_col)
                            if ref_col_index < len(reference_row):
                                reference_value = reference_row[ref_col_index]
                            break
                    
                    if reference_value is not None and str(current_value) != str(reference_value):
                        risk_level = self.column_risk_levels.get(standard_col, "L3")
                        changes.append({
                            "row_index": row_index,
                            "column_name": standard_col,
                            "original_value": reference_value,
                            "new_value": current_value,
                            "risk_level": risk_level,
                            "change_type": "modification"
                        })
        
        return {
            "changes": changes,
            "summary": f"检测到 {len(changes)} 个变更",
            "risk_distribution": self._categorize_changes_by_risk(changes)
        }
    
    def _categorize_changes_by_risk(self, changes: List[Dict]) -> Dict[str, int]:
        """按风险等级分类变更"""
        risk_distribution = {"L1": 0, "L2": 0, "L3": 0}
        
        for change in changes:
            risk_level = change.get("risk_level", "L3")
            risk_distribution[risk_level] += 1
        
        return risk_distribution
    
    def _build_matrix_row(self, standardized_data: List[Dict]) -> List[float]:
        """构建标准化矩阵行（19列）"""
        if not standardized_data:
            return [0.0] * 19
        
        # 简化的矩阵构建逻辑
        # 这里可以根据实际需求调整数值计算方式
        row_values = []
        
        for standard_col in self.column_matcher.standard_columns[:19]:
            # 计算该列的"活跃度"或"风险值"
            column_value = 0.0
            
            for row_data in standardized_data:
                if standard_col in row_data and row_data[standard_col]:
                    # 根据数据类型计算相应的数值
                    if isinstance(row_data[standard_col], str) and row_data[standard_col].strip():
                        column_value += 0.1  # 有内容就增加活跃度
                    elif isinstance(row_data[standard_col], (int, float)) and row_data[standard_col] > 0:
                        column_value += 0.2
            
            # 根据风险等级调整权重
            risk_level = self.column_risk_levels.get(standard_col, "L3")
            if risk_level == "L1":
                column_value *= 1.5  # L1高风险列权重更高
            elif risk_level == "L2":
                column_value *= 1.2  # L2中风险列权重适中
            
            row_values.append(min(1.0, column_value))  # 限制在0-1范围内
        
        return row_values
    
    def _generate_processing_report(self, comparison_results: List[Dict], processing_time: float) -> str:
        """生成处理报告"""
        successful_count = sum(1 for result in comparison_results if "error" not in result)
        failed_count = len(comparison_results) - successful_count
        
        report = f"""
=== 自适应表格对比处理报告 ===
处理时间: {processing_time:.2f}秒
总表格数: {len(comparison_results)}
成功处理: {successful_count}
失败处理: {failed_count}
平均匹配置信度: {self.processing_stats.get('average_match_confidence', 0):.3f}

=== 处理详情 ===
"""
        
        for i, result in enumerate(comparison_results[:5]):  # 只显示前5个
            if "error" not in result:
                matching_result = result.get("matching_result", {})
                match_rate = len(matching_result.get("mapping", {})) / len(matching_result.get("mapping", {})) if matching_result.get("mapping") else 0
                report += f"• {result['table_name']}: 匹配成功 {len(matching_result.get('mapping', {}))} 列 ({match_rate:.1%})\n"
            else:
                report += f"• {result['table_name']}: 处理失败 - {result['error']}\n"
        
        if len(comparison_results) > 5:
            report += f"... 还有 {len(comparison_results) - 5} 个表格\n"
        
        return report.strip()
    
    def _generate_quality_summary(self, comparison_results: List[Dict]) -> Dict[str, Any]:
        """生成质量汇总"""
        quality_scores = []
        total_changes = 0
        risk_distribution = {"L1": 0, "L2": 0, "L3": 0}
        
        for result in comparison_results:
            if "error" not in result:
                # 标准化质量分数
                std_result = result.get("standardization_result", {})
                if "data_quality_score" in std_result:
                    quality_scores.append(std_result["data_quality_score"])
                
                # 变更统计
                change_result = result.get("change_detection_result", {})
                if change_result and "changes" in change_result:
                    total_changes += len(change_result["changes"])
                    
                    # 风险分布
                    risk_dist = change_result.get("risk_distribution", {})
                    for risk_level, count in risk_dist.items():
                        risk_distribution[risk_level] += count
        
        return {
            "average_quality_score": np.mean(quality_scores) if quality_scores else 0.0,
            "quality_scores_distribution": {
                "excellent": sum(1 for s in quality_scores if s >= 0.9),
                "good": sum(1 for s in quality_scores if 0.7 <= s < 0.9),
                "poor": sum(1 for s in quality_scores if s < 0.7)
            },
            "total_changes_detected": total_changes,
            "risk_distribution": risk_distribution,
            "processing_success_rate": sum(1 for r in comparison_results if "error" not in r) / len(comparison_results) if comparison_results else 0.0
        }


# 使用示例和测试
if __name__ == "__main__":
    # 创建自适应表格对比器
    comparator = AdaptiveTableComparator()
    
    # 模拟测试数据
    test_tables = [
        {
            "name": "小红书部门-工作表1",
            "data": [
                ["序号", "项目分类", "数据来源", "发起时间", "目标对齐", "KR对齐", "计划内容", "邓总指导", "责任人", "协助", "监督", "重要性", "截止时间", "进度", "清单", "复盘", "汇报", "应用", "总结"],
                [1, "内容优化", "运营部", "2025-01-10", "品牌提升", "用户增长20%", "优化内容策略", "已指导", "张三", "李四", "王五", "高", "2025-01-31", "30%", "已制定", "待安排", "已汇报", "执行中", "进展顺利"]
            ]
        },
        {
            "name": "小红书部门-工作表2",
            "data": [
                ["编号", "类型", "source", "start_date", "目标", "关键结果", "详细计划", "指导记录", "owner", "assistant", "supervisor", "priority", "end_date", "完成率", "checklist", "review", "report_status", "usage", "analysis"],
                [2, "用户运营", "产品部", "2025-01-12", "用户活跃", "DAU提升15%", "用户激活策略", "需指导", "赵六", "钱七", "孙八", "中", "2025-02-15", "20%", "制定中", "未安排", "待汇报", "准备中", "需关注"]
            ]
        }
    ]
    
    # 执行自适应对比
    result = comparator.adaptive_compare_tables(test_tables)
    
    # 输出结果
    print("=== 自适应表格对比结果 ===")
    print(f"处理报告:\n{result['processing_report']}")
    print(f"\n质量汇总: {result['quality_summary']}")
    print(f"\n标准化矩阵形状: {len(result['standardized_matrix'])} × {len(result['standardized_matrix'][0]) if result['standardized_matrix'] else 0}")
    
    # 详细结果（仅显示第一个表格的结果）
    if result['comparison_results']:
        first_result = result['comparison_results'][0]
        if 'matching_result' in first_result:
            print(f"\n第一个表格匹配报告:\n{first_result['matching_result']['matching_report']}")