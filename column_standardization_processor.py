#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV列名智能标准化处理器
提取有修改的列，添加序号，调用AI标准化，回写结果
"""

import json
import csv
import os
import asyncio
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import string
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入DeepSeek客户端
from deepseek_client import DeepSeekClient

class ColumnStandardizationProcessor:
    """列名标准化处理器"""
    
    def __init__(self, api_key: str):
        """初始化处理器"""
        self.api_key = api_key
        self.deepseek_client = DeepSeekClient(api_key)
        
        # 19个标准列名
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
        
        logger.info("列名标准化处理器初始化完成")
    
    def generate_column_labels(self, count: int) -> List[str]:
        """
        生成英文字母序号标签
        1-26: A-Z
        27-52: AA-AZ
        以此类推
        """
        labels = []
        chars = string.ascii_uppercase
        
        for i in range(count):
            if i < 26:
                labels.append(chars[i])
            else:
                # 处理超过26列的情况
                first = (i - 26) // 26
                second = (i - 26) % 26
                if first < 26:
                    labels.append(chars[first] + chars[second])
                else:
                    # 处理超过52列的极端情况
                    labels.append(f"COL{i+1}")
        
        return labels
    
    def extract_modified_columns(self, comparison_result: Dict) -> Tuple[List[str], Dict[str, List[Any]]]:
        """
        从CSV对比结果中提取有修改的列
        
        Args:
            comparison_result: CSV对比结果字典
            
        Returns:
            (去重的列名列表, 列名对应的所有修改数据)
        """
        modified_columns = set()
        column_data = {}
        
        # 分析差异数据
        if 'differences' in comparison_result:
            for diff in comparison_result['differences']:
                for column, values in diff.items():
                    if column == 'row_number':
                        continue
                        
                    # 检查是否有实际修改
                    if isinstance(values, dict):
                        baseline = values.get('baseline_value', '')
                        target = values.get('target_value', '')
                        changed = values.get('changed', False)
                        
                        # 只收集有变化的列
                        if changed and baseline != target:
                            modified_columns.add(column)
                            if column not in column_data:
                                column_data[column] = []
                            column_data[column].append(values)
        
        # 去重并排序
        unique_columns = sorted(list(modified_columns))
        
        logger.info(f"提取到 {len(unique_columns)} 个有修改的列")
        return unique_columns, column_data
    
    def build_numbered_prompt(self, columns_with_labels: Dict[str, str]) -> str:
        """
        构建带序号的AI提示词
        
        Args:
            columns_with_labels: {序号: 列名} 的字典
        """
        prompt = f"""你是专业的CSV列名标准化专家。请将带序号的列名映射到19个标准列名。

## 🎯 核心任务
分析带英文序号的列名，将其映射到标准列名。保持序号不变，只改变列名部分。

## 📋 19个标准列名
{json.dumps(self.standard_columns, ensure_ascii=False, indent=2)}

## 📝 需要标准化的列名（共{len(columns_with_labels)}个）
"""
        for label, column in columns_with_labels.items():
            prompt += f"{label}: {column}\n"
        
        prompt += """
## 🔄 处理规则
1. 保持英文序号不变（A、B、C等）
2. 将每个列名映射到最匹配的标准列名
3. 如果列数超过19个，选择最重要的19个，其余标记为丢弃
4. 如果某些标准列没有对应，标记为缺失

## 📊 输出格式（严格JSON）
{
    "success": true,
    "numbered_mapping": {
        "A": "映射后的标准列名",
        "B": "映射后的标准列名",
        // ... 所有序号的映射
    },
    "discarded_labels": ["X", "Y"],  // 被丢弃的序号列表
    "missing_standard_columns": ["标准列1", "标准列2"],  // 缺失的标准列
    "statistics": {
        "total_input": 数字,
        "mapped_count": 数字,
        "discarded_count": 数字,
        "missing_standard_count": 数字
    }
}

请立即分析并返回标准化映射结果。"""
        
        return prompt
    
    async def standardize_columns(self, columns: List[str]) -> Dict[str, Any]:
        """
        调用AI进行列名标准化
        
        Args:
            columns: 需要标准化的列名列表
            
        Returns:
            标准化结果字典
        """
        # 生成序号标签
        labels = self.generate_column_labels(len(columns))
        columns_with_labels = {labels[i]: columns[i] for i in range(len(columns))}
        
        logger.info(f"生成序号映射: {columns_with_labels}")
        
        # 构建提示词
        prompt = self.build_numbered_prompt(columns_with_labels)
        
        # 调用AI
        messages = [
            {
                "role": "system",
                "content": "你是专业的数据分析专家，精通CSV列名标准化。总是返回有效的JSON格式。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        result = await self.deepseek_client.chat_completion(messages, temperature=0.1)
        
        if result["success"]:
            try:
                content = result["content"]
                # 提取JSON部分
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > 0:
                    json_str = content[json_start:json_end]
                    parsed = json.loads(json_str)
                    
                    # 添加原始映射信息
                    parsed['original_columns'] = columns_with_labels
                    return {
                        "success": True,
                        "result": parsed
                    }
            except Exception as e:
                logger.error(f"解析AI响应失败: {e}")
                return {"success": False, "error": str(e)}
        
        return result
    
    def apply_standardization(self, comparison_result: Dict, standardization_result: Dict) -> Dict:
        """
        将标准化结果应用到CSV对比结果
        
        Args:
            comparison_result: 原始CSV对比结果
            standardization_result: AI标准化结果
            
        Returns:
            标准化后的CSV对比结果
        """
        if not standardization_result.get("success"):
            logger.error("标准化失败，返回原始结果")
            return comparison_result
        
        mapping = standardization_result["result"].get("numbered_mapping", {})
        original_columns = standardization_result["result"].get("original_columns", {})
        discarded_labels = standardization_result["result"].get("discarded_labels", [])
        
        # 创建原始列名到标准列名的映射
        column_mapping = {}
        for label, standard_name in mapping.items():
            if label not in discarded_labels and label in original_columns:
                original_name = original_columns[label]
                column_mapping[original_name] = standard_name
        
        logger.info(f"列名映射关系: {column_mapping}")
        
        # 创建新的标准化结果
        standardized_result = {
            "metadata": {
                "original_file": comparison_result.get("metadata", {}).get("original_file", ""),
                "standardization_time": datetime.now().isoformat(),
                "column_mapping": column_mapping,
                "discarded_columns": [original_columns.get(label, label) for label in discarded_labels],
                "standard_columns_count": len(self.standard_columns)
            },
            "differences": []
        }
        
        # 处理每条差异记录
        for diff in comparison_result.get("differences", []):
            standardized_diff = {"row_number": diff.get("row_number", 0)}
            
            # 先添加所有标准列（初始化为null）
            for std_col in self.standard_columns:
                standardized_diff[std_col] = None
            
            # 填充有映射的列数据
            for original_col, values in diff.items():
                if original_col == "row_number":
                    continue
                
                if original_col in column_mapping:
                    standard_col = column_mapping[original_col]
                    standardized_diff[standard_col] = values
                # 丢弃未映射的列
            
            standardized_result["differences"].append(standardized_diff)
        
        # 添加统计信息
        standardized_result["statistics"] = {
            "total_differences": len(standardized_result["differences"]),
            "mapped_columns": len(column_mapping),
            "discarded_columns": len(discarded_labels),
            "standard_columns": len(self.standard_columns)
        }
        
        return standardized_result
    
    async def process_file(self, input_file: str, output_file: str = None) -> Dict:
        """
        处理CSV对比文件
        
        Args:
            input_file: 输入的CSV对比结果文件路径
            output_file: 输出的标准化文件路径（可选）
            
        Returns:
            处理结果
        """
        logger.info(f"开始处理文件: {input_file}")
        
        try:
            # 读取输入文件
            with open(input_file, 'r', encoding='utf-8') as f:
                if input_file.endswith('.json'):
                    comparison_result = json.load(f)
                else:
                    # 处理CSV格式
                    comparison_result = self.parse_csv_to_json(input_file)
            
            # 提取有修改的列
            modified_columns, column_data = self.extract_modified_columns(comparison_result)
            
            if not modified_columns:
                logger.warning("没有发现有修改的列")
                return {"success": False, "message": "没有发现有修改的列"}
            
            logger.info(f"发现 {len(modified_columns)} 个有修改的列: {modified_columns}")
            
            # 调用AI标准化
            standardization_result = await self.standardize_columns(modified_columns)
            
            if not standardization_result.get("success"):
                return standardization_result
            
            # 应用标准化
            standardized_result = self.apply_standardization(
                comparison_result, 
                standardization_result
            )
            
            # 保存结果
            if output_file is None:
                # 自动生成输出文件名
                base_name = os.path.splitext(input_file)[0]
                output_file = f"{base_name}_standardized.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(standardized_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"标准化结果已保存到: {output_file}")
            
            return {
                "success": True,
                "input_file": input_file,
                "output_file": output_file,
                "statistics": standardized_result["statistics"],
                "column_mapping": standardized_result["metadata"]["column_mapping"]
            }
            
        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def parse_csv_to_json(self, csv_file: str) -> Dict:
        """
        将CSV文件解析为JSON格式的对比结果
        """
        differences = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                diff = {"row_number": row_num}
                for column, value in row.items():
                    # 简单解析，实际需要根据CSV格式调整
                    diff[column] = {
                        "baseline_value": value,
                        "target_value": value,
                        "changed": False  # 需要根据实际情况判断
                    }
                differences.append(diff)
        
        return {"differences": differences}
    
    def sync_process_file(self, input_file: str, output_file: str = None) -> Dict:
        """同步版本的文件处理（供非异步环境使用）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.process_file(input_file, output_file))
        finally:
            loop.close()


# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV列名标准化处理器")
    parser.add_argument("input_file", help="输入的CSV对比结果文件")
    parser.add_argument("-o", "--output", help="输出文件路径（可选）")
    parser.add_argument("--api-key", default="sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb",
                       help="DeepSeek API密钥")
    
    args = parser.parse_args()
    
    # 创建处理器
    processor = ColumnStandardizationProcessor(args.api_key)
    
    # 处理文件
    result = processor.sync_process_file(args.input_file, args.output)
    
    # 显示结果
    if result.get("success"):
        print("\n✅ 处理成功！")
        print(f"输入文件: {result['input_file']}")
        print(f"输出文件: {result['output_file']}")
        print(f"\n统计信息:")
        for key, value in result['statistics'].items():
            print(f"  {key}: {value}")
        print(f"\n列名映射:")
        for original, standard in result['column_mapping'].items():
            print(f"  {original} → {standard}")
    else:
        print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")