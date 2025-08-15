import aiohttp
import asyncio
import json
import time
import hashlib
from typing import Dict, Any, Optional, AsyncGenerator, List
from functools import lru_cache
import logging
from datetime import datetime

from config import ClaudeConfig
from models import AnalyzeRequest, AnalyzeResponse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeAPIException(Exception):
    """Claude API异常"""
    def __init__(self, message: str, status_code: int = None, details: str = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class ClaudeClientWrapper:
    """Claude API客户端包装器"""
    
    def __init__(self):
        self.api_key = ClaudeConfig.API_KEY
        self.base_url = ClaudeConfig.BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
        self.start_time = time.time()
        
        # API统计信息
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0,
            "average_response_time": 0,
            "cache_hits": 0
        }
        
        # 智能分析提示词模板
        self.analysis_prompts = {
            "risk_assessment": """你是一个专业的风险评估专家。请分析以下内容的修改风险：

内容：{content}
上下文：{context}

请按以下格式回答：
- 风险等级：L1（高风险）/ L2（中风险）/ L3（低风险）
- 风险分析：详细说明风险原因
- 建议操作：具体的处理建议
- 置信度：0-1之间的数值""",

            "content_analysis": """你是一个专业的内容分析专家。请深入分析以下内容：

内容：{content}
上下文：{context}

请提供：
- 内容摘要：核心信息概括
- 关键要素：重要信息提取
- 改进建议：具体优化方案
- 质量评分：0-1之间的评分""",

            "optimization": """你是一个专业的优化顾问。请为以下内容提供优化建议：

内容：{content}
上下文：{context}

请提供：
- 优化方向：主要改进方向
- 具体建议：详细优化措施
- 实施步骤：执行方案
- 预期效果：优化后的预期结果"""
        }
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=ClaudeConfig.CONNECTION_POOL_SIZE,
            limit_per_host=ClaudeConfig.MAX_CONCURRENT_REQUESTS,
            keepalive_timeout=ClaudeConfig.KEEPALIVE_TIMEOUT,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=ClaudeConfig.DEFAULT_TIMEOUT)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    def _generate_cache_key(self, messages: List[dict], model: str) -> str:
        """生成缓存键"""
        content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    @lru_cache(maxsize=ClaudeConfig.CACHE_SIZE)
    def _get_cached_result(self, cache_key: str) -> Optional[dict]:
        """获取缓存结果（这里使用LRU缓存，实际项目中可以使用Redis）"""
        return None  # LRU缓存在重启后会丢失，这里返回None表示未命中
    
    async def chat_completion(
        self,
        messages: List[dict],
        model: str = None,
        max_tokens: int = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """聊天完成API"""
        
        start_time = time.time()
        self.api_stats["total_requests"] += 1
        
        # 检查缓存
        cache_key = self._generate_cache_key(messages, model or ClaudeConfig.DEFAULT_MODEL)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            self.api_stats["cache_hits"] += 1
            logger.info(f"缓存命中: {cache_key[:8]}")
            return cached_result
        
        payload = {
            "model": model or ClaudeConfig.DEFAULT_MODEL,
            "max_tokens": max_tokens or ClaudeConfig.MAX_TOKENS,
            "messages": messages,
            "temperature": temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            if stream:
                return await self._stream_completion(payload, headers)
            else:
                result = await self._single_completion(payload, headers)
                
                # 更新统计信息
                response_time = time.time() - start_time
                self.api_stats["total_response_time"] += response_time
                self.api_stats["successful_requests"] += 1
                self.api_stats["average_response_time"] = (
                    self.api_stats["total_response_time"] / self.api_stats["successful_requests"]
                )
                
                return result
                
        except Exception as e:
            self.api_stats["failed_requests"] += 1
            logger.error(f"API调用失败: {str(e)}")
            raise ClaudeAPIException(f"API调用失败: {str(e)}")
    
    async def _single_completion(self, payload: dict, headers: dict) -> dict:
        """单次完成请求（带重试机制）"""
        last_exception = None
        
        for attempt in range(ClaudeConfig.MAX_RETRIES):
            try:
                async with self.session.post(
                    f"{self.base_url}/v1/messages",
                    json=payload,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "data": result,
                            "usage": result.get("usage", {}),
                            "model": payload["model"]
                        }
                    elif response.status == 429:
                        # 处理限流
                        delay = (2 ** attempt) * ClaudeConfig.BASE_DELAY
                        logger.warning(f"API限流，等待 {delay}秒 重试...")
                        await asyncio.sleep(min(delay, ClaudeConfig.MAX_DELAY))
                        continue
                    else:
                        error_text = await response.text()
                        raise ClaudeAPIException(
                            f"HTTP {response.status}: API调用失败",
                            response.status,
                            error_text
                        )
                        
            except asyncio.TimeoutError:
                last_exception = ClaudeAPIException("API调用超时")
                if attempt < ClaudeConfig.MAX_RETRIES - 1:
                    delay = (2 ** attempt) * ClaudeConfig.BASE_DELAY
                    await asyncio.sleep(min(delay, ClaudeConfig.MAX_DELAY))
                    continue
                    
            except Exception as e:
                last_exception = ClaudeAPIException(f"请求异常: {str(e)}")
                if attempt < ClaudeConfig.MAX_RETRIES - 1:
                    delay = ClaudeConfig.BASE_DELAY
                    await asyncio.sleep(delay)
                    continue
        
        raise last_exception or ClaudeAPIException("未知错误")
    
    async def stream_completion(self, messages: List[dict], model: str = None, max_tokens: int = None, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """流式完成请求"""
        payload = {
            "model": model or ClaudeConfig.DEFAULT_MODEL,
            "max_tokens": max_tokens or ClaudeConfig.MAX_TOKENS,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ClaudeAPIException(f"流式请求失败: {response.status} - {error_text}")
                
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith('data: '):
                            content = decoded_line[6:]  # 去除 'data: ' 前缀
                            if content and content != '[DONE]':
                                yield content
                            
        except Exception as e:
            logger.error(f"流式请求异常: {str(e)}")
            raise ClaudeAPIException(f"流式请求异常: {str(e)}")
    
    async def _stream_completion(self, payload: dict, headers: dict) -> AsyncGenerator[str, None]:
        """内部流式完成请求（保留原方法用于兼容）"""
        payload["stream"] = True
        
        try:
            async with self.session.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ClaudeAPIException(f"流式请求失败: {response.status} - {error_text}")
                
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith('data: '):
                            yield decoded_line[6:]  # 去除 'data: ' 前缀
                            
        except Exception as e:
            logger.error(f"流式请求异常: {str(e)}")
            raise ClaudeAPIException(f"流式请求异常: {str(e)}")
    
    async def intelligent_analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """智能分析方法"""
        start_time = time.time()
        
        # 构建分析提示词
        prompt_template = self.analysis_prompts.get(request.analysis_type)
        if not prompt_template:
            raise ClaudeAPIException(f"不支持的分析类型: {request.analysis_type}")
        
        context_str = json.dumps(request.context, ensure_ascii=False, indent=2) if request.context else "无"
        
        analysis_prompt = prompt_template.format(
            content=request.content,
            context=context_str
        )
        
        messages = [
            {"role": "user", "content": analysis_prompt}
        ]
        
        # 调用Claude API
        result = await self.chat_completion(
            messages=messages,
            model=request.model,
            temperature=0.3  # 分析任务使用较低的温度
        )
        
        if not result["success"]:
            raise ClaudeAPIException("智能分析失败")
        
        analysis_text = result["data"]["content"][0]["text"]
        processing_time = time.time() - start_time
        
        # 解析风险等级（简单的文本解析）
        risk_level = None
        confidence = 0.8  # 默认置信度
        
        if "L1" in analysis_text or "高风险" in analysis_text:
            risk_level = "L1"
            confidence = 0.9
        elif "L2" in analysis_text or "中风险" in analysis_text:
            risk_level = "L2"
            confidence = 0.85
        elif "L3" in analysis_text or "低风险" in analysis_text:
            risk_level = "L3"
            confidence = 0.8
        
        # 提取建议操作（简单的文本处理）
        recommendations = []
        lines = analysis_text.split('\n')
        for line in lines:
            if '建议' in line and '：' in line:
                recommendations.append(line.split('：', 1)[1].strip())
        
        return AnalyzeResponse(
            analysis_type=request.analysis_type,
            result=analysis_text,
            confidence=confidence,
            risk_level=risk_level,
            recommendations=recommendations,
            model_used=result["model"],
            processing_time=processing_time,
            timestamp=datetime.now()
        )
    
    async def batch_analyze(self, requests: List[AnalyzeRequest], parallel: bool = True) -> Dict[str, Any]:
        """批量智能分析"""
        start_time = time.time()
        
        if parallel:
            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(ClaudeConfig.MAX_CONCURRENT_REQUESTS)
            
            async def analyze_with_semaphore(req):
                async with semaphore:
                    try:
                        return await self.intelligent_analyze(req), None
                    except Exception as e:
                        return None, str(e)
            
            tasks = [analyze_with_semaphore(req) for req in requests]
            results = await asyncio.gather(*tasks)
        else:
            # 串行处理
            results = []
            for req in requests:
                try:
                    result = await self.intelligent_analyze(req)
                    results.append((result, None))
                except Exception as e:
                    results.append((None, str(e)))
        
        # 统计结果
        successful_results = []
        failed_count = 0
        
        for result, error in results:
            if result:
                successful_results.append(result)
            else:
                failed_count += 1
                logger.error(f"批量分析失败: {error}")
        
        total_processing_time = time.time() - start_time
        
        return {
            "results": successful_results,
            "total_count": len(requests),
            "success_count": len(successful_results),
            "failed_count": failed_count,
            "total_processing_time": total_processing_time
        }
    
    def get_api_stats(self) -> Dict[str, Any]:
        """获取API统计信息"""
        uptime = time.time() - self.start_time
        return {
            **self.api_stats,
            "uptime": uptime,
            "uptime_formatted": f"{uptime:.2f}秒",
            "success_rate": (
                self.api_stats["successful_requests"] / max(self.api_stats["total_requests"], 1)
            ) * 100
        }