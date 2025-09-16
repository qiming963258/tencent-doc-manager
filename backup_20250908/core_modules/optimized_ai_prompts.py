# -*- coding: utf-8 -*-
"""
优化的AI提示词设计方案 - 用于CSV对比的列名归类和L2级别语义分析
基于2025年最佳实践设计
"""

import json
from typing import Dict, List, Any, Tuple


class OptimizedPromptEngine:
    """优化的提示词引擎 - 专注于CSV对比的语义分析"""
    
    def __init__(self):
        # 列名分类规则
        self.column_categories = {
            "人员类": {
                "patterns": ["负责人", "协助人", "监督人", "执行人", "审批人"],
                "risk_level": "L2",
                "sensitivity": "HIGH"
            },
            "时间类": {
                "patterns": ["日期", "时间", "截止", "开始", "结束", "更新时间"],
                "risk_level": "L3",
                "sensitivity": "MEDIUM"
            },
            "内容类": {
                "patterns": ["计划", "内容", "描述", "说明", "备注", "详情"],
                "risk_level": "L2",
                "sensitivity": "MEDIUM"
            },
            "状态类": {
                "patterns": ["状态", "进度", "阶段", "完成度"],
                "risk_level": "L3",
                "sensitivity": "LOW"
            },
            "标识类": {
                "patterns": ["ID", "编号", "序号", "代码"],
                "risk_level": "L1",
                "sensitivity": "CRITICAL"
            },
            "数值类": {
                "patterns": ["价格", "数量", "库存", "金额", "成本"],
                "risk_level": "L2",
                "sensitivity": "HIGH"
            }
        }
    
    def build_column_categorization_prompt(self, column_names: List[str]) -> str:
        """
        构建列名分类提示词
        使用2025年最佳实践：结构化输出、清晰分隔符、JSON格式
        """
        prompt = f"""<task>
分析和分类以下CSV表格的列名，判断每个列的业务类型和风险等级。
</task>

<context>
这是一个企业级项目管理系统的CSV表格，需要对每个列进行智能分类。
</context>

<column_list>
{json.dumps(column_names, ensure_ascii=False, indent=2)}
</column_list>

<classification_rules>
人员类: 涉及人员分配和责任，需要审批 (L2级别)
时间类: 时间相关字段，可以自由修改 (L3级别)
内容类: 业务内容描述，需要语义审核 (L2级别)
状态类: 状态和进度信息，低风险 (L3级别)
标识类: 唯一标识符，禁止修改 (L1级别)
数值类: 数值和金额，需要合理性检查 (L2级别)
</classification_rules>

<output_format>
请以JSON格式返回分类结果，每个列包含以下信息：
{{
    "column_name": "列名",
    "category": "分类名称",
    "risk_level": "L1/L2/L3",
    "sensitivity": "CRITICAL/HIGH/MEDIUM/LOW",
    "change_rules": "修改规则说明"
}}
</output_format>

<requirements>
1. 必须为每个列名提供分类
2. 使用精确的类别名称
3. 基于业务逻辑判断风险等级
4. 输出必须是有效的JSON格式
</requirements>"""
        
        return prompt
    
    def build_l2_semantic_comparison_prompt(self, comparison_data: Dict[str, Any]) -> str:
        """
        构建L2级别语义对比提示词
        专注于单元格级别的变更分析
        """
        # 提取关键信息
        column_name = comparison_data.get("column_name", "未知")
        baseline_value = comparison_data.get("baseline_value", "")
        target_value = comparison_data.get("target_value", "")
        row_context = comparison_data.get("row_context", {})
        
        # 判断列类别
        column_category = self._identify_column_category(column_name)
        
        prompt = f"""<task>
分析CSV表格中L2级别字段的修改，评估变更的合理性和风险。
</task>

<modification_details>
列名: {column_name}
列类别: {column_category}
原始值: "{baseline_value}"
修改后: "{target_value}"
所在行: 第{comparison_data.get('row_number', '未知')}行
</modification_details>

<row_context>
{json.dumps(row_context, ensure_ascii=False, indent=2)}
</row_context>

<analysis_criteria>
1. 语义一致性: 修改是否保持业务语义的连贯性
2. 数据合理性: 新值是否在合理范围内
3. 上下文相关性: 与同行其他字段的关联性
4. 业务影响: 修改对业务流程的潜在影响
</analysis_criteria>

<scoring_rules>
- 完全合理且无风险: 0.9-1.0
- 基本合理但需注意: 0.7-0.89
- 存在问题需审核: 0.4-0.69
- 高风险需拒绝: 0.0-0.39
</scoring_rules>

<output_format>
{{
    "decision": "APPROVE/REVIEW/REJECT",
    "confidence_score": 0.0-1.0,
    "semantic_analysis": {{
        "change_type": "内容更新/格式调整/错误修正/业务变更",
        "consistency_check": "一致/部分一致/不一致",
        "impact_level": "LOW/MEDIUM/HIGH"
    }},
    "reasoning": "详细分析理由",
    "risk_factors": ["识别的风险点"],
    "recommendations": ["具体建议"]
}}
</output_format>

<instructions>
1. 使用简洁清晰的语言
2. 基于具体数据提供分析
3. 避免模糊的判断
4. 必须输出有效JSON
</instructions>"""
        
        return prompt
    
    def build_batch_comparison_prompt(self, modifications: List[Dict]) -> str:
        """
        构建批量对比提示词
        使用压缩技术提高效率（基于2025最佳实践）
        """
        # 将修改项按列分组
        grouped_mods = {}
        for mod in modifications:
            col = mod.get("column_name", "未知")
            if col not in grouped_mods:
                grouped_mods[col] = []
            grouped_mods[col].append({
                "row": mod.get("row_number"),
                "old": mod.get("baseline_value"),
                "new": mod.get("target_value")
            })
        
        prompt = f"""<task>
批量分析CSV表格修改项，快速评估风险等级。
</task>

<modifications_summary>
总修改数: {len(modifications)}
涉及列数: {len(grouped_mods)}
</modifications_summary>

<grouped_changes>
{json.dumps(grouped_mods, ensure_ascii=False, indent=2)}
</grouped_changes>

<quick_analysis_rules>
HIGH_RISK: 标识符修改、未授权人员变更、金额异常变化
MEDIUM_RISK: 内容大幅修改、时间逻辑错误、状态回退
LOW_RISK: 格式调整、拼写修正、正常进度更新
</quick_analysis_rules>

<output_format>
{{
    "summary": {{
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
        "auto_approve_count": 0
    }},
    "column_analysis": {{
        "列名": {{
            "risk_level": "HIGH/MEDIUM/LOW",
            "change_pattern": "描述变更模式",
            "action_required": true/false
        }}
    }},
    "critical_findings": ["需要立即关注的问题"],
    "batch_recommendation": "APPROVE_ALL/REVIEW_SELECTED/REJECT_ALL"
}}
</output_format>

<performance_hints>
- 优先识别高风险模式
- 相似修改合并分析
- 跳过明显安全的修改
- 保持输出简洁
</performance_hints>"""
        
        return prompt
    
    def _identify_column_category(self, column_name: str) -> str:
        """识别列的类别"""
        for category, info in self.column_categories.items():
            for pattern in info["patterns"]:
                if pattern in column_name:
                    return category
        return "其他类"
    
    def optimize_prompt(self, original_prompt: str) -> str:
        """
        优化提示词 - 基于2025最佳实践压缩40%
        """
        # 移除冗余空格
        optimized = " ".join(original_prompt.split())
        
        # 使用缩写
        replacements = {
            "分析结果": "结果",
            "详细说明": "说明",
            "具体建议": "建议",
            "风险等级": "风险",
            "修改规则": "规则"
        }
        
        for old, new in replacements.items():
            optimized = optimized.replace(old, new)
        
        return optimized
    
    def create_semantic_hash_key(self, column: str, old_val: str, new_val: str) -> str:
        """
        创建语义哈希键用于缓存
        """
        import hashlib
        
        # 规范化值
        normalized_old = str(old_val).strip().lower()
        normalized_new = str(new_val).strip().lower()
        
        # 判断变更类型
        if not normalized_old and normalized_new:
            change_type = "addition"
        elif normalized_old and not normalized_new:
            change_type = "deletion"
        elif normalized_old == normalized_new:
            change_type = "no_change"
        else:
            # 计算相似度
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, normalized_old, normalized_new).ratio()
            if similarity > 0.8:
                change_type = "minor_edit"
            elif similarity > 0.5:
                change_type = "moderate_edit"
            else:
                change_type = "major_change"
        
        # 生成哈希
        key_components = [
            column,
            change_type,
            str(len(normalized_old)),
            str(len(normalized_new))
        ]
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()


class PromptValidator:
    """提示词验证器 - 确保输出质量"""
    
    @staticmethod
    def validate_json_response(response: str) -> Tuple[bool, Dict[str, Any]]:
        """验证JSON响应格式"""
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return False, {"error": "未找到JSON格式"}
            
            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)
            
            return True, parsed
            
        except json.JSONDecodeError as e:
            return False, {"error": f"JSON解析错误: {str(e)}"}
    
    @staticmethod
    def validate_categorization_result(result: Dict) -> bool:
        """验证分类结果完整性"""
        required_fields = ["column_name", "category", "risk_level", "sensitivity"]
        
        if isinstance(result, list):
            for item in result:
                for field in required_fields:
                    if field not in item:
                        return False
        else:
            for field in required_fields:
                if field not in result:
                    return False
        
        return True
    
    @staticmethod
    def validate_semantic_score(score: float) -> bool:
        """验证语义评分有效性"""
        return 0.0 <= score <= 1.0