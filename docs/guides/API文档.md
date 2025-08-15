# 腾讯文档管理系统 API 文档

**版本**: Enhanced API v2.0.0 + Claude Wrapper v1.0.0  
**更新时间**: 2025-08-12  
**集成状态**: Claude封装程序已完全集成

## 📋 API概述

腾讯文档管理系统提供两层API服务：
1. **Claude封装程序API** (端口8081) - AI语义分析服务
2. **增强版主系统API** (端口5000) - 完整的文档分析和管理服务

## 🚀 Claude封装程序API (端口8081)

### 基础信息
- **Base URL**: `http://localhost:8081`
- **协议**: HTTP/HTTPS
- **认证**: 无需认证 (内部服务)
- **内容类型**: `application/json`

### 1. 健康检查

获取Claude封装程序的健康状态和统计信息。

**接口**: `GET /health`

**响应示例**:
```json
{
  "status": "healthy",
  "service": "Claude Mini Wrapper",
  "version": "1.0.0",
  "uptime": 7235.37,
  "proxy_url": "https://code2.ppchat.vip",
  "models_available": [
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022", 
    "claude-3-7-sonnet-20250219",
    "claude-sonnet-4-20250514-thinking"
  ],
  "api_stats": {
    "total_requests": 149,
    "successful_requests": 131,
    "failed_requests": 18,
    "average_response_time": 14.23,
    "success_rate": 87.92,
    "uptime_formatted": "2小时0分钟"
  }
}
```

### 2. 智能分析

对指定内容进行AI语义分析，支持多种分析类型。

**接口**: `POST /analyze`

**请求参数**:
```json
{
  "content": "要分析的内容",
  "analysis_type": "分析类型",
  "context": {
    "table_name": "表格名称",
    "column_name": "列名", 
    "modification_id": "修改ID"
  }
}
```

**分析类型**:
- `risk_assessment` - 风险评估分析
- `compliance_check` - 合规性检查  
- `content_quality` - 内容质量评估
- `business_impact` - 业务影响分析

**响应示例**:
```json
{
  "analysis_type": "risk_assessment",
  "result": "基于提供的信息，我进行如下风险评估：\n\n**风险等级：L2（中风险）**\n\n**风险分析：**\n1. **权责转移风险**：负责人变更涉及重要职责转移...",
  "confidence": 0.85,
  "risk_level": "L2",
  "recommendations": ["建议1", "建议2"],
  "model_used": "claude-sonnet-4-20250514",
  "processing_time": 10.25,
  "timestamp": "2025-08-12T16:42:45.817821"
}
```

### 3. 模型列表

获取可用的Claude模型列表。

**接口**: `GET /models`

**响应示例**:
```json
{
  "models": [
    {
      "id": "claude-sonnet-4-20250514",
      "name": "Claude Sonnet 4",
      "description": "最新版Claude模型，适合复杂分析任务"
    },
    {
      "id": "claude-3-5-haiku-20241022", 
      "name": "Claude 3.5 Haiku",
      "description": "快速响应模型，适合简单分析"
    }
  ]
}
```

### 4. 批量分析

支持批量处理多个分析请求。

**接口**: `POST /batch/analyze`

**请求参数**:
```json
{
  "requests": [
    {
      "content": "分析内容1",
      "analysis_type": "risk_assessment",
      "context": {...}
    },
    {
      "content": "分析内容2", 
      "analysis_type": "compliance_check",
      "context": {...}
    }
  ]
}
```

**响应示例**:
```json
{
  "batch_id": "batch_20250812_164245_abc123",
  "total_requests": 2,
  "results": [
    {
      "index": 0,
      "status": "success",
      "result": {...}
    },
    {
      "index": 1,
      "status": "success", 
      "result": {...}
    }
  ],
  "processing_summary": {
    "total_time": 25.67,
    "average_time": 12.84,
    "success_count": 2,
    "failure_count": 0
  }
}
```

## 🏗️ 增强版主系统API (端口5000)

### 基础信息
- **Base URL**: `http://localhost:5000`
- **协议**: HTTP/HTTPS
- **认证**: 基于用户名的简单认证
- **内容类型**: `application/json` 或 `multipart/form-data`

### 1. 系统健康检查

获取整个系统的健康状态，包括所有组件的状态。

**接口**: `GET /api/health`

**响应示例**:
```json
{
  "status": "healthy",
  "service": "腾讯文档管理系统 - 增强版",
  "version": "2.0.0",
  "timestamp": "2025-08-12T17:30:15.123456",
  "component_status": {
    "document_analyzer": true,
    "adaptive_comparator": true,
    "column_matcher": true,
    "ai_analyzer": true,
    "excel_visualizer": true,
    "database": true
  },
  "system_stats": {
    "total_analyses": 15,
    "successful_analyses": 14,
    "success_rate": 0.933,
    "ai_analyses_performed": 8,
    "visualizations_created": 3,
    "uptime_hours": 2.5
  }
}
```

### 2. 用户管理

#### 保存用户Cookies
保存用户的腾讯文档认证信息。

**接口**: `POST /api/save_cookies`

**请求参数**:
```json
{
  "username": "用户名",
  "cookies": "加密的cookies字符串"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "Cookies保存成功",
  "username": "test_user"
}
```

### 3. 文档分析

#### 单文件分析
对单个文件进行全面的智能分析。

**接口**: `POST /api/v2/analysis/single`  
**Content-Type**: `multipart/form-data`

**请求参数**:
- `file` (文件): 要分析的文件 (支持CSV、Excel格式)
- `username` (字符串): 用户名
- `enable_ai` (布尔): 是否启用AI分析 (默认true)
- `enable_visualization` (布尔): 是否启用可视化 (默认true)

**响应示例**:
```json
{
  "success": true,
  "message": "单文件分析作业已创建",
  "job_id": "single_analysis_1723464123_abc123def",
  "file_name": "项目管理表.csv",
  "config": {
    "enable_ai_analysis": true,
    "enable_visualization": true,
    "file_paths": ["/path/to/uploaded/file.csv"]
  }
}
```

#### 批量文件分析
对多个文件进行批量分析比较。

**接口**: `POST /api/v2/analysis/batch`  
**Content-Type**: `multipart/form-data`

**请求参数**:
- `files` (文件列表): 要分析的多个文件
- `reference_file` (文件,可选): 参考对比文件
- `username` (字符串): 用户名
- `enable_ai` (布尔): 是否启用AI分析
- `enable_visualization` (布尔): 是否启用可视化
- `job_name` (字符串,可选): 自定义作业名称

**响应示例**:
```json
{
  "success": true,
  "message": "批量分析作业已创建，共5个文件",
  "job_id": "batch_analysis_1723464456_xyz789",
  "job_name": "项目管理表批量分析-20250812",
  "total_files": 5,
  "config": {
    "ai_analysis_enabled": true,
    "visualization_enabled": true,
    "has_reference_file": true
  }
}
```

### 4. 作业管理

#### 获取作业状态
查询分析作业的执行状态。

**接口**: `GET /api/v2/jobs/{job_id}/status`

**路径参数**:
- `job_id`: 作业ID

**响应示例**:
```json
{
  "success": true,
  "job_status": {
    "job_id": "single_analysis_1723464123_abc123def",
    "job_name": "单文件分析-项目管理表.csv",
    "job_type": "single_analysis",
    "status": "completed",
    "progress": 100.0,
    "result_path": "/path/to/result.json",
    "error_message": null,
    "created_at": "2025-08-12T17:42:03.123456",
    "started_at": "2025-08-12T17:42:05.234567", 
    "completed_at": "2025-08-12T17:43:15.345678",
    "processing_time_seconds": 70.11
  }
}
```

**状态值说明**:
- `created` - 已创建，等待执行
- `running` - 正在执行
- `completed` - 执行完成
- `failed` - 执行失败

#### 获取作业结果
获取已完成作业的分析结果。

**接口**: `GET /api/v2/jobs/{job_id}/result`

**响应示例**:
```json
{
  "success": true,
  "job_id": "single_analysis_1723464123_abc123def",
  "result": {
    "job_id": "single_analysis_1723464123_abc123def",
    "analysis_timestamp": "2025-08-12T17:43:15.123456",
    "file_paths": ["/path/to/file.csv"],
    "processing_summary": {
      "total_processing_time": 70.11,
      "files_processed": 1,
      "phases_completed": 4,
      "ai_analysis_enabled": true,
      "visualization_enabled": true,
      "success": true
    },
    "adaptive_comparison_results": {
      "comparison_results": [...],
      "processing_stats": {...}
    },
    "ai_analysis_results": {
      "individual_analyses": {
        "mod_id_1": {
          "recommendation": "REVIEW",
          "confidence": 0.85,
          "reasoning": "详细分析结果...",
          "business_impact": "MEDIUM",
          "suggested_action": "需要人工审核",
          "risk_factors": ["风险因素1", "风险因素2"]
        }
      },
      "summary": {
        "total_analyzed": 3,
        "recommendation_distribution": {"REVIEW": 2, "APPROVE": 1},
        "average_confidence": 0.82
      }
    },
    "visualization_results": {
      "report_path": "/path/to/analysis_report.xlsx",
      "visualization_type": "comprehensive_risk_report",
      "generated_at": "2025-08-12T17:43:10.123456"
    },
    "risk_summary": {
      "overall_risk_level": "MEDIUM",
      "critical_issues_count": 0,
      "high_risk_issues_count": 1,
      "medium_risk_issues_count": 2,
      "l1_violations": 0,
      "l2_modifications": 3,
      "l3_modifications": 5
    },
    "recommendations": [
      {
        "priority": "medium",
        "category": "review",
        "title": "需要语义审核的修改",
        "description": "3个L2级别修改需要人工确认",
        "action_items": [
          "安排业务专家审核L2级别修改",
          "确认修改符合业务规则"
        ],
        "estimated_effort": "3-5个工作日"
      }
    ]
  }
}
```

#### 下载分析报告
下载分析结果文件（Excel报告或JSON数据）。

**接口**: `GET /api/v2/jobs/{job_id}/download`

**响应**: 直接返回文件下载

### 5. 作业列表

获取用户的作业历史列表。

**接口**: `GET /api/v2/jobs`

**查询参数**:
- `username` (字符串,可选): 用户名过滤
- `status` (字符串,可选): 状态过滤
- `limit` (整数,可选): 返回数量限制 (默认50)

**响应示例**:
```json
{
  "success": true,
  "jobs": [
    {
      "job_id": "batch_analysis_1723464456_xyz789",
      "job_name": "项目管理表批量分析-20250812",
      "job_type": "batch_analysis",
      "status": "completed",
      "progress": 100.0,
      "created_at": "2025-08-12T17:40:56.123456",
      "started_at": "2025-08-12T17:41:00.234567",
      "completed_at": "2025-08-12T17:45:30.345678",
      "username": "test_user"
    }
  ],
  "total_count": 1
}
```

### 6. 系统统计

获取系统整体运行统计信息。

**接口**: `GET /api/v2/system/stats`

**响应示例**:
```json
{
  "success": true,
  "system_statistics": {
    "service_info": {
      "version": "2.0.0",
      "uptime_hours": 2.5,
      "start_time": "2025-08-12T15:00:00.000000"
    },
    "users": {
      "total_registered": 5
    },
    "jobs": {
      "total_jobs": 15,
      "status_distribution": {
        "completed": 12,
        "failed": 2,
        "running": 1
      },
      "jobs_last_24h": 15,
      "jobs_last_7d": 15
    },
    "processing": {
      "total_analyses": 15,
      "successful_analyses": 14,
      "failed_analyses": 1,
      "success_rate": 0.933,
      "ai_analyses_performed": 8,
      "visualizations_created": 3
    },
    "components": {
      "ai_analyzer_available": true,
      "claude_api_configured": false,
      "excel_visualizer_available": true,
      "adaptive_comparator_available": true
    }
  }
}
```

## 📊 错误响应格式

所有API接口在出现错误时返回统一的错误格式：

```json
{
  "success": false,
  "error": "错误描述信息",
  "error_code": "ERROR_CODE",
  "details": {
    "additional_info": "额外错误信息"
  }
}
```

**常见错误码**:
- `INVALID_REQUEST` - 请求参数无效
- `USER_NOT_FOUND` - 用户不存在
- `JOB_NOT_FOUND` - 作业不存在  
- `AI_SERVICE_UNAVAILABLE` - AI服务不可用
- `PROCESSING_TIMEOUT` - 处理超时
- `INTERNAL_SERVER_ERROR` - 服务器内部错误

## 🔄 集成流程示例

### 完整的文档分析流程

```bash
# 1. 检查系统健康状态
curl -X GET http://localhost:5000/api/health

# 2. 保存用户认证信息 (如果需要)
curl -X POST http://localhost:5000/api/save_cookies \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","cookies":"encrypted_cookies"}'

# 3. 上传文件进行分析
curl -X POST http://localhost:5000/api/v2/analysis/single \
  -F "file=@项目管理表.csv" \
  -F "username=test_user" \
  -F "enable_ai=true" \
  -F "enable_visualization=true"

# 响应: {"success":true,"job_id":"single_analysis_123456"}

# 4. 查询分析状态
curl -X GET http://localhost:5000/api/v2/jobs/single_analysis_123456/status

# 5. 获取分析结果 (状态为completed后)
curl -X GET http://localhost:5000/api/v2/jobs/single_analysis_123456/result

# 6. 下载Excel报告
curl -X GET http://localhost:5000/api/v2/jobs/single_analysis_123456/download \
  -o analysis_report.xlsx
```

### 直接使用Claude分析服务

```bash
# 1. 检查Claude服务健康状态
curl -X GET http://localhost:8081/health

# 2. 进行风险评估分析
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "负责人从张三改为李四", 
    "analysis_type": "risk_assessment",
    "context": {
      "table_name": "项目管理表",
      "column_name": "负责人"
    }
  }'

# 响应包含分析结果、置信度、风险等级等信息
```

## 🛡️ 安全说明

### 认证方式
- **主系统**: 基于用户名的简单认证，支持Cookie存储
- **Claude封装程序**: 内部服务，无需认证

### 数据安全
- 用户Cookies使用AES-256加密存储
- 所有API访问记录完整的审计日志
- 支持HTTPS加密传输 (生产环境)

### 访问控制
- API请求频率限制
- 文件大小限制 (500MB)
- 处理超时控制 (5分钟)

## 📈 性能指标

### 系统容量
- **并发处理**: 最大3个并发分析作业
- **文件大小**: 单文件最大500MB
- **批处理**: 最大30个文件批量处理
- **API频率**: 未设置严格限制 (内部服务)

### 响应时间
- **健康检查**: < 100ms
- **单次AI分析**: 10-15秒
- **批量AI分析**: 平均12秒/个
- **文件分析**: 依据文件大小和复杂度

### 可用性
- **Claude封装程序**: 88%+ API成功率
- **主系统**: 93%+ 分析成功率
- **系统稳定性**: 100% (测试环境)

---

## 📞 技术支持

### 开发团队
- **系统架构**: Claude Code System Integration Team
- **AI集成**: Claude Wrapper Development Team  
- **文档维护**: Technical Documentation Team

### 故障排查
1. **AI分析失败**: 检查Claude封装程序健康状态
2. **文件解析错误**: 验证文件格式和编码
3. **系统响应慢**: 检查并发作业数量和资源使用
4. **可视化生成失败**: 确认Excel MCP服务状态

### 监控告警
- 系统健康检查端点: `/api/health`
- Claude服务健康检查: `:8081/health`  
- 详细系统统计: `/api/v2/system/stats`

---
**API文档版本**: v2.0.0  
**最后更新**: 2025-08-12  
**维护团队**: Claude Code System Integration Team