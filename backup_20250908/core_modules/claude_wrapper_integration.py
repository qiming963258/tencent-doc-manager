#!/usr/bin/env python3
"""
Claude封装程序集成适配器
将Claude Mini Wrapper API集成到现有的腾讯文档管理系统中
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ClaudeWrapperConfig:
    """Claude封装程序配置"""
    base_url: str = "http://localhost:8081"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

class ClaudeWrapperClient:
    """Claude封装程序客户端适配器"""
    
    def __init__(self, config: ClaudeWrapperConfig = None):
        self.config = config or ClaudeWrapperConfig()
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def check_health(self) -> Dict[str, Any]:
        """检查Claude封装服务健康状态"""
        try:
            async with self.session.get(f"{self.config.base_url}/health") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def analyze_risk(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """风险评估分析"""
        payload = {
            "content": content,
            "analysis_type": "risk_assessment"
        }
        
        if context:
            payload["context"] = context
            
        return await self._call_analyze_api(payload)
    
    async def analyze_modification_batch(self, modifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量修改分析"""
        results = []
        
        for mod in modifications:
            try:
                content = self._format_modification_for_analysis(mod)
                context = {
                    "table_name": mod.get("table_name", ""),
                    "column_name": mod.get("column_name", ""),
                    "modification_id": mod.get("modification_id", "")
                }
                
                result = await self.analyze_risk(content, context)
                result["modification_id"] = mod.get("modification_id")
                results.append(result)
                
                # 避免API频率限制
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"批量分析失败 {mod.get('modification_id')}: {e}")
                results.append({
                    "modification_id": mod.get("modification_id"),
                    "error": str(e),
                    "analysis_type": "risk_assessment",
                    "result": "分析失败，建议人工审核",
                    "confidence": 0.0,
                    "risk_level": "L2"
                })
        
        return results
    
    async def _call_analyze_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """调用分析API（带重试机制）"""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.post(
                    f"{self.config.base_url}/analyze",
                    json=payload
                ) as resp:
                    
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        raise Exception(f"HTTP {resp.status}: {error_text}")
                        
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                else:
                    break
        
        # 重试失败，返回安全默认值
        return {
            "error": str(last_error),
            "analysis_type": payload.get("analysis_type"),
            "result": "API调用失败，建议人工审核",
            "confidence": 0.0,
            "risk_level": "L2",
            "timestamp": time.time()
        }
    
    def _format_modification_for_analysis(self, modification: Dict[str, Any]) -> str:
        """格式化修改信息为分析内容"""
        table_name = modification.get("table_name", "未知表格")
        column_name = modification.get("column_name", "未知字段")
        original_value = modification.get("original_value", "")
        new_value = modification.get("new_value", "")
        
        content = f"在{table_name}中，{column_name}字段从'{original_value}'修改为'{new_value}'"
        
        # 添加上下文信息
        if modification.get("change_context"):
            content += f"。修改背景：{modification['change_context']}"
            
        return content

class AISemanticAnalysisOrchestrator:
    """AI语义分析编排器 - 使用Claude封装程序"""
    
    def __init__(self, claude_wrapper_url: str = "http://localhost:8081"):
        self.claude_client = ClaudeWrapperClient(
            ClaudeWrapperConfig(base_url=claude_wrapper_url)
        )
        
    async def analyze_modifications_with_caching(
        self, 
        modifications: List[Any], 
        use_cache: bool = True
    ) -> List[Any]:
        """
        使用缓存分析修改项
        
        Args:
            modifications: ModificationAnalysisRequest对象列表（或兼容字典）
            use_cache: 是否使用缓存
            
        Returns:
            ModificationAnalysisResult对象列表（或兼容字典）
        """
        
        # 转换输入格式
        modification_dicts = []
        for mod in modifications:
            if hasattr(mod, '__dict__'):
                # 如果是dataclass对象
                mod_dict = mod.__dict__
            else:
                # 如果是字典
                mod_dict = mod
                
            modification_dicts.append({
                "modification_id": mod_dict.get("modification_id"),
                "table_name": mod_dict.get("table_name"),
                "column_name": mod_dict.get("column_name"),
                "original_value": mod_dict.get("original_value"),
                "new_value": mod_dict.get("new_value"),
                "change_context": mod_dict.get("change_context")
            })
        
        # 调用Claude封装程序
        async with self.claude_client as client:
            # 检查服务健康状态
            health = await client.check_health()
            if health.get("status") != "healthy":
                logger.warning(f"Claude封装服务状态异常: {health}")
            
            # 批量分析
            results = await client.analyze_modification_batch(modification_dicts)
        
        # 转换输出格式为期望的ModificationAnalysisResult格式
        formatted_results = []
        for result in results:
            formatted_result = self._convert_wrapper_result_to_standard(result)
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _convert_wrapper_result_to_standard(self, wrapper_result: Dict[str, Any]) -> Any:
        """将Claude封装程序结果转换为标准格式"""
        
        # 解析风险评估结果
        analysis_result = wrapper_result.get("result", "")
        confidence = wrapper_result.get("confidence", 0.0)
        risk_level = wrapper_result.get("risk_level", "L2")
        
        # 从分析结果中提取结构化信息
        recommendation = "REVIEW"  # 默认需要审核
        business_impact = "MEDIUM"  # 默认中等影响
        suggested_action = "需要人工审核确认"
        risk_factors = ["自动检测的风险因素"]
        approval_conditions = ["人工确认业务合理性"]
        
        if "建议操作" in analysis_result:
            if "批准" in analysis_result or "通过" in analysis_result:
                recommendation = "APPROVE"
            elif "拒绝" in analysis_result or "禁止" in analysis_result:
                recommendation = "REJECT"
        
        if "高风险" in analysis_result or "严重" in analysis_result:
            business_impact = "HIGH"
        elif "低风险" in analysis_result or "轻微" in analysis_result:
            business_impact = "LOW"
        
        # 创建结果对象（兼容原有数据结构）
        try:
            # 尝试导入原有的数据类
            from claude_semantic_analysis import ModificationAnalysisResult
            return ModificationAnalysisResult(
                modification_id=wrapper_result.get("modification_id", ""),
                recommendation=recommendation,
                confidence=confidence,
                reasoning=analysis_result,
                business_impact=business_impact,
                suggested_action=suggested_action,
                risk_factors=risk_factors,
                approval_conditions=approval_conditions,
                analysis_timestamp=datetime.now().isoformat(),
                ai_model="claude-wrapper"
            )
        except ImportError:
            # 如果无法导入，返回字典格式
            return {
                "modification_id": wrapper_result.get("modification_id", ""),
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": analysis_result,
                "business_impact": business_impact,
                "suggested_action": suggested_action,
                "risk_factors": risk_factors,
                "approval_conditions": approval_conditions,
                "analysis_timestamp": datetime.now().isoformat(),
                "ai_model": "claude-wrapper"
            }
    
    def generate_analysis_summary(self, analysis_results: List[Any]) -> Dict[str, Any]:
        """生成分析摘要"""
        if not analysis_results:
            return {"total_analyzed": 0, "summary": "无分析结果"}
        
        total_count = len(analysis_results)
        recommendations = []
        confidence_scores = []
        business_impacts = []
        
        for result in analysis_results:
            if hasattr(result, '__dict__'):
                result_dict = result.__dict__
            else:
                result_dict = result
                
            recommendations.append(result_dict.get("recommendation", "REVIEW"))
            confidence_scores.append(result_dict.get("confidence", 0.0))
            business_impacts.append(result_dict.get("business_impact", "MEDIUM"))
        
        # 统计分析
        from collections import Counter
        rec_counts = Counter(recommendations)
        impact_counts = Counter(business_impacts)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            "total_analyzed": total_count,
            "recommendation_distribution": dict(rec_counts),
            "business_impact_distribution": dict(impact_counts),
            "average_confidence": avg_confidence,
            "high_confidence_rejections": sum(1 for r, c in zip(recommendations, confidence_scores) 
                                            if r == "REJECT" and c > 0.8),
            "summary": f"分析了{total_count}个修改项，平均置信度{avg_confidence:.2f}"
        }

# 兼容性导入 - 支持现有系统直接导入
try:
    from claude_semantic_analysis import ModificationAnalysisRequest, ModificationAnalysisResult
except ImportError:
    # 如果原模块不存在，提供基本的数据结构
    pass