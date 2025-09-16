#!/usr/bin/env python3
"""
标准化变更参数输出生成器

基于CSV对比结果，生成符合系统标准的输出格式，包括：
1. 标准JSON输出格式（符合系统规格要求）
2. UI参数文件生成
3. 热力图数据处理
4. 变更风险评估

功能：
- 读取comparison_cache中的对比结果
- 转换为符合系统规格的标准格式
- 生成UI参数文件
- 输出30×19热力图矩阵数据
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StandardOutputGenerator:
    """标准化输出生成器"""
    
    def __init__(self, base_dir: str = "/root/projects/tencent-doc-manager"):
        self.base_dir = Path(base_dir)
        self.comparison_cache_dir = self.base_dir / "csv_versions" / "comparison_cache"
        self.standard_outputs_dir = self.base_dir / "csv_versions" / "standard_outputs"
        
        # 确保输出目录存在
        self.standard_outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # 标准列名定义（19个标准列）
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐", 
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人", 
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
    
    def load_comparison_result(self, result_file: str) -> Dict[str, Any]:
        """
        加载对比结果文件
        
        Args:
            result_file: 对比结果文件名
            
        Returns:
            对比结果数据
        """
        try:
            file_path = self.comparison_cache_dir / result_file
            if not file_path.exists():
                raise FileNotFoundError(f"对比结果文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"成功加载对比结果文件: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"加载对比结果文件失败: {e}")
            raise
    
    def extract_baseline_modified_files(self, comparison_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        从对比数据中提取基准文件和修改文件名
        
        Args:
            comparison_data: 对比数据
            
        Returns:
            (baseline_file, modified_file)
        """
        # 从第一个表格结果中提取文件信息
        if "comparison_results" in comparison_data and comparison_data["comparison_results"]:
            table_result = comparison_data["comparison_results"][0]
            table_name = table_result.get("table_name", "unknown_table")
            
            # 基于表格名生成基准文件名和修改文件名
            baseline_file = f"{table_name}_基准版.csv"
            
            # 如果表格名包含时间戳，则为修改文件，否则生成时间戳
            if any(char.isdigit() for char in table_name[-20:]):
                modified_file = f"{table_name}.csv"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                modified_file = f"{table_name}_{timestamp}.csv"
                
            return baseline_file, modified_file
        
        # 默认文件名
        return "baseline_file.csv", "modified_file.csv"
    
    def convert_changes_to_standard_format(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将变更数据转换为标准格式
        
        Args:
            changes: 原始变更数据列表
            
        Returns:
            标准格式的变更数据列表
        """
        standard_modifications = []
        
        for change in changes:
            modification = {
                "row_index": change.get("row_index", 0),
                "column_name": change.get("column_name", ""),
                "original_value": change.get("original_value", ""),
                "new_value": change.get("new_value", ""),
                "change_type": change.get("change_type", "modification"),
                "risk_level": change.get("risk_level", "L2")
            }
            standard_modifications.append(modification)
        
        return standard_modifications
    
    def calculate_table_metadata(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算表格元数据
        
        Args:
            comparison_data: 对比数据
            
        Returns:
            表格元数据
        """
        # 从quality_summary获取统计信息
        quality_summary = comparison_data.get("quality_summary", {})
        
        # 从第一个表格结果获取数据行数
        original_rows = 0
        modified_rows = 0
        if "comparison_results" in comparison_data and comparison_data["comparison_results"]:
            table_result = comparison_data["comparison_results"][0]
            standardized_data = table_result.get("standardization_result", {}).get("standardized_data", [])
            modified_rows = len(standardized_data)
            original_rows = modified_rows  # 如果没有删除行，原始行数等于修改后行数
        
        total_changes = quality_summary.get("total_changes_detected", 0)
        average_quality_score = quality_summary.get("average_quality_score", 0.0)
        risk_distribution = quality_summary.get("risk_distribution", {})
        
        metadata = {
            "original_rows": original_rows,
            "modified_rows": modified_rows,
            "total_changes": total_changes,
            "quality_score": round(average_quality_score, 3),
            "risk_distribution": {
                "L1_critical": risk_distribution.get("L1", 0),
                "L2_moderate": risk_distribution.get("L2", 0),
                "L3_minor": risk_distribution.get("L3", 0)
            },
            "processing_success_rate": quality_summary.get("processing_success_rate", 1.0)
        }
        
        return metadata
    
    def generate_standard_output(self, comparison_result_file: str) -> Dict[str, Any]:
        """
        生成标准化输出格式
        
        Args:
            comparison_result_file: 对比结果文件名
            
        Returns:
            标准化输出数据
        """
        # 1. 加载对比结果
        comparison_data = self.load_comparison_result(comparison_result_file)
        
        # 2. 提取基准文件和修改文件名
        baseline_file, modified_file = self.extract_baseline_modified_files(comparison_data)
        
        # 3. 提取变更数据
        modifications = []
        actual_columns = []
        
        if "comparison_results" in comparison_data and comparison_data["comparison_results"]:
            table_result = comparison_data["comparison_results"][0]
            
            # 提取变更数据
            changes = table_result.get("change_detection_result", {}).get("changes", [])
            modifications = self.convert_changes_to_standard_format(changes)
            
            # 提取实际列名
            mapping = table_result.get("matching_result", {}).get("mapping", {})
            actual_columns = list(mapping.keys())
        
        # 4. 计算表格元数据
        table_metadata = self.calculate_table_metadata(comparison_data)
        
        # 5. 提取热力图数据
        heatmap_data = comparison_data.get("standardized_matrix", [])
        
        # 6. 构建标准输出格式
        standard_output = {
            "comparison_result": {
                "baseline_file": baseline_file,
                "modified_file": modified_file,
                "modifications": modifications,
                "actual_columns": actual_columns,
                "table_metadata": table_metadata,
                "heatmap_data": heatmap_data
            },
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0.0",
                "source_file": comparison_result_file,
                "total_modifications": len(modifications),
                "heatmap_dimensions": f"{len(heatmap_data)}×{len(heatmap_data[0]) if heatmap_data else 0}"
            }
        }
        
        return standard_output
    
    def generate_ui_parameters(self, standard_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成UI参数文件
        
        Args:
            standard_output: 标准输出数据
            
        Returns:
            UI参数数据
        """
        comparison_result = standard_output["comparison_result"]
        modifications = comparison_result["modifications"]
        table_metadata = comparison_result["table_metadata"]
        heatmap_data = comparison_result["heatmap_data"]
        
        # 计算变更统计
        change_type_stats = {}
        risk_level_stats = {}
        column_change_stats = {}
        
        for mod in modifications:
            # 变更类型统计
            change_type = mod["change_type"]
            change_type_stats[change_type] = change_type_stats.get(change_type, 0) + 1
            
            # 风险级别统计
            risk_level = mod["risk_level"]
            risk_level_stats[risk_level] = risk_level_stats.get(risk_level, 0) + 1
            
            # 列变更统计
            column_name = mod["column_name"]
            column_change_stats[column_name] = column_change_stats.get(column_name, 0) + 1
        
        # 生成热力图配置
        heatmap_config = {
            "dimensions": {
                "rows": len(heatmap_data),
                "columns": len(heatmap_data[0]) if heatmap_data else 0
            },
            "data_range": {
                "min_value": min(min(row) for row in heatmap_data) if heatmap_data else 0,
                "max_value": max(max(row) for row in heatmap_data) if heatmap_data else 1
            },
            "color_scheme": "viridis",
            "smoothing": "gaussian"
        }
        
        # 排序配置
        sort_configs = [
            {"field": "row_index", "direction": "asc", "priority": 1},
            {"field": "risk_level", "direction": "desc", "priority": 2},
            {"field": "column_name", "direction": "asc", "priority": 3}
        ]
        
        ui_parameters = {
            "table_display": {
                "total_rows": table_metadata["modified_rows"],
                "total_columns": len(comparison_result["actual_columns"]),
                "page_size": 50,
                "sort_configs": sort_configs
            },
            "change_statistics": {
                "total_changes": len(modifications),
                "change_type_distribution": change_type_stats,
                "risk_level_distribution": risk_level_stats,
                "column_change_distribution": column_change_stats
            },
            "heatmap_config": heatmap_config,
            "filter_options": {
                "available_columns": comparison_result["actual_columns"],
                "available_risk_levels": list(risk_level_stats.keys()),
                "available_change_types": list(change_type_stats.keys())
            },
            "quality_indicators": {
                "overall_score": table_metadata["quality_score"],
                "risk_distribution": table_metadata["risk_distribution"],
                "processing_success_rate": table_metadata["processing_success_rate"]
            }
        }
        
        return ui_parameters
    
    def save_outputs(self, standard_output: Dict[str, Any], ui_parameters: Dict[str, Any], 
                    output_prefix: str = "standard_output") -> Tuple[str, str]:
        """
        保存标准输出和UI参数文件
        
        Args:
            standard_output: 标准输出数据
            ui_parameters: UI参数数据
            output_prefix: 输出文件前缀
            
        Returns:
            (标准输出文件路径, UI参数文件路径)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存标准输出文件
        standard_output_file = self.standard_outputs_dir / f"{output_prefix}_{timestamp}.json"
        with open(standard_output_file, 'w', encoding='utf-8') as f:
            json.dump(standard_output, f, ensure_ascii=False, indent=2)
        
        # 保存UI参数文件
        ui_parameters_file = self.standard_outputs_dir / f"ui_parameters_{timestamp}.json"
        with open(ui_parameters_file, 'w', encoding='utf-8') as f:
            json.dump(ui_parameters, f, ensure_ascii=False, indent=2)
        
        logger.info(f"标准输出已保存: {standard_output_file}")
        logger.info(f"UI参数已保存: {ui_parameters_file}")
        
        return str(standard_output_file), str(ui_parameters_file)
    
    def process_comparison_result(self, comparison_result_file: str, 
                                output_prefix: str = "standard_output") -> Dict[str, str]:
        """
        处理对比结果并生成所有输出文件
        
        Args:
            comparison_result_file: 对比结果文件名
            output_prefix: 输出文件前缀
            
        Returns:
            输出文件路径字典
        """
        try:
            logger.info(f"开始处理对比结果: {comparison_result_file}")
            
            # 1. 生成标准输出
            standard_output = self.generate_standard_output(comparison_result_file)
            
            # 2. 生成UI参数
            ui_parameters = self.generate_ui_parameters(standard_output)
            
            # 3. 保存输出文件
            standard_file, ui_file = self.save_outputs(standard_output, ui_parameters, output_prefix)
            
            # 4. 生成处理报告
            report = {
                "processing_status": "success",
                "standard_output_file": standard_file,
                "ui_parameters_file": ui_file,
                "total_modifications": len(standard_output["comparison_result"]["modifications"]),
                "heatmap_dimensions": standard_output["generation_metadata"]["heatmap_dimensions"],
                "processing_time": datetime.now().isoformat()
            }
            
            logger.info("标准化输出生成完成")
            logger.info(f"总变更数: {report['total_modifications']}")
            logger.info(f"热力图尺寸: {report['heatmap_dimensions']}")
            
            return report
            
        except Exception as e:
            logger.error(f"处理对比结果失败: {e}")
            raise


def main():
    """主函数 - 测试标准化输出生成器"""
    try:
        # 创建生成器实例
        generator = StandardOutputGenerator()
        
        # 处理测试对比结果
        result_file = "test_comparison_result.json"
        report = generator.process_comparison_result(result_file, "test_standard_output")
        
        print("=" * 60)
        print("标准化输出生成器测试结果")
        print("=" * 60)
        print(f"处理状态: {report['processing_status']}")
        print(f"标准输出文件: {report['standard_output_file']}")
        print(f"UI参数文件: {report['ui_parameters_file']}")
        print(f"总变更数: {report['total_modifications']}")
        print(f"热力图尺寸: {report['heatmap_dimensions']}")
        print(f"处理时间: {report['processing_time']}")
        print("=" * 60)
        
        # 验证输出格式
        with open(report['standard_output_file'], 'r', encoding='utf-8') as f:
            standard_data = json.load(f)
            
        print("\n标准输出格式验证:")
        comparison_result = standard_data['comparison_result']
        print(f"✓ baseline_file: {comparison_result['baseline_file']}")
        print(f"✓ modified_file: {comparison_result['modified_file']}")
        print(f"✓ modifications数组: {len(comparison_result['modifications'])} 项")
        print(f"✓ actual_columns列表: {len(comparison_result['actual_columns'])} 项")
        print(f"✓ table_metadata包含: {list(comparison_result['table_metadata'].keys())}")
        print(f"✓ heatmap_data矩阵: {len(comparison_result['heatmap_data'])}×{len(comparison_result['heatmap_data'][0]) if comparison_result['heatmap_data'] else 0}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)