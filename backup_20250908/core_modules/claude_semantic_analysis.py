# -*- coding: utf-8 -*-
"""
AI语义分析集成模块
基于Claude Sonnet API的L2级别修改智能分析系统
"""

import asyncio
import aiohttp
import json
import hashlib
import redis
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging
from collections import Counter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModificationAnalysisRequest:
    """修改分析请求数据结构"""
    modification_id: str
    column_name: str
    original_value: str
    new_value: str
    table_name: str
    row_index: int
    change_context: Optional[str] = None
    modification_time: Optional[str] = None
    modifier: Optional[str] = None


@dataclass 
class ModificationAnalysisResult:
    """修改分析结果数据结构"""
    modification_id: str
    recommendation: str  # APPROVE | REJECT | REVIEW
    confidence: float  # 0.0 - 1.0
    reasoning: str
    business_impact: str  # HIGH | MEDIUM | LOW
    suggested_action: str
    risk_factors: List[str]
    approval_conditions: List[str]
    analysis_timestamp: str
    ai_model: str = "claude-3-sonnet"
    processing_version: str = "1.0"


class ClaudeAPIException(Exception):
    """Claude API异常"""
    pass


class ClaudeSemanticAnalysisClient:
    """Claude语义分析API客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
        # API调用统计
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "average_response_time": 0
        }
        
        # 重试配置
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 10.0,
            "backoff_factor": 2.0
        }
        
        # 会话配置
        self.timeout = aiohttp.ClientTimeout(total=60)
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Anthropic-Version": "2023-06-01"
                }
            )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            
    async def analyze_modification_batch(self, modifications: List[ModificationAnalysisRequest], 
                                       batch_size: int = 5) -> List[ModificationAnalysisResult]:
        """批量分析修改项"""
        results = []
        
        logger.info(f"开始批量分析 {len(modifications)} 个修改项，批大小: {batch_size}")
        
        # 分批处理以避免API限流
        for i in range(0, len(modifications), batch_size):
            batch = modifications[i:i + batch_size]
            
            # 并发处理当前批次
            batch_tasks = [
                self._analyze_single_modification(mod) for mod in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 处理批次结果
            for mod, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    # 处理异常情况
                    results.append(ModificationAnalysisResult(
                        modification_id=mod.modification_id,
                        recommendation="REVIEW",
                        confidence=0.0,
                        reasoning=f"AI分析失败: {str(result)}",
                        business_impact="MEDIUM",
                        suggested_action="需要人工审核",
                        risk_factors=["AI分析不可用"],
                        approval_conditions=["人工审核确认"],
                        analysis_timestamp=datetime.now().isoformat()
                    ))
                else:
                    results.append(result)
            
            # 批次间延迟以遵守API限流
            if i + batch_size < len(modifications):
                await asyncio.sleep(0.5)
                
        logger.info(f"批量分析完成，成功分析: {len(results)}个")
        return results
    
    async def _analyze_single_modification(self, modification: ModificationAnalysisRequest) -> ModificationAnalysisResult:
        """分析单个修改项"""
        
        # 构建分析提示词
        analysis_prompt = self._build_analysis_prompt(modification)
        
        # 调用Claude API
        try:
            start_time = time.time()
            
            response = await self._call_claude_api({
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 500,
                "temperature": 0.1,  # 低温度确保分析一致性
                "messages": [
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 解析响应
            analysis_result = self._parse_claude_response(response, modification, response_time)
            
            # 更新统计
            self._update_api_stats(True, response_time)
            
            return analysis_result
            
        except Exception as e:
            self._update_api_stats(False, 0)
            logger.error(f"修改项 {modification.modification_id} 分析失败: {e}")
            
            # 降级处理
            return ModificationAnalysisResult(
                modification_id=modification.modification_id,
                recommendation="REVIEW",
                confidence=0.0,
                reasoning=f"API调用失败: {str(e)}",
                business_impact="MEDIUM",
                suggested_action="需要人工审核",
                risk_factors=["API服务不可用"],
                approval_conditions=["人工审核确认"],
                analysis_timestamp=datetime.now().isoformat()
            )
    
    async def _call_claude_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """调用Claude API（带重试机制）"""
        
        for attempt in range(self.retry_config["max_retries"] + 1):
            try:
                async with self.session.post(
                    f"{self.base_url}/v1/messages",
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        self.api_stats["total_requests"] += 1
                        return result
                    elif response.status == 429:  # 速率限制
                        if attempt < self.retry_config["max_retries"]:
                            delay = min(
                                self.retry_config["base_delay"] * 
                                (self.retry_config["backoff_factor"] ** attempt),
                                self.retry_config["max_delay"]
                            )
                            logger.warning(f"API限流，等待 {delay}秒 重试...")
                            await asyncio.sleep(delay)
                            continue
                    else:
                        error_text = await response.text()
                        raise ClaudeAPIException(f"HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                if attempt < self.retry_config["max_retries"]:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ClaudeAPIException("API调用超时")
            
            except Exception as e:
                if attempt < self.retry_config["max_retries"]:
                    await asyncio.sleep(1)
                    continue
                raise ClaudeAPIException(f"API调用失败: {str(e)}")
        
        raise ClaudeAPIException("API调用重试次数超限")
    
    def _build_analysis_prompt(self, modification: ModificationAnalysisRequest) -> str:
        """构建分析提示词"""
        
        # 获取列特定的业务规则
        column_rules = self._get_column_business_rules(modification.column_name)
        
        prompt = f"""
        你是一个专业的企业文档变更分析专家。请分析以下腾讯文档表格的字段修改，判断其合理性和风险等级。
        
        ## 业务背景
        这是一个企业级项目管理表格，用于追踪项目进度和人员安排。该字段属于L2级别（需要语义审核），不是绝对禁止修改的L1字段，也不是可自由编辑的L3字段。
        
        ## 分析要求
        请从以下维度进行分析：
        1. **业务合理性**: 这个修改在业务逻辑上是否合理
        2. **影响范围**: 修改可能影响的其他字段或流程  
        3. **风险评估**: 修改可能带来的风险
        4. **建议操作**: 应该批准、拒绝还是需要进一步审核
        
        ## 修改详情
        表格名称: {modification.table_name}
        字段名称: {modification.column_name}
        原始值: {modification.original_value}
        修改值: {modification.new_value}
        修改时间: {modification.modification_time or "未知"}
        修改人: {modification.modifier or "未知"}
        变更背景: {modification.change_context or "无额外上下文"}
        
        ## 业务规则参考
        {column_rules}
        
        请以JSON格式返回分析结果：
        {{
            "recommendation": "APPROVE|REJECT|REVIEW",
            "confidence": 0.0-1.0,
            "reasoning": "详细分析理由",
            "business_impact": "HIGH|MEDIUM|LOW",
            "suggested_action": "具体建议操作",
            "risk_factors": ["识别的风险因素"],
            "approval_conditions": ["批准所需条件"]
        }}
        """
        
        return prompt.strip()
    
    def _get_column_business_rules(self, column_name: str) -> str:
        """获取列特定的业务规则"""
        
        # 不同列类型的专用规则
        column_specific_rules = {
            "负责人": {
                "business_context": "人员调配通常涉及权限和责任转移",
                "approval_criteria": [
                    "新负责人具备相应技能和权限",
                    "原负责人确认交接",
                    "项目经理批准人员变更"
                ],
                "risk_factors": [
                    "知识传承中断",
                    "进度延误风险",
                    "质量控制变化"
                ]
            },
            "具体计划内容": {
                "business_context": "计划内容变更可能影响项目范围和资源分配", 
                "approval_criteria": [
                    "变更符合项目目标",
                    "资源需求在可承受范围",
                    "时间线调整合理"
                ],
                "risk_factors": [
                    "范围蔓延",
                    "资源冲突",
                    "交付延期"
                ]
            },
            "协助人": {
                "business_context": "协助人变更影响团队协作和工作分配",
                "approval_criteria": [
                    "新协助人有相关技能",
                    "工作负荷平衡",
                    "团队协作顺畅"
                ],
                "risk_factors": [
                    "协作效率下降",
                    "沟通成本增加",
                    "技能不匹配"
                ]
            }
        }
        
        rules = column_specific_rules.get(column_name, {
            "business_context": "通用业务字段修改",
            "approval_criteria": ["符合业务逻辑", "无明显风险"],
            "risk_factors": ["数据一致性", "流程影响"]
        })
        
        # 构建业务规则文本
        rules_text = f"""
        **业务背景**: {rules['business_context']}
        
        **批准标准**:
        {chr(10).join([f"- {criteria}" for criteria in rules['approval_criteria']])}
        
        **风险因素**:
        {chr(10).join([f"- {risk}" for risk in rules['risk_factors']])}
        """
        
        return rules_text.strip()
    
    def _parse_claude_response(self, raw_response: Dict[str, Any], 
                             modification_context: ModificationAnalysisRequest,
                             response_time: float) -> ModificationAnalysisResult:
        """解析Claude API响应"""
        try:
            # 提取消息内容
            content = raw_response["content"][0]["text"]
            
            # 尝试提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("响应中未找到JSON格式数据")
            
            json_content = content[json_start:json_end]
            parsed_result = json.loads(json_content)
            
            # 验证和标准化结果
            validated_result = self._validate_analysis_result(parsed_result)
            
            # 创建结果对象
            result = ModificationAnalysisResult(
                modification_id=modification_context.modification_id,
                recommendation=validated_result.get("recommendation", "REVIEW"),
                confidence=validated_result.get("confidence", 0.0),
                reasoning=validated_result.get("reasoning", "分析成功"),
                business_impact=validated_result.get("business_impact", "MEDIUM"),
                suggested_action=validated_result.get("suggested_action", "需要进一步评估"),
                risk_factors=validated_result.get("risk_factors", []),
                approval_conditions=validated_result.get("approval_conditions", []),
                analysis_timestamp=datetime.now().isoformat()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"解析Claude响应失败: {e}")
            # 解析失败时返回安全默认值
            return ModificationAnalysisResult(
                modification_id=modification_context.modification_id,
                recommendation="REVIEW",
                confidence=0.0,
                reasoning=f"AI分析解析失败: {str(e)}",
                business_impact="MEDIUM",
                suggested_action="需要人工审核",
                risk_factors=["AI分析不可用"],
                approval_conditions=["人工审核确认"],
                analysis_timestamp=datetime.now().isoformat()
            )
    
    def _validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证分析结果格式"""
        validated = {}
        
        # 验证recommendation
        recommendation = result.get("recommendation", "REVIEW")
        if recommendation not in ["APPROVE", "REJECT", "REVIEW"]:
            recommendation = "REVIEW"
        validated["recommendation"] = recommendation
        
        # 验证confidence
        try:
            confidence = float(result.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.0
        validated["confidence"] = confidence
        
        # 验证business_impact
        business_impact = result.get("business_impact", "MEDIUM")
        if business_impact not in ["HIGH", "MEDIUM", "LOW"]:
            business_impact = "MEDIUM"
        validated["business_impact"] = business_impact
        
        # 验证其他字段
        validated["reasoning"] = str(result.get("reasoning", ""))
        validated["suggested_action"] = str(result.get("suggested_action", ""))
        
        # 验证列表字段
        risk_factors = result.get("risk_factors", [])
        if isinstance(risk_factors, list):
            validated["risk_factors"] = [str(factor) for factor in risk_factors]
        else:
            validated["risk_factors"] = []
            
        approval_conditions = result.get("approval_conditions", [])
        if isinstance(approval_conditions, list):
            validated["approval_conditions"] = [str(condition) for condition in approval_conditions]
        else:
            validated["approval_conditions"] = []
        
        return validated
        
    def _update_api_stats(self, success: bool, response_time: float):
        """更新API统计"""
        self.api_stats["total_requests"] += 1
        
        if success:
            self.api_stats["successful_requests"] += 1
        else:
            self.api_stats["failed_requests"] += 1
        
        # 更新平均响应时间
        total_requests = self.api_stats["total_requests"]
        current_avg = self.api_stats["average_response_time"]
        self.api_stats["average_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )


class SemanticCacheManager:
    """语义哈希缓存管理器"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        if redis_client:
            self.redis = redis_client
        else:
            # 默认Redis连接
            try:
                self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
                # 测试连接
                self.redis.ping()
            except (redis.ConnectionError, redis.ResponseError):
                logger.warning("Redis连接失败，缓存功能将被禁用")
                self.redis = None
        
        self.cache_prefix = "ai_analysis"
        self.default_ttl = 86400  # 24小时
        
    def generate_semantic_hash(self, modification: ModificationAnalysisRequest) -> str:
        """生成语义哈希键"""
        # 提取核心语义特征
        semantic_features = {
            "column_name": modification.column_name,
            "change_type": self._classify_change_type(
                modification.original_value, 
                modification.new_value
            ),
            "value_similarity": self._calculate_value_similarity(
                modification.original_value,
                modification.new_value
            ),
            "context_hash": self._hash_context(modification.change_context or "")
        }
        
        # 生成稳定的哈希
        feature_string = "|".join([
            str(semantic_features["column_name"]),
            str(semantic_features["change_type"]), 
            f"{semantic_features['value_similarity']:.2f}",
            str(semantic_features["context_hash"])
        ])
        
        return hashlib.md5(feature_string.encode()).hexdigest()
    
    async def get_cached_analysis(self, cache_key: str) -> Optional[ModificationAnalysisResult]:
        """获取缓存的分析结果"""
        if not self.redis:
            return None
            
        try:
            cached_data = self.redis.get(f"{self.cache_prefix}:{cache_key}")
            if cached_data:
                data = json.loads(cached_data)
                return ModificationAnalysisResult(**data)
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
        return None
    
    async def cache_analysis_result(self, cache_key: str, result: ModificationAnalysisResult, 
                                  ttl: Optional[int] = None) -> bool:
        """缓存分析结果"""
        if not self.redis:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            # 转换为字典以便序列化
            result_dict = {
                "modification_id": result.modification_id,
                "recommendation": result.recommendation,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "business_impact": result.business_impact,
                "suggested_action": result.suggested_action,
                "risk_factors": result.risk_factors,
                "approval_conditions": result.approval_conditions,
                "analysis_timestamp": result.analysis_timestamp,
                "ai_model": result.ai_model,
                "processing_version": result.processing_version
            }
            
            serialized = json.dumps(result_dict, ensure_ascii=False)
            self.redis.setex(
                f"{self.cache_prefix}:{cache_key}",
                ttl,
                serialized
            )
            return True
            
        except Exception as e:
            logger.error(f"缓存写入失败: {e}")
            return False
    
    def _classify_change_type(self, original: str, new: str) -> str:
        """分类变更类型"""
        if not original and new:
            return "addition"
        elif original and not new:
            return "deletion"
        elif str(original).lower() == str(new).lower():
            return "case_change"
        elif self._is_typo_correction(original, new):
            return "typo_correction"
        elif self._is_format_change(original, new):
            return "format_change"
        else:
            return "content_change"
    
    def _calculate_value_similarity(self, original: str, new: str) -> float:
        """计算值相似度"""
        if not original and not new:
            return 1.0
        if not original or not new:
            return 0.0
        
        # 简单的相似度计算
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, str(original), str(new))
        return matcher.ratio()
    
    def _hash_context(self, context: str) -> str:
        """哈希上下文"""
        if not context:
            return "empty"
        return hashlib.md5(context.encode()).hexdigest()[:8]
    
    def _is_typo_correction(self, original: str, new: str) -> bool:
        """判断是否为拼写纠错"""
        # 简单的拼写纠错判断
        similarity = self._calculate_value_similarity(original, new)
        return 0.7 <= similarity < 0.95
    
    def _is_format_change(self, original: str, new: str) -> bool:
        """判断是否为格式变更"""
        # 移除空格和标点后比较
        import re
        clean_original = re.sub(r'[^\w]', '', str(original).lower())
        clean_new = re.sub(r'[^\w]', '', str(new).lower())
        return clean_original == clean_new


class AISemanticAnalysisOrchestrator:
    """AI语义分析协调器 - 主类"""
    
    def __init__(self, claude_api_key: str, redis_client: Optional[redis.Redis] = None):
        self.claude_client = ClaudeSemanticAnalysisClient(claude_api_key)
        self.cache_manager = SemanticCacheManager(redis_client)
        
        # 统计信息
        self.processing_stats = {
            "total_modifications_analyzed": 0,
            "cache_hit_rate": 0.0,
            "average_processing_time": 0.0,
            "recommendation_distribution": Counter()
        }
        
    async def analyze_modifications_with_caching(self, 
                                               modifications: List[ModificationAnalysisRequest],
                                               use_cache: bool = True) -> List[ModificationAnalysisResult]:
        """
        带缓存的修改分析
        
        Args:
            modifications: 修改请求列表
            use_cache: 是否使用缓存
            
        Returns:
            分析结果列表
        """
        
        start_time = time.time()
        logger.info(f"开始分析 {len(modifications)} 个L2级别修改，缓存模式: {use_cache}")
        
        results = []
        uncached_modifications = []
        cache_hits = 0
        
        # 检查缓存
        if use_cache:
            for mod in modifications:
                cache_key = self.cache_manager.generate_semantic_hash(mod)
                cached_result = await self.cache_manager.get_cached_analysis(cache_key)
                
                if cached_result:
                    # 更新修改ID（缓存结果可能有不同的ID）
                    cached_result.modification_id = mod.modification_id
                    results.append(cached_result)
                    cache_hits += 1
                    logger.debug(f"缓存命中: {mod.modification_id}")
                else:
                    uncached_modifications.append((mod, cache_key))
        else:
            uncached_modifications = [(mod, None) for mod in modifications]
        
        logger.info(f"缓存命中: {cache_hits}个，需要AI分析: {len(uncached_modifications)}个")
        
        # AI分析未缓存的修改
        if uncached_modifications:
            async with self.claude_client as client:
                ai_results = await client.analyze_modification_batch(
                    [mod for mod, _ in uncached_modifications]
                )
                
                # 缓存AI分析结果
                if use_cache:
                    for (mod, cache_key), ai_result in zip(uncached_modifications, ai_results):
                        if cache_key and ai_result.confidence > 0.5:  # 只缓存高置信度结果
                            await self.cache_manager.cache_analysis_result(cache_key, ai_result)
                
                results.extend(ai_results)
        
        # 更新统计
        processing_time = time.time() - start_time
        self._update_processing_stats(results, cache_hits, len(modifications), processing_time)
        
        logger.info(f"AI语义分析完成，处理时间: {processing_time:.2f}秒，缓存命中率: {cache_hits/len(modifications)*100:.1f}%")
        
        return results
    
    def _update_processing_stats(self, results: List[ModificationAnalysisResult], 
                               cache_hits: int, total_modifications: int, 
                               processing_time: float):
        """更新处理统计"""
        self.processing_stats["total_modifications_analyzed"] += total_modifications
        self.processing_stats["cache_hit_rate"] = cache_hits / total_modifications if total_modifications > 0 else 0.0
        self.processing_stats["average_processing_time"] = processing_time / total_modifications if total_modifications > 0 else 0.0
        
        # 统计推荐分布
        for result in results:
            self.processing_stats["recommendation_distribution"][result.recommendation] += 1
    
    def generate_analysis_summary(self, results: List[ModificationAnalysisResult]) -> Dict[str, Any]:
        """生成分析摘要"""
        if not results:
            return {"error": "没有分析结果"}
        
        # 基本统计
        total_count = len(results)
        recommendation_counts = Counter(result.recommendation for result in results)
        business_impact_counts = Counter(result.business_impact for result in results)
        
        # 平均置信度
        average_confidence = sum(result.confidence for result in results) / total_count
        
        # 高置信度结果
        high_confidence_results = [r for r in results if r.confidence >= 0.8]
        
        # 关键风险因素
        all_risk_factors = []
        for result in results:
            all_risk_factors.extend(result.risk_factors)
        top_risk_factors = Counter(all_risk_factors).most_common(5)
        
        return {
            "summary": {
                "total_modifications": total_count,
                "recommendations": dict(recommendation_counts),
                "business_impacts": dict(business_impact_counts),
                "average_confidence": round(average_confidence, 3),
                "high_confidence_count": len(high_confidence_results),
                "high_confidence_rate": round(len(high_confidence_results) / total_count, 3)
            },
            "risk_analysis": {
                "top_risk_factors": top_risk_factors,
                "critical_modifications": [
                    {
                        "id": r.modification_id,
                        "recommendation": r.recommendation,
                        "reasoning": r.reasoning[:100] + "..." if len(r.reasoning) > 100 else r.reasoning
                    }
                    for r in results if r.recommendation == "REJECT" or r.business_impact == "HIGH"
                ][:5]
            },
            "processing_stats": self.processing_stats.copy(),
            "analysis_timestamp": datetime.now().isoformat()
        }


# 使用示例和测试
async def test_ai_semantic_analysis():
    """AI语义分析测试"""
    
    # 注意：需要真实的Claude API密钥
    api_key = "your-claude-api-key-here"  # 请替换为实际的API密钥
    
    if api_key == "your-claude-api-key-here":
        print("⚠️ 请设置真实的Claude API密钥以进行测试")
        return
    
    # 创建AI分析协调器
    orchestrator = AISemanticAnalysisOrchestrator(api_key)
    
    # 模拟L2级别修改数据
    test_modifications = [
        ModificationAnalysisRequest(
            modification_id="mod_001",
            column_name="负责人",
            original_value="张三",
            new_value="李四",
            table_name="小红书部门-工作表2",
            row_index=5,
            change_context="项目负责人调整",
            modification_time="2025-01-15 10:30:00",
            modifier="admin"
        ),
        ModificationAnalysisRequest(
            modification_id="mod_002",
            column_name="具体计划内容",
            original_value="用户增长策略优化",
            new_value="用户增长策略优化及数据分析",
            table_name="小红书部门-工作表2",
            row_index=8,
            change_context="计划内容补充完善",
            modification_time="2025-01-15 11:00:00",
            modifier="project_manager"
        )
    ]
    
    try:
        # 执行AI分析
        results = await orchestrator.analyze_modifications_with_caching(test_modifications)
        
        print("=== AI语义分析测试结果 ===")
        for result in results:
            print(f"\n修改ID: {result.modification_id}")
            print(f"推荐操作: {result.recommendation}")
            print(f"置信度: {result.confidence:.3f}")
            print(f"业务影响: {result.business_impact}")
            print(f"分析理由: {result.reasoning[:100]}...")
            print(f"建议操作: {result.suggested_action}")
            print(f"风险因素: {result.risk_factors}")
        
        # 生成分析摘要
        summary = orchestrator.generate_analysis_summary(results)
        print(f"\n=== 分析摘要 ===")
        print(f"总修改数: {summary['summary']['total_modifications']}")
        print(f"推荐分布: {summary['summary']['recommendations']}")
        print(f"平均置信度: {summary['summary']['average_confidence']}")
        
    except Exception as e:
        print(f"❌ AI分析测试失败: {e}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_ai_semantic_analysis())