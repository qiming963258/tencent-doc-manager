# 腾讯文档监控系统 - 架构设计文档 v2.0
_更新日期: 2025-09-15_

## 🏗️ 系统架构概述

本系统采用**前后端分离架构**，通过RESTful API进行通信：

```
┌─────────────────────────────────────────────┐
│          用户浏览器 (http://202.140.143.88:8089)         │
└─────────────────┬───────────────────────────┘
                  │ HTTP/AJAX
                  ▼
┌─────────────────────────────────────────────┐
│     前端UI服务 (8089端口)                    │
│     - React热力图组件                        │
│     - 监控设置面板                           │
│     - 实时日志显示                           │
│     - API代理层                              │
└─────────────────┬───────────────────────────┘
                  │ REST API
                  ▼
┌─────────────────────────────────────────────┐
│     后端API服务 (8093端口)                   │
│     - 文档下载引擎                           │
│     - CSV对比分析                            │
│     - AI语义分析                             │
│     - Excel标记生成                          │
│     - 工作流管理                             │
└─────────────────────────────────────────────┘
```

## 📦 服务组件详解

### 1. 后端API服务 (端口 8093)
**文件**: `production_integrated_test_system_8093.py`

**核心功能**:
- 完整的文档处理工作流
- 腾讯文档下载与版本管理
- CSV智能对比分析
- DeepSeek AI语义分析
- Excel半填充标记生成
- 实时状态与日志管理

**API端点**:
```
GET  /api/status          - 获取工作流状态
POST /api/start           - 启动文档处理
POST /api/stop            - 停止工作流
GET  /api/logs            - 获取详细日志
GET  /api/results         - 获取处理结果
```

### 2. 前端UI服务 (端口 8089)
**文件**: `production/servers/final_heatmap_server.py`

**核心功能**:
- 科学热力图可视化
- 监控设置管理界面
- 实时日志展示
- 基线文件管理
- API请求代理

**特色功能**:
- 高斯平滑算法热力图
- 动态N×19矩阵显示
- 智能数据排序
- URL软删除管理
- 基线文件归档

## 🔄 数据流程

### 刷新工作流
```
1. 用户点击"立即刷新"
   ↓
2. 8089发送请求到8093 (baseline_url=null)
   ↓
3. 8093使用现有基线文件
   ↓
4. 8093下载最新目标文档
   ↓
5. 执行CSV对比分析
   ↓
6. AI语义分析(可选)
   ↓
7. 生成Excel标记文件
   ↓
8. 返回结果到8089
   ↓
9. 更新UI热力图显示
```

### 文件存储结构
```
csv_versions/
├── 2025_W37/
│   ├── baseline/     # 基准版文件(周二)
│   ├── midweek/      # 周中版本
│   └── weekend/      # 周末版本
├── 2025_W38/
│   └── ...
└── current_week -> 2025_W38  # 软链接
```

## 🚀 部署与运维

### 快速启动
```bash
# 使用启动脚本
./start_services.sh

# 或手动启动
python3 production_integrated_test_system_8093.py &  # 后端
python3 production/servers/final_heatmap_server.py & # 前端
```

### 服务监控
```bash
# 检查服务状态
curl http://localhost:8093/api/status | python3 -m json.tool
curl http://localhost:8089/api/workflow-status | python3 -m json.tool

# 查看日志
tail -f logs/backend_8093.log
tail -f logs/frontend_8089.log
```

### 故障排查
1. **502错误**: 重启服务，确保8093先启动
2. **连接拒绝**: 检查端口占用 `lsof -i:8093`
3. **日志不更新**: 检查API代理配置

## 🔧 配置管理

### 关键配置文件
- `config/download_settings.json` - 下载配置
- `config/cookies.json` - Cookie存储
- `config/unified_paths.json` - 路径配置
- `production/config/real_documents.json` - 文档URL映射

### 环境变量
```bash
# .env 文件
DEEPSEEK_API_KEY=your_api_key
COOKIE_ENCRYPTION_KEY=your_encryption_key
```

## 📊 性能优化

### 当前优化
- API请求使用连接池
- 日志限制最近100条
- 文件缓存机制
- 异步工作流处理

### 建议优化
- 使用Redis缓存状态
- WebSocket替代轮询
- 数据库存储历史记录
- 负载均衡多实例

## 🔒 安全考虑

1. **Cookie加密**: 使用AES加密存储
2. **API限流**: 防止恶意请求
3. **CORS配置**: 限制跨域访问
4. **输入验证**: 防止注入攻击

## 📝 维护建议

1. **定期清理**:
   - 清理旧的CSV文件
   - 归档历史日志
   - 删除临时文件

2. **监控告警**:
   - 设置服务健康检查
   - 配置错误日志告警
   - 监控磁盘使用

3. **备份策略**:
   - 定期备份基线文件
   - 备份配置文件
   - 导出重要数据

## 🎯 未来改进方向

1. **微服务化**: 拆分为独立微服务
2. **容器化**: Docker/K8s部署
3. **实时通信**: WebSocket推送
4. **分布式处理**: 支持多文档并行
5. **智能调度**: 基于负载的任务分配

---

_本文档为腾讯文档监控系统的核心架构说明，请根据实际运维需求持续更新。_