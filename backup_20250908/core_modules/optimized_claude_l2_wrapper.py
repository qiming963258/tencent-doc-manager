#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 6: 优化Claude API封装 - L2语义变化检测专用
确保Claude API达到稳定可用，正确识别L2语义变化
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import deque
import hashlib
import statistics

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class L2SemanticAnalysisRequest:
    """L2语义分析请求"""
    change_id: str
    column_name: str
    original_value: str
    new_value: str
    table_context: str
    business_context: str = ""
    priority: str = "normal"  # high, normal, low


@dataclass
class L2SemanticAnalysisResult:
    """L2语义分析结果"""
    change_id: str
    semantic_decision: str  # APPROVE, REJECT, REVIEW
    confidence_score: float  # 0.0 - 1.0
    semantic_reasoning: str
    risk_level: str  # L1, L2, L3
    business_impact: str  # HIGH, MEDIUM, LOW
    approval_required: bool
    auto_processable: bool
    l2_specific_factors: List[str]
    processing_time: float
    api_model_used: str
    analysis_timestamp: str


class ClaudeAPIStabilityMonitor:
    """Claude API稳定性监控器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.response_times = deque(maxlen=window_size)
        self.success_history = deque(maxlen=window_size)
        self.error_counts = {}
        self.health_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'success_rate': 100.0,
            'error_rate': 0.0,
            'stability_score': 100.0,
            'last_check': datetime.now().isoformat()
        }
    
    def record_request(self, success: bool, response_time: float, error_type: str = None):
        """记录请求结果"""
        self.response_times.append(response_time)
        self.success_history.append(success)
        
        self.health_metrics['total_requests'] += 1
        
        if success:
            self.health_metrics['successful_requests'] += 1
        else:
            self.health_metrics['failed_requests'] += 1
            if error_type:
                self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # 更新指标
        self._update_metrics()
    
    def _update_metrics(self):
        """更新健康指标"""
        if self.response_times:
            self.health_metrics['avg_response_time'] = statistics.mean(self.response_times)
        
        if self.health_metrics['total_requests'] > 0:
            self.health_metrics['success_rate'] = (
                self.health_metrics['successful_requests'] / 
                self.health_metrics['total_requests'] * 100
            )
            self.health_metrics['error_rate'] = (
                self.health_metrics['failed_requests'] / 
                self.health_metrics['total_requests'] * 100
            )
        
        # 计算稳定性评分
        success_rate = self.health_metrics['success_rate']
        avg_response_time = self.health_metrics['avg_response_time']
        
        # 基础评分基于成功率
        stability_score = success_rate
        
        # 响应时间惩罚
        if avg_response_time > 5.0:
            stability_score *= 0.8
        elif avg_response_time > 10.0:
            stability_score *= 0.6
        
        # 近期表现加权
        if len(self.success_history) >= 10:
            recent_success_rate = sum(self.success_history[-10:]) / 10 * 100
            stability_score = (stability_score * 0.7) + (recent_success_rate * 0.3)
        
        self.health_metrics['stability_score'] = round(stability_score, 1)
        self.health_metrics['last_check'] = datetime.now().isoformat()
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        status = "healthy"
        if self.health_metrics['stability_score'] < 80:
            status = "degraded"
        if self.health_metrics['stability_score'] < 60:
            status = "unhealthy"
        
        return {
            **self.health_metrics,
            'status': status,
            'error_distribution': dict(self.error_counts),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if self.health_metrics['success_rate'] < 95:
            recommendations.append("提高错误处理和重试机制")
        
        if self.health_metrics['avg_response_time'] > 5.0:
            recommendations.append("优化API请求性能")
        
        if len(self.error_counts) > 3:
            recommendations.append("分析错误模式并优化")
        
        return recommendations


class OptimizedClaudeL2Wrapper:
    """优化的Claude L2语义分析包装器"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.session = None
        self.stability_monitor = ClaudeAPIStabilityMonitor()
        
        # 重试配置
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 8.0,
            'backoff_multiplier': 2.0
        }
        
        # L2语义分析专用配置
        self.l2_config = {
            'enable_context_enhancement': True,
            'enable_business_rules_validation': True,
            'enable_semantic_similarity_check': True,
            'confidence_threshold': 0.7,
            'auto_approve_threshold': 0.9
        }
        
        # L2专用提示词模板
        self.l2_prompt_template = """
你是一个专门处理L2级别语义变更的AI分析师。L2级别的修改需要语义审核，不是绝对禁止的L1级别，也不是可以自由编辑的L3级别。

请分析以下表格字段修改的语义合理性：

## 修改详情
表格背景: {table_context}
字段名称: {column_name}
原始值: {original_value}
新值: {new_value}
业务背景: {business_context}

## L2语义审核要点
1. **语义一致性**: 修改是否保持原有语义意图
2. **业务逻辑性**: 修改是否符合业务流程逻辑
3. **影响范围评估**: 修改可能影响的关联字段或流程
4. **风险等级判断**: 评估修改的潜在风险

## 特殊关注字段（L2级别）
- 负责人、协助人: 涉及权限和责任转移
- 具体计划内容: 影响项目范围和资源
- 监督人: 涉及审批链和管控
- 重要程度: 影响优先级和资源分配

请以JSON格式返回分析结果：
{{
    "semantic_decision": "APPROVE|REJECT|REVIEW",
    "confidence_score": 0.0-1.0,
    "semantic_reasoning": "详细的语义分析理由",
    "risk_level": "L1|L2|L3",
    "business_impact": "HIGH|MEDIUM|LOW",
    "approval_required": true|false,
    "auto_processable": true|false,
    "l2_specific_factors": ["识别的L2级别特定因素"]
}}
        """
        
        logger.info("✅ 优化Claude L2语义分析包装器初始化完成")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def analyze_l2_semantic_change(self, request: L2SemanticAnalysisRequest) -> L2SemanticAnalysisResult:
        """分析L2语义变化"""
        start_time = time.time()
        
        try:
            # 生成L2专用分析提示词
            prompt = self._generate_l2_prompt(request)
            
            # 调用Claude API
            api_response = await self._call_claude_with_retry(prompt)
            
            # 解析并验证结果
            analysis_result = self._parse_l2_response(api_response, request)
            
            processing_time = time.time() - start_time
            analysis_result.processing_time = processing_time
            
            # 记录成功
            self.stability_monitor.record_request(True, processing_time)
            
            logger.info(f"✅ L2语义分析完成: {request.change_id}, 决策: {analysis_result.semantic_decision}")
            
            return analysis_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_type = type(e).__name__
            
            # 记录失败
            self.stability_monitor.record_request(False, processing_time, error_type)
            
            logger.error(f"❌ L2语义分析失败: {request.change_id}, 错误: {e}")
            
            # 返回安全默认结果
            return self._create_fallback_result(request, str(e), processing_time)
    
    async def analyze_l2_batch(self, requests: List[L2SemanticAnalysisRequest]) -> List[L2SemanticAnalysisResult]:
        """批量L2语义分析"""
        logger.info(f"🔍 开始批量L2语义分析: {len(requests)}个修改")
        
        results = []
        
        # 按优先级排序
        sorted_requests = sorted(requests, key=lambda x: {'high': 0, 'normal': 1, 'low': 2}[x.priority])
        
        # 批量处理
        batch_size = 3  # 控制并发数避免API限流
        for i in range(0, len(sorted_requests), batch_size):
            batch = sorted_requests[i:i + batch_size]
            
            # 并发处理当前批次
            batch_tasks = [self.analyze_l2_semantic_change(req) for req in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 处理结果
            for req, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    fallback_result = self._create_fallback_result(req, str(result), 0.0)
                    results.append(fallback_result)
                else:
                    results.append(result)
            
            # 批次间暂停避免API限流
            if i + batch_size < len(sorted_requests):
                await asyncio.sleep(0.5)
        
        logger.info(f"✅ 批量L2语义分析完成: {len(results)}个结果")
        return results
    
    def _generate_l2_prompt(self, request: L2SemanticAnalysisRequest) -> str:
        """生成L2专用分析提示词"""
        
        # 增强上下文信息
        enhanced_context = self._enhance_context(request)
        
        prompt = self.l2_prompt_template.format(
            table_context=enhanced_context['table_context'],
            column_name=request.column_name,
            original_value=request.original_value,
            new_value=request.new_value,
            business_context=enhanced_context['business_context']
        )
        
        return prompt.strip()
    
    def _enhance_context(self, request: L2SemanticAnalysisRequest) -> Dict[str, str]:
        """增强上下文信息"""
        
        # L2级别字段的特殊规则
        l2_field_rules = {
            '负责人': '涉及项目责任转移，需确认新负责人具备相应能力和权限',
            '协助人': '影响团队协作，需评估工作负荷分配和技能匹配',
            '监督人': '涉及管控链路，需确认新监督人的管理权限',
            '具体计划内容': '影响项目范围和资源分配，需评估变更的合理性',
            '重要程度': '影响优先级和资源投入，需评估调整的业务依据',
            '预计完成时间': '影响项目排期和里程碑，需评估时间调整的可行性'
        }
        
        # 获取字段特定规则
        field_rule = l2_field_rules.get(request.column_name, '通用L2字段，需要语义审核确认')
        
        # 增强业务上下文
        enhanced_business_context = f"{request.business_context}\n\n字段规则: {field_rule}"
        
        # 语义相似性分析
        similarity_info = self._analyze_semantic_similarity(request.original_value, request.new_value)
        
        return {
            'table_context': f"{request.table_context}\n语义相似度: {similarity_info}",
            'business_context': enhanced_business_context
        }
    
    def _analyze_semantic_similarity(self, original: str, new: str) -> str:
        """分析语义相似性"""
        try:
            from difflib import SequenceMatcher
            
            # 字符级相似度
            char_similarity = SequenceMatcher(None, str(original), str(new)).ratio()
            
            # 词汇级相似度（简化版）
            orig_words = set(str(original).split())
            new_words = set(str(new).split())
            
            if orig_words or new_words:
                word_similarity = len(orig_words & new_words) / max(len(orig_words | new_words), 1)
            else:
                word_similarity = 1.0
            
            # 长度相似度
            if len(str(original)) == 0 and len(str(new)) == 0:
                length_similarity = 1.0
            else:
                max_len = max(len(str(original)), len(str(new)))
                min_len = min(len(str(original)), len(str(new)))
                length_similarity = min_len / max_len if max_len > 0 else 0.0
            
            # 综合相似度
            overall_similarity = (char_similarity + word_similarity + length_similarity) / 3
            
            if overall_similarity > 0.8:
                return f"高相似度({overall_similarity:.2f}) - 可能是格式调整或错误修正"
            elif overall_similarity > 0.5:
                return f"中等相似度({overall_similarity:.2f}) - 部分内容修改"
            else:
                return f"低相似度({overall_similarity:.2f}) - 重要内容变更"
                
        except Exception:
            return "相似度分析不可用"
    
    async def _call_claude_with_retry(self, prompt: str) -> Dict[str, Any]:
        """带重试的Claude API调用"""
        last_error = None
        
        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                # 构建请求载荷 - 使用Claude服务支持的格式
                payload = {
                    "content": prompt,
                    "analysis_type": "risk_assessment"  # 使用支持的分析类型
                }
                
                # 调用API
                async with self.session.post(
                    f"{self.base_url}/analyze",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # 限流
                        if attempt < self.retry_config['max_retries']:
                            delay = min(
                                self.retry_config['base_delay'] * 
                                (self.retry_config['backoff_multiplier'] ** attempt),
                                self.retry_config['max_delay']
                            )
                            logger.warning(f"API限流，等待{delay}秒后重试...")
                            await asyncio.sleep(delay)
                            continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                last_error = Exception("API调用超时")
                if attempt < self.retry_config['max_retries']:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                last_error = e
                if attempt < self.retry_config['max_retries']:
                    await asyncio.sleep(1.0)
                    continue
                    
        raise last_error or Exception("API调用失败")
    
    def _parse_l2_response(self, api_response: Dict[str, Any], request: L2SemanticAnalysisRequest) -> L2SemanticAnalysisResult:
        """解析L2分析响应"""
        try:
            # 提取结果内容
            result_content = api_response.get('result', '')
            confidence = api_response.get('confidence', 0.0)
            
            # 尝试解析JSON结果
            json_data = self._extract_json_from_response(result_content)
            
            if json_data:
                # 验证和标准化结果
                validated = self._validate_l2_result(json_data)
                
                return L2SemanticAnalysisResult(
                    change_id=request.change_id,
                    semantic_decision=validated['semantic_decision'],
                    confidence_score=validated['confidence_score'],
                    semantic_reasoning=validated['semantic_reasoning'],
                    risk_level=validated['risk_level'],
                    business_impact=validated['business_impact'],
                    approval_required=validated['approval_required'],
                    auto_processable=validated['auto_processable'],
                    l2_specific_factors=validated['l2_specific_factors'],
                    processing_time=0.0,  # 将在外部设置
                    api_model_used=api_response.get('model', 'claude-wrapper'),
                    analysis_timestamp=datetime.now().isoformat()
                )
            else:
                # JSON解析失败，使用启发式方法
                return self._heuristic_parse_result(result_content, request, confidence)
                
        except Exception as e:
            logger.error(f"解析L2响应失败: {e}")
            raise Exception(f"响应解析失败: {e}")
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """从响应中提取JSON"""
        try:
            # 查找JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
                
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _heuristic_parse_result(self, content: str, request: L2SemanticAnalysisRequest, confidence: float) -> L2SemanticAnalysisResult:
        """启发式解析结果"""
        content_lower = content.lower()
        
        # 决策判断
        if 'approve' in content_lower or '批准' in content_lower or '通过' in content_lower:
            decision = 'APPROVE'
        elif 'reject' in content_lower or '拒绝' in content_lower or '禁止' in content_lower:
            decision = 'REJECT'
        else:
            decision = 'REVIEW'
        
        # 业务影响
        if 'high' in content_lower or '高' in content_lower or '严重' in content_lower:
            impact = 'HIGH'
        elif 'low' in content_lower or '低' in content_lower or '轻微' in content_lower:
            impact = 'LOW'
        else:
            impact = 'MEDIUM'
        
        return L2SemanticAnalysisResult(
            change_id=request.change_id,
            semantic_decision=decision,
            confidence_score=confidence,
            semantic_reasoning=content[:500],  # 截取前500字符
            risk_level='L2',  # 默认L2
            business_impact=impact,
            approval_required=decision != 'APPROVE',
            auto_processable=decision == 'APPROVE' and confidence > 0.8,
            l2_specific_factors=[request.column_name],
            processing_time=0.0,
            api_model_used='claude-wrapper-heuristic',
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _validate_l2_result(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证L2分析结果"""
        validated = {}
        
        # 语义决策
        decision = json_data.get('semantic_decision', 'REVIEW')
        validated['semantic_decision'] = decision if decision in ['APPROVE', 'REJECT', 'REVIEW'] else 'REVIEW'
        
        # 置信度
        confidence = json_data.get('confidence_score', 0.0)
        try:
            confidence = float(confidence)
            validated['confidence_score'] = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            validated['confidence_score'] = 0.0
        
        # 其他字段
        validated['semantic_reasoning'] = str(json_data.get('semantic_reasoning', ''))[:1000]  # 限制长度
        
        risk_level = json_data.get('risk_level', 'L2')
        validated['risk_level'] = risk_level if risk_level in ['L1', 'L2', 'L3'] else 'L2'
        
        business_impact = json_data.get('business_impact', 'MEDIUM')
        validated['business_impact'] = business_impact if business_impact in ['HIGH', 'MEDIUM', 'LOW'] else 'MEDIUM'
        
        validated['approval_required'] = bool(json_data.get('approval_required', True))
        validated['auto_processable'] = bool(json_data.get('auto_processable', False))
        
        # L2特定因素
        l2_factors = json_data.get('l2_specific_factors', [])
        if isinstance(l2_factors, list):
            validated['l2_specific_factors'] = [str(f)[:100] for f in l2_factors[:10]]  # 最多10个，每个最多100字符
        else:
            validated['l2_specific_factors'] = []
        
        return validated
    
    def _create_fallback_result(self, request: L2SemanticAnalysisRequest, error_msg: str, processing_time: float) -> L2SemanticAnalysisResult:
        """创建降级结果"""
        return L2SemanticAnalysisResult(
            change_id=request.change_id,
            semantic_decision='REVIEW',
            confidence_score=0.0,
            semantic_reasoning=f"AI分析失败，需要人工审核。错误信息: {error_msg[:200]}",
            risk_level='L2',
            business_impact='MEDIUM',
            approval_required=True,
            auto_processable=False,
            l2_specific_factors=['分析失败', request.column_name],
            processing_time=processing_time,
            api_model_used='fallback',
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def get_stability_status(self) -> Dict[str, Any]:
        """获取稳定性状态"""
        return self.stability_monitor.get_health_status()


# 命令行接口
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='优化Claude L2语义分析API')
    parser.add_argument('--url', default='http://localhost:8081', help='Claude服务URL')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--status', action='store_true', help='显示稳定性状态')
    
    args = parser.parse_args()
    
    async with OptimizedClaudeL2Wrapper(args.url) as wrapper:
        if args.status:
            print("🔍 Claude L2语义分析API稳定性状态:")
            status = wrapper.get_stability_status()
            print(f"   状态: {status['status']}")
            print(f"   稳定性评分: {status['stability_score']}/100")
            print(f"   成功率: {status['success_rate']:.1f}%")
            print(f"   平均响应时间: {status['avg_response_time']:.2f}秒")
            print(f"   总请求数: {status['total_requests']}")
            if status['recommendations']:
                print("   改进建议:")
                for rec in status['recommendations']:
                    print(f"     - {rec}")
        
        if args.test:
            print("🧪 开始L2语义分析测试...")
            
            # 测试请求
            test_request = L2SemanticAnalysisRequest(
                change_id="test_001",
                column_name="负责人",
                original_value="张三",
                new_value="李四",
                table_context="小红书部门项目管理表",
                business_context="项目负责人调整，需要确认权限转移",
                priority="high"
            )
            
            # 执行测试
            result = await wrapper.analyze_l2_semantic_change(test_request)
            
            print(f"\n✅ 测试完成:")
            print(f"   变更ID: {result.change_id}")
            print(f"   语义决策: {result.semantic_decision}")
            print(f"   置信度: {result.confidence_score:.2f}")
            print(f"   风险等级: {result.risk_level}")
            print(f"   业务影响: {result.business_impact}")
            print(f"   需要审批: {result.approval_required}")
            print(f"   可自动处理: {result.auto_processable}")
            print(f"   处理时间: {result.processing_time:.3f}秒")
            print(f"   分析理由: {result.semantic_reasoning[:100]}...")
            
            # 显示稳定性状态
            status = wrapper.get_stability_status()
            print(f"\n📊 API稳定性: {status['stability_score']}/100 ({status['status']})")


if __name__ == "__main__":
    asyncio.run(main())