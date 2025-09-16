#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV列名智能标准化处理器 V3
适配simplified_csv_comparator的新输出格式
支持超过19列时的智能筛选
"""

import json
import os
import asyncio
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入DeepSeek客户端
from deepseek_client import DeepSeekClient

class ColumnStandardizationProcessorV3:
    """列名标准化处理器V3 - 适配简化输出格式，支持智能筛选"""
    
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
        
        logger.info("列名标准化处理器V3初始化完成 - 支持简化格式和智能筛选")
    
    def extract_columns_from_simplified_comparison(self, comparison_file_path: str) -> Dict[str, str]:
        """
        从简化的CSV对比结果中提取修改列信息
        
        Args:
            comparison_file_path: 简化CSV对比结果文件路径
            
        Returns:
            column_mapping: {Excel列标识: 列名} 如 {"C": "项目类型", "D": "来源"}
        """
        with open(comparison_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 直接从modified_columns字段获取
        column_mapping = data.get('modified_columns', {})
        
        logger.info(f"从简化格式提取到 {len(column_mapping)} 个修改列")
        logger.info(f"列映射: {column_mapping}")
        
        return column_mapping
    
    def build_smart_standardization_prompt(self, column_mapping: Dict[str, str]) -> str:
        """
        构建智能标准化提示词
        支持超过19列时的智能筛选
        
        Args:
            column_mapping: {Excel列标识: 列名} 的字典
        """
        column_count = len(column_mapping)
        
        # 判断是否需要智能筛选
        needs_filtering = column_count > 19
        
        prompt = f"""你是专业的CSV列名标准化专家。请将Excel列标识对应的列名映射到19个标准列名。

## 🎯 核心任务
{"【智能筛选模式】从" + str(column_count) + "个修改列中选择最相似的19个进行映射" if needs_filtering else "将所有修改列映射到标准列名"}

## 📋 19个标准列名（固定顺序）
{json.dumps(self.standard_columns, ensure_ascii=False, indent=2)}

## 📝 需要标准化的列（共{column_count}个修改列）
"""
        for col_id, col_name in sorted(column_mapping.items()):
            prompt += f"列{col_id}: {col_name}\n"
        
        if needs_filtering:
            prompt += f"""
## ⚠️ 智能筛选规则（当前有{column_count}个列，需筛选到19个）
1. **优先级1**: 完全匹配的列名（如"序号"="序号"）
2. **优先级2**: 高度相似的变异形式（如"编号"→"序号"）
3. **优先级3**: 语义相关的列（如"执行人"→"负责人"）
4. **优先级4**: 重要的业务列（L1和L2级别的列）
5. **丢弃原则**: 
   - 无法映射到任何标准列的
   - 相似度极低的
   - 多个类似列时选择最相似的一个

## 🎯 筛选要求
- 必须选出恰好19个最相似的列进行映射
- 每个标准列最多映射一个实际列
- 记录被丢弃的列及原因
"""
        
        prompt += f"""
## 📊 输出格式（严格JSON）
{{
    "success": true,
    "column_mapping": {{
        // Excel列标识 → 标准列名的映射
        "C": "映射后的标准列名",
        "D": "映射后的标准列名"
        // ... {"最多19个映射" if needs_filtering else "所有列的映射"}
    }},
    "confidence_scores": {{
        // 每个映射的置信度
        "C": 0.95,
        "D": 0.88
    }},
    {'filtered_out' if needs_filtering else 'unmapped_columns'}: {{
        // {'被筛选掉的列（超过19个的部分）' if needs_filtering else '无法映射的列'}
        "列标识": {{
            "original_name": "原始列名",
            "reason": "{'筛选原因：相似度太低/已有更好的映射/无法匹配等' if needs_filtering else '无法映射原因'}"
        }}
    }},
    "statistics": {{
        "total_columns": {column_count},
        "mapped_count": 数字,  // {'应该≤19' if needs_filtering else '成功映射数'}
        {'filtered_count": 数字,  // 被筛选掉的列数' if needs_filtering else '"unmapped_count": 数字  // 无法映射数'}
        "average_confidence": 数字  // 平均置信度
    }}
}}

请立即分析并返回{'智能筛选后的' if needs_filtering else ''}标准化映射结果。"""
        
        return prompt
    
    async def standardize_column_names(self, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        调用AI进行列名标准化（支持智能筛选）
        
        Args:
            column_mapping: {Excel列标识: 列名} 的字典
            
        Returns:
            标准化结果
        """
        prompt = self.build_smart_standardization_prompt(column_mapping)
        
        messages = [
            {
                "role": "system",
                "content": "你是专业的数据分析专家，精通CSV列名标准化和智能筛选。总是返回有效的JSON格式。"
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
                    
                    # 验证映射数量（最多19个）
                    mapping_count = len(parsed.get("column_mapping", {}))
                    if mapping_count > 19:
                        logger.warning(f"AI返回了{mapping_count}个映射，超过19个限制")
                        # 只保留置信度最高的19个
                        scores = parsed.get("confidence_scores", {})
                        sorted_mappings = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:19]
                        filtered_mapping = {k: parsed["column_mapping"][k] for k, _ in sorted_mappings}
                        parsed["column_mapping"] = filtered_mapping
                        parsed["statistics"]["mapped_count"] = 19
                    
                    return {
                        "success": True,
                        "result": parsed,
                        "original_mapping": column_mapping
                    }
            except Exception as e:
                logger.error(f"解析AI响应失败: {e}")
                return {"success": False, "error": str(e)}
        
        return result
    
    def apply_standardization_to_simplified_file(self, 
                                                comparison_file_path: str,
                                                standardization_result: Dict[str, Any],
                                                output_path: str = None) -> Dict[str, Any]:
        """
        将标准化结果应用到简化的CSV对比文件
        
        Args:
            comparison_file_path: 原始简化CSV对比结果文件路径
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
        
        # 创建标准化后的列映射
        standardized_columns = {}
        for col_id, original_name in data.get("modified_columns", {}).items():
            if col_id in column_name_mapping:
                standardized_columns[col_id] = column_name_mapping[col_id]
            else:
                # 保留未映射的列（如果被筛选掉）
                standardized_columns[col_id] = original_name
        
        # 更新数据
        data["standardized_columns"] = standardized_columns
        data["original_modified_columns"] = data.get("modified_columns", {})
        data["modified_columns"] = standardized_columns
        
        # 添加标准化元数据
        data["standardization_metadata"] = {
            "standardized_at": datetime.now().isoformat(),
            "column_mapping": column_name_mapping,
            "statistics": standardization_result["result"].get("statistics", {}),
            "filtered_out": standardization_result["result"].get("filtered_out", {}),
            "confidence_scores": standardization_result["result"].get("confidence_scores", {})
        }
        
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
            "statistics": standardization_result["result"].get("statistics", {}),
            "filtered_count": len(standardization_result["result"].get("filtered_out", {}))
        }
    
    async def process_simplified_comparison_file(self, comparison_file_path: str) -> Dict[str, Any]:
        """
        处理简化CSV对比结果文件的完整流程
        
        Args:
            comparison_file_path: 简化CSV对比结果文件路径
            
        Returns:
            处理结果
        """
        logger.info(f"开始处理简化格式文件: {comparison_file_path}")
        
        try:
            # 步骤1：提取修改列信息
            column_mapping = self.extract_columns_from_simplified_comparison(
                comparison_file_path
            )
            
            if not column_mapping:
                return {"success": False, "error": "未找到修改列"}
            
            # 步骤2：调用AI标准化（支持智能筛选）
            standardization_result = await self.standardize_column_names(column_mapping)
            
            if not standardization_result.get("success"):
                return standardization_result
            
            # 步骤3：应用标准化
            result = self.apply_standardization_to_simplified_file(
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
                self.process_simplified_comparison_file(comparison_file_path)
            )
        finally:
            loop.close()


# 测试代码
if __name__ == "__main__":
    import sys
    
    # 测试简化格式文件
    test_file = "/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250905_224147.json"
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    if not Path(test_file).exists():
        print(f"文件不存在: {test_file}")
        sys.exit(1)
    
    api_key = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
    
    processor = ColumnStandardizationProcessorV3(api_key)
    
    # 先测试列提取
    columns = processor.extract_columns_from_simplified_comparison(test_file)
    print(f"\n📊 提取到的修改列 ({len(columns)}个):")
    for col_id, col_name in sorted(columns.items()):
        print(f"  {col_id}: {col_name}")
    
    # 测试完整处理
    print("\n🚀 开始标准化处理...")
    result = processor.sync_process_file(test_file)
    
    if result.get("success"):
        print("\n✅ 处理成功！")
        print(f"输入文件: {result['input_file']}")
        print(f"输出文件: {result['output_file']}")
        print(f"\n统计信息:")
        print(f"  映射列数: {result['statistics'].get('mapped_count', 0)}")
        print(f"  筛选掉列数: {result.get('filtered_count', 0)}")
        print(f"\n列映射:")
        for col_id, standard_name in result['column_mapping'].items():
            print(f"  列{col_id} → {standard_name}")
    else:
        print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")