# -*- coding: utf-8 -*-
"""
列名标准化提示词设计 - 专门用于将CSV对比结果的列名映射到19个标准列名
单次会话完成，无需上下文记忆
"""

import json
from typing import List, Dict, Any


class ColumnStandardizationPrompt:
    """列名标准化提示词生成器"""
    
    def __init__(self):
        # 19个标准列名（硬编码，与系统保持一致）
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
        
        # 风险等级分类（参考03-列名标准化技术实现规范.md）
        self.risk_levels = {
            "L1": ["来源", "任务发起时间", "目标对齐", "关键KR对齐", "重要程度", "预计完成时间", "完成进度"],
            "L2": ["项目类型", "具体计划内容", "邓总指导登记", "负责人", "协助人", "监督人", "形成计划清单"],
            "L3": ["序号", "复盘时间", "对上汇报", "应用情况", "进度分析总结"]
        }
        
        # 常见变异模式
        self.variation_patterns = {
            "序号": ["序列号", "编号", "ID", "索引", "NO", "No.", "行号"],
            "项目类型": ["项目类别", "项目分类", "类型", "类别", "项目种类"],
            "来源": ["数据来源", "信息来源", "来源渠道", "源头"],
            "任务发起时间": ["发起时间", "任务时间", "开始时间", "创建时间", "发起日期"],
            "目标对齐": ["目标", "对齐目标", "业务目标", "战略对齐"],
            "关键KR对齐": ["KR", "关键结果", "KR对齐", "关键指标"],
            "具体计划内容": ["计划内容", "计划", "内容", "具体内容", "任务内容", "工作内容"],
            "邓总指导登记": ["邓总指导", "领导指导", "指导登记", "上级指导"],
            "负责人": ["责任人", "主负责人", "负责人员", "执行人"],
            "协助人": ["协助人员", "协同人", "配合人", "助理"],
            "监督人": ["监督人员", "监管人", "督导人", "检查人"],
            "重要程度": ["重要性", "优先级", "重要等级", "紧急程度"],
            "预计完成时间": ["完成时间", "截止时间", "预计时间", "结束时间", "deadline"],
            "完成进度": ["进度", "完成度", "进展", "完成百分比", "进度百分比"],
            "形成计划清单": ["计划清单", "清单", "任务清单", "工作清单"],
            "复盘时间": ["复盘日期", "回顾时间", "总结时间", "评审时间"],
            "对上汇报": ["汇报", "向上汇报", "上报", "报告"],
            "应用情况": ["应用", "使用情况", "实施情况", "执行情况"],
            "进度分析总结": ["进度分析", "总结", "分析总结", "进展总结", "情况总结"]
        }
    
    def build_single_session_prompt(self, actual_columns: List[str]) -> str:
        """
        构建单次会话提示词，处理多列/少列情况
        
        Args:
            actual_columns: CSV对比结果中的实际列名列表
            
        Returns:
            完整的提示词字符串
        """
        # 构建变异模式提示
        variation_hints = self._build_variation_hints()
        
        prompt = f"""你是一个专业的列名标准化专家。你的任务是分析CSV表格列名，并生成完整的19列标准化映射结果。

## 核心任务
1. 将实际列名映射到19个标准列名
2. 识别缺失的标准列（标记为空白）
3. 过滤掉无法映射的多余列（丢弃）
4. 最终输出必须包含全部19个标准列的状态

## 19个标准列名（固定顺序，必须全部输出）
{json.dumps(self.standard_columns, ensure_ascii=False, indent=2)}

## 实际列名（共{len(actual_columns)}个）
{json.dumps(actual_columns, ensure_ascii=False, indent=2)}

## 列数情况分析
- 标准列数：19个
- 实际列数：{len(actual_columns)}个
- 状态：{'列数不足，需要识别缺失列' if len(actual_columns) < 19 else '列数过多，需要过滤无关列' if len(actual_columns) > 19 else '列数匹配'}

## 常见变异模式（参考）
{variation_hints}

## 处理策略
### 情况1：实际列少于19个（缺列）
- 识别能映射的列
- 标记缺失的标准列为null或空字符串
- 在missing_standard_columns中列出缺失的标准列名

### 情况2：实际列多于19个（多列）
- 尝试映射所有实际列到标准列
- 无法映射到标准列的列名放入discarded_columns
- 这些列将被完全丢弃，不参与后续对比

### 情况3：实际列等于19个
- 尽可能一对一映射
- 处理可能的重复映射

## 映射规则
1. 精确匹配：完全相同，置信度1.0
2. 变异匹配：已知变异形式，置信度0.8-0.95
3. 语义匹配：语义相似，置信度0.6-0.79
4. 位置匹配：基于位置推测，置信度0.4-0.59
5. 无匹配：无法映射，标记为缺失

## 输出要求（必须包含所有字段）
{{
    "success": true,
    "standard_columns_status": {{
        "序号": "ID",  // 映射到的实际列名，如果缺失则为null
        "项目类型": "项目类别",
        "来源": null,  // 表示这个标准列缺失
        "任务发起时间": null,
        "目标对齐": null,
        // ... 必须包含全部19个标准列
    }},
    "mapping": {{
        "ID": "序号",
        "项目类别": "项目类型"
        // 只包含成功映射的实际列
    }},
    "confidence_scores": {{
        "ID": 0.95,
        "项目类别": 0.90
    }},
    "missing_standard_columns": [
        "来源",
        "任务发起时间",
        "目标对齐"
        // 缺失的标准列列表
    ],
    "discarded_columns": [
        "额外列1",
        "无关列2"
        // 无法映射被丢弃的实际列
    ],
    "statistics": {{
        "total_standard": 19,
        "mapped_count": 映射成功数,
        "missing_count": 缺失标准列数,
        "discarded_count": 丢弃的多余列数
    }}
}}

## 关键要求
1. standard_columns_status必须包含全部19个标准列
2. 缺失的标准列值设为null
3. 多余的实际列放入discarded_columns
4. 输出严格的JSON格式"""
        
        return prompt
    
    def build_batch_mapping_prompt(self, csv_comparison_result: Dict[str, Any]) -> str:
        """
        构建批量映射提示词，处理整个CSV对比结果
        
        Args:
            csv_comparison_result: CSV对比结果字典，包含modified_cells等信息
            
        Returns:
            批量处理的提示词
        """
        # 提取所有涉及的列名
        unique_columns = set()
        
        # 从modified_cells提取列名
        if "details" in csv_comparison_result and "modified_cells" in csv_comparison_result["details"]:
            for cell in csv_comparison_result["details"]["modified_cells"]:
                if "column_name" in cell:
                    unique_columns.add(cell["column_name"])
        
        # 从metadata提取列名
        if "metadata" in csv_comparison_result:
            if "baseline_structure" in csv_comparison_result["metadata"]:
                columns = csv_comparison_result["metadata"]["baseline_structure"].get("column_names", [])
                unique_columns.update(columns)
            if "target_structure" in csv_comparison_result["metadata"]:
                columns = csv_comparison_result["metadata"]["target_structure"].get("column_names", [])
                unique_columns.update(columns)
        
        actual_columns = list(unique_columns)
        
        prompt = f"""分析CSV对比结果并标准化所有列名。

## CSV对比结果统计
- 基线文件列数: {csv_comparison_result.get('metadata', {}).get('baseline_structure', {}).get('columns', '未知')}
- 目标文件列数: {csv_comparison_result.get('metadata', {}).get('target_structure', {}).get('columns', '未知')}
- 总差异数: {csv_comparison_result.get('summary', {}).get('total_differences', 0)}
- 涉及的列名数量: {len(actual_columns)}

## 待标准化的列名
{json.dumps(actual_columns, ensure_ascii=False, indent=2)}

## 19个标准列名
{json.dumps(self.standard_columns, ensure_ascii=False, indent=2)}

## 风险等级分类
L1级（禁止修改）: {json.dumps(self.risk_levels['L1'], ensure_ascii=False)}
L2级（需要审核）: {json.dumps(self.risk_levels['L2'], ensure_ascii=False)}
L3级（自由编辑）: {json.dumps(self.risk_levels['L3'], ensure_ascii=False)}

## 输出格式
{{
    "success": true,
    "mapping": {{实际列名->标准列名映射}},
    "confidence_scores": {{实际列名->置信度}},
    "risk_levels": {{标准列名->风险等级}},
    "statistics": {{
        "total_columns": {len(actual_columns)},
        "mapped_count": 映射成功数量,
        "high_confidence_count": 高置信度数量（>0.8）,
        "low_confidence_count": 低置信度数量（<0.6）
    }}
}}

注意：必须将所有列名映射到19个标准列名之一，不允许使用标准列名之外的名称。"""
        
        return prompt
    
    def build_intelligent_prompt(self, actual_columns: List[str], context: Dict[str, Any] = None) -> str:
        """
        构建智能提示词，包含上下文信息提高映射准确度
        
        Args:
            actual_columns: 实际列名列表
            context: 上下文信息（如表格内容样本）
            
        Returns:
            智能提示词
        """
        # 分析列名特征
        column_features = self._analyze_column_features(actual_columns)
        
        # 生成智能提示
        prompt = f"""执行智能列名标准化映射任务。

## 列名特征分析
{json.dumps(column_features, ensure_ascii=False, indent=2)}

## 实际列名列表
{json.dumps(actual_columns, ensure_ascii=False, indent=2)}

## 标准列名（必须映射到这些）
{json.dumps(self.standard_columns, ensure_ascii=False, indent=2)}

## 智能映射策略
1. **完全匹配**：检查是否与标准列名完全一致
2. **变异识别**：检查是否为已知变异形式
3. **语义分析**：分析业务含义的相似性
4. **关键词匹配**：寻找关键词重叠
5. **位置推断**：基于列的位置推断可能的标准列名

## 特殊处理规则
- 含"时间"、"日期"的优先匹配时间相关标准列
- 含"人"、"负责"、"协助"的优先匹配人员相关标准列
- 含"内容"、"计划"、"任务"的优先匹配内容相关标准列
- 数字类（如"序号"、"ID"、"编号"）映射到"序号"
- 百分比类（如"进度"、"完成度"）映射到"完成进度"

## 输出JSON格式
{{
    "success": true,
    "mapping": {{
        // 所有实际列名到标准列名的映射
    }},
    "confidence_scores": {{
        // 每个映射的置信度（0.0-1.0）
    }},
    "mapping_strategy": {{
        // 每个映射使用的策略说明
    }},
    "quality_metrics": {{
        "average_confidence": 平均置信度,
        "exact_matches": 精确匹配数量,
        "semantic_matches": 语义匹配数量,
        "forced_matches": 强制匹配数量
    }}
}}

必须确保：
1. 每个实际列名都有对应的标准列名
2. 只使用19个预定义的标准列名
3. 输出有效的JSON格式"""
        
        return prompt
    
    def _build_variation_hints(self) -> str:
        """构建变异模式提示"""
        hints = []
        for standard, variations in self.variation_patterns.items():
            hint = f"- {standard}: {', '.join(variations[:3])}..."  # 只显示前3个例子
            hints.append(hint)
        return '\n'.join(hints)
    
    def _analyze_column_features(self, columns: List[str]) -> Dict[str, Any]:
        """分析列名特征"""
        features = {
            "total_columns": len(columns),
            "exact_matches": [],
            "possible_variations": [],
            "unknown_columns": []
        }
        
        for col in columns:
            # 检查精确匹配
            if col in self.standard_columns:
                features["exact_matches"].append(col)
                continue
            
            # 检查是否为已知变异
            found_variation = False
            for standard, variations in self.variation_patterns.items():
                if col in variations:
                    features["possible_variations"].append({
                        "actual": col,
                        "likely_standard": standard,
                        "confidence": "high"
                    })
                    found_variation = True
                    break
            
            if not found_variation:
                features["unknown_columns"].append(col)
        
        return features
    
    def build_csv_comparison_standardization_prompt(self, csv_comparison_result: Dict[str, Any]) -> str:
        """
        专门为CSV对比结果构建的标准化提示词
        处理多列/少列情况，确保输出19列标准格式
        
        Args:
            csv_comparison_result: 完整的CSV对比结果
            
        Returns:
            用于标准化的提示词
        """
        # 提取所有涉及的列名
        actual_columns = self._extract_columns_from_comparison(csv_comparison_result)
        
        # 提取差异数据
        modified_cells = csv_comparison_result.get("details", {}).get("modified_cells", [])
        
        prompt = f"""分析CSV对比结果并生成标准化的19列对比输出。

## CSV对比结果概览
- 总差异数: {csv_comparison_result.get('summary', {}).get('total_differences', 0)}
- 修改的单元格数: {len(modified_cells)}
- 实际列数: {len(actual_columns)}
- 需要标准化到: 19列固定格式

## 实际列名（从对比结果提取）
{json.dumps(actual_columns, ensure_ascii=False, indent=2)}

## 19个标准列名（必须全部包含在输出中）
{json.dumps(self.standard_columns, ensure_ascii=False, indent=2)}

## 差异数据样本（前5个）
{json.dumps(modified_cells[:5], ensure_ascii=False, indent=2)}

## 标准化任务
1. **映射实际列到标准列**
   - 将每个实际列名映射到最匹配的标准列名
   - 一个标准列只能映射一个实际列

2. **处理缺失列**
   - 识别哪些标准列没有对应的实际列
   - 这些列在对比结果中应标记为"NO_DATA"或空值

3. **过滤多余列**
   - 识别无法映射到标准列的实际列
   - 这些列的数据将被丢弃，不参与对比

4. **生成19列标准输出**
   - 每行必须包含19个字段
   - 保持标准列名的固定顺序
   - 缺失的列用null填充

## 输出格式要求
{{
    "success": true,
    "standardized_mapping": {{
        // 19个标准列名到实际列名的映射
        "序号": "ID",  // 如果有映射
        "项目类型": "项目类别",
        "来源": null,  // 如果缺失
        "任务发起时间": null,
        // ... 全部19个
    }},
    "column_transformation": {{
        "mapped_columns": {{
            "ID": "序号",
            "项目类别": "项目类型"
        }},
        "missing_standard_columns": ["来源", "任务发起时间", ...],
        "discarded_actual_columns": ["额外列1", "额外列2", ...]
    }},
    "standardized_differences": [
        {{
            "row": 行号,
            "序号": 值或null,
            "项目类型": 值或null,
            "来源": null,
            // ... 全部19个标准列
        }}
    ],
    "quality_metrics": {{
        "coverage_rate": 覆盖率（映射成功的标准列数/19）,
        "data_loss_rate": 数据丢失率（丢弃的实际列数/总实际列数）,
        "confidence_average": 平均置信度
    }}
}}

## 重要规则
1. 输出的standardized_differences中每行必须有19个字段
2. 字段顺序必须与标准列名顺序一致
3. 缺失的标准列统一用null值
4. 被丢弃的实际列数据不出现在输出中"""
        
        return prompt
    
    def _extract_columns_from_comparison(self, comparison_result: Dict[str, Any]) -> List[str]:
        """从CSV对比结果中提取所有列名"""
        columns = set()
        
        # 从metadata提取
        if "metadata" in comparison_result:
            for structure_key in ["baseline_structure", "target_structure"]:
                if structure_key in comparison_result["metadata"]:
                    cols = comparison_result["metadata"][structure_key].get("column_names", [])
                    columns.update(cols)
        
        # 从modified_cells提取
        if "details" in comparison_result:
            if "modified_cells" in comparison_result["details"]:
                for cell in comparison_result["details"]["modified_cells"]:
                    if "column_name" in cell:
                        columns.add(cell["column_name"])
        
        return list(columns)
    
    def process_standardization_result(self, ai_response: Dict[str, Any], original_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理AI返回的标准化结果，生成最终的19列对比输出
        
        Args:
            ai_response: AI返回的标准化映射结果
            original_comparison: 原始CSV对比结果
            
        Returns:
            标准化的19列对比结果
        """
        # 获取映射关系
        standardized_mapping = ai_response.get("standardized_mapping", {})
        
        # 初始化19列输出结构
        standardized_output = {
            "metadata": {
                "standard_columns": self.standard_columns,
                "original_columns": self._extract_columns_from_comparison(original_comparison),
                "mapping": standardized_mapping,
                "timestamp": original_comparison.get("metadata", {}).get("comparison_time")
            },
            "summary": {
                "total_differences": 0,
                "mapped_columns": 0,
                "missing_columns": 0,
                "discarded_columns": 0
            },
            "standardized_differences": []
        }
        
        # 统计映射情况
        for std_col in self.standard_columns:
            if standardized_mapping.get(std_col) is not None:
                standardized_output["summary"]["mapped_columns"] += 1
            else:
                standardized_output["summary"]["missing_columns"] += 1
        
        # 处理差异数据
        modified_cells = original_comparison.get("details", {}).get("modified_cells", [])
        
        # 按行组织差异
        rows_data = {}
        for cell in modified_cells:
            row_num = cell.get("row_number", 0)
            col_name = cell.get("column_name", "")
            
            # 查找这个列名对应的标准列名
            standard_col = None
            for std_col, actual_col in standardized_mapping.items():
                if actual_col == col_name:
                    standard_col = std_col
                    break
            
            if standard_col:  # 只处理能映射到标准列的数据
                if row_num not in rows_data:
                    # 初始化这一行的19列数据
                    rows_data[row_num] = {col: None for col in self.standard_columns}
                    rows_data[row_num]["row_number"] = row_num
                
                # 填充数据
                rows_data[row_num][standard_col] = {
                    "baseline_value": cell.get("baseline_value"),
                    "target_value": cell.get("target_value"),
                    "changed": True
                }
        
        # 转换为列表格式
        for row_num in sorted(rows_data.keys()):
            standardized_output["standardized_differences"].append(rows_data[row_num])
        
        standardized_output["summary"]["total_differences"] = len(standardized_output["standardized_differences"])
        
        return standardized_output


# 使用示例
if __name__ == "__main__":
    # 创建提示词生成器
    prompt_generator = ColumnStandardizationPrompt()
    
    # 示例1：简单映射
    actual_columns = ["ID", "项目类别", "负责人员", "完成度", "内容"]
    prompt = prompt_generator.build_single_session_prompt(actual_columns)
    print("=== 单次会话提示词 ===")
    print(prompt[:500] + "...")  # 只显示前500字符
    
    # 示例2：CSV对比结果映射
    csv_result = {
        "metadata": {
            "baseline_structure": {
                "columns": 6,
                "column_names": ["ID", "产品名称", "价格", "库存", "状态", "更新时间"]
            }
        },
        "summary": {
            "total_differences": 9
        }
    }
    batch_prompt = prompt_generator.build_batch_mapping_prompt(csv_result)
    print("\n=== 批量映射提示词 ===")
    print(batch_prompt[:500] + "...")
    
    # 示例3：智能映射
    context = {"table_name": "项目管理表", "row_count": 100}
    intelligent_prompt = prompt_generator.build_intelligent_prompt(actual_columns, context)
    print("\n=== 智能映射提示词 ===")
    print(intelligent_prompt[:500] + "...")