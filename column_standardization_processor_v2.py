#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV列名智能标准化处理器 V2
使用CSV对比结果中已有的column标识（C、D、E等）
无需自编序号，直接利用Excel列标识定位和覆盖
"""

import json
import os
import asyncio
import logging
from typing import Dict, List, Tuple, Any, Optional, Set
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入DeepSeek客户端
from deepseek_client import DeepSeekClient

class ColumnStandardizationProcessorV2:
    """列名标准化处理器V2 - 使用现有column标识"""
    
    def __init__(self, api_key: str):
        """初始化处理器"""
        self.api_key = api_key
        self.deepseek_client = DeepSeekClient(api_key)
        
        # 19个标准列名（与综合打分文件保持一致）
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
            "完成链接", "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
        ]
        
        logger.info("列名标准化处理器V2初始化完成")
    
    def extract_columns_from_comparison(self, comparison_file_path: str) -> Tuple[Dict[str, str], Set[str]]:
        """
        从CSV对比结果中提取有修改的列信息
        
        Args:
            comparison_file_path: CSV对比结果文件路径
            
        Returns:
            (column_mapping, modified_column_names)
            column_mapping: {Excel列标识: 列名} 如 {"C": "项目类型", "D": "来源"}
            modified_column_names: 有修改的列名集合（去重）
        """
        with open(comparison_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        column_mapping = {}  # Excel列标识 -> 列名
        modified_column_names = set()  # 去重的列名集合
        
        # 从modified_cells中提取信息
        if 'details' in data and 'modified_cells' in data['details']:
            for cell_info in data['details']['modified_cells']:
                column_id = cell_info.get('column')  # 如 "C", "D", "E"
                column_name = cell_info.get('column_name')  # 如 "项目类型", "来源"
                
                if column_id and column_name:
                    # 记录列标识到列名的映射
                    if column_id not in column_mapping:
                        column_mapping[column_id] = column_name
                    
                    # 收集所有有修改的列名
                    modified_column_names.add(column_name)
        
        logger.info(f"提取到 {len(column_mapping)} 个有修改的列")
        logger.info(f"列映射: {column_mapping}")
        
        return column_mapping, modified_column_names
    
    def build_column_standardization_prompt(self, column_mapping: Dict[str, str]) -> str:
        """
        构建列名标准化提示词
        使用现有的Excel列标识
        
        Args:
            column_mapping: {Excel列标识: 列名} 的字典
        """
        prompt = f"""你是专业的CSV列名标准化专家。请将Excel列标识对应的列名映射到19个标准列名。

## 🎯 核心任务
分析带Excel列标识的列名，将其映射到标准列名。保持列标识不变，只改变列名部分。

## 📋 19个标准列名
{json.dumps(self.standard_columns, ensure_ascii=False, indent=2)}

## 📝 需要标准化的列（从CSV对比中提取的有修改的列）
"""
        for col_id, col_name in sorted(column_mapping.items()):
            prompt += f"列{col_id}: {col_name}\n"
        
        prompt += f"""
## 🔄 处理规则
1. 保持Excel列标识不变（C、D、E等）
2. 将每个列名映射到最匹配的标准列名
3. 如果某个列无法映射到任何标准列，标记为"无法映射"
4. 这些都是有实际修改的列（修改值≠0）

## 📊 输出格式（严格JSON）
{{
    "success": true,
    "column_mapping": {{
        "C": "映射后的标准列名",
        "D": "映射后的标准列名",
        // ... 所有列标识的映射
    }},
    "unmapped_columns": {{
        "列标识": "原始列名"  // 无法映射的列
    }},
    "statistics": {{
        "total_columns": {len(column_mapping)},
        "mapped_count": 数字,
        "unmapped_count": 数字
    }}
}}

请立即分析并返回标准化映射结果。"""
        
        return prompt
    
    async def standardize_column_names(self, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        调用AI进行列名标准化
        
        Args:
            column_mapping: {Excel列标识: 列名} 的字典
            
        Returns:
            标准化结果
        """
        prompt = self.build_column_standardization_prompt(column_mapping)
        
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
                    return {
                        "success": True,
                        "result": parsed,
                        "original_mapping": column_mapping
                    }
            except Exception as e:
                logger.error(f"解析AI响应失败: {e}")
                return {"success": False, "error": str(e)}
        
        return result
    
    def apply_standardization_to_file(self, 
                                     comparison_file_path: str,
                                     standardization_result: Dict[str, Any],
                                     output_path: str = None) -> Dict[str, Any]:
        """
        将标准化结果应用到CSV对比文件
        
        Args:
            comparison_file_path: 原始CSV对比结果文件路径
            standardization_result: AI标准化结果
            output_path: 输出文件路径（可选）
            
        Returns:
            处理结果
        """
        # 读取原始文件
        with open(comparison_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not standardization_result.get("success"):
            return {"success": False, "error": "标准化失败"}
        
        column_name_mapping = standardization_result["result"].get("column_mapping", {})
        
        # 更新metadata中的列名
        if 'metadata' in data:
            # 更新baseline_structure的列名
            if 'baseline_structure' in data['metadata']:
                updated_columns = []
                for i, col_name in enumerate(data['metadata']['baseline_structure']['column_names']):
                    # 查找这个列名对应的Excel列标识
                    col_id = self._find_column_id_by_name(
                        col_name, 
                        standardization_result.get("original_mapping", {})
                    )
                    if col_id and col_id in column_name_mapping:
                        updated_columns.append(column_name_mapping[col_id])
                    else:
                        updated_columns.append(col_name)
                data['metadata']['baseline_structure']['column_names'] = updated_columns
            
            # 记录标准化信息
            data['metadata']['standardization'] = {
                "standardized_at": datetime.now().isoformat(),
                "column_mapping": column_name_mapping,
                "statistics": standardization_result["result"].get("statistics", {})
            }
        
        # 更新details中的column_name
        if 'details' in data and 'modified_cells' in data['details']:
            for cell_info in data['details']['modified_cells']:
                col_id = cell_info.get('column')
                if col_id and col_id in column_name_mapping:
                    # 保留原始列名
                    cell_info['original_column_name'] = cell_info.get('column_name')
                    # 更新为标准列名
                    cell_info['column_name'] = column_name_mapping[col_id]
        
        # 保存结果
        if output_path is None:
            base_name = os.path.splitext(comparison_file_path)[0]
            output_path = f"{base_name}_standardized.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"标准化结果已保存到: {output_path}")
        
        return {
            "success": True,
            "input_file": comparison_file_path,
            "output_file": output_path,
            "column_mapping": column_name_mapping,
            "statistics": standardization_result["result"].get("statistics", {})
        }
    
    def _find_column_id_by_name(self, column_name: str, original_mapping: Dict[str, str]) -> Optional[str]:
        """根据列名查找对应的Excel列标识"""
        for col_id, name in original_mapping.items():
            if name == column_name:
                return col_id
        return None
    
    async def process_comparison_file(self, comparison_file_path: str) -> Dict[str, Any]:
        """
        处理CSV对比结果文件的完整流程
        
        Args:
            comparison_file_path: CSV对比结果文件路径
            
        Returns:
            处理结果
        """
        logger.info(f"开始处理文件: {comparison_file_path}")
        
        try:
            # 步骤1：提取有修改的列信息
            column_mapping, modified_columns = self.extract_columns_from_comparison(
                comparison_file_path
            )
            
            if not column_mapping:
                return {"success": False, "error": "未找到有修改的列"}
            
            # 步骤2：调用AI标准化
            standardization_result = await self.standardize_column_names(column_mapping)
            
            if not standardization_result.get("success"):
                return standardization_result
            
            # 步骤3：应用标准化
            result = self.apply_standardization_to_file(
                comparison_file_path,
                standardization_result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def sync_process_file(self, comparison_file_path: str) -> Dict[str, Any]:
        """同步版本的文件处理"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.process_comparison_file(comparison_file_path)
            )
        finally:
            loop.close()


# 测试代码
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python column_standardization_processor_v2.py <comparison_file.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    api_key = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
    
    processor = ColumnStandardizationProcessorV2(api_key)
    result = processor.sync_process_file(file_path)
    
    if result.get("success"):
        print("\n✅ 处理成功！")
        print(f"输入文件: {result['input_file']}")
        print(f"输出文件: {result['output_file']}")
        print(f"\n列映射:")
        for col_id, standard_name in result['column_mapping'].items():
            print(f"  列{col_id} → {standard_name}")
    else:
        print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")