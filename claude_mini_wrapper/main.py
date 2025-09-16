from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
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

# 挂载静态文件目录
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

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

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回Web UI界面"""
    html_file = os.path.join(static_dir, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Claude AI API Service</h1><p>UI file not found. API is running at port 8081.</p>")

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

@app.post("/api/ai-column-mapping")
async def ai_column_mapping(request: dict):
    """
    列名标准化API接口
    
    专门处理CSV差异文件中的列名标准化
    集成IntelligentColumnMatcher进行智能列匹配
    """
    try:
        # 提取差异文件中的列名
        differences = request.get("differences", [])
        columns = list(set([diff.get("列名", "") for diff in differences if diff.get("列名")]))
        
        if not columns:
            return {
                "success": False,
                "error": "未找到有效的列名数据",
                "mapping": {},
                "confidence_scores": {}
            }
        
        # 创建分析请求
        analyze_request = AnalyzeRequest(
            content=f"请对以下CSV列名进行标准化映射分析，将实际列名映射到标准列名。实际列名：{columns}。请返回映射关系和置信度分数。",
            analysis_type="content_analysis",
            context={
                "columns": columns,
                "standard_columns": [
                    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
                    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
                    "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
                    "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
                ],
                "task": "column_standardization"
            }
        )
        
        # 调用Claude AI进行智能分析
        async with claude_client as client:
            result = await client.intelligent_analyze(analyze_request)
            
            # 处理AnalyzeResponse对象
            if hasattr(result, 'dict'):
                result_dict = result.dict()
            elif hasattr(result, '__dict__'):
                result_dict = result.__dict__
            else:
                result_dict = result
            
            # 构建标准化响应
            response = {
                "success": True,
                "mapping": result_dict.get("analysis_result", {}).get("mapping", {}),
                "confidence_scores": result_dict.get("analysis_result", {}).get("confidence_scores", {}),
                "analysis_result": result_dict,
                "processed_columns": columns,
                "timestamp": time.time()
            }
            
            return response
            
    except Exception as e:
        logger.error(f"列名标准化失败: {str(e)}")
        return {
            "success": False,
            "error": f"列名标准化失败: {str(e)}",
            "mapping": {},
            "confidence_scores": {}
        }

@app.post("/api/l2-semantic-analysis")
async def l2_semantic_analysis(request: dict):
    """
    L2级语义分析接口
    
    接收第三步列名标准化结果，对L2级字段进行智能语义分析
    提供APPROVE/REJECT/REVIEW/CONDITIONAL决策建议
    """
    try:
        # 提取第三步输出的数据
        processed_columns = request.get("processed_columns", [])
        differences = request.get("original_differences", [])
        
        if not processed_columns or not differences:
            return {
                "success": False,
                "error": "缺少必要的输入数据：processed_columns或original_differences",
                "l2_analysis_results": []
            }
        
        # 定义L2级字段（需要语义审核的字段）
        l2_fields = [
            "项目类型", "具体计划内容", "邓总指导登记", "负责人", 
            "协助人", "监督人", "形成计划清单"
        ]
        
        # 筛选L2级字段的变更
        l2_changes = []
        for diff in differences:
            column_name = diff.get("列名", "")
            if column_name in l2_fields and column_name in processed_columns:
                l2_changes.append({
                    "column_name": column_name,
                    "original_value": diff.get("原值", ""),
                    "new_value": diff.get("新值", ""),
                    "row_number": diff.get("行号", 0),
                    "position": diff.get("位置", "")
                })
        
        if not l2_changes:
            return {
                "success": True,
                "message": "未发现L2级字段变更，无需语义分析",
                "l2_analysis_results": [],
                "summary": {
                    "total_l2_changes": 0,
                    "approved": 0,
                    "rejected": 0,
                    "review_required": 0,
                    "conditional": 0
                }
            }
        
        # 对每个L2字段变更进行语义分析
        analysis_results = []
        
        for change in l2_changes:
            # 构建语义分析请求
            analyze_request = AnalyzeRequest(
                content=f"对L2级字段[{change['column_name']}]的修改进行专业语义分析：\n原值：{change['original_value']}\n新值：{change['new_value']}\n请判断这个修改的合理性和风险级别。",
                analysis_type="risk_assessment",
                context={
                    "column_name": change['column_name'],
                    "original_value": change['original_value'],
                    "new_value": change['new_value'],
                    "risk_level": "L2",
                    "business_context": "项目管理系统",
                    "position": change['position']
                }
            )
            
            # 调用Claude进行语义分析
            async with claude_client as client:
                result = await client.intelligent_analyze(analyze_request)
                
                # 解析分析结果
                if hasattr(result, 'dict'):
                    result_dict = result.dict()
                elif hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                else:
                    result_dict = result
                
                # 提取决策建议（简单解析）
                analysis_text = result_dict.get("result", "")
                confidence = result_dict.get("confidence", 0.5)
                
                # 简单的决策逻辑
                decision = "REVIEW"
                if "APPROVE" in analysis_text.upper() or "批准" in analysis_text or "同意" in analysis_text:
                    decision = "APPROVE"
                elif "REJECT" in analysis_text.upper() or "拒绝" in analysis_text or "不合理" in analysis_text:
                    decision = "REJECT"
                elif "CONDITIONAL" in analysis_text.upper() or "条件" in analysis_text:
                    decision = "CONDITIONAL"
                
                analysis_results.append({
                    "column_name": change['column_name'],
                    "original_value": change['original_value'],
                    "new_value": change['new_value'],
                    "position": change['position'],
                    "decision": decision,
                    "confidence_score": confidence,
                    "analysis_result": analysis_text,
                    "risk_level": result_dict.get("risk_level", "L2"),
                    "processing_time": result_dict.get("processing_time", 0),
                    "timestamp": time.time()
                })
        
        # 统计分析结果
        summary = {
            "total_l2_changes": len(analysis_results),
            "approved": len([r for r in analysis_results if r["decision"] == "APPROVE"]),
            "rejected": len([r for r in analysis_results if r["decision"] == "REJECT"]),
            "review_required": len([r for r in analysis_results if r["decision"] == "REVIEW"]),
            "conditional": len([r for r in analysis_results if r["decision"] == "CONDITIONAL"]),
            "average_confidence": sum(r["confidence_score"] for r in analysis_results) / len(analysis_results) if analysis_results else 0
        }
        
        return {
            "success": True,
            "l2_analysis_results": analysis_results,
            "summary": summary,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"L2语义分析失败: {str(e)}")
        return {
            "success": False,
            "error": f"L2语义分析失败: {str(e)}",
            "l2_analysis_results": []
        }

@app.post("/api/risk-scoring")
async def risk_scoring(request: dict):
    """
    第五步: 数据按规则打分
    
    基于L1/L2/L3风险等级和第四步AI分析结果重新计算风险分数
    集成document_change_analyzer.py的风险评级算法
    """
    try:
        logger.info(f"🎯 开始第五步风险评分处理")
        
        # 提取输入数据
        l2_analysis_results = request.get("l2_analysis_results", [])
        original_differences = request.get("original_differences", [])
        processed_columns = request.get("processed_columns", [])
        
        if not original_differences:
            return {
                "success": False,
                "error": "缺少原始差异数据",
                "risk_scoring_results": []
            }
        
        logger.info(f"📊 输入数据: {len(original_differences)}个差异, {len(l2_analysis_results)}个L2分析结果")
        
        # 定义列风险等级配置
        column_risk_levels = {
            "序号": "L3",                    # 可自由编辑
            "项目类型": "L2",                # 需要语义审核  
            "来源": "L1",                    # 绝对不能修改
            "任务发起时间": "L1",            # 绝对不能修改
            "目标对齐": "L1",                # 绝对不能修改
            "关键KR对齐": "L1",              # 绝对不能修改
            "具体计划内容": "L2",            # 需要语义审核
            "邓总指导登记": "L2",            # 需要语义审核
            "负责人": "L2",                  # 需要语义审核
            "协助人": "L2",                  # 需要语义审核
            "监督人": "L2",                  # 需要语义审核
            "重要程度": "L1",                # 绝对不能修改
            "预计完成时间": "L1",            # 绝对不能修改
            "完成进度": "L1",                # 绝对不能修改
            "形成计划清单": "L2",            # 需要语义审核
            "复盘时间": "L3",                # 可自由编辑
            "对上汇报": "L3",                # 可自由编辑
            "应用情况": "L3",                # 可自由编辑
            "进度分析总结": "L3",            # 可自由编辑
            "周度分析总结": "L3"             # 可自由编辑
        }
        
        # 基础风险评分配置
        base_risk_scores = {
            "L1": 1.0,    # 最高风险
            "L2": 0.6,    # 中等风险
            "L3": 0.2     # 最低风险
        }
        
        # 创建L2分析结果查找表
        l2_analysis_lookup = {}
        for result in l2_analysis_results:
            key = f"{result.get('column_name', '')}_{result.get('position', '')}"
            l2_analysis_lookup[key] = result
        
        # 处理每个差异并计算风险分数
        risk_scoring_results = []
        risk_distribution = {"L1": 0, "L2": 0, "L3": 0}
        
        for diff in original_differences:
            column_name = diff.get("列名", "")
            position = diff.get("位置", "")
            
            # 获取基础风险等级
            base_risk_level = column_risk_levels.get(column_name, "L3")
            base_risk_score = base_risk_scores[base_risk_level]
            
            # 查找对应的L2分析结果
            lookup_key = f"{column_name}_{position}"
            l2_result = l2_analysis_lookup.get(lookup_key)
            
            # 计算调整后的风险分数
            adjusted_risk_score = base_risk_score
            final_risk_level = base_risk_level
            ai_adjustment_factor = 1.0
            
            if l2_result:
                # 基于AI决策调整风险分数
                ai_decision = l2_result.get("decision", "REVIEW")
                ai_confidence = l2_result.get("confidence_score", 0.5)
                ai_risk_level = l2_result.get("risk_level", base_risk_level)
                
                # 决策权重调整
                decision_weights = {
                    "APPROVE": 0.7,      # 降低风险
                    "REVIEW": 1.0,       # 保持原风险
                    "REJECT": 1.5,       # 提高风险
                    "CONDITIONAL": 1.2   # 略微提高风险
                }
                
                # 置信度权重调整
                confidence_factor = 0.5 + (ai_confidence * 0.5)  # 0.5-1.0范围
                
                # 综合调整系数
                ai_adjustment_factor = decision_weights.get(ai_decision, 1.0) * confidence_factor
                
                # AI风险等级优先级处理
                if ai_risk_level in base_risk_scores:
                    ai_risk_score = base_risk_scores[ai_risk_level]
                    # 使用加权平均
                    adjusted_risk_score = (base_risk_score * 0.4) + (ai_risk_score * 0.6)
                    adjusted_risk_score *= ai_adjustment_factor
                    
                    # 确定最终风险等级
                    if adjusted_risk_score >= 0.8:
                        final_risk_level = "L1"
                    elif adjusted_risk_score >= 0.4:
                        final_risk_level = "L2"
                    else:
                        final_risk_level = "L3"
                else:
                    adjusted_risk_score = base_risk_score * ai_adjustment_factor
            
            # 限制分数范围
            adjusted_risk_score = max(0.0, min(1.0, adjusted_risk_score))
            
            # 统计风险分布
            risk_distribution[final_risk_level] += 1
            
            # 构建风险评分结果
            scoring_result = {
                "序号": diff.get("序号", 0),
                "行号": diff.get("行号", 0),
                "列名": column_name,
                "位置": position,
                "原值": diff.get("原值", ""),
                "新值": diff.get("新值", ""),
                "base_risk_level": base_risk_level,
                "base_risk_score": base_risk_score,
                "final_risk_level": final_risk_level,
                "adjusted_risk_score": round(adjusted_risk_score, 3),
                "ai_adjustment_factor": round(ai_adjustment_factor, 3),
                "ai_decision": l2_result.get("decision", "N/A") if l2_result else "N/A",
                "ai_confidence": l2_result.get("confidence_score", 0.0) if l2_result else 0.0,
                "has_ai_analysis": bool(l2_result)
            }
            
            risk_scoring_results.append(scoring_result)
        
        # 计算汇总统计
        total_changes = len(risk_scoring_results)
        average_risk_score = sum(r["adjusted_risk_score"] for r in risk_scoring_results) / total_changes if total_changes > 0 else 0
        ai_analyzed_count = sum(1 for r in risk_scoring_results if r["has_ai_analysis"])
        
        summary = {
            "total_changes": total_changes,
            "ai_analyzed_changes": ai_analyzed_count,
            "ai_analysis_coverage": round(ai_analyzed_count / total_changes * 100, 1) if total_changes > 0 else 0,
            "risk_distribution": risk_distribution,
            "average_risk_score": round(average_risk_score, 3),
            "highest_risk_score": max(r["adjusted_risk_score"] for r in risk_scoring_results) if risk_scoring_results else 0,
            "lowest_risk_score": min(r["adjusted_risk_score"] for r in risk_scoring_results) if risk_scoring_results else 0,
            "l1_high_risk_count": risk_distribution["L1"],
            "l2_medium_risk_count": risk_distribution["L2"],
            "l3_low_risk_count": risk_distribution["L3"]
        }
        
        logger.info(f"✅ 第五步风险评分完成: {total_changes}个变更, 平均风险{average_risk_score:.3f}")
        
        return {
            "success": True,
            "risk_scoring_results": risk_scoring_results,
            "summary": summary,
            "processing_info": {
                "total_processed": total_changes,
                "ai_enhanced": ai_analyzed_count,
                "base_algorithm": "document_change_analyzer",
                "ai_integration": "l2_semantic_analysis",
                "risk_levels": list(column_risk_levels.keys()),
                "adjustment_factors": ["decision_weight", "confidence_factor", "risk_level_override"]
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"风险评分失败: {str(e)}")
        return {
            "success": False,
            "error": f"风险评分失败: {str(e)}",
            "risk_scoring_results": []
        }

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