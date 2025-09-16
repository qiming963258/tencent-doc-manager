#!/usr/bin/env python3
"""
标准化输出格式验证器

验证生成的标准输出是否完全符合系统规格要求，包括：
1. 所有必需字段的存在性检查
2. 数据格式和类型验证
3. 数据完整性和一致性检查
4. 热力图矩阵验证
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StandardOutputValidator:
    """标准化输出验证器"""
    
    def __init__(self):
        # 必需的字段定义
        self.required_comparison_fields = [
            'baseline_file', 'modified_file', 'modifications', 
            'actual_columns', 'table_metadata', 'heatmap_data'
        ]
        
        self.required_modification_fields = [
            'row_index', 'column_name', 'original_value', 
            'new_value', 'change_type', 'risk_level'
        ]
        
        self.required_metadata_fields = [
            'original_rows', 'modified_rows', 'total_changes', 
            'quality_score', 'risk_distribution', 'processing_success_rate'
        ]
        
        self.valid_risk_levels = ['L1', 'L2', 'L3']
        self.valid_change_types = ['modification', 'addition', 'deletion', 'content_change']
    
    def validate_standard_output(self, file_path: str) -> Dict[str, Any]:
        """
        验证标准输出文件
        
        Args:
            file_path: 标准输出文件路径
            
        Returns:
            验证结果字典
        """
        validation_result = {
            'file_path': file_path,
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # 1. 加载JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 2. 验证顶层结构
            if 'comparison_result' not in data:
                validation_result['errors'].append('缺少顶层字段: comparison_result')
                validation_result['valid'] = False
                return validation_result
            
            comparison_result = data['comparison_result']
            
            # 3. 验证必需字段存在性
            missing_fields = []
            for field in self.required_comparison_fields:
                if field not in comparison_result:
                    missing_fields.append(field)
            
            if missing_fields:
                validation_result['errors'].append(f'缺少必需字段: {missing_fields}')
                validation_result['valid'] = False
            
            # 4. 验证各个字段的内容
            self._validate_baseline_modified_files(comparison_result, validation_result)
            self._validate_modifications(comparison_result, validation_result)
            self._validate_actual_columns(comparison_result, validation_result)
            self._validate_table_metadata(comparison_result, validation_result)
            self._validate_heatmap_data(comparison_result, validation_result)
            
            # 5. 生成统计信息
            self._generate_statistics(comparison_result, validation_result)
            
        except Exception as e:
            validation_result['errors'].append(f'文件解析错误: {str(e)}')
            validation_result['valid'] = False
        
        return validation_result
    
    def _validate_baseline_modified_files(self, comparison_result: Dict, validation_result: Dict):
        """验证基准文件和修改文件字段"""
        baseline_file = comparison_result.get('baseline_file', '')
        modified_file = comparison_result.get('modified_file', '')
        
        if not baseline_file or not isinstance(baseline_file, str):
            validation_result['errors'].append('baseline_file字段无效')
            validation_result['valid'] = False
        
        if not modified_file or not isinstance(modified_file, str):
            validation_result['errors'].append('modified_file字段无效')
            validation_result['valid'] = False
        
        # 检查文件名格式
        if baseline_file and not baseline_file.endswith('.csv'):
            validation_result['warnings'].append('baseline_file应以.csv结尾')
        
        if modified_file and not modified_file.endswith('.csv'):
            validation_result['warnings'].append('modified_file应以.csv结尾')
    
    def _validate_modifications(self, comparison_result: Dict, validation_result: Dict):
        """验证变更数据数组"""
        modifications = comparison_result.get('modifications', [])
        
        if not isinstance(modifications, list):
            validation_result['errors'].append('modifications字段必须是数组')
            validation_result['valid'] = False
            return
        
        for i, mod in enumerate(modifications):
            if not isinstance(mod, dict):
                validation_result['errors'].append(f'modifications[{i}]必须是对象')
                validation_result['valid'] = False
                continue
            
            # 检查必需字段
            for field in self.required_modification_fields:
                if field not in mod:
                    validation_result['errors'].append(f'modifications[{i}]缺少字段: {field}')
                    validation_result['valid'] = False
            
            # 检查数据类型
            if 'row_index' in mod and not isinstance(mod['row_index'], int):
                validation_result['errors'].append(f'modifications[{i}].row_index必须是整数')
                validation_result['valid'] = False
            
            if 'column_name' in mod and not isinstance(mod['column_name'], str):
                validation_result['errors'].append(f'modifications[{i}].column_name必须是字符串')
                validation_result['valid'] = False
            
            # 检查风险级别
            if 'risk_level' in mod and mod['risk_level'] not in self.valid_risk_levels:
                validation_result['warnings'].append(
                    f'modifications[{i}].risk_level值异常: {mod["risk_level"]}'
                )
            
            # 检查变更类型
            if 'change_type' in mod and mod['change_type'] not in self.valid_change_types:
                validation_result['warnings'].append(
                    f'modifications[{i}].change_type值异常: {mod["change_type"]}'
                )
    
    def _validate_actual_columns(self, comparison_result: Dict, validation_result: Dict):
        """验证实际列名列表"""
        actual_columns = comparison_result.get('actual_columns', [])
        
        if not isinstance(actual_columns, list):
            validation_result['errors'].append('actual_columns字段必须是数组')
            validation_result['valid'] = False
            return
        
        if not actual_columns:
            validation_result['warnings'].append('actual_columns数组为空')
        
        # 检查列名类型
        for i, col in enumerate(actual_columns):
            if not isinstance(col, str):
                validation_result['errors'].append(f'actual_columns[{i}]必须是字符串')
                validation_result['valid'] = False
        
        # 检查重复列名
        if len(actual_columns) != len(set(actual_columns)):
            validation_result['warnings'].append('actual_columns包含重复的列名')
    
    def _validate_table_metadata(self, comparison_result: Dict, validation_result: Dict):
        """验证表格元数据"""
        table_metadata = comparison_result.get('table_metadata', {})
        
        if not isinstance(table_metadata, dict):
            validation_result['errors'].append('table_metadata字段必须是对象')
            validation_result['valid'] = False
            return
        
        # 检查必需字段
        for field in self.required_metadata_fields:
            if field not in table_metadata:
                validation_result['errors'].append(f'table_metadata缺少字段: {field}')
                validation_result['valid'] = False
        
        # 检查数据类型
        numeric_fields = ['original_rows', 'modified_rows', 'total_changes']
        for field in numeric_fields:
            if field in table_metadata and not isinstance(table_metadata[field], int):
                validation_result['errors'].append(f'table_metadata.{field}必须是整数')
                validation_result['valid'] = False
        
        if 'quality_score' in table_metadata:
            score = table_metadata['quality_score']
            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                validation_result['errors'].append('table_metadata.quality_score必须是0-1之间的数值')
                validation_result['valid'] = False
        
        if 'processing_success_rate' in table_metadata:
            rate = table_metadata['processing_success_rate']
            if not isinstance(rate, (int, float)) or not (0 <= rate <= 1):
                validation_result['errors'].append('table_metadata.processing_success_rate必须是0-1之间的数值')
                validation_result['valid'] = False
        
        # 检查风险分布
        if 'risk_distribution' in table_metadata:
            risk_dist = table_metadata['risk_distribution']
            if not isinstance(risk_dist, dict):
                validation_result['errors'].append('table_metadata.risk_distribution必须是对象')
                validation_result['valid'] = False
    
    def _validate_heatmap_data(self, comparison_result: Dict, validation_result: Dict):
        """验证热力图数据"""
        heatmap_data = comparison_result.get('heatmap_data', [])
        
        if not isinstance(heatmap_data, list):
            validation_result['errors'].append('heatmap_data字段必须是数组')
            validation_result['valid'] = False
            return
        
        if not heatmap_data:
            validation_result['warnings'].append('heatmap_data数组为空')
            return
        
        # 检查矩阵尺寸（期望30×19）
        rows = len(heatmap_data)
        cols = len(heatmap_data[0]) if heatmap_data else 0
        
        if rows != 30:
            validation_result['warnings'].append(f'热力图行数为{rows}，期望30行')
        
        if cols != 19:
            validation_result['warnings'].append(f'热力图列数为{cols}，期望19列')
        
        # 检查每行的列数一致性
        for i, row in enumerate(heatmap_data):
            if not isinstance(row, list):
                validation_result['errors'].append(f'heatmap_data[{i}]必须是数组')
                validation_result['valid'] = False
                continue
            
            if len(row) != cols:
                validation_result['errors'].append(f'heatmap_data[{i}]列数不一致')
                validation_result['valid'] = False
            
            # 检查数据类型和范围
            for j, value in enumerate(row):
                if not isinstance(value, (int, float)):
                    validation_result['errors'].append(f'heatmap_data[{i}][{j}]必须是数值类型')
                    validation_result['valid'] = False
                elif not (0 <= value <= 1):
                    validation_result['warnings'].append(f'heatmap_data[{i}][{j}]值超出0-1范围: {value}')
    
    def _generate_statistics(self, comparison_result: Dict, validation_result: Dict):
        """生成统计信息"""
        stats = {}
        
        # 变更统计
        modifications = comparison_result.get('modifications', [])
        stats['total_modifications'] = len(modifications)
        
        # 风险级别统计
        risk_counts = {'L1': 0, 'L2': 0, 'L3': 0}
        change_types = {}
        
        for mod in modifications:
            risk_level = mod.get('risk_level', 'Unknown')
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
            
            change_type = mod.get('change_type', 'Unknown')
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        stats['risk_level_distribution'] = risk_counts
        stats['change_type_distribution'] = change_types
        
        # 列统计
        actual_columns = comparison_result.get('actual_columns', [])
        stats['total_columns'] = len(actual_columns)
        
        # 热力图统计
        heatmap_data = comparison_result.get('heatmap_data', [])
        if heatmap_data:
            stats['heatmap_dimensions'] = f"{len(heatmap_data)}×{len(heatmap_data[0])}"
            
            # 计算热力图数据范围
            all_values = [val for row in heatmap_data for val in row]
            if all_values:
                stats['heatmap_value_range'] = {
                    'min': min(all_values),
                    'max': max(all_values),
                    'avg': sum(all_values) / len(all_values)
                }
        
        validation_result['statistics'] = stats
    
    def validate_ui_parameters(self, file_path: str) -> Dict[str, Any]:
        """
        验证UI参数文件
        
        Args:
            file_path: UI参数文件路径
            
        Returns:
            验证结果字典
        """
        validation_result = {
            'file_path': file_path,
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ui_params = json.load(f)
            
            # 检查必需的顶层字段
            required_top_fields = [
                'table_display', 'change_statistics', 'heatmap_config',
                'filter_options', 'quality_indicators'
            ]
            
            for field in required_top_fields:
                if field not in ui_params:
                    validation_result['errors'].append(f'UI参数缺少字段: {field}')
                    validation_result['valid'] = False
            
            # 验证表格显示配置
            if 'table_display' in ui_params:
                table_display = ui_params['table_display']
                if not isinstance(table_display.get('total_rows'), int):
                    validation_result['errors'].append('table_display.total_rows必须是整数')
                    validation_result['valid'] = False
                
                if not isinstance(table_display.get('total_columns'), int):
                    validation_result['errors'].append('table_display.total_columns必须是整数')
                    validation_result['valid'] = False
            
            # 验证热力图配置
            if 'heatmap_config' in ui_params:
                heatmap_config = ui_params['heatmap_config']
                if 'dimensions' in heatmap_config:
                    dims = heatmap_config['dimensions']
                    if not isinstance(dims.get('rows'), int) or not isinstance(dims.get('columns'), int):
                        validation_result['errors'].append('heatmap_config.dimensions必须包含整数类型的rows和columns')
                        validation_result['valid'] = False
            
        except Exception as e:
            validation_result['errors'].append(f'UI参数文件解析错误: {str(e)}')
            validation_result['valid'] = False
        
        return validation_result


def main():
    """主函数 - 验证生成的标准输出"""
    validator = StandardOutputValidator()
    
    # 查找最新生成的文件
    standard_outputs_dir = Path("/root/projects/tencent-doc-manager/csv_versions/standard_outputs")
    
    standard_files = list(standard_outputs_dir.glob("test_standard_output_*.json"))
    ui_files = list(standard_outputs_dir.glob("ui_parameters_*.json"))
    
    if not standard_files:
        print("❌ 未找到标准输出文件")
        return False
    
    if not ui_files:
        print("❌ 未找到UI参数文件")
        return False
    
    # 验证最新的标准输出文件
    latest_standard_file = max(standard_files, key=lambda x: x.stat().st_mtime)
    latest_ui_file = max(ui_files, key=lambda x: x.stat().st_mtime)
    
    print("=" * 80)
    print("标准化输出格式验证报告")
    print("=" * 80)
    
    # 验证标准输出
    print(f"\n📋 验证标准输出文件: {latest_standard_file.name}")
    standard_result = validator.validate_standard_output(str(latest_standard_file))
    
    if standard_result['valid']:
        print("✅ 标准输出格式验证通过")
    else:
        print("❌ 标准输出格式验证失败")
        for error in standard_result['errors']:
            print(f"  错误: {error}")
    
    if standard_result['warnings']:
        print("⚠️  警告信息:")
        for warning in standard_result['warnings']:
            print(f"  警告: {warning}")
    
    # 显示统计信息
    if 'statistics' in standard_result:
        stats = standard_result['statistics']
        print(f"\n📊 数据统计:")
        print(f"  总变更数: {stats.get('total_modifications', 0)}")
        print(f"  总列数: {stats.get('total_columns', 0)}")
        print(f"  热力图尺寸: {stats.get('heatmap_dimensions', 'N/A')}")
        
        if 'risk_level_distribution' in stats:
            risk_dist = stats['risk_level_distribution']
            print(f"  风险分布: L1={risk_dist.get('L1', 0)}, L2={risk_dist.get('L2', 0)}, L3={risk_dist.get('L3', 0)}")
    
    # 验证UI参数
    print(f"\n📋 验证UI参数文件: {latest_ui_file.name}")
    ui_result = validator.validate_ui_parameters(str(latest_ui_file))
    
    if ui_result['valid']:
        print("✅ UI参数格式验证通过")
    else:
        print("❌ UI参数格式验证失败")
        for error in ui_result['errors']:
            print(f"  错误: {error}")
    
    if ui_result['warnings']:
        print("⚠️  UI参数警告:")
        for warning in ui_result['warnings']:
            print(f"  警告: {warning}")
    
    print("=" * 80)
    
    # 总体验证结果
    overall_valid = standard_result['valid'] and ui_result['valid']
    if overall_valid:
        print("🎉 所有输出格式验证通过！符合系统规格要求。")
    else:
        print("❌ 输出格式验证存在问题，需要修正。")
    
    return overall_valid


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)