from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色：user, assistant, system")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="使用的模型，不指定则使用默认模型")
    max_tokens: Optional[int] = Field(4000, description="最大生成token数", ge=1, le=8000)
    temperature: Optional[float] = Field(0.7, description="温度参数", ge=0.0, le=2.0)
    stream: Optional[bool] = Field(False, description="是否流式返回")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str = Field(..., description="响应ID")
    object: str = Field("chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    choices: List[Dict[str, Any]] = Field(..., description="响应选择")
    usage: Dict[str, int] = Field(..., description="使用统计")

class AnalyzeRequest(BaseModel):
    """智能分析请求模型"""
    content: str = Field(..., description="待分析的内容")
    analysis_type: str = Field(..., description="分析类型：risk_assessment, content_analysis, optimization")
    context: Optional[Dict[str, Any]] = Field({}, description="分析上下文信息")
    model: Optional[str] = Field(None, description="使用的模型")

class AnalyzeResponse(BaseModel):
    """智能分析响应模型"""
    analysis_type: str = Field(..., description="分析类型")
    result: str = Field(..., description="分析结果")
    confidence: float = Field(..., description="置信度评分", ge=0.0, le=1.0)
    risk_level: Optional[str] = Field(None, description="风险等级：L1, L2, L3")
    recommendations: List[str] = Field([], description="建议操作")
    model_used: str = Field(..., description="使用的模型")
    processing_time: float = Field(..., description="处理时间（秒）")
    timestamp: datetime = Field(..., description="分析时间戳")

class BatchAnalyzeRequest(BaseModel):
    """批量分析请求模型"""
    requests: List[AnalyzeRequest] = Field(..., description="分析请求列表", min_items=1, max_items=20)
    parallel: Optional[bool] = Field(True, description="是否并行处理")

class BatchAnalyzeResponse(BaseModel):
    """批量分析响应模型"""
    results: List[AnalyzeResponse] = Field(..., description="分析结果列表")
    total_count: int = Field(..., description="总处理数量")
    success_count: int = Field(..., description="成功处理数量")
    failed_count: int = Field(..., description="失败处理数量")
    total_processing_time: float = Field(..., description="总处理时间（秒）")

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="版本号")
    uptime: float = Field(..., description="运行时间（秒）")
    proxy_url: str = Field(..., description="代理URL")
    models_available: List[str] = Field(..., description="可用模型列表")
    api_stats: Dict[str, Any] = Field(..., description="API统计信息")

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[str] = Field(None, description="错误详情")
    timestamp: datetime = Field(..., description="错误时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")