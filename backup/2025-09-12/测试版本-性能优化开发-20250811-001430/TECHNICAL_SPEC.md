# 腾讯文档自动化服务技术规格文档
**Technical Specification Document**

---

## 1. 系统概述

### 1.1 项目背景
腾讯文档自动化服务是一个企业级文档处理平台，提供腾讯文档的自动化下载、上传、分析和修改功能。

### 1.2 核心目标
- 自动化腾讯文档导出流程
- 提供Excel文档智能分析
- 支持批量文档处理
- 提供现代化Web界面
- 确保数据安全和用户隐私

### 1.3 技术栈选择
| 层级 | 技术 | 版本 | 选择理由 |
|------|------|------|----------|
| 前端 | 原生JavaScript + Bootstrap | ES6+ / 5.1.3 | 轻量、高性能、无框架依赖 |
| 后端 | Flask + Python | 2.3.3 / 3.11+ | 简单、灵活、快速开发 |
| 自动化 | Playwright | 1.40.0 | 现代浏览器自动化、稳定性好 |
| 数据库 | SQLite | 3.x | 轻量、零配置、适合中小规模 |
| 缓存 | Redis | 7.x | 高性能、支持队列和缓存 |
| 容器化 | Docker + Docker Compose | Latest | 标准化部署、环境一致性 |

---

## 2. 系统架构

### 2.1 整体架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户浏览器     │    │   Nginx代理      │    │   Flask应用      │
│                │ -> │                │ -> │                │
│ - 现代化界面     │    │ - 负载均衡       │    │ - API服务        │
│ - Cookie管理     │    │ - SSL终端       │    │ - 业务逻辑       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │   Playwright     │ <-----------┘
                       │                │
                       │ - 浏览器控制     │
                       │ - 腾讯文档操作   │
                       └─────────────────┘
                                │
        ┌─────────────────┐     │     ┌─────────────────┐
        │   SQLite数据库   │ <---+---> │   Redis缓存      │
        │                │           │                │
        │ - 用户数据       │           │ - 会话缓存       │
        │ - 操作历史       │           │ - 任务队列       │
        └─────────────────┘           └─────────────────┘
```

### 2.2 模块设计
| 模块 | 责任 | 文件 |
|------|------|------|
| 文档下载 | 自动化导出腾讯文档 | `tencent_export_automation.py` |
| 文档上传 | 自动化上传文件到腾讯文档 | `tencent_upload_automation.py` |
| API服务 | 提供RESTful接口 | `app.py` |
| 前端界面 | 用户交互界面 | `templates/index.html` |
| 数据管理 | 用户和文档数据管理 | SQLite数据库 |

---

## 3. API接口规范

### 3.1 基础信息
- **Base URL**: `/api`
- **认证方式**: Session-based
- **数据格式**: JSON
- **编码**: UTF-8

### 3.2 接口列表

#### 3.2.1 健康检查
```http
GET /api/health
```
**响应:**
```json
{
  "status": "healthy",
  "service": "腾讯文档自动化服务",
  "version": "1.0.0",
  "timestamp": "2025-08-09T10:30:00.000Z"
}
```

#### 3.2.2 保存用户Cookies
```http
POST /api/save_cookies
Content-Type: application/json

{
  "username": "string",
  "cookies": "string"
}
```

**响应:**
```json
{
  "success": true,
  "message": "Cookies保存成功",
  "username": "string"
}
```

#### 3.2.3 下载文档
```http
POST /api/download
Content-Type: application/json

{
  "doc_url": "https://docs.qq.com/sheet/...",
  "username": "string",
  "format": "excel|csv"
}
```

**响应:**
```json
{
  "success": true,
  "message": "文档下载成功",
  "file_path": "string",
  "file_name": "string"
}
```

#### 3.2.4 上传文档
```http
POST /api/upload
Content-Type: multipart/form-data

file: [binary data]
username: string
```

#### 3.2.5 分析文档
```http
POST /api/analyze
Content-Type: multipart/form-data

file: [binary data]
```

**响应:**
```json
{
  "success": true,
  "analysis": {
    "file_name": "string",
    "total_rows": number,
    "total_columns": number,
    "columns": ["string"],
    "data_types": {"column": "type"},
    "null_counts": {"column": number},
    "preview": [{"column": "value"}]
  }
}
```

---

## 4. 数据库设计

### 4.1 表结构

#### 4.1.1 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    cookie_hash TEXT NOT NULL,
    encrypted_cookies TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);
```

#### 4.1.2 文档历史表 (documents)
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    doc_url TEXT,
    doc_name TEXT,
    file_path TEXT,
    operation TEXT CHECK(operation IN ('download', 'upload', 'analyze')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### 4.2 数据加密策略
- **Cookie加密**: XOR + SHA256哈希（生产环境建议使用Fernet）
- **用户密钥**: username + SECRET_KEY组合
- **存储安全**: 敏感数据加密存储，不存储明文

---

## 5. 浏览器自动化规范

### 5.1 腾讯文档UI选择器映射

#### 5.1.1 导出流程
```javascript
// 步骤1: 三横线菜单
'.titlebar-icon.titlebar-icon-more'

// 步骤2: 导出为选项
'li.dui-menu-item.dui-menu-submenu.mainmenu-submenu-exportAs'

// 步骤3: 格式选择
// Excel: 'li.dui-menu-item.mainmenu-item-export-local'
// CSV: 'li.dui-menu-item.mainmenu-item-export-csv'
```

#### 5.1.2 上传流程
```javascript
// 步骤1: 导入按钮
'button.desktop-import-button-pc'

// 步骤2: 文件选择
'input[type="file"]'

// 步骤3: 确认上传
'div.dui-button-container:has-text("确定")'
```

### 5.2 错误处理策略
| 错误类型 | 处理方式 | 重试次数 |
|----------|----------|----------|
| 页面加载超时 | 降级到domcontentloaded | 2次 |
| 元素未找到 | 尝试备用选择器 | 4种方法 |
| 权限不足 | 提示用户检查Cookie | 不重试 |
| 网络异常 | 延长等待时间 | 3次 |

---

## 6. 前端组件规范

### 6.1 主要组件
| 组件名 | 功能 | 状态管理 |
|--------|------|----------|
| SettingsPanel | Cookie和用户配置 | localStorage |
| DownloadPanel | 文档下载界面 | API状态 |
| UploadPanel | 文件上传界面 | 拖拽状态 |
| AnalyzePanel | 数据分析展示 | 分析结果 |
| HistoryPanel | 操作历史记录 | API数据 |

### 6.2 状态管理
```javascript
// 全局状态结构
AppState = {
  user: {
    username: string,
    isLoggedIn: boolean
  },
  ui: {
    currentTab: string,
    loading: boolean,
    theme: 'light' | 'dark'
  },
  data: {
    downloadHistory: Array,
    analysisResult: Object
  }
}
```

---

## 7. 安全机制设计

### 7.1 认证安全
- **Cookie存储**: AES加密存储在SQLite
- **会话管理**: Redis存储临时会话
- **权限验证**: 每次API调用验证用户权限

### 7.2 文件安全
- **上传限制**: 100MB大小限制，文件类型白名单
- **存储隔离**: 用户文件按用户ID隔离存储
- **定期清理**: 7天自动清理临时文件

### 7.3 网络安全
- **HTTPS强制**: 生产环境强制HTTPS
- **CORS配置**: 限制跨域请求来源
- **请求限流**: API请求频率限制

---

## 8. 性能指标

### 8.1 响应时间要求
| 操作 | 目标响应时间 | 最大响应时间 |
|------|-------------|-------------|
| 页面加载 | < 2秒 | < 5秒 |
| API响应 | < 500ms | < 2秒 |
| 文档下载 | < 30秒 | < 60秒 |
| 文件上传 | < 15秒 | < 30秒 |
| 数据分析 | < 5秒 | < 10秒 |

### 8.2 并发性能
- **最大并发用户**: 100
- **Playwright实例**: 最多5个并发
- **内存使用**: < 2GB
- **CPU使用**: < 80%

### 8.3 可用性指标
- **系统可用性**: 99.5%
- **数据持久性**: 99.9%
- **平均故障恢复时间**: < 5分钟

---

## 9. 部署规范

### 9.1 系统要求
| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 存储 | 20GB | 50GB |
| 网络 | 100Mbps | 1Gbps |

### 9.2 容器资源配置
```yaml
# Docker Compose资源限制
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### 9.3 环境变量配置
```bash
# 必需环境变量
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
DATABASE_URL=sqlite:///data/tencent_docs.db

# 可选环境变量
MAX_WORKERS=4
TENCENT_TIMEOUT=60
DOWNLOAD_RETENTION_DAYS=7
```

---

## 10. 运维监控

### 10.1 监控指标
#### 应用层监控
- API响应时间和错误率
- 活跃用户数和并发数
- 文档处理成功率
- 系统资源使用率

#### 业务层监控
- 下载/上传操作成功率
- 用户行为分析
- 错误模式分析
- 性能瓶颈识别

### 10.2 告警策略
| 指标 | 阈值 | 告警级别 | 处理方式 |
|------|------|----------|----------|
| API错误率 | > 5% | 警告 | 邮件通知 |
| 响应时间 | > 10秒 | 严重 | 短信 + 邮件 |
| CPU使用率 | > 90% | 警告 | 自动扩容 |
| 内存使用率 | > 95% | 严重 | 立即重启 |

### 10.3 日志管理
```python
# 日志格式规范
{
  "timestamp": "2025-08-09T10:30:00.000Z",
  "level": "INFO|WARN|ERROR",
  "module": "download|upload|analyze|auth",
  "user_id": "string",
  "operation": "string",
  "duration": number,
  "success": boolean,
  "error_message": "string"
}
```

---

## 11. 测试策略

### 11.1 测试类型
#### 单元测试
- 核心业务逻辑函数
- API端点功能
- 数据处理算法
- 覆盖率要求: > 80%

#### 集成测试
- 腾讯文档API集成
- 文件上传/下载流程
- 数据库操作
- 浏览器自动化

#### 端到端测试
- 完整用户工作流
- 多浏览器兼容性
- 移动端响应式测试

### 11.2 测试环境
```bash
# 开发环境
python -m pytest tests/ -v

# Docker测试环境
docker-compose -f docker-compose.test.yml up --build
```

---

## 12. 安全规范

### 12.1 数据安全
```python
# Cookie加密示例
def encrypt_cookies(cookies, user_key):
    key_hash = hashlib.sha256(user_key.encode()).hexdigest()
    # XOR加密实现（生产环境应使用Fernet）
    encrypted = []
    for i, char in enumerate(cookies):
        encrypted.append(chr(ord(char) ^ ord(key_hash[i % len(key_hash)])))
    return ''.join(encrypted)
```

### 12.2 输入验证
- URL格式验证：`^https://docs\.qq\.com/.*`
- 文件类型验证：`.xlsx, .xls, .csv`
- 文件大小限制：100MB
- 用户名格式：字母数字，3-50字符

### 12.3 错误处理
```python
# 标准错误响应格式
{
  "error": "错误描述",
  "error_code": "ERROR_001",
  "timestamp": "2025-08-09T10:30:00.000Z",
  "request_id": "uuid"
}
```

---

## 13. 部署指南

### 13.1 生产部署流程
```bash
# 1. 服务器准备
sudo apt update && sudo apt install docker.io docker-compose

# 2. 项目部署
git clone [repository] tencent-docs
cd tencent-docs
chmod +x deploy.sh

# 3. 一键部署
./deploy.sh deploy

# 4. 验证部署
./deploy.sh health
```

### 13.2 配置管理
```yaml
# docker-compose.yml关键配置
services:
  app:
    environment:
      - FLASK_ENV=production
      - MAX_WORKERS=4
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./downloads:/app/downloads
```

### 13.3 备份策略
- **数据库备份**: 每日自动备份SQLite
- **文件备份**: 7天保留策略
- **配置备份**: Git版本控制
- **恢复测试**: 月度备份恢复验证

---

## 14. 扩展性考虑

### 14.1 水平扩展
- **负载均衡**: Nginx多实例分发
- **数据库**: 可迁移到PostgreSQL集群
- **缓存**: Redis Cluster部署
- **存储**: 可接入对象存储服务

### 14.2 功能扩展
- **批量处理**: 支持多文档并行处理
- **定时任务**: Celery定时任务系统
- **通知系统**: 邮件/短信/WebHook通知
- **API开放**: 为第三方提供API接口

### 14.3 技术升级路径
```
当前架构 -> 微服务架构
├── 文档服务 (独立的下载/上传服务)
├── 分析服务 (独立的数据分析服务)
├── 用户服务 (认证和用户管理)
└── 网关服务 (API网关和路由)
```

---

## 15. 风险评估与缓解

### 15.1 技术风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 腾讯文档UI变更 | 高 | 中 | 多重选择器备用方案 |
| Playwright兼容性 | 中 | 高 | 版本锁定 + 回归测试 |
| 大文件处理失败 | 中 | 中 | 分片上传 + 重试机制 |
| 并发资源竞争 | 低 | 高 | Redis队列 + 限流 |

### 15.2 业务风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 用户Cookie泄露 | 低 | 高 | 加密存储 + 定期清理 |
| 服务不可用 | 中 | 高 | 多节点部署 + 自动重启 |
| 数据丢失 | 低 | 高 | 定期备份 + 冗余存储 |

---

## 16. 实施计划

### 16.1 部署阶段
1. **阶段1** (Week 1): 基础功能部署和测试
2. **阶段2** (Week 2): 监控系统和安全加固
3. **阶段3** (Week 3): 性能优化和压力测试
4. **阶段4** (Week 4): 用户培训和文档完善

### 16.2 成功标准
- ✅ 所有API接口正常响应
- ✅ 文档下载成功率 > 95%
- ✅ 文件上传成功率 > 95%
- ✅ 系统可用性 > 99%
- ✅ 用户界面响应时间 < 2秒

---

## 17. 维护指南

### 17.1 日常维护
```bash
# 服务状态检查
./deploy.sh status

# 查看系统日志
./deploy.sh logs

# 健康检查
./deploy.sh health

# 数据库备份
sqlite3 data/tencent_docs.db ".backup backup_$(date +%Y%m%d).db"
```

### 17.2 故障排查
1. **下载失败**: 检查Cookie有效性和文档权限
2. **上传失败**: 检查文件格式和大小限制
3. **性能问题**: 查看Grafana监控面板
4. **容器异常**: 检查Docker日志和资源使用

---

## 18. 版本历史

| 版本 | 发布日期 | 主要功能 |
|------|----------|----------|
| v1.0.0 | 2025-08-09 | 基础下载/上传功能 |
| v1.1.0 | 计划中 | 批量处理和定时任务 |
| v2.0.0 | 计划中 | 微服务架构重构 |

---

**文档版本**: v1.0.0  
**最后更新**: 2025-08-09  
**维护团队**: 腾讯文档自动化项目组