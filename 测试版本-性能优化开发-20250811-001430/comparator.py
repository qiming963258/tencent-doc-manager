#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档差异对比器 - 实现同一表格两次状态的差异性检测
支持细粒度的单元格级别对比和JSON格式输出
"""

import json
import csv
import hashlib
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
from difflib import SequenceMatcher


@dataclass
class CellChange:
    """单元格变化"""
    type: str  # "modified" | "added" | "deleted"
    position: Dict[str, int]  # {"row": int, "col": int}
    previous_value: Optional[str] = None
    current_value: Optional[str] = None
    value_type: str = "string"  # "string" | "number" | "boolean" | "empty"


@dataclass
class RowChange:
    """行变化"""
    type: str  # "added" | "deleted" | "modified"
    row_index: int
    data: Optional[List[str]] = None
    previous_data: Optional[List[str]] = None


@dataclass
class DocumentVersionInfo:
    """文档版本信息"""
    timestamp: float
    data_hash: str
    row_count: int
    col_count: int
    file_path: str


@dataclass
class ComparisonSummary:
    """对比摘要"""
    total_changes: int
    added_rows: int
    deleted_rows: int
    modified_cells: int
    structure_changed: bool
    similarity_score: float


@dataclass
class DocumentComparison:
    """文档对比结果"""
    comparison_id: str
    doc_info: Dict[str, str]
    versions: Dict[str, DocumentVersionInfo]
    changes: Dict[str, Any]
    metadata: Dict[str, Any]


class DocumentComparator:
    """文档差异对比器"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
    
    async def compare_documents(self, previous_file: str, current_file: str, 
                              doc_id: str = None, tab_id: str = None) -> DocumentComparison:
        """对比两个文档版本"""
        try:
            # 读取文档数据
            previous_data, previous_info = await self._load_document(previous_file)
            current_data, current_info = await self._load_document(current_file)
            
            # 生成对比ID
            comparison_id = f"{doc_id or 'unknown'}_{tab_id or 'default'}_{int(previous_info.timestamp)}_vs_{int(current_info.timestamp)}"
            
            # 执行对比
            changes = await self._compare_data(previous_data, current_data)
            
            # 计算相似度
            similarity_score = self._calculate_similarity(previous_data, current_data)
            
            # 创建对比结果
            comparison = DocumentComparison(
                comparison_id=comparison_id,
                doc_info={
                    "doc_id": doc_id or "unknown",
                    "tab_id": tab_id or "default", 
                    "title": f"文档对比_{comparison_id}"
                },
                versions={
                    "previous": previous_info,
                    "current": current_info
                },
                changes=changes,
                metadata={
                    "comparison_time": time.time(),
                    "algorithm": "deep_cell_comparison",
                    "threshold": self.similarity_threshold,
                    "similarity_score": similarity_score
                }
            )
            
            self.logger.info(f"文档对比完成: {comparison_id}, 相似度: {similarity_score:.2f}")
            return comparison
            
        except Exception as e:
            self.logger.error(f"文档对比失败: {e}")
            raise
    
    async def _load_document(self, file_path: str) -> Tuple[List[List[str]], DocumentVersionInfo]:
        """加载文档数据"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取CSV数据
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                csv_reader = csv.reader(f)
                data = [row for row in csv_reader]
        except Exception as e:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk', newline='') as f:
                    csv_reader = csv.reader(f)
                    data = [row for row in csv_reader]
            except:
                raise Exception(f"无法读取CSV文件: {e}")
        
        # 计算文件哈希
        with open(file_path, 'rb') as f:
            file_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
        
        # 获取文件时间戳
        timestamp = file_path.stat().st_mtime
        
        # 创建版本信息
        version_info = DocumentVersionInfo(
            timestamp=timestamp,
            data_hash=file_hash,
            row_count=len(data),
            col_count=len(data[0]) if data else 0,
            file_path=str(file_path)
        )
        
        return data, version_info
    
    async def _compare_data(self, previous_data: List[List[str]], 
                          current_data: List[List[str]]) -> Dict[str, Any]:
        """对比数据内容"""
        # 初始化变化跟踪
        cell_changes = []
        row_changes = []
        
        # 检查结构变化
        previous_rows = len(previous_data)
        current_rows = len(current_data)
        previous_cols = len(previous_data[0]) if previous_data else 0
        current_cols = len(current_data[0]) if current_data else 0
        
        structure_changed = (previous_rows != current_rows) or (previous_cols != current_cols)
        
        # 对齐数据进行对比
        max_rows = max(previous_rows, current_rows)
        max_cols = max(previous_cols, current_cols)
        
        # 逐行对比
        for row_idx in range(max_rows):
            previous_row = previous_data[row_idx] if row_idx < previous_rows else None
            current_row = current_data[row_idx] if row_idx < current_rows else None
            
            if previous_row is None and current_row is not None:
                # 新增行
                row_changes.append(RowChange(
                    type="added",
                    row_index=row_idx,
                    data=current_row
                ))
            elif previous_row is not None and current_row is None:
                # 删除行
                row_changes.append(RowChange(
                    type="deleted", 
                    row_index=row_idx,
                    previous_data=previous_row
                ))
            elif previous_row is not None and current_row is not None:
                # 对比行内容
                row_cell_changes = await self._compare_row(
                    previous_row, current_row, row_idx, max_cols
                )
                cell_changes.extend(row_cell_changes)
                
                # 如果整行都变了，标记为行修改
                if len(row_cell_changes) == len(current_row):
                    row_changes.append(RowChange(
                        type="modified",
                        row_index=row_idx,
                        data=current_row,
                        previous_data=previous_row
                    ))
        
        # 创建变化摘要
        summary = ComparisonSummary(
            total_changes=len(cell_changes) + len(row_changes),
            added_rows=sum(1 for r in row_changes if r.type == "added"),
            deleted_rows=sum(1 for r in row_changes if r.type == "deleted"),
            modified_cells=len(cell_changes),
            structure_changed=structure_changed,
            similarity_score=self._calculate_similarity(previous_data, current_data)
        )
        
        return {
            "summary": asdict(summary),
            "details": {
                "row_changes": [asdict(change) for change in row_changes],
                "cell_changes": [asdict(change) for change in cell_changes]
            }
        }
    
    async def _compare_row(self, previous_row: List[str], current_row: List[str], 
                         row_idx: int, max_cols: int) -> List[CellChange]:
        """对比单行数据"""
        cell_changes = []
        
        for col_idx in range(max_cols):
            previous_cell = previous_row[col_idx] if col_idx < len(previous_row) else ""
            current_cell = current_row[col_idx] if col_idx < len(current_row) else ""
            
            # 标准化值（去除首尾空白）
            previous_cell = previous_cell.strip()
            current_cell = current_cell.strip()
            
            if previous_cell != current_cell:
                # 检测值类型
                current_type = self._detect_value_type(current_cell)
                
                cell_change = CellChange(
                    type="modified",
                    position={"row": row_idx, "col": col_idx},
                    previous_value=previous_cell,
                    current_value=current_cell,
                    value_type=current_type
                )
                cell_changes.append(cell_change)
        
        return cell_changes
    
    def _detect_value_type(self, value: str) -> str:
        """检测值类型"""
        if not value or value == "":
            return "empty"
        
        # 尝试转换为数字
        try:
            float(value)
            return "number"
        except:
            pass
        
        # 检查布尔值
        if value.lower() in ["true", "false", "是", "否", "真", "假"]:
            return "boolean"
        
        return "string"
    
    def _calculate_similarity(self, data1: List[List[str]], data2: List[List[str]]) -> float:
        """计算两个文档的相似度"""
        if not data1 and not data2:
            return 1.0
        
        if not data1 or not data2:
            return 0.0
        
        # 将数据展平为字符串
        text1 = "\n".join([",".join(row) for row in data1])
        text2 = "\n".join([",".join(row) for row in data2])
        
        # 使用序列匹配器计算相似度
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    async def compare_multiple_versions(self, file_paths: List[str], 
                                      doc_id: str = None) -> List[DocumentComparison]:
        """对比多个版本"""
        if len(file_paths) < 2:
            raise ValueError("至少需要两个文件进行对比")
        
        comparisons = []
        
        # 按时间排序文件
        sorted_files = sorted(file_paths, key=lambda f: Path(f).stat().st_mtime)
        
        # 两两对比
        for i in range(len(sorted_files) - 1):
            comparison = await self.compare_documents(
                sorted_files[i], sorted_files[i + 1], doc_id
            )
            comparisons.append(comparison)
        
        return comparisons
    
    async def export_comparison_to_file(self, comparison: DocumentComparison, 
                                      output_path: str):
        """导出对比结果到文件"""
        try:
            # 转换为可序列化格式
            comparison_dict = asdict(comparison)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comparison_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"对比结果已导出到: {output_path}")
            
        except Exception as e:
            self.logger.error(f"导出对比结果失败: {e}")
            raise
    
    def get_change_statistics(self, comparison: DocumentComparison) -> Dict[str, Any]:
        """获取变化统计信息"""
        summary = comparison.changes["summary"]
        details = comparison.changes["details"]
        
        # 按变化类型分组
        cell_changes_by_type = {}
        for change in details["cell_changes"]:
            change_type = change["value_type"]
            if change_type not in cell_changes_by_type:
                cell_changes_by_type[change_type] = 0
            cell_changes_by_type[change_type] += 1
        
        # 按行变化类型分组
        row_changes_by_type = {}
        for change in details["row_changes"]:
            change_type = change["type"]
            if change_type not in row_changes_by_type:
                row_changes_by_type[change_type] = 0
            row_changes_by_type[change_type] += 1
        
        return {
            "overview": summary,
            "cell_changes_by_type": cell_changes_by_type,
            "row_changes_by_type": row_changes_by_type,
            "change_density": {
                "cells_changed_percent": (summary["modified_cells"] / 
                    (comparison.versions["current"].row_count * comparison.versions["current"].col_count) * 100
                    if comparison.versions["current"].row_count > 0 and comparison.versions["current"].col_count > 0 else 0),
                "rows_changed_percent": ((summary["added_rows"] + summary["deleted_rows"]) /
                    max(comparison.versions["previous"].row_count, comparison.versions["current"].row_count) * 100
                    if max(comparison.versions["previous"].row_count, comparison.versions["current"].row_count) > 0 else 0)
            }
        }


class BatchComparator:
    """批量对比器"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.comparator = DocumentComparator()
        self.logger = logging.getLogger(__name__)
    
    async def compare_collection_batch(self, previous_collection: Dict[str, str],
                                     current_collection: Dict[str, str]) -> Dict[str, DocumentComparison]:
        """批量对比两个采集结果"""
        comparisons = {}
        
        # 创建对比任务
        tasks = []
        for url in current_collection:
            if url in previous_collection:
                task = self._compare_single_document(
                    url, previous_collection[url], current_collection[url]
                )
                tasks.append((url, task))
        
        # 控制并发执行
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def execute_comparison(url, task):
            async with semaphore:
                try:
                    return await task
                except Exception as e:
                    self.logger.error(f"对比文档失败 {url}: {e}")
                    return None
        
        # 执行所有对比任务
        results = await asyncio.gather(*[
            execute_comparison(url, task) for url, task in tasks
        ])
        
        # 收集结果
        for (url, _), result in zip(tasks, results):
            if result:
                comparisons[url] = result
        
        self.logger.info(f"批量对比完成，成功: {len(comparisons)}, 总计: {len(tasks)}")
        return comparisons
    
    async def _compare_single_document(self, url: str, previous_file: str, 
                                     current_file: str) -> DocumentComparison:
        """对比单个文档"""
        # 从URL提取文档信息
        doc_id = self._extract_doc_id(url)
        tab_id = self._extract_tab_id(url)
        
        return await self.comparator.compare_documents(
            previous_file, current_file, doc_id, tab_id
        )
    
    def _extract_doc_id(self, url: str) -> str:
        """从URL提取文档ID"""
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) >= 2 and path_parts[0] == 'sheet':
                return path_parts[1]
            
            return "unknown"
        except:
            return "unknown"
    
    def _extract_tab_id(self, url: str) -> str:
        """从URL提取标签页ID"""
        try:
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'tab' in query_params:
                return query_params['tab'][0]
            
            return "default"
        except:
            return "default"


async def main():
    """测试对比器"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建测试数据
    test_data_dir = Path("./test_comparisons")
    test_data_dir.mkdir(exist_ok=True)
    
    # 创建两个测试CSV文件
    previous_data = [
        ["姓名", "年龄", "城市", "薪资"],
        ["张三", "25", "北京", "10000"],
        ["李四", "30", "上海", "15000"],
        ["王五", "28", "广州", "12000"]
    ]
    
    current_data = [
        ["姓名", "年龄", "城市", "薪资"],
        ["张三", "26", "北京", "11000"],  # 年龄和薪资修改
        ["李四", "30", "上海", "15000"],   # 无变化
        ["王五", "28", "深圳", "13000"],   # 城市和薪资修改
        ["赵六", "32", "杭州", "16000"]    # 新增行
    ]
    
    # 写入测试文件
    previous_file = test_data_dir / "previous.csv"
    current_file = test_data_dir / "current.csv"
    
    with open(previous_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(previous_data)
    
    with open(current_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(current_data)
    
    try:
        comparator = DocumentComparator()
        
        print("开始文档对比测试...")
        
        # 执行对比
        comparison = await comparator.compare_documents(
            str(previous_file), str(current_file),
            doc_id="test_doc", tab_id="test_tab"
        )
        
        # 显示结果
        print(f"\n对比ID: {comparison.comparison_id}")
        print(f"相似度: {comparison.metadata['similarity_score']:.2f}")
        
        summary = comparison.changes["summary"]
        print(f"\n变化摘要:")
        print(f"  总变化数: {summary['total_changes']}")
        print(f"  新增行: {summary['added_rows']}")
        print(f"  删除行: {summary['deleted_rows']}")
        print(f"  修改单元格: {summary['modified_cells']}")
        print(f"  结构变化: {summary['structure_changed']}")
        
        # 导出结果
        output_file = test_data_dir / "comparison_result.json"
        await comparator.export_comparison_to_file(comparison, str(output_file))
        
        # 获取统计信息
        stats = comparator.get_change_statistics(comparison)
        print(f"\n统计信息:")
        print(f"  单元格变化密度: {stats['change_density']['cells_changed_percent']:.1f}%")
        print(f"  行变化密度: {stats['change_density']['rows_changed_percent']:.1f}%")
        
        print(f"\n测试完成，结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())