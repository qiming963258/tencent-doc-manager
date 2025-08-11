# Ubuntu 自动化定时采集系统

本系统提供完整的腾讯文档自动化定时采集解决方案，支持灵活的时间调度、高并发处理、文档差异对比和历史数据管理。

## 🎯 系统特性

### 核心功能
- **灵活调度**: 支持 cron 表达式和简化时间格式
- **高并发采集**: 优化的浏览器池管理，支持并发采集
- **智能对比**: 细粒度文档差异检测和JSON格式输出
- **数据管理**: SQLite数据库存储，自动清理历史数据
- **Ubuntu优化**: 专门针对4H2G服务器配置优化

### 性能优化
- 浏览器实例复用，减少启动开销
- 内存使用控制，严格限制在1.5GB以内
- 异步并发处理，提升采集效率
- 智能重试机制，保证采集成功率

## 📁 目录结构

```
测试版本-性能优化开发-20250811-001430/
├── main.py                 # 系统主脚本
├── scheduler.py            # 定时任务调度器
├── collector.py            # 文档数据采集器
├── comparator.py           # 文档差异对比器
├── storage.py             # 数据存储管理器
├── manage-collection.sh    # 系统管理脚本
├── config/                # 配置文件目录
│   ├── system.json        # 系统配置
│   └── tasks/             # 任务配置示例
│       ├── daily_task_example.json
│       ├── hourly_task_example.json
│       └── weekly_task_example.json
└── 定时采集系统设计.md      # 系统设计文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip3 install playwright croniter pytz pandas psutil

# 安装Playwright浏览器
playwright install chromium

# 设置执行权限
chmod +x manage-collection.sh
```

### 2. 系统配置

编辑 `config/system.json`：

```json
{
  "system": {
    "max_concurrent": 3,
    "log_level": "INFO", 
    "data_retention_days": 30
  },
  "performance": {
    "browser_pool_size": 3,
    "page_timeout": 60,
    "retry_times": 2
  }
}
```

### 3. 创建采集任务

复制并修改任务配置文件：

```bash
cp config/tasks/daily_task_example.json config/tasks/my_task.json
```

编辑任务配置，设置实际的URL和cookies：

```json
{
  "task_id": "my_daily_task",
  "name": "我的日常采集任务",
  "schedule": {
    "type": "simple",
    "expression": "daily:09:00"
  },
  "urls": [
    "https://docs.qq.com/sheet/YOUR_DOC_URL"
  ],
  "cookies": "your_actual_cookies_here"
}
```

### 4. 启动系统

```bash
# 启动采集系统
python3 main.py start

# 或使用管理脚本
./manage-collection.sh start
```

## 🔧 使用指南

### 命令行操作

```bash
# 系统管理
python3 main.py start                    # 启动系统
python3 main.py stop                     # 停止系统
python3 main.py status                   # 查看状态

# 任务管理
python3 main.py add-task --task-file config/tasks/my_task.json
python3 main.py remove-task --task-id my_daily_task
python3 main.py list-tasks               # 列出所有任务
python3 main.py execute --task-id my_daily_task  # 手动执行

# 数据管理
python3 main.py cleanup --days 7         # 清理7天前数据
```

### 管理脚本操作

```bash
# 系统服务
./manage-collection.sh install          # 安装系统服务
./manage-collection.sh start            # 启动服务
./manage-collection.sh stop             # 停止服务
./manage-collection.sh status           # 查看状态

# 任务管理  
./manage-collection.sh add-task config/tasks/my_task.json
./manage-collection.sh remove-task my_daily_task
./manage-collection.sh list-tasks
./manage-collection.sh execute-task my_daily_task

# 日志和数据
./manage-collection.sh logs 100         # 查看最近100行日志
./manage-collection.sh backup           # 备份数据
./manage-collection.sh cleanup 7        # 清理历史数据
```

## ⚙️ 配置说明

### 系统配置 (config/system.json)

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| max_concurrent | 最大并发数 | 3 |
| log_level | 日志级别 | INFO |
| data_retention_days | 数据保留天数 | 30 |
| browser_pool_size | 浏览器池大小 | 3 |
| page_timeout | 页面超时时间(秒) | 60 |

### 任务配置格式

```json
{
  "task_id": "unique_task_id",
  "name": "任务显示名称",
  "schedule": {
    "type": "simple|cron",
    "expression": "调度表达式",
    "timezone": "Asia/Shanghai"
  },
  "urls": ["文档URL列表"],
  "cookies": "认证cookies",
  "options": {
    "concurrent_limit": 2,
    "timeout": 60,
    "compare_with_previous": true
  },
  "notification": {
    "enabled": true,
    "notify_on_change": true,
    "webhook_url": "通知webhook地址"
  }
}
```

### 调度表达式格式

#### 简化格式
- `daily:09:00` - 每天上午9点
- `hourly:30` - 每小时30分
- `weekly:monday:09:00` - 每周一上午9点
- `monthly:1:09:00` - 每月1号上午9点

#### Cron格式
- `0 9 * * *` - 每天上午9点
- `0 */6 * * *` - 每6小时一次
- `0 0 * * 1` - 每周一午夜
- `0 18 * * 5` - 每周五下午6点

## 📊 数据格式

### 采集结果格式

```json
{
  "collection_id": "task_20250811_091500",
  "timestamp": "2025-08-11T09:15:00.123Z",
  "status": "completed",
  "results": [
    {
      "url": "https://docs.qq.com/sheet/...",
      "success": true,
      "duration": 5.2,
      "row_count": 150,
      "data_path": "/data/collections/.../doc.csv"
    }
  ]
}
```

### 差异对比格式

```json
{
  "comparison_id": "doc_20250810_vs_20250811",
  "changes": {
    "summary": {
      "total_changes": 17,
      "added_rows": 5,
      "modified_cells": 12
    },
    "details": {
      "cell_changes": [
        {
          "type": "modified",
          "position": {"row": 10, "col": 3},
          "previous_value": "500",
          "current_value": "800"
        }
      ]
    }
  }
}
```

## 🔍 监控和故障排查

### 查看系统状态

```bash
# 系统整体状态
./manage-collection.sh status

# 任务执行状态  
python3 main.py status --task-id my_task

# 系统日志
./manage-collection.sh logs 100
```

### 常见问题

#### 1. Cookie认证失败
```bash
# 获取最新cookies
# 1. 浏览器F12 -> Network -> 复制cookies
# 2. 更新任务配置文件中的cookies字段
```

#### 2. 内存不足
```bash
# 查看内存使用
free -h

# 调整并发数
# 编辑config/system.json，减少max_concurrent值
```

#### 3. 采集失败
```bash
# 查看详细日志
tail -f data/system.log

# 手动测试采集
python3 main.py execute --task-id problem_task
```

## 🛡️ 生产环境部署

### Ubuntu系统优化

```bash
# 应用系统参数优化
sudo cp ubuntu-sysctl.conf /etc/sysctl.d/99-tencent-collection.conf
sudo sysctl -p /etc/sysctl.d/99-tencent-collection.conf

# 安装为系统服务
sudo ./manage-collection.sh install

# 启动服务
sudo systemctl start tencent-collection
sudo systemctl enable tencent-collection
```

### 数据备份

```bash
# 定期备份
./manage-collection.sh backup

# 设置定时备份任务
echo "0 2 * * * cd /opt/tencent-collection && ./manage-collection.sh backup" | crontab -
```

### 监控设置

```bash
# 设置日志轮转
sudo logrotate -f /etc/logrotate.d/tencent-collection

# 监控系统资源
./manage-collection.sh status
```

## 📈 性能指标

### 预期性能（4H2G配置）
- **采集吞吐量**: 2-3 文档/秒
- **内存使用**: 1.2-1.5GB 峰值  
- **CPU使用**: 60-80% 峰值
- **成功率**: >95%

### 优化建议
- 单任务URL数量建议不超过10个
- 合理设置调度间隔，避免任务重叠
- 定期清理历史数据，保持系统性能
- 监控系统资源，必要时调整并发参数

---

## 🆘 技术支持

遇到问题时请提供：
1. 系统版本信息
2. 错误日志内容
3. 任务配置文件
4. 系统资源使用情况

此系统专为Ubuntu 4H2G环境优化，支持高效的腾讯文档自动化采集和对比，能够满足企业级数据监控需求。