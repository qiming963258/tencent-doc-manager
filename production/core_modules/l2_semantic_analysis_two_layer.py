# -*- coding: utf-8 -*-
"""
L2语义分析两层架构模块 - 真实AI分析实现
在列名标准化之后运行，对L2级别的修改进行语义分析
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class L2ModificationRequest:
    """L2修改分析请求"""
    modification_id: str
    column_name: str
    old_value: str
    new_value: str
    table_name: str
    row_index: int
    cell: str


@dataclass 
class L2AnalysisResult:
    """L2分析结果"""
    modification_id: str
    layer1_judgment: str  # SAFE/RISKY/UNSURE
    layer1_confidence: float
    layer1_reason: str
    needs_layer2: bool
    layer2_result: Optional[Dict] = None
    final_decision: str = ""  # APPROVE/REVIEW/REJECT
    approval_required: bool = False


class L2SemanticAnalyzer:
    """L2语义分析器 - 两层架构实现"""
    
    def __init__(self, api_client=None):
        """
        初始化分析器
        Args:
            api_client: DeepSeek或Claude的API客户端
        """
        self.api_client = api_client
        
        # L2列定义（中等风险列）
        self.L2_COLUMNS = [
            "项目类型", "具体计划内容", "邓总指导登记（日更新）",
            "负责人", "协助人", "监督人", "形成计划清单"
        ]
        
        # 初始化输出目录
        self.ensure_output_directories()
    
    def ensure_output_directories(self):
        """确保输出目录存在"""
        directories = [
            "semantic_results/2025_W36",
            "semantic_results/latest",
            "approval_workflows/pending",
            "approval_workflows/approved",
            "approval_workflows/rejected"
        ]
        for dir_path in directories:
            os.makedirs(dir_path, exist_ok=True)
    
    def build_layer1_prompt(self, modifications: List[Dict]) -> str:
        """
        构建第一层快速筛选提示词
        """
        prompt = """你是项目管理专家。快速判断以下修改的风险等级。

修改列表：
"""
        for i, mod in enumerate(modifications, 1):
            old_preview = mod['old_value'][:30] if mod['old_value'] else "[空]"
            new_preview = mod['new_value'][:30] if mod['new_value'] else "[空]"
            prompt += f"{i}. {mod['column_name']}: '{old_preview}' → '{new_preview}'\n"
        
        prompt += """
对每个修改回答：
ID|判断(SAFE/RISKY/UNSURE)|置信度(0-100)|理由(5字内)

示例：
1|SAFE|95|日期微调
2|RISKY|85|删除内容
3|UNSURE|40|语义变化"""
        
        return prompt
    
    def build_layer2_prompt(self, modification: Dict) -> str:
        """
        构建第二层深度分析提示词
        """
        prompt = f"""你是项目风险评估专家，负责深度分析表格修改的风险。

## 待分析修改
单元格：{modification['cell']}
列名：{modification['column_name']}
原值：{modification['old_value'][:200]}
新值：{modification['new_value'][:200]}

## 分析要求
1. 变化本质分析（形式调整/内容补充/内容删减/性质改变/状态改变）
2. 影响评估（1-10分）：
   - 对项目目标的影响
   - 对执行计划的影响
   - 对团队协作的影响
   - 对交付时间的影响

3. 针对"{modification['column_name']}"的特殊检查
4. 风险等级判断（LOW/MEDIUM/HIGH/CRITICAL）

## 输出格式（JSON）
{{
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "decision": "APPROVE/CONDITIONAL/REVIEW/REJECT",
    "confidence": 0-100,
    "key_risks": ["风险1", "风险2"],
    "recommendation": "具体建议"
}}"""
        
        return prompt
    
    def parse_layer1_response(self, response: str, modifications: List[Dict]) -> List[L2AnalysisResult]:
        """解析第一层响应"""
        results = []
        lines = response.strip().split('\n')
        
        for i, mod in enumerate(modifications):
            # 默认值（防止解析失败）
            result = L2AnalysisResult(
                modification_id=f"M{i+1:03d}",
                layer1_judgment="UNSURE",
                layer1_confidence=50,
                layer1_reason="需要分析",
                needs_layer2=True
            )
            
            # 尝试解析AI响应
            for line in lines:
                if line.startswith(f"{i+1}|"):
                    parts = line.split('|')
                    if len(parts) >= 4:
                        result.layer1_judgment = parts[1].strip()
                        result.layer1_confidence = float(parts[2].strip())
                        result.layer1_reason = parts[3].strip()
                        
                        # 判断是否需要第二层
                        result.needs_layer2 = (
                            result.layer1_judgment in ['RISKY', 'UNSURE'] or
                            (result.layer1_judgment == 'SAFE' and result.layer1_confidence < 70)
                        )
                        break
            
            results.append(result)
        
        return results
    
    def parse_layer2_response(self, response: str) -> Dict:
        """解析第二层响应"""
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 默认值
        return {
            "risk_level": "MEDIUM",
            "decision": "REVIEW",
            "confidence": 70,
            "key_risks": ["需要人工审核"],
            "recommendation": "建议人工确认修改合理性"
        }

    def build_batch_layer2_prompt(self, modifications: List[Dict]) -> str:
        """构建批量第二层深度分析提示词"""
        prompt = f"""你是项目风险评估专家，负责批量深度分析表格修改的风险。

## 待分析修改列表
分析以下{len(modifications)}个修改，为每个修改返回独立的风险评估结果。

"""
        for i, mod in enumerate(modifications):
            prompt += f"""
### 修改 {i+1}
单元格：{mod['cell']}
列名：{mod['column_name']}
原值：{mod['old_value'][:100]}
新值：{mod['new_value'][:100]}

"""

        prompt += """
## 分析要求
对每个修改进行独立评估，返回JSON数组格式：

```json
[
    {
        "index": 1,
        "risk_level": "LOW/MEDIUM/HIGH",
        "decision": "APPROVE/REVIEW/REJECT",
        "confidence": 85,
        "reason": "简要说明"
    },
    ...
]
```

## 决策标准
- APPROVE: 低风险，可自动批准
- REVIEW: 中等风险，需人工审查
- REJECT: 高风险，建议拒绝

请直接返回JSON数组，不要包含其他内容。"""

        return prompt

    def parse_batch_layer2_response(self, response: str, expected_count: int) -> List[Dict]:
        """解析批量第二层响应"""
        results = []

        try:
            # 尝试从响应中提取JSON数组
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                parsed_results = json.loads(json_match.group())

                # 确保结果按索引排序
                parsed_results.sort(key=lambda x: x.get('index', 0))

                for item in parsed_results:
                    results.append({
                        "risk_level": item.get("risk_level", "MEDIUM"),
                        "decision": item.get("decision", "REVIEW"),
                        "confidence": item.get("confidence", 70),
                        "reason": item.get("reason", "需要人工审查")
                    })
        except Exception as e:
            logger.warning(f"批量响应解析失败: {e}")

        # 如果结果数量不足，用默认值填充
        while len(results) < expected_count:
            results.append({
                "risk_level": "MEDIUM",
                "decision": "REVIEW",
                "confidence": 70,
                "reason": "无法解析响应"
            })

        return results[:expected_count]

    def analyze_modifications(self, modifications: List[Dict]) -> Dict:
        """
        分析L2修改（主入口）
        Args:
            modifications: 标准化后的修改列表
        Returns:
            完整的分析结果
        """
        start_time = time.time()
        
        # 数据格式兼容性处理
        for i, mod in enumerate(modifications):
            if 'old' in mod and 'old_value' not in mod:
                mod['old_value'] = mod['old']
            if 'new' in mod and 'new_value' not in mod:
                mod['new_value'] = mod['new']
            if 'column' in mod and 'column_name' not in mod:
                mod['column_name'] = mod['column']
            if 'cell' not in mod:
                row = mod.get('row', i+1)
                mod['cell'] = f"A{row}"
        
        # 筛选L2列的修改
        l2_modifications = [
            mod for mod in modifications 
            if mod.get('column_name') in self.L2_COLUMNS
        ]
        
        if not l2_modifications:
            logger.info("没有L2列的修改需要分析")
            return {"results": [], "summary": {}}
        
        logger.info(f"开始分析 {len(l2_modifications)} 个L2修改")
        
        # 第一层：批量快速筛选
        layer1_results = self._run_layer1_analysis(l2_modifications)
        
        # 第二层：深度分析需要的项
        final_results = self._run_layer2_analysis(l2_modifications, layer1_results)
        
        # 生成报告
        report = self._generate_report(
            final_results, 
            l2_modifications,
            time.time() - start_time
        )
        
        # 保存报告文件
        report_path = self._save_report(report)
        workflow_path = self._create_workflow(report)
        
        report['files_generated'] = {
            'semantic_report': report_path,
            'workflow_file': workflow_path
        }
        
        return report
    
    def _run_layer1_analysis(self, modifications: List[Dict]) -> List[L2AnalysisResult]:
        """运行第一层分析"""
        # 分批处理（每批20个）
        batch_size = 20
        all_results = []
        
        for i in range(0, len(modifications), batch_size):
            batch = modifications[i:i+batch_size]
            
            # 必须使用API，不允许降级
            if not self.api_client:
                raise Exception("L2语义分析必须使用API客户端")
            
            # 真实API调用（必须成功）
            prompt = self.build_layer1_prompt(batch)
            try:
                response = self.api_client.call_api(prompt, max_tokens=200)
                results = self.parse_layer1_response(response, batch)
            except Exception as e:
                logger.error(f"第一层API调用失败: {e}")
                # 不允许降级，必须报错
                raise Exception(f"L2第一层API调用失败，无法继续: {e}")
            
            all_results.extend(results)
        
        logger.info(f"第一层分析完成: {len(all_results)} 项")
        return all_results
    
    
    def _run_layer2_analysis(self, modifications: List[Dict], layer1_results: List[L2AnalysisResult]) -> List[L2AnalysisResult]:
        """运行第二层分析（批处理版本）"""
        # 收集需要第二层分析的项
        layer2_items = []
        layer2_indices = []

        for i, result in enumerate(layer1_results):
            if result.needs_layer2:
                layer2_items.append(modifications[i])
                layer2_indices.append(i)
            else:
                # 第一层通过，直接批准
                result.final_decision = 'APPROVE'
                result.approval_required = False

        if not layer2_items:
            logger.info("所有项第一层通过，无需第二层分析")
            return layer1_results

        logger.info(f"需要第二层分析的项数: {len(layer2_items)}")

        # 必须使用API，不允许降级
        if not self.api_client:
            raise Exception("L2第二层分析必须使用API客户端")

        # 批处理第二层分析（扩大批次大小到50）
        batch_size = 50  # 增加批次大小以减少API调用

        for batch_start in range(0, len(layer2_items), batch_size):
            batch_end = min(batch_start + batch_size, len(layer2_items))
            batch_mods = layer2_items[batch_start:batch_end]
            batch_indices = layer2_indices[batch_start:batch_end]

            # 构建批量分析提示
            batch_prompt = self.build_batch_layer2_prompt(batch_mods)

            try:
                # 批量API调用
                response = self.api_client.call_api(batch_prompt, max_tokens=2000)
                batch_results = self.parse_batch_layer2_response(response, len(batch_mods))

                # 更新结果
                for j, idx in enumerate(batch_indices):
                    if j < len(batch_results):
                        result = layer1_results[idx]
                        result.layer2_result = batch_results[j]
                        result.final_decision = result.layer2_result['decision']
                        result.approval_required = result.final_decision in ['REVIEW', 'REJECT']
                    else:
                        # 如果解析失败，默认需要审查
                        result = layer1_results[idx]
                        result.final_decision = 'REVIEW'
                        result.approval_required = True

            except Exception as e:
                logger.error(f"第二层批量API调用失败: {e}")
                # 为这批次的所有项设置为需要审查
                for idx in batch_indices:
                    result = layer1_results[idx]
                    result.final_decision = 'REVIEW'
                    result.approval_required = True
                    result.layer2_result = {'decision': 'REVIEW', 'reason': f'API调用失败: {str(e)}'}

        logger.info(f"第二层分析完成: {len(layer2_items)} 项")
        return layer1_results
    
    
    def _generate_report(self, results: List[L2AnalysisResult], modifications: List[Dict], processing_time: float) -> Dict:
        """生成分析报告"""
        # 统计
        approved = sum(1 for r in results if r.final_decision == 'APPROVE')
        review_required = sum(1 for r in results if r.final_decision == 'REVIEW')
        rejected = sum(1 for r in results if r.final_decision == 'REJECT')
        layer1_passed = sum(1 for r in results if not r.needs_layer2)
        layer2_analyzed = sum(1 for r in results if r.needs_layer2)
        
        # 构建详细结果
        detailed_results = []
        for i, result in enumerate(results):
            mod = modifications[i]
            detailed_results.append({
                "modification_id": result.modification_id,
                "cell": mod.get('cell', 'N/A'),
                "column": mod.get('column_name'),
                "old_value": mod.get('old_value', '')[:100],
                "new_value": mod.get('new_value', '')[:100],
                "layer1_result": {
                    "judgment": result.layer1_judgment,
                    "confidence": result.layer1_confidence,
                    "reason": result.layer1_reason
                },
                "layer2_result": result.layer2_result,
                "final_decision": result.final_decision,
                "approval_required": result.approval_required
            })
        
        report = {
            "metadata": {
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_modifications": len(modifications),
                "layer1_passed": layer1_passed,
                "layer2_analyzed": layer2_analyzed,
                "processing_time": f"{processing_time:.1f}s"
            },
            "results": detailed_results,
            "summary": {
                "approved": approved,
                "conditional": sum(1 for r in results if r.final_decision == 'CONDITIONAL'),
                "review_required": review_required,
                "rejected": rejected,
                "risk_distribution": {
                    "LOW": approved,
                    "MEDIUM": max(0, review_required // 2),
                    "HIGH": max(0, review_required - review_required // 2),
                    "CRITICAL": rejected
                }
            }
        }
        
        return report
    
    def _save_report(self, report: Dict) -> str:
        """保存报告到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"semantic_analysis_L2_{timestamp}.json"
        filepath = os.path.join("semantic_results", "2025_W36", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告已保存: {filepath}")
        return filepath
    
    def _create_workflow(self, report: Dict) -> str:
        """创建审批工作流文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_id = f"WF-L2-{timestamp}"
        
        # 提取需要审批的项
        pending_approvals = [
            r for r in report['results'] 
            if r['approval_required']
        ]
        
        workflow = {
            "workflow_id": workflow_id,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pending_approvals": pending_approvals,
            "auto_approved": [
                r for r in report['results'] 
                if not r['approval_required']
            ]
        }
        
        filename = f"workflow_{workflow_id}.json"
        filepath = os.path.join("approval_workflows", "pending", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
        
        logger.info(f"工作流已创建: {filepath}")
        return filepath
    
    def analyze_single_modification(self, modification: Dict) -> Dict:
        """
        分析单个修改（为integrated_scorer提供的接口）
        
        Args:
            modification: 单个修改数据
            
        Returns:
            分析结果字典，包含layer1和layer2结果
        """
        # 数据格式兼容性处理
        if 'old' in modification and 'old_value' not in modification:
            modification['old_value'] = modification['old']
        if 'new' in modification and 'new_value' not in modification:
            modification['new_value'] = modification['new']
        if 'column' in modification and 'column_name' not in modification:
            modification['column_name'] = modification['column']
        if 'cell' not in modification:
            row = modification.get('row', 1)
            modification['cell'] = f"A{row}"
        
        # 确保修改是L2列
        if modification.get('column_name') not in self.L2_COLUMNS:
            return {
                'layer1_result': {'judgment': 'N/A', 'confidence': 0},
                'layer2_result': None,
                'final_decision': 'N/A',
                'error': 'Not an L2 column'
            }
        
        # 调用批量分析接口
        result = self.analyze_modifications([modification])
        
        # 提取单个结果
        if result and result.get('results') and len(result['results']) > 0:
            single_result = result['results'][0]
            
            # 格式化返回结果
            return {
                'layer1_result': single_result.get('layer1_result', {}),
                'layer2_result': single_result.get('layer2_result'),
                'final_decision': single_result.get('final_decision', 'UNSURE'),
                'approval_required': single_result.get('approval_required', False),
                'modification_id': single_result.get('modification_id'),
                'analysis_time': result['metadata'].get('analysis_time')
            }
        else:
            # 不允许任何降级，必须报错
            error_msg = f"L2语义分析失败，无法获取有效结果"
            logger.error(error_msg)
            raise Exception(error_msg)


# 集成函数 - 供主程序调用
def analyze_l2_modifications_after_standardization(standardized_data: Dict, api_client=None) -> Dict:
    """
    在列名标准化后分析L2修改
    
    Args:
        standardized_data: 列名标准化后的数据
        api_client: AI API客户端（DeepSeek或Claude）
    
    Returns:
        L2语义分析结果
    """
    analyzer = L2SemanticAnalyzer(api_client)
    
    # 从标准化数据中提取修改列表
    modifications = standardized_data.get('modifications', [])
    
    # 执行分析
    result = analyzer.analyze_modifications(modifications)
    
    return result