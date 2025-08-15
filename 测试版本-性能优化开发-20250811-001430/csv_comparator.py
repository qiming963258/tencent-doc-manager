#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV对比分析器 - 智能表格变更检测和分析
集成到腾讯文档版本管理系统中
"""

import csv
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import json
from datetime import datetime
import difflib


class CSVComparator:
    """CSV文件智能对比分析器"""
    
    def __init__(self, precision_threshold: float = 0.01):
        """
        初始化对比器
        
        Args:
            precision_threshold: 数值比较精度阈值
        """
        self.precision_threshold = precision_threshold
        self.comparison_result = {}
    
    def load_csv_safe(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        安全加载CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            DataFrame或None
        """
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"成功加载 {Path(file_path).name}，使用编码: {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            # 如果都失败，尝试忽略错误
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            print(f"加载 {Path(file_path).name}，忽略编码错误")
            return df
            
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return None
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame
        
        Args:
            df: 原始DataFrame
            
        Returns:
            标准化后的DataFrame
        """
        # 去除完全空白的行和列
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # 填充NaN值
        df = df.fillna('')
        
        # 标准化列名
        df.columns = [str(col).strip() for col in df.columns]
        
        # 转换数据类型
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def analyze_structure_changes(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict:
        """
        分析结构变化
        
        Args:
            df1: 旧版本DataFrame
            df2: 新版本DataFrame
            
        Returns:
            结构变化分析结果
        """
        analysis = {
            "row_changes": {
                "old_count": len(df1),
                "new_count": len(df2),
                "added": len(df2) - len(df1),
                "change_percentage": ((len(df2) - len(df1)) / len(df1) * 100) if len(df1) > 0 else 0
            },
            "column_changes": {
                "old_columns": list(df1.columns),
                "new_columns": list(df2.columns),
                "added_columns": list(set(df2.columns) - set(df1.columns)),
                "removed_columns": list(set(df1.columns) - set(df2.columns)),
                "common_columns": list(set(df1.columns) & set(df2.columns))
            }
        }
        
        return analysis
    
    def compare_cell_values(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict:
        """
        逐单元格对比分析
        
        Args:
            df1: 旧版本DataFrame
            df2: 新版本DataFrame
            
        Returns:
            单元格变化详情
        """
        changes = {
            "modified_cells": [],
            "statistics": {
                "total_cells_compared": 0,
                "changed_cells": 0,
                "unchanged_cells": 0,
                "change_rate": 0.0
            }
        }
        
        # 找到共同的列和行范围
        common_columns = list(set(df1.columns) & set(df2.columns))
        min_rows = min(len(df1), len(df2))
        
        total_cells = 0
        changed_cells = 0
        
        for i in range(min_rows):
            for col in common_columns:
                total_cells += 1
                
                old_value = str(df1.iloc[i][col])
                new_value = str(df2.iloc[i][col])
                
                # 数值比较
                if self._is_numeric(old_value) and self._is_numeric(new_value):
                    old_num = float(old_value)
                    new_num = float(new_value)
                    if abs(old_num - new_num) > self.precision_threshold:
                        changes["modified_cells"].append({
                            "position": f"行{i+1},列{col}",
                            "old_value": old_value,
                            "new_value": new_value,
                            "change_type": "数值变更",
                            "change_amount": new_num - old_num
                        })
                        changed_cells += 1
                else:
                    # 文本比较
                    if old_value != new_value:
                        changes["modified_cells"].append({
                            "position": f"行{i+1},列{col}",
                            "old_value": old_value,
                            "new_value": new_value,
                            "change_type": "文本变更",
                            "similarity": self._calculate_similarity(old_value, new_value)
                        })
                        changed_cells += 1
        
        changes["statistics"]["total_cells_compared"] = total_cells
        changes["statistics"]["changed_cells"] = changed_cells
        changes["statistics"]["unchanged_cells"] = total_cells - changed_cells
        changes["statistics"]["change_rate"] = (changed_cells / total_cells * 100) if total_cells > 0 else 0
        
        return changes
    
    def _is_numeric(self, value: str) -> bool:
        """检查值是否为数值"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        return difflib.SequenceMatcher(None, str1, str2).ratio()
    
    def analyze_data_quality(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict:
        """
        数据质量分析
        
        Args:
            df1: 旧版本DataFrame
            df2: 新版本DataFrame
            
        Returns:
            数据质量分析结果
        """
        quality_analysis = {
            "completeness": {
                "old_empty_cells": int(df1.isnull().sum().sum()),
                "new_empty_cells": int(df2.isnull().sum().sum()),
                "empty_cells_change": int(df2.isnull().sum().sum() - df1.isnull().sum().sum())
            },
            "consistency": {
                "old_duplicates": int(df1.duplicated().sum()),
                "new_duplicates": int(df2.duplicated().sum()),
                "duplicate_change": int(df2.duplicated().sum() - df1.duplicated().sum())
            }
        }
        
        return quality_analysis
    
    def generate_change_summary(self, comparison_result: Dict) -> Dict:
        """
        生成变更摘要
        
        Args:
            comparison_result: 完整对比结果
            
        Returns:
            变更摘要
        """
        structure = comparison_result["structure_analysis"]
        cells = comparison_result["cell_analysis"]
        quality = comparison_result["data_quality"]
        
        # 确定变更级别
        change_level = "无变化"
        if structure["row_changes"]["added"] != 0 or structure["column_changes"]["added_columns"] or structure["column_changes"]["removed_columns"]:
            change_level = "结构变更"
        elif cells["statistics"]["change_rate"] > 10:
            change_level = "重大变更"
        elif cells["statistics"]["change_rate"] > 1:
            change_level = "中等变更"
        elif cells["statistics"]["changed_cells"] > 0:
            change_level = "轻微变更"
        
        summary = {
            "change_level": change_level,
            "key_changes": [],
            "recommendations": []
        }
        
        # 关键变更
        if structure["row_changes"]["added"] > 0:
            summary["key_changes"].append(f"新增 {structure['row_changes']['added']} 行数据")
        if structure["row_changes"]["added"] < 0:
            summary["key_changes"].append(f"删除 {abs(structure['row_changes']['added'])} 行数据")
        if structure["column_changes"]["added_columns"]:
            summary["key_changes"].append(f"新增列: {', '.join(structure['column_changes']['added_columns'])}")
        if structure["column_changes"]["removed_columns"]:
            summary["key_changes"].append(f"删除列: {', '.join(structure['column_changes']['removed_columns'])}")
        if cells["statistics"]["changed_cells"] > 0:
            summary["key_changes"].append(f"修改 {cells['statistics']['changed_cells']} 个单元格")
        
        # 建议
        if cells["statistics"]["change_rate"] > 20:
            summary["recommendations"].append("变更率较高，建议仔细检查数据准确性")
        if quality["completeness"]["empty_cells_change"] > 0:
            summary["recommendations"].append("空白单元格增加，注意数据完整性")
        if quality["consistency"]["duplicate_change"] > 0:
            summary["recommendations"].append("重复数据增加，建议数据清理")
        
        return summary
    
    def compare_files(self, old_file: str, new_file: str) -> Dict:
        """
        完整的文件对比分析
        
        Args:
            old_file: 旧文件路径
            new_file: 新文件路径
            
        Returns:
            完整的对比分析结果
        """
        print(f"开始对比分析...")
        print(f"旧版本: {Path(old_file).name}")
        print(f"新版本: {Path(new_file).name}")
        
        # 加载文件
        df1 = self.load_csv_safe(old_file)
        df2 = self.load_csv_safe(new_file)
        
        if df1 is None or df2 is None:
            return {
                "success": False,
                "error": "无法加载文件",
                "timestamp": datetime.now().isoformat()
            }
        
        # 标准化数据
        df1 = self.normalize_dataframe(df1)
        df2 = self.normalize_dataframe(df2)
        
        # 执行各项分析
        result = {
            "success": True,
            "file_info": {
                "old_file": str(Path(old_file).name),
                "new_file": str(Path(new_file).name),
                "old_size": Path(old_file).stat().st_size,
                "new_size": Path(new_file).stat().st_size
            },
            "structure_analysis": self.analyze_structure_changes(df1, df2),
            "cell_analysis": self.compare_cell_values(df1, df2),
            "data_quality": self.analyze_data_quality(df1, df2),
            "timestamp": datetime.now().isoformat()
        }
        
        # 生成摘要
        result["summary"] = self.generate_change_summary(result)
        
        self.comparison_result = result
        return result
    
    def save_comparison_report(self, output_file: str) -> bool:
        """
        保存对比报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            是否保存成功
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.comparison_result, f, ensure_ascii=False, indent=2)
            
            print(f"对比报告已保存: {output_file}")
            return True
            
        except Exception as e:
            print(f"保存对比报告失败: {e}")
            return False
    
    def print_summary_report(self):
        """打印摘要报告"""
        if not self.comparison_result:
            print("没有对比结果可显示")
            return
        
        result = self.comparison_result
        summary = result["summary"]
        
        print("\n" + "="*60)
        print("📊 CSV文件对比分析报告")
        print("="*60)
        
        print(f"\n📁 文件信息:")
        print(f"  旧版本: {result['file_info']['old_file']} ({result['file_info']['old_size']} 字节)")
        print(f"  新版本: {result['file_info']['new_file']} ({result['file_info']['new_size']} 字节)")
        
        print(f"\n🎯 变更级别: {summary['change_level']}")
        
        print(f"\n📈 结构变化:")
        structure = result['structure_analysis']
        print(f"  行数变化: {structure['row_changes']['old_count']} → {structure['row_changes']['new_count']} ({structure['row_changes']['added']:+d})")
        if structure['column_changes']['added_columns']:
            print(f"  新增列: {', '.join(structure['column_changes']['added_columns'])}")
        if structure['column_changes']['removed_columns']:
            print(f"  删除列: {', '.join(structure['column_changes']['removed_columns'])}")
        
        print(f"\n🔄 单元格变化:")
        cells = result['cell_analysis']
        print(f"  总对比单元格: {cells['statistics']['total_cells_compared']}")
        print(f"  变更单元格: {cells['statistics']['changed_cells']}")
        print(f"  变更率: {cells['statistics']['change_rate']:.2f}%")
        
        print(f"\n📋 关键变更:")
        for change in summary['key_changes']:
            print(f"  • {change}")
        
        if summary['recommendations']:
            print(f"\n💡 建议:")
            for rec in summary['recommendations']:
                print(f"  • {rec}")
        
        print(f"\n📅 分析时间: {result['timestamp']}")
        print("="*60)


def main():
    """命令行工具入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSV对比分析工具')
    parser.add_argument('old_file', help='旧版本文件路径')
    parser.add_argument('new_file', help='新版本文件路径')
    parser.add_argument('-o', '--output', help='输出报告文件路径')
    parser.add_argument('--precision', type=float, default=0.01, help='数值比较精度阈值')
    
    args = parser.parse_args()
    
    # 执行对比分析
    comparator = CSVComparator(precision_threshold=args.precision)
    result = comparator.compare_files(args.old_file, args.new_file)
    
    if result["success"]:
        # 打印摘要报告
        comparator.print_summary_report()
        
        # 保存详细报告
        if args.output:
            comparator.save_comparison_report(args.output)
    else:
        print(f"❌ 对比分析失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()