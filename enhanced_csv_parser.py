# -*- coding: utf-8 -*-
"""
增强型CSV解析器
解决Excel合并单元格、多级表头、Unnamed列等问题
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedCSVParser:
    """增强型CSV解析器，专门处理复杂Excel表格"""
    
    def __init__(self):
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
        
    def parse_complex_csv(self, file_path: str) -> Dict[str, Any]:
        """
        解析复杂CSV文件，智能识别表头和数据区域
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            解析结果包含清理后的数据和元信息
        """
        try:
            # 尝试多种读取策略
            strategies = [
                self._strategy_standard_read,
                self._strategy_skip_title_rows,
                self._strategy_multi_header,
                self._strategy_smart_detection
            ]
            
            best_result = None
            best_score = -1
            
            for strategy in strategies:
                try:
                    result = strategy(file_path)
                    score = self._evaluate_parse_quality(result)
                    
                    logger.info(f"策略 {strategy.__name__} 得分: {score}")
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
                        
                except Exception as e:
                    logger.warning(f"策略 {strategy.__name__} 失败: {e}")
                    continue
            
            if best_result is None:
                raise Exception("所有解析策略都失败了")
                
            # 后处理：清理和标准化
            best_result = self._post_process_data(best_result)
            
            return {
                "success": True,
                "data": best_result["data"],
                "columns": best_result["columns"],
                "metadata": {
                    "original_file": file_path,
                    "parse_strategy": best_result["strategy"],
                    "quality_score": best_score,
                    "rows_count": len(best_result["data"]),
                    "columns_count": len(best_result["columns"])
                }
            }
            
        except Exception as e:
            logger.error(f"CSV解析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "columns": [],
                "metadata": {}
            }
    
    def _strategy_standard_read(self, file_path: str) -> Dict[str, Any]:
        """策略1：标准读取"""
        df = pd.read_csv(file_path)
        return {
            "data": df,
            "columns": df.columns.tolist(),
            "strategy": "standard_read"
        }
    
    def _strategy_skip_title_rows(self, file_path: str) -> Dict[str, Any]:
        """策略2：跳过标题行"""
        # 尝试跳过不同数量的行
        for skip_rows in [1, 2, 3]:
            try:
                df = pd.read_csv(file_path, skiprows=skip_rows)
                if self._has_valid_columns(df.columns):
                    return {
                        "data": df,
                        "columns": df.columns.tolist(),
                        "strategy": f"skip_{skip_rows}_rows"
                    }
            except:
                continue
        
        raise Exception("跳过标题行策略失败")
    
    def _strategy_multi_header(self, file_path: str) -> Dict[str, Any]:
        """策略3：多级表头处理"""
        # 读取前几行分析表头结构
        header_data = pd.read_csv(file_path, nrows=5, header=None)
        
        # 寻找最可能的表头行
        best_header_row = 0
        best_score = 0
        
        for i in range(min(3, len(header_data))):
            row_data = header_data.iloc[i].fillna("")
            score = self._score_header_row(row_data.tolist())
            if score > best_score:
                best_score = score
                best_header_row = i
        
        # 使用找到的表头行读取数据
        df = pd.read_csv(file_path, skiprows=best_header_row, nrows=1000)
        
        return {
            "data": df,
            "columns": df.columns.tolist(),
            "strategy": f"multi_header_row_{best_header_row}"
        }
    
    def _strategy_smart_detection(self, file_path: str) -> Dict[str, Any]:
        """策略4：智能检测"""
        # 读取整个文件但不设置表头
        raw_data = pd.read_csv(file_path, header=None, nrows=20)
        
        # 分析每行的特征
        header_candidates = []
        for i, row in raw_data.iterrows():
            row_data = row.fillna("").tolist()
            
            # 评估这一行作为表头的可能性
            score = self._score_potential_header(row_data)
            header_candidates.append({
                "row_index": i,
                "score": score,
                "data": row_data
            })
        
        # 选择最佳表头行
        best_header = max(header_candidates, key=lambda x: x["score"])
        
        if best_header["score"] < 0.3:
            raise Exception("无法找到合适的表头行")
        
        # 使用确定的表头重新读取
        df = pd.read_csv(file_path, skiprows=best_header["row_index"])
        
        # 手动设置列名
        if len(best_header["data"]) >= len(df.columns):
            column_names = []
            for i, col in enumerate(df.columns):
                if i < len(best_header["data"]) and best_header["data"][i].strip():
                    column_names.append(best_header["data"][i].strip())
                else:
                    column_names.append(f"列{i+1}")
            
            df.columns = column_names
        
        return {
            "data": df,
            "columns": df.columns.tolist(),
            "strategy": f"smart_detection_row_{best_header['row_index']}"
        }
    
    def _has_valid_columns(self, columns: List[str]) -> bool:
        """检查列名是否有效"""
        unnamed_count = sum(1 for col in columns if 'Unnamed' in str(col))
        return unnamed_count < len(columns) * 0.5  # 少于50%的unnamed列
    
    def _score_header_row(self, row_data: List[str]) -> float:
        """评估行作为表头的得分"""
        score = 0.0
        total_cells = len(row_data)
        
        if total_cells == 0:
            return 0.0
        
        # 非空单元格比例
        non_empty = sum(1 for cell in row_data if str(cell).strip())
        score += (non_empty / total_cells) * 0.4
        
        # 包含标准列名的比例
        standard_matches = 0
        for cell in row_data:
            cell_str = str(cell).strip()
            if any(std_col in cell_str for std_col in self.standard_columns):
                standard_matches += 1
        score += (standard_matches / total_cells) * 0.6
        
        return score
    
    def _score_potential_header(self, row_data: List[str]) -> float:
        """评估潜在表头行的质量"""
        score = 0.0
        
        # 文本特征评分
        text_cells = 0
        number_cells = 0
        
        for cell in row_data:
            cell_str = str(cell).strip()
            if not cell_str:
                continue
                
            # 检查是否包含中文或常见表头词汇
            if re.search(r'[\u4e00-\u9fff]', cell_str) or any(keyword in cell_str 
                for keyword in ['序号', '类型', '时间', '负责', '进度', '内容']):
                text_cells += 1
                score += 0.1
            
            # 检查是否为纯数字（数据行特征）
            try:
                float(cell_str)
                number_cells += 1
            except:
                pass
        
        # 表头行应该以文本为主，不是数字
        if len(row_data) > 0:
            text_ratio = text_cells / len(row_data)
            score += text_ratio * 0.5
            
            # 惩罚纯数字行
            number_ratio = number_cells / len(row_data)
            score -= number_ratio * 0.3
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_parse_quality(self, result: Dict[str, Any]) -> float:
        """评估解析质量"""
        if "data" not in result or result["data"] is None:
            return 0.0
        
        df = result["data"]
        columns = result["columns"]
        
        score = 0.0
        
        # 列名质量评分
        unnamed_count = sum(1 for col in columns if 'Unnamed' in str(col))
        if len(columns) > 0:
            score += (1 - unnamed_count / len(columns)) * 0.4
        
        # 数据完整性评分
        if len(df) > 0:
            non_empty_ratio = df.notna().sum().sum() / (len(df) * len(columns))
            score += non_empty_ratio * 0.3
        
        # 标准列匹配评分
        standard_matches = 0
        for col in columns:
            if any(std_col in str(col) for std_col in self.standard_columns):
                standard_matches += 1
        
        if len(columns) > 0:
            score += (standard_matches / len(columns)) * 0.3
        
        return score
    
    def _post_process_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理：清理和标准化数据"""
        df = result["data"]
        
        # 清理列名
        cleaned_columns = []
        for col in df.columns:
            col_str = str(col).strip()
            # 移除特殊字符，保留中英文和数字
            col_str = re.sub(r'[^\u4e00-\u9fff\w\s]', '', col_str)
            if not col_str or col_str == 'nan':
                col_str = f"列{len(cleaned_columns)+1}"
            cleaned_columns.append(col_str)
        
        df.columns = cleaned_columns
        
        # 移除完全空白的行和列
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        result["data"] = df
        result["columns"] = df.columns.tolist()
        
        return result


class ColumnIntelligentMatcher:
    """智能列名匹配器 - 增强版本"""
    
    def __init__(self):
        self.enhanced_variations = {
            "序号": ["序号", "编号", "ID", "id", "索引", "No", "NO", "num", "number"],
            "项目类型": ["项目类型", "类型", "分类", "项目分类", "category", "type"],
            "来源": ["来源", "源头", "数据来源", "source", "起源"],
            "任务发起时间": ["任务发起时间", "发起时间", "开始时间", "创建时间", "时间"],
            "目标对齐": ["目标对齐", "目标", "对齐", "目标匹配", "goal"],
            "关键KR对齐": ["关键KR对齐", "KR对齐", "KR", "关键结果", "kr"],
            "具体计划内容": ["具体计划内容", "计划内容", "内容", "计划", "详情"],
            "负责人": ["负责人", "责任人", "负责", "主负责", "owner"],
            "协助人": ["协助人", "协助", "助手", "辅助", "协作"],
            "监督人": ["监督人", "监督", "督导", "检查人", "supervisor"],
            "重要程度": ["重要程度", "重要性", "优先级", "紧急程度", "priority"],
            "预计完成时间": ["预计完成时间", "完成时间", "截止时间", "deadline"],
            "完成进度": ["完成进度", "进度", "完成度", "进展", "progress"],
            "形成计划清单": ["形成计划清单", "计划清单", "清单", "任务清单"],
            "复盘时间": ["复盘时间", "复盘", "回顾时间", "总结时间"],
            "对上汇报": ["对上汇报", "汇报", "上报", "报告"],
            "应用情况": ["应用情况", "应用", "使用情况", "执行情况"],
            "进度分析总结": ["进度分析总结", "分析总结", "总结", "分析"]
        }
    
    def intelligent_match(self, actual_columns: List[str]) -> Dict[str, Any]:
        """
        智能匹配列名，支持模糊匹配和语义理解
        
        Args:
            actual_columns: 实际的列名列表
            
        Returns:
            匹配结果
        """
        mapping = {}
        confidence_scores = {}
        unmatched = []
        
        for actual_col in actual_columns:
            best_match = None
            best_score = 0.0
            
            actual_clean = str(actual_col).strip()
            
            for standard_col, variations in self.enhanced_variations.items():
                for variation in variations:
                    # 计算相似度
                    score = self._calculate_similarity(actual_clean, variation)
                    
                    if score > best_score and score > 0.6:  # 阈值0.6
                        best_score = score
                        best_match = standard_col
            
            if best_match:
                mapping[actual_col] = best_match
                confidence_scores[actual_col] = best_score
            else:
                unmatched.append(actual_col)
        
        # 计算缺失的标准列
        mapped_standards = set(mapping.values())
        missing_standards = [col for col in self.enhanced_variations.keys() 
                           if col not in mapped_standards]
        
        return {
            "mapping": mapping,
            "confidence_scores": confidence_scores,
            "unmatched_columns": unmatched,
            "missing_columns": missing_standards,
            "match_success_rate": len(mapping) / len(actual_columns) if actual_columns else 0
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        # 1. 完全匹配
        if text1 == text2:
            return 1.0
        
        # 2. 包含关系
        if text2 in text1 or text1 in text2:
            return 0.8
        
        # 3. 编辑距离相似度
        edit_distance = self._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0.0
        
        similarity = 1 - (edit_distance / max_len)
        
        # 4. 关键词匹配
        keywords1 = set(re.findall(r'[\u4e00-\u9fff]+|\w+', text1))
        keywords2 = set(re.findall(r'[\u4e00-\u9fff]+|\w+', text2))
        
        if keywords1 and keywords2:
            keyword_similarity = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            similarity = max(similarity, keyword_similarity)
        
        return similarity
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
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