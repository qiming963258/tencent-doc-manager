#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业CSV对比算法
实现精确到单元格级别的对比，包含列码、行号、列名识别等功能
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import hashlib

class ProfessionalCSVComparator:
    """专业CSV对比器"""
    
    def __init__(self):
        self.title_row_index = None  # 标题行索引（通常是第0行）
        self.column_name_row_index = 0  # 列名行索引（默认第1行）
        
    def get_column_letter(self, col_index: int) -> str:
        """
        将列索引转换为Excel风格的列字母（A, B, C...AA, AB等）
        
        Args:
            col_index: 列索引（从0开始）
            
        Returns:
            Excel风格的列字母
        """
        result = ""
        col_num = col_index + 1  # 转换为1开始的索引
        
        while col_num > 0:
            col_num -= 1
            result = chr(65 + col_num % 26) + result
            col_num //= 26
            
        return result
    
    def get_cell_address(self, row: int, col: int) -> str:
        """
        获取单元格地址（如A1, B2, C3等）
        
        Args:
            row: 行号（从0开始）
            col: 列号（从0开始）
            
        Returns:
            Excel风格的单元格地址
        """
        return f"{self.get_column_letter(col)}{row + 1}"
    
    def detect_header_rows(self, data: List[List[str]]) -> Tuple[Optional[int], int]:
        """
        智能检测标题行和列名行
        
        Args:
            data: CSV数据
            
        Returns:
            (标题行索引, 列名行索引)
        """
        if not data:
            return None, 0
            
        # 简单策略：
        # - 如果第一行包含合并的标题性质内容（如很多空格、特殊字符），视为标题行
        # - 否则第一行就是列名行
        
        first_row = data[0] if len(data) > 0 else []
        
        # 检查第一行是否像标题（包含很多空值或重复值）
        non_empty = [cell for cell in first_row if cell.strip()]
        if len(non_empty) < len(first_row) * 0.5:  # 超过一半是空的
            return 0, 1 if len(data) > 1 else 0
        
        # 默认第一行是列名
        return None, 0
    
    def read_csv_with_structure(self, filepath: str) -> Dict[str, Any]:
        """
        读取CSV文件并识别结构
        
        Args:
            filepath: CSV文件路径
            
        Returns:
            包含数据和结构信息的字典
        """
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = list(reader)
        
        title_row_idx, column_row_idx = self.detect_header_rows(data)
        
        # 提取列名
        column_names = []
        if column_row_idx < len(data):
            column_names = data[column_row_idx]
        
        # 提取数据行（跳过标题和列名行）
        data_start_idx = column_row_idx + 1
        data_rows = data[data_start_idx:] if data_start_idx < len(data) else []
        
        return {
            'raw_data': data,
            'title_row': data[title_row_idx] if title_row_idx is not None else None,
            'column_names': column_names,
            'data_rows': data_rows,
            'data_start_row': data_start_idx,
            'column_count': len(column_names),
            'row_count': len(data_rows)
        }
    
    def compare_rows(self, row1: List[str], row2: List[str]) -> bool:
        """
        比较两行是否相同
        
        Args:
            row1: 第一行数据
            row2: 第二行数据
            
        Returns:
            是否相同
        """
        if len(row1) != len(row2):
            return False
        return all(str(cell1).strip() == str(cell2).strip() for cell1, cell2 in zip(row1, row2))
    
    def find_row_in_data(self, row: List[str], data_rows: List[List[str]], 
                        id_column: int = 0) -> Optional[int]:
        """
        在数据中查找匹配的行（基于ID列）
        
        Args:
            row: 要查找的行
            data_rows: 数据行列表
            id_column: ID列索引（默认第0列）
            
        Returns:
            匹配行的索引，如果没找到返回None
        """
        if not row or id_column >= len(row):
            return None
            
        row_id = str(row[id_column]).strip()
        
        for idx, data_row in enumerate(data_rows):
            if id_column < len(data_row) and str(data_row[id_column]).strip() == row_id:
                return idx
                
        return None
    
    def compare_cells(self, baseline_data: Dict, target_data: Dict) -> Dict[str, Any]:
        """
        执行单元格级别的详细对比
        
        Args:
            baseline_data: 基线文件数据结构
            target_data: 目标文件数据结构
            
        Returns:
            详细的对比结果
        """
        differences = []
        modified_cells = []
        added_rows = []
        deleted_rows = []
        
        baseline_rows = baseline_data['data_rows']
        target_rows = target_data['data_rows']
        column_names = baseline_data['column_names']
        data_start_row = baseline_data['data_start_row']
        
        # 处理基线中的每一行（行对比仅用于定位，不输出内容）
        for base_idx, base_row in enumerate(baseline_rows):
            actual_row_num = base_idx + data_start_row + 1  # Excel行号（从1开始）
            
            # 在目标中查找对应行（基于ID列）- 仅定位不输出
            target_idx = self.find_row_in_data(base_row, target_rows)
            
            if target_idx is None:
                # 行被删除 - 仅记录行号和ID，不记录内容
                deleted_rows.append({
                    'row_number': actual_row_num,
                    'row_id': base_row[0] if base_row else ''
                    # 不输出content，仅用于定位
                })
            else:
                # 行存在，比较每个单元格
                target_row = target_rows[target_idx]
                
                for col_idx in range(max(len(base_row), len(target_row))):
                    base_value = str(base_row[col_idx]) if col_idx < len(base_row) else ''
                    target_value = str(target_row[col_idx]) if col_idx < len(target_row) else ''
                    
                    if base_value.strip() != target_value.strip():
                        # 单元格有差异
                        cell_address = self.get_cell_address(base_idx + data_start_row, col_idx)
                        column_letter = self.get_column_letter(col_idx)
                        column_name = column_names[col_idx] if col_idx < len(column_names) else f'Column{col_idx}'
                        
                        modified_cells.append({
                            'cell': cell_address,
                            'column': column_letter,
                            'column_name': column_name,
                            'row_number': actual_row_num,
                            'baseline_value': base_value,
                            'target_value': target_value
                        })
                        
                        # 创建差异参数行
                        diff_param = f"{cell_address}_{column_name}_{base_value}|{target_value}"
                        differences.append(diff_param)
        
        # 查找新增的行（仅定位不输出内容）
        for target_idx, target_row in enumerate(target_rows):
            actual_row_num = target_idx + data_start_row + 1
            
            # 在基线中查找
            if self.find_row_in_data(target_row, baseline_rows) is None:
                added_rows.append({
                    'row_number': actual_row_num,
                    'row_id': target_row[0] if target_row else ''
                    # 不输出content，仅用于定位
                })
        
        return {
            'modified_cells': modified_cells,
            'added_rows': added_rows,
            'deleted_rows': deleted_rows,
            'differences': differences,
            'total_differences': len(differences),
            'total_added': len(added_rows),
            'total_deleted': len(deleted_rows),
            'total_modified_cells': len(modified_cells)
        }
    
    def generate_parameter_filename(self, baseline_path: str, target_path: str, 
                                  diff_count: int) -> str:
        """
        生成规范的参数文件名
        
        格式：comparison_params_{基线文件名}_{目标文件名}_{时间戳}_{差异条数}.json
        """
        baseline_name = Path(baseline_path).stem
        target_name = Path(target_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 改进的文档名称提取逻辑
        def extract_doc_name(full_name: str) -> str:
            """从文件名中提取有意义的文档名称"""
            # 格式: tencent_{文档名}_csv_{时间戳}_{版本类型}_W{周数}
            parts = full_name.split('_csv_')
            if len(parts) >= 2:
                # 获取csv前面的部分
                name_part = parts[0]
                # 去掉tencent_前缀
                if name_part.startswith('tencent_'):
                    name_part = name_part[8:]
                
                # 对于包含test_comparison的，保留完整名称
                if 'test' in name_part and 'comparison' in full_name:
                    return 'test_comparison'
                
                # 对于中文名称，截取关键部分
                if '销售计划表' in name_part:
                    if '出国' in name_part:
                        return '出国销售表'
                    elif '回国' in name_part:
                        return '回国销售表'
                    else:
                        return '销售计划表'
                
                # 如果太长，截取前20个字符
                if len(name_part) > 20:
                    return name_part[:20]
                
                return name_part
            
            # 如果解析失败，返回前20个字符
            return full_name[:20]
        
        baseline_short = extract_doc_name(baseline_name)
        target_short = extract_doc_name(target_name)
        
        return f"comparison_params_{baseline_short}_vs_{target_short}_{timestamp}_{diff_count}diffs.json"
    
    def compare(self, baseline_path: str, target_path: str, 
                output_dir: str = None) -> Dict[str, Any]:
        """
        执行完整的专业对比
        
        Args:
            baseline_path: 基线CSV文件路径
            target_path: 目标CSV文件路径
            output_dir: 输出目录（可选）
            
        Returns:
            完整的对比结果
        """
        # 读取文件结构
        baseline_data = self.read_csv_with_structure(baseline_path)
        target_data = self.read_csv_with_structure(target_path)
        
        # 执行详细对比
        comparison = self.compare_cells(baseline_data, target_data)
        
        # 计算相似度（更精确的算法）
        total_cells_baseline = baseline_data['row_count'] * baseline_data['column_count']
        total_cells_target = target_data['row_count'] * target_data['column_count']
        max_cells = max(total_cells_baseline, total_cells_target)
        
        if max_cells > 0:
            changed_cells = comparison['total_modified_cells'] + \
                          (comparison['total_added'] * target_data['column_count']) + \
                          (comparison['total_deleted'] * baseline_data['column_count'])
            similarity = 1 - (changed_cells / max_cells)
            similarity = max(0, min(1, similarity))  # 确保在0-1范围内
        else:
            similarity = 1.0
        
        # 构建完整结果
        result = {
            'metadata': {
                'baseline_file': baseline_path,
                'target_file': target_path,
                'comparison_time': datetime.now().isoformat(),
                'baseline_structure': {
                    'rows': baseline_data['row_count'],
                    'columns': baseline_data['column_count'],
                    'column_names': baseline_data['column_names']
                },
                'target_structure': {
                    'rows': target_data['row_count'],
                    'columns': target_data['column_count'],
                    'column_names': target_data['column_names']
                }
            },
            'summary': {
                'similarity_score': similarity,
                'total_differences': comparison['total_differences'],
                'modified_cells': comparison['total_modified_cells'],
                'added_rows': comparison['total_added'],
                'deleted_rows': comparison['total_deleted']
            },
            'details': {
                'modified_cells': comparison['modified_cells'][:20],  # 前20个修改
                'added_rows': comparison['added_rows'][:10],  # 前10个新增行
                'deleted_rows': comparison['deleted_rows'][:10],  # 前10个删除行
            },
            'difference_parameters': comparison['differences'][:50],  # 前50个差异参数
            'all_differences': comparison  # 保留所有差异供进一步处理
        }
        
        # 如果指定了输出目录，保存参数文件
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            param_filename = self.generate_parameter_filename(
                baseline_path, target_path, 
                comparison['total_differences']
            )
            param_filepath = output_path / param_filename
            
            # 保存参数文件
            with open(param_filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            result['parameter_file'] = str(param_filepath)
            print(f"✅ 参数文件已保存: {param_filepath}")
        
        return result


def test_professional_comparator():
    """测试专业对比器"""
    comparator = ProfessionalCSVComparator()
    
    # 使用实际的测试文件
    baseline = '/root/projects/tencent-doc-manager/csv_versions/2025_W36/baseline/tencent_test_comparison_csv_20250903_1200_baseline_W36.csv'
    target = '/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_test_comparison_csv_20250904_1000_midweek_W36.csv'
    output_dir = '/root/projects/tencent-doc-manager/comparison_results'
    
    if Path(baseline).exists() and Path(target).exists():
        result = comparator.compare(baseline, target, output_dir)
        
        print("=" * 60)
        print("专业CSV对比结果")
        print("=" * 60)
        print(f"相似度: {result['summary']['similarity_score'] * 100:.2f}%")
        print(f"总差异数: {result['summary']['total_differences']}")
        print(f"修改单元格: {result['summary']['modified_cells']}")
        print(f"新增行: {result['summary']['added_rows']}")
        print(f"删除行: {result['summary']['deleted_rows']}")
        
        print("\n前5个单元格修改:")
        for cell in result['details']['modified_cells'][:5]:
            print(f"  {cell['cell']} ({cell['column_name']}): '{cell['baseline_value']}' → '{cell['target_value']}'")
        
        print("\n前5个差异参数:")
        for param in result['difference_parameters'][:5]:
            print(f"  {param}")
            
        if 'parameter_file' in result:
            print(f"\n参数文件: {result['parameter_file']}")
        
        return result
    else:
        print("测试文件不存在")
        return None


if __name__ == "__main__":
    test_professional_comparator()