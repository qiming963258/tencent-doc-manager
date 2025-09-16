# -*- coding: utf-8 -*-
"""
AI语义分析集成流程 - Claude API调用策略
专门处理L2级别变更的智能分析和决策支持
"""

import asyncio
import aiohttp
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
from collections import defaultdict
import sqlite3
from pathlib import Path
import pickle
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SemanticAnalysisTask:
    """语义分析任务数据结构"""
    task_id: str
    modification_id: str
    column_name: str
    original_value: str
    new_value: str
    table_context: Dict[str, Any]
    business_rules: Dict[str, Any]
    priority: int = 1  # 1=高优先级, 2=中等, 3=低优先级
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class SemanticAnalysisResult:
    """语义分析结果"""
    task_id: str
    modification_id: str
    analysis_type: str  # "content_semantic", "business_logic", "data_consistency"
    decision: str  # "APPROVE", "REJECT", "REVIEW", "CONDITIONAL"
    confidence_score: float  # 0.0 - 1.0
    reasoning: str
    business_impact_assessment: str
    suggested_actions: List[str]
    risk_factors: List[str]
    approval_conditions: List[str]
    analysis_timestamp: str
    processing_time_ms: int
    ai_model_version: str = "claude-3-sonnet"


class SemanticAnalysisEngine:
    """AI语义分析引擎 - 专门处理L2级别变更"""
    
    def __init__(self, claude_api_key: str, config: Dict[str, Any] = None):
        self.claude_api_key = claude_api_key
        self.config = config or {}
        
        # API配置
        self.api_base_url = "https://api.anthropic.com"
        self.api_version = "2023-06-01"
        self.model_name = "claude-3-sonnet-20240229"
        
        # 分析配置
        self.batch_size = self.config.get("batch_size", 5)
        self.max_retry_attempts = self.config.get("max_retry_attempts", 3)
        self.request_timeout = self.config.get("request_timeout", 30)
        self.rate_limit_delay = self.config.get("rate_limit_delay", 1.0)
        
        # 缓存配置
        self.enable_caching = self.config.get("enable_caching", True)
        self.cache_ttl_hours = self.config.get("cache_ttl_hours", 24)
        self.cache_db_path = self.config.get("cache_db_path", "semantic_analysis_cache.db")
        
        # 业务规则库
        self.business_rules = self._load_business_rules()
        
        # 初始化缓存数据库
        if self.enable_caching:
            self._init_cache_db()
        
        # 统计信息
        self.analysis_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "api_calls": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_response_time": 0.0
        }
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """加载业务规则库"""
        return {
            "column_sensitivity": {
                "项目类型": {
                    "allowed_values": ["战略项目", "运营项目", "创新项目", "维护项目"],
                    "change_approval_required": True,
                    "business_impact": "MEDIUM"
                },
                "具体计划内容": {
                    "min_length": 10,
                    "max_length": 500,
                    "forbidden_keywords": ["删除", "取消", "停止"],
                    "business_impact": "HIGH"
                },
                "负责人": {
                    "format_validation": r"^[\u4e00-\u9fff]{2,4}$",  # 中文姓名
                    "change_notification_required": True,
                    "business_impact": "HIGH"
                },
                "协助人": {
                    "format_validation": r"^[\u4e00-\u9fff]{2,4}(,[\u4e00-\u9fff]{2,4})*$",
                    "business_impact": "MEDIUM"
                },
                "监督人": {
                    "approval_required": True,
                    "business_impact": "HIGH"
                }
            },
            "semantic_patterns": {
                "responsibility_change": {
                    "pattern": r"(负责|协助|监督)",
                    "requires_approval": True,
                    "notification_required": True
                },
                "timeline_change": {
                    "pattern": r"(时间|日期|截止|deadline)",
                    "requires_justification": True
                },
                "scope_change": {
                    "pattern": r"(范围|内容|计划|目标)",
                    "requires_business_review": True
                }
            },
            "consistency_rules": {
                "person_role_consistency": {
                    "description": "检查人员角色的一致性",
                    "validation_logic": "person_in_multiple_roles_check"
                },
                "timeline_logical_consistency": {
                    "description": "检查时间线的逻辑一致性",
                    "validation_logic": "timeline_sequence_check"
                }
            }
        }
    
    def _init_cache_db(self):
        """初始化缓存数据库"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semantic_analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE NOT NULL,
                    analysis_input TEXT NOT NULL,
                    analysis_result TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引提高查询性能
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_content_hash 
                ON semantic_analysis_cache(content_hash)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON semantic_analysis_cache(expires_at)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("语义分析缓存数据库初始化完成")
            
        except Exception as e:
            logger.error(f"缓存数据库初始化失败: {e}")
    
    async def analyze_l2_modifications_batch(self, tasks: List[SemanticAnalysisTask]) -> List[SemanticAnalysisResult]:
        """
        批量分析L2级别修改
        
        Args:
            tasks: 语义分析任务列表
            
        Returns:
            分析结果列表
        """
        logger.info(f"开始批量语义分析，任务数量: {len(tasks)}")
        
        start_time = time.time()
        results = []
        
        try:
            # 按优先级排序任务
            sorted_tasks = sorted(tasks, key=lambda t: t.priority)
            
            # 分批处理
            for i in range(0, len(sorted_tasks), self.batch_size):
                batch = sorted_tasks[i:i + self.batch_size]
                batch_results = await self._process_task_batch(batch)
                results.extend(batch_results)
                
                # 速率限制
                if i + self.batch_size < len(sorted_tasks):
                    await asyncio.sleep(self.rate_limit_delay)
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self.analysis_stats["total_requests"] += len(tasks)
            self.analysis_stats["successful_analyses"] += len(results)
            self.analysis_stats["average_response_time"] = (
                (self.analysis_stats["average_response_time"] + processing_time) / 2
            )
            
            logger.info(f"批量分析完成，处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"批量语义分析失败: {e}")
            self.analysis_stats["failed_analyses"] += len(tasks) - len(results)
        
        return results
    
    async def _process_task_batch(self, batch: List[SemanticAnalysisTask]) -> List[SemanticAnalysisResult]:
        """处理单个批次的任务"""
        batch_results = []
        
        for task in batch:
            try:
                # 检查缓存
                cached_result = self._get_cached_result(task)
                if cached_result:
                    batch_results.append(cached_result)
                    self.analysis_stats["cache_hits"] += 1
                    continue
                
                # 执行AI分析
                result = await self._perform_ai_analysis(task)
                if result:
                    batch_results.append(result)
                    
                    # 缓存结果
                    self._cache_result(task, result)
                    self.analysis_stats["cache_misses"] += 1
                    self.analysis_stats["api_calls"] += 1
                
            except Exception as e:
                logger.error(f"任务处理失败 {task.task_id}: {e}")
                # 创建错误结果
                error_result = SemanticAnalysisResult(
                    task_id=task.task_id,
                    modification_id=task.modification_id,
                    analysis_type="error",
                    decision="REVIEW",
                    confidence_score=0.0,
                    reasoning=f"分析过程中出现错误: {str(e)}",
                    business_impact_assessment="UNKNOWN",
                    suggested_actions=["人工审核"],
                    risk_factors=["系统错误"],
                    approval_conditions=["需要人工介入"],
                    analysis_timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
                batch_results.append(error_result)
        
        return batch_results
    
    def _get_cached_result(self, task: SemanticAnalysisTask) -> Optional[SemanticAnalysisResult]:
        """从缓存中获取分析结果"""
        if not self.enable_caching:
            return None
        
        try:
            # 计算内容哈希
            content_hash = self._calculate_content_hash(task)
            
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # 查询缓存
            cursor.execute('''
                SELECT analysis_result FROM semantic_analysis_cache 
                WHERE content_hash = ? AND expires_at > ?
            ''', (content_hash, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            if row:
                # 更新访问统计
                cursor.execute('''
                    UPDATE semantic_analysis_cache 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE content_hash = ?
                ''', (datetime.now().isoformat(), content_hash))
                
                conn.commit()
                conn.close()
                
                # 反序列化结果
                result_data = json.loads(row[0])
                return SemanticAnalysisResult(**result_data)
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"缓存查询失败: {e}")
        
        return None
    
    def _cache_result(self, task: SemanticAnalysisTask, result: SemanticAnalysisResult):
        """缓存分析结果"""
        if not self.enable_caching:
            return
        
        try:
            content_hash = self._calculate_content_hash(task)
            expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
            
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO semantic_analysis_cache 
                (content_hash, analysis_input, analysis_result, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (
                content_hash,
                json.dumps(asdict(task)),
                json.dumps(asdict(result)),
                expires_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"结果缓存失败: {e}")
    
    def _calculate_content_hash(self, task: SemanticAnalysisTask) -> str:
        """计算任务内容的哈希值"""
        # 只包含影响分析结果的关键字段
        key_content = f"{task.column_name}|{task.original_value}|{task.new_value}"
        return hashlib.md5(key_content.encode('utf-8')).hexdigest()
    
    async def _perform_ai_analysis(self, task: SemanticAnalysisTask) -> Optional[SemanticAnalysisResult]:
        """执行AI语义分析"""
        start_time = time.time()
        
        try:
            # 构建分析提示词
            analysis_prompt = self._build_analysis_prompt(task)
            
            # 调用Claude API
            api_response = await self._call_claude_api(analysis_prompt)
            
            # 解析响应
            analysis_result = self._parse_api_response(task, api_response)
            
            # 计算处理时间
            processing_time_ms = int((time.time() - start_time) * 1000)
            analysis_result.processing_time_ms = processing_time_ms
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI分析失败 {task.task_id}: {e}")
            return None
    
    def _build_analysis_prompt(self, task: SemanticAnalysisTask) -> str:
        """构建用于Claude API的分析提示词"""
        
        # 获取相关业务规则
        column_rules = self.business_rules["column_sensitivity"].get(task.column_name, {})
        
        prompt = f"""
你是一个专业的企业文档变更审核专家。请分析以下L2级别的文档修改，并提供专业的审核建议。

## 修改详情
- 列名: {task.column_name}
- 原始值: "{task.original_value}"
- 修改后值: "{task.new_value}"
- 表格上下文: {json.dumps(task.table_context, ensure_ascii=False)}

## 业务规则
{json.dumps(column_rules, ensure_ascii=False, indent=2)}

## 分析要求
请从以下维度进行专业分析：

1. **内容语义分析**
   - 修改是否保持了原有语义
   - 是否存在概念性错误或误解
   - 新内容的专业性和准确性

2. **业务逻辑一致性**
   - 修改是否符合业务流程
   - 是否影响其他相关字段的逻辑
   - 是否违反既定的业务规则

3. **数据完整性检查**
   - 修改是否影响数据的完整性
   - 是否存在格式或规范问题
   - 是否需要联动修改其他相关数据

4. **风险评估**
   - 修改可能带来的业务风险
   - 对下游流程的潜在影响
   - 是否需要额外的验证步骤

## 输出格式
请严格按照以下JSON格式输出分析结果：

```json
{{
    "decision": "APPROVE|REJECT|REVIEW|CONDITIONAL",
    "confidence_score": 0.0-1.0,
    "reasoning": "详细的分析推理过程",
    "business_impact_assessment": "HIGH|MEDIUM|LOW",
    "suggested_actions": ["具体的行动建议"],
    "risk_factors": ["识别的风险因素"],
    "approval_conditions": ["如果是CONDITIONAL决策，列出条件"]
}}
```

## 决策标准
- APPROVE: 修改合理，无明显问题，可以直接通过
- REJECT: 修改存在严重问题，不应该被采纳
- REVIEW: 需要人工进一步审核，存在不确定因素
- CONDITIONAL: 在满足特定条件下可以通过

请确保你的分析客观、专业，基于提供的业务规则和最佳实践。
"""
        
        return prompt.strip()
    
    async def _call_claude_api(self, prompt: str) -> Dict[str, Any]:
        """调用Claude API"""
        headers = {
            "Authorization": f"Bearer {self.claude_api_key}",
            "Content-Type": "application/json",
            "Anthropic-Version": self.api_version
        }
        
        payload = {
            "model": self.model_name,
            "max_tokens": 2000,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        
        for attempt in range(self.max_retry_attempts):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.api_base_url}/v1/messages",
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # 速率限制
                            wait_time = 2 ** attempt
                            logger.warning(f"API速率限制，等待 {wait_time} 秒后重试")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            response_text = await response.text()
                            raise Exception(f"API调用失败: {response.status} - {response_text}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"API调用超时，第 {attempt + 1} 次尝试")
                if attempt == self.max_retry_attempts - 1:
                    raise Exception("API调用多次超时失败")
            except Exception as e:
                if attempt == self.max_retry_attempts - 1:
                    raise e
                logger.warning(f"API调用失败，第 {attempt + 1} 次尝试: {e}")
                await asyncio.sleep(1)
        
        raise Exception("API调用最终失败")
    
    def _parse_api_response(self, task: SemanticAnalysisTask, 
                          api_response: Dict[str, Any]) -> SemanticAnalysisResult:
        """解析Claude API响应"""
        try:
            # 提取响应内容
            content = api_response["content"][0]["text"]
            
            # 提取JSON部分
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if not json_match:
                # 尝试直接解析整个内容
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                analysis_data = json.loads(json_match.group(1))
            else:
                raise ValueError("无法从响应中提取JSON格式的分析结果")
            
            # 创建结果对象
            result = SemanticAnalysisResult(
                task_id=task.task_id,
                modification_id=task.modification_id,
                analysis_type="semantic_analysis",
                decision=analysis_data.get("decision", "REVIEW"),
                confidence_score=float(analysis_data.get("confidence_score", 0.5)),
                reasoning=analysis_data.get("reasoning", ""),
                business_impact_assessment=analysis_data.get("business_impact_assessment", "MEDIUM"),
                suggested_actions=analysis_data.get("suggested_actions", []),
                risk_factors=analysis_data.get("risk_factors", []),
                approval_conditions=analysis_data.get("approval_conditions", []),
                analysis_timestamp=datetime.now().isoformat(),
                processing_time_ms=0  # 将在调用处设置
            )
            
            return result
            
        except Exception as e:
            logger.error(f"API响应解析失败: {e}")
            logger.error(f"原始响应: {api_response}")
            
            # 返回错误结果
            return SemanticAnalysisResult(
                task_id=task.task_id,
                modification_id=task.modification_id,
                analysis_type="parse_error",
                decision="REVIEW",
                confidence_score=0.0,
                reasoning=f"响应解析失败: {str(e)}",
                business_impact_assessment="UNKNOWN",
                suggested_actions=["人工审核"],
                risk_factors=["API响应解析错误"],
                approval_conditions=["需要人工介入"],
                analysis_timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        return {
            "statistics": self.analysis_stats.copy(),
            "cache_status": {
                "enabled": self.enable_caching,
                "hit_rate": (
                    self.analysis_stats["cache_hits"] / 
                    max(1, self.analysis_stats["cache_hits"] + self.analysis_stats["cache_misses"])
                ),
                "db_path": self.cache_db_path
            },
            "configuration": {
                "batch_size": self.batch_size,
                "max_retry_attempts": self.max_retry_attempts,
                "request_timeout": self.request_timeout,
                "rate_limit_delay": self.rate_limit_delay
            }
        }
    
    def cleanup_expired_cache(self):
        """清理过期的缓存记录"""
        if not self.enable_caching:
            return
        
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM semantic_analysis_cache 
                WHERE expires_at < ?
            ''', (datetime.now().isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"清理了 {deleted_count} 条过期缓存记录")
            
        except Exception as e:
            logger.error(f"缓存清理失败: {e}")


class L2ModificationProcessor:
    """L2级别修改处理器 - 集成语义分析引擎"""
    
    def __init__(self, semantic_engine: SemanticAnalysisEngine):
        self.semantic_engine = semantic_engine
        
    async def process_l2_modifications(self, modifications: List[Dict[str, Any]], 
                                     table_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理L2级别修改的完整流程
        
        Args:
            modifications: L2级别修改列表
            table_context: 表格上下文信息
            
        Returns:
            处理结果汇总
        """
        
        # 转换为语义分析任务
        tasks = []
        for i, mod in enumerate(modifications):
            task = SemanticAnalysisTask(
                task_id=f"l2_task_{i}_{int(time.time())}",
                modification_id=mod.get("modification_id", f"mod_{i}"),
                column_name=mod.get("column_name", ""),
                original_value=str(mod.get("original_value", "")),
                new_value=str(mod.get("new_value", "")),
                table_context=table_context,
                business_rules={},  # 将从semantic_engine的业务规则中获取
                priority=self._calculate_priority(mod)
            )
            tasks.append(task)
        
        # 执行批量分析
        analysis_results = await self.semantic_engine.analyze_l2_modifications_batch(tasks)
        
        # 汇总结果
        summary = self._generate_processing_summary(analysis_results)
        
        return {
            "total_l2_modifications": len(modifications),
            "analyzed_modifications": len(analysis_results),
            "analysis_results": [asdict(result) for result in analysis_results],
            "summary": summary,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _calculate_priority(self, modification: Dict[str, Any]) -> int:
        """计算修改的优先级"""
        column_name = modification.get("column_name", "")
        
        # 高优先级列
        high_priority_columns = ["负责人", "监督人", "重要程度", "预计完成时间"]
        if column_name in high_priority_columns:
            return 1
        
        # 中等优先级列
        medium_priority_columns = ["项目类型", "具体计划内容", "协助人"]
        if column_name in medium_priority_columns:
            return 2
        
        # 默认低优先级
        return 3
    
    def _generate_processing_summary(self, analysis_results: List[SemanticAnalysisResult]) -> Dict[str, Any]:
        """生成处理结果汇总"""
        if not analysis_results:
            return {"message": "没有分析结果"}
        
        # 按决策类型统计
        decision_counts = defaultdict(int)
        confidence_scores = []
        
        for result in analysis_results:
            decision_counts[result.decision] += 1
            confidence_scores.append(result.confidence_score)
        
        # 风险因素统计
        all_risk_factors = []
        for result in analysis_results:
            all_risk_factors.extend(result.risk_factors)
        
        risk_factor_counts = dict(Counter(all_risk_factors))
        
        return {
            "decision_distribution": dict(decision_counts),
            "average_confidence": np.mean(confidence_scores) if confidence_scores else 0.0,
            "confidence_std": np.std(confidence_scores) if len(confidence_scores) > 1 else 0.0,
            "most_common_risks": sorted(
                risk_factor_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            "requires_review_count": decision_counts["REVIEW"] + decision_counts["CONDITIONAL"],
            "high_confidence_decisions": sum(
                1 for score in confidence_scores if score > 0.8
            ),
            "recommendations": self._generate_recommendations(analysis_results)
        }
    
    def _generate_recommendations(self, analysis_results: List[SemanticAnalysisResult]) -> List[str]:
        """生成处理建议"""
        recommendations = []
        
        # 检查拒绝率
        reject_count = sum(1 for r in analysis_results if r.decision == "REJECT")
        if reject_count > len(analysis_results) * 0.3:
            recommendations.append("拒绝率较高，建议重新审查修改策略")
        
        # 检查置信度
        low_confidence_count = sum(1 for r in analysis_results if r.confidence_score < 0.6)
        if low_confidence_count > 0:
            recommendations.append(f"有 {low_confidence_count} 项修改置信度较低，建议人工复审")
        
        # 检查需要条件批准的项目
        conditional_count = sum(1 for r in analysis_results if r.decision == "CONDITIONAL")
        if conditional_count > 0:
            recommendations.append(f"有 {conditional_count} 项修改需要满足特定条件才能批准")
        
        return recommendations