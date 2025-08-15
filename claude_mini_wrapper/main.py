from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import time
import uuid
import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from config import ClaudeConfig
from models import (
    ChatRequest, ChatResponse, ChatMessage,
    AnalyzeRequest, AnalyzeResponse,
    BatchAnalyzeRequest, BatchAnalyzeResponse,
    HealthResponse, ErrorResponse
)
from claude_client import ClaudeClientWrapper, ClaudeAPIException

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Claude Mini Wrapper",
    description="最小Claude API封装服务 - 基于现有代理和SKR码的智能分析接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局Claude客户端
claude_client = ClaudeClientWrapper()

# 启动时间记录
start_time = time.time()

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 Claude Mini Wrapper 启动中...")
    
    # 验证配置
    if not ClaudeConfig.validate_config():
        logger.error("❌ 配置验证失败，服务可能无法正常工作")
    else:
        logger.info("✅ 配置验证成功")
    
    # 测试API连接
    try:
        async with claude_client as client:
            test_result = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello, this is a connection test."}],
                max_tokens=10
            )
            if test_result.get("success"):
                logger.info("✅ Claude API连接测试成功")
            else:
                logger.warning("⚠️ Claude API连接测试失败")
    except Exception as e:
        logger.error(f"❌ Claude API连接测试异常: {str(e)}")
    
    logger.info(f"🎯 服务已启动: http://{ClaudeConfig.HOST}:{ClaudeConfig.PORT}")
    logger.info(f"📚 API文档: http://{ClaudeConfig.HOST}:{ClaudeConfig.PORT}/docs")

@app.exception_handler(ClaudeAPIException)
async def claude_api_exception_handler(request, exc: ClaudeAPIException):
    """Claude API异常处理器"""
    return HTTPException(
        status_code=exc.status_code or 500,
        detail={
            "error": "Claude API Error",
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """请求验证异常处理器"""
    return HTTPException(
        status_code=422,
        detail={
            "error": "Validation Error",
            "message": "请求参数验证失败",
            "details": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口
    
    返回服务运行状态、配置信息和API统计
    """
    uptime = time.time() - start_time
    api_stats = claude_client.get_api_stats()
    
    return HealthResponse(
        status="healthy",
        service="Claude Mini Wrapper",
        version="1.0.0",
        uptime=uptime,
        proxy_url=ClaudeConfig.BASE_URL,
        models_available=[model["id"] for model in ClaudeConfig.get_available_models()],
        api_stats=api_stats
    )

@app.get("/models")
async def list_models():
    """
    获取可用模型列表
    
    返回所有配置的Claude模型信息
    """
    return {
        "models": ClaudeConfig.get_available_models(),
        "default_model": ClaudeConfig.DEFAULT_MODEL
    }

@app.post("/chat")
async def chat_completion(request: ChatRequest):
    """
    标准聊天完成接口
    
    兼容OpenAI API格式的聊天接口
    """
    try:
        async with claude_client as client:
            result = await client.chat_completion(
                messages=[msg.dict() for msg in request.messages],
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False
            )
            
            if result["success"]:
                # 构建OpenAI格式响应
                response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                created = int(time.time())
                
                return {
                    "id": response_id,
                    "object": "chat.completion",
                    "created": created,
                    "model": result["model"],
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result["data"]["content"][0]["text"]
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": result.get("usage", {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    })
                }
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "未知错误"))
                
    except ClaudeAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"聊天完成接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口
    
    支持服务器发送事件(SSE)的实时流式响应
    """
    try:
        async def generate_stream():
            response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            created = int(time.time())
            
            async with claude_client as client:
                async for chunk in client.stream_completion(
                    messages=[msg.dict() for msg in request.messages],
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    # 构建流式响应格式
                    if chunk and chunk != "[DONE]":
                        try:
                            # 尝试解析JSON内容
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("content"):
                                stream_data = {
                                    "id": response_id,
                                    "object": "chat.completion.chunk",
                                    "created": created,
                                    "model": request.model or ClaudeConfig.DEFAULT_MODEL,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"content": chunk_data["content"]},
                                        "finish_reason": None
                                    }]
                                }
                                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            # 如果不是JSON，直接作为文本内容
                            stream_data = {
                                "id": response_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": request.model or ClaudeConfig.DEFAULT_MODEL,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": chunk},
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                
                # 发送结束标记
                final_chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk", 
                    "created": created,
                    "model": request.model or ClaudeConfig.DEFAULT_MODEL,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"流式聊天接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"流式处理失败: {str(e)}")

@app.post("/analyze", response_model=AnalyzeResponse)
async def intelligent_analyze(request: AnalyzeRequest):
    """
    智能分析接口
    
    专门针对腾讯文档场景的智能分析功能
    支持风险评估、内容分析、优化建议等分析类型
    """
    try:
        async with claude_client as client:
            result = await client.intelligent_analyze(request)
            return result
            
    except ClaudeAPIException as e:
        logger.error(f"智能分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"智能分析失败: {str(e)}")
    except Exception as e:
        logger.error(f"智能分析接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

@app.post("/batch", response_model=BatchAnalyzeResponse)
async def batch_analyze(request: BatchAnalyzeRequest):
    """
    批量分析接口
    
    支持批量处理多个智能分析请求
    可选择并行或串行处理模式
    """
    try:
        async with claude_client as client:
            batch_result = await client.batch_analyze(
                request.requests, 
                request.parallel
            )
            
            return BatchAnalyzeResponse(**batch_result)
            
    except Exception as e:
        logger.error(f"批量分析接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")

@app.get("/stats")
async def get_api_stats():
    """
    获取API统计信息
    
    返回详细的API调用统计和性能指标
    """
    stats = claude_client.get_api_stats()
    uptime = time.time() - start_time
    
    return {
        "service_info": {
            "name": "Claude Mini Wrapper",
            "version": "1.0.0",
            "uptime": uptime,
            "uptime_formatted": f"{int(uptime//3600)}h{int((uptime%3600)//60)}m{int(uptime%60)}s"
        },
        "api_statistics": stats,
        "configuration": {
            "default_model": ClaudeConfig.DEFAULT_MODEL,
            "max_tokens": ClaudeConfig.MAX_TOKENS,
            "max_concurrent": ClaudeConfig.MAX_CONCURRENT_REQUESTS,
            "timeout": ClaudeConfig.DEFAULT_TIMEOUT
        }
    }

@app.get("/")
async def root():
    """根路径接口 - 服务信息"""
    return {
        "service": "Claude Mini Wrapper",
        "version": "1.0.0",
        "description": "基于现有代理和SKR码的Claude API封装服务",
        "endpoints": {
            "health": "/health",
            "models": "/models", 
            "chat": "/chat",
            "chat_stream": "/chat/stream",
            "analyze": "/analyze",
            "batch": "/batch",
            "stats": "/stats",
            "docs": "/docs"
        },
        "proxy_url": ClaudeConfig.BASE_URL,
        "status": "running"
    }

if __name__ == "__main__":
    logger.info("🚀 启动 Claude Mini Wrapper...")
    
    # 验证配置
    if not ClaudeConfig.validate_config():
        logger.error("❌ 配置验证失败，请检查环境变量")
        exit(1)
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=ClaudeConfig.HOST,
        port=ClaudeConfig.PORT,
        reload=False,  # 生产环境建议设置为False
        access_log=True
    )