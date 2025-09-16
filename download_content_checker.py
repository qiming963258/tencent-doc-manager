#!/usr/bin/env python3
"""
下载内容检查器
用于验证下载的文档是否为真实内容，并提供详细分析
"""

import os
import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import hashlib
import re
from collections import Counter

class DownloadContentChecker:
    """下载内容检查器 - 验证和分析下载的文档"""
    
    # 演示数据特征（用于识别假数据）
    DEMO_INDICATORS = [
        "张三", "李四", "王五", "赵六",  # 常见测试姓名
        "test", "demo", "example", "sample",  # 测试标识
        "测试", "示例", "演示",  # 中文测试标识
        "test_cookie", "demo_purposes"  # 测试Cookie
    ]
    
    # 真实文档特征
    REAL_INDICATORS = [
        "实际", "真实", "正式", "生产",
        "计划", "报表", "统计", "分析"
    ]
    
    def __init__(self):
        """初始化检查器"""
        self.check_results = []
        self.stats = {}
        
    def check_file(self, file_path: str) -> Dict[str, Any]:
        """
        检查单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            检查结果字典
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'success': False,
                'error': f'文件不存在: {file_path}',
                'file_path': str(file_path)
            }
        
        # 基础信息
        result = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_size_readable': self._format_size(file_path.stat().st_size),
            'modified_time': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'file_hash': self._calculate_hash(file_path),
            'file_type': file_path.suffix.lower()
        }
        
        # 根据文件类型进行内容检查
        if file_path.suffix.lower() == '.csv':
            result.update(self._check_csv_content(file_path))
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            result.update(self._check_excel_content(file_path))
        elif file_path.suffix.lower() == '.json':
            result.update(self._check_json_content(file_path))
        else:
            result.update(self._check_text_content(file_path))
        
        # 真实性评分
        result['authenticity_score'] = self._calculate_authenticity_score(result)
        result['is_demo_data'] = result['authenticity_score'] < 50
        
        # 生成总结
        result['summary'] = self._generate_summary(result)
        
        return result
    
    def _check_csv_content(self, file_path: Path) -> Dict[str, Any]:
        """检查CSV文件内容"""
        try:
            # 读取CSV
            df = pd.read_csv(file_path, encoding='utf-8-sig', nrows=1000)
            
            content_info = {
                'content_type': 'csv',
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'data_preview': df.head(5).to_dict('records'),
                'empty_cells': df.isna().sum().sum(),
                'duplicate_rows': df.duplicated().sum()
            }
            
            # 内容分析
            content_text = df.to_string()
            content_info.update(self._analyze_content(content_text))
            
            # 数据质量检查
            content_info['data_quality'] = {
                'completeness': (1 - content_info['empty_cells'] / (len(df) * len(df.columns))) * 100,
                'uniqueness': (1 - content_info['duplicate_rows'] / len(df)) * 100,
                'has_headers': self._check_has_headers(df)
            }
            
            # 列类型分析
            column_types = {}
            for col in df.columns:
                try:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        column_types[col] = 'numeric'
                    elif pd.api.types.is_datetime64_any_dtype(df[col]):
                        column_types[col] = 'datetime'
                    else:
                        column_types[col] = 'text'
                except:
                    column_types[col] = 'mixed'
            content_info['column_types'] = column_types
            
            return content_info
            
        except Exception as e:
            return {
                'content_type': 'csv',
                'error': f'CSV读取错误: {str(e)}'
            }
    
    def _check_excel_content(self, file_path: Path) -> Dict[str, Any]:
        """检查Excel文件内容"""
        try:
            # 读取Excel
            xl_file = pd.ExcelFile(file_path)
            
            content_info = {
                'content_type': 'excel',
                'sheet_count': len(xl_file.sheet_names),
                'sheet_names': xl_file.sheet_names,
                'sheets_info': {}
            }
            
            # 分析每个工作表
            total_text = ""
            for sheet_name in xl_file.sheet_names[:5]:  # 最多检查5个工作表
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=100)
                content_info['sheets_info'][sheet_name] = {
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': list(df.columns)[:20]  # 最多显示20列
                }
                total_text += df.to_string()
            
            # 内容分析
            content_info.update(self._analyze_content(total_text))
            
            return content_info
            
        except Exception as e:
            return {
                'content_type': 'excel',
                'error': f'Excel读取错误: {str(e)}'
            }
    
    def _check_json_content(self, file_path: Path) -> Dict[str, Any]:
        """检查JSON文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            content_info = {
                'content_type': 'json',
                'structure': self._analyze_json_structure(data),
                'key_count': len(data) if isinstance(data, dict) else None,
                'item_count': len(data) if isinstance(data, list) else None
            }
            
            # 内容分析
            content_text = json.dumps(data, ensure_ascii=False)
            content_info.update(self._analyze_content(content_text))
            
            return content_info
            
        except Exception as e:
            return {
                'content_type': 'json',
                'error': f'JSON读取错误: {str(e)}'
            }
    
    def _check_text_content(self, file_path: Path) -> Dict[str, Any]:
        """检查文本文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(10000)  # 读取前10000字符
            
            content_info = {
                'content_type': 'text',
                'character_count': len(content),
                'line_count': content.count('\n') + 1
            }
            
            # 内容分析
            content_info.update(self._analyze_content(content))
            
            return content_info
            
        except Exception as e:
            return {
                'content_type': 'text',
                'error': f'文本读取错误: {str(e)}'
            }
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """分析文本内容"""
        content_lower = content.lower()
        
        # 检查演示数据标识
        demo_count = sum(1 for indicator in self.DEMO_INDICATORS 
                        if indicator.lower() in content_lower)
        
        # 检查真实数据标识
        real_count = sum(1 for indicator in self.REAL_INDICATORS 
                        if indicator in content)
        
        # 提取数字
        numbers = re.findall(r'\d+\.?\d*', content)
        
        # 提取日期
        dates = re.findall(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', content)
        
        # 词频统计（中文）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]+', content)
        word_freq = Counter(chinese_words).most_common(10)
        
        return {
            'demo_indicators_found': demo_count,
            'real_indicators_found': real_count,
            'contains_numbers': len(numbers) > 0,
            'number_count': len(numbers),
            'contains_dates': len(dates) > 0,
            'date_count': len(dates),
            'top_words': word_freq,
            'has_chinese': len(chinese_words) > 0,
            'chinese_ratio': len(''.join(chinese_words)) / max(len(content), 1)
        }
    
    def _analyze_json_structure(self, data: Any, max_depth: int = 3, current_depth: int = 0) -> str:
        """分析JSON结构"""
        if current_depth >= max_depth:
            return "..."
        
        if isinstance(data, dict):
            if not data:
                return "{}"
            keys = list(data.keys())[:5]  # 最多显示5个键
            return "{" + ", ".join(f'"{k}": {self._analyze_json_structure(data[k], max_depth, current_depth+1)}' 
                                  for k in keys) + ("..." if len(data) > 5 else "") + "}"
        elif isinstance(data, list):
            if not data:
                return "[]"
            return f"[{self._analyze_json_structure(data[0], max_depth, current_depth+1)}...] (len={len(data)})"
        elif isinstance(data, str):
            return f'"{data[:20]}..."' if len(data) > 20 else f'"{data}"'
        else:
            return str(type(data).__name__)
    
    def _check_has_headers(self, df: pd.DataFrame) -> bool:
        """检查CSV是否有合理的表头"""
        # 检查第一行是否都是字符串
        first_row = df.iloc[0] if len(df) > 0 else []
        
        # 如果列名都是数字，可能没有表头
        if all(isinstance(col, (int, float)) for col in df.columns):
            return False
        
        # 如果列名包含Unnamed，可能没有表头
        if any('Unnamed' in str(col) for col in df.columns):
            return False
        
        return True
    
    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def _calculate_authenticity_score(self, result: Dict[str, Any]) -> float:
        """计算真实性评分（0-100）"""
        score = 50.0  # 基础分
        
        # 文件大小评分
        if result['file_size'] > 1024:  # 大于1KB
            score += 10
        if result['file_size'] > 10240:  # 大于10KB
            score += 10
        
        # 内容评分
        if 'demo_indicators_found' in result:
            score -= result['demo_indicators_found'] * 10
        if 'real_indicators_found' in result:
            score += result['real_indicators_found'] * 5
        
        # CSV/Excel特定评分
        if 'row_count' in result:
            if result['row_count'] > 10:
                score += 10
            if result['row_count'] > 100:
                score += 10
        
        if 'column_count' in result:
            if result['column_count'] > 3:
                score += 5
        
        # 数据质量评分
        if 'data_quality' in result:
            score += result['data_quality']['completeness'] * 0.2
            score += result['data_quality']['uniqueness'] * 0.1
        
        # 确保分数在0-100之间
        return max(0, min(100, score))
    
    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """生成检查总结"""
        summary_parts = []
        
        # 文件基本信息
        summary_parts.append(f"文件: {result['file_name']} ({result['file_size_readable']})")
        
        # 真实性判断
        if result['is_demo_data']:
            summary_parts.append("⚠️ 疑似演示数据")
        else:
            summary_parts.append("✅ 可能是真实数据")
        
        summary_parts.append(f"真实性评分: {result['authenticity_score']:.1f}/100")
        
        # 内容特征
        if 'row_count' in result:
            summary_parts.append(f"数据规模: {result['row_count']}行 × {result['column_count']}列")
        
        if 'demo_indicators_found' in result and result['demo_indicators_found'] > 0:
            summary_parts.append(f"发现{result['demo_indicators_found']}个演示数据标识")
        
        if 'real_indicators_found' in result and result['real_indicators_found'] > 0:
            summary_parts.append(f"发现{result['real_indicators_found']}个真实数据标识")
        
        return " | ".join(summary_parts)
    
    def check_download_batch(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        批量检查下载的文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            批量检查结果
        """
        results = []
        all_demo = True
        all_real = True
        
        for file_path in file_paths:
            result = self.check_file(file_path)
            results.append(result)
            
            if not result.get('is_demo_data', True):
                all_demo = False
            else:
                all_real = False
        
        # 汇总统计
        total_size = sum(r.get('file_size', 0) for r in results)
        avg_score = sum(r.get('authenticity_score', 0) for r in results) / max(len(results), 1)
        
        return {
            'file_count': len(results),
            'total_size': self._format_size(total_size),
            'average_authenticity_score': avg_score,
            'all_demo_data': all_demo,
            'all_real_data': all_real,
            'mixed_data': not all_demo and not all_real,
            'individual_results': results,
            'overall_assessment': self._generate_overall_assessment(results, avg_score)
        }
    
    def _generate_overall_assessment(self, results: List[Dict], avg_score: float) -> str:
        """生成整体评估"""
        if avg_score >= 80:
            return "✅ 高可信度：下载的文件很可能是真实的腾讯文档"
        elif avg_score >= 60:
            return "⚠️ 中等可信度：文件可能是真实的，但包含一些可疑特征"
        elif avg_score >= 40:
            return "⚠️ 低可信度：文件包含较多演示数据特征"
        else:
            return "❌ 极低可信度：文件很可能是演示或测试数据"


# 便捷函数
def quick_check(file_path: str) -> None:
    """快速检查单个文件并打印结果"""
    checker = DownloadContentChecker()
    result = checker.check_file(file_path)
    
    print("=" * 60)
    print("📊 下载内容检查报告")
    print("=" * 60)
    print(f"文件: {result['file_name']}")
    print(f"大小: {result['file_size_readable']}")
    print(f"类型: {result.get('content_type', 'unknown')}")
    print("-" * 60)
    
    if result['is_demo_data']:
        print("⚠️ 检测结果: 疑似演示数据")
    else:
        print("✅ 检测结果: 可能是真实数据")
    
    print(f"真实性评分: {result['authenticity_score']:.1f}/100")
    
    if 'row_count' in result:
        print(f"数据规模: {result['row_count']}行 × {result['column_count']}列")
    
    if 'demo_indicators_found' in result:
        print(f"演示标识: {result['demo_indicators_found']}个")
        
    if 'real_indicators_found' in result:
        print(f"真实标识: {result['real_indicators_found']}个")
    
    print("-" * 60)
    print("总结:", result['summary'])
    print("=" * 60)


if __name__ == "__main__":
    # 测试示例
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        quick_check(file_path)
    else:
        print("使用方法: python download_content_checker.py <文件路径>")
        print("示例: python download_content_checker.py /root/projects/tencent-doc-manager/downloads/document.csv")