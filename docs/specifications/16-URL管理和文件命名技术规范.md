# 16-URL管理和文件命名技术规范

**文档编号**: 16
**创建日期**: 2025-09-27
**文档类型**: 技术规范
**版本**: v1.0

---

## 一、系统概述

腾讯文档管理系统使用多层次的URL管理和文件命名机制，确保文档的唯一性、可追踪性和版本管理。本规范详细说明URL的管理流程、文件命名规则和查找机制。

## 二、URL字段命名规则

### 2.1 URL结构
```
https://docs.qq.com/sheet/{doc_id}[?tab={tab_id}]
```

#### 字段说明
- **doc_id**: 文档唯一标识符（例如：`DWEFNU25TemFnZXJN`）
- **tab_id**: 可选的工作表标签（例如：`c2p5hs`）

### 2.2 URL提取规则
```python
def _extract_doc_id(self, url: str) -> str:
    """从URL提取文档ID"""
    if 'docs.qq.com/sheet/' in url:
        # 处理可能的查询参数
        url_without_query = url.split('?')[0]
        # 提取最后一段作为doc_id
        return url_without_query.split('/')[-1]
    return None
```

## 三、文件命名规则

### 3.1 标准格式（当前实现）
```
tencent_{文档名}_{doc_id}_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.{扩展名}
```

#### 命名组成部分
| 组件 | 描述 | 示例 | 规则 |
|------|------|------|------|
| 前缀 | 固定前缀 | `tencent_` | 必须 |
| 文档名 | 清理后的文档名称 | `出国销售计划表` | 移除非法字符和扩展名 |
| doc_id | 从URL提取的唯一标识 | `DWEFNU25TemFnZXJN` | 必须，确保唯一性 |
| 时间戳 | 文件生成时间 | `20250927_1430` | 格式：YYYYMMDD_HHMM |
| 版本类型 | 版本标识 | `baseline`/`midweek`/`weekend` | 三选一 |
| 周数 | ISO周数 | `W39` | 2位数字，带前导零 |
| 扩展名 | 文件格式 | `csv`/`xlsx`/`xls` | 根据实际格式 |

### 3.2 示例
```
tencent_出国销售计划表_DWEFNU25TemFnZXJN_20250926_2011_baseline_W39.csv
tencent_小红书部门_DWEVjZndkR2xVSWJN_20250927_0346_midweek_W39.xlsx
```

### 3.3 字符清理规则
```python
# 移除文件名中的非法字符
doc_name = re.sub(r'[<>:"/\\|?*]', '', doc_name)
# 移除已有的扩展名
doc_name = re.sub(r'\.(csv|xlsx|xls)$', '', doc_name, flags=re.IGNORECASE)
```

## 四、配置文件体系

### 4.1 配置文件层级

| 配置文件 | 路径 | 用途 | 优先级 |
|----------|------|------|---------|
| download_config.json | `/config/download_config.json` | **主配置**：8089界面使用 | 最高 |
| real_documents.json | `/production/config/real_documents.json` | 备用配置（未使用） | 低 |
| document_links.json | `/uploads/document_links.json` | 上传记录 | 仅记录 |

### 4.2 主配置结构（download_config.json）
```json
{
    "document_links": [
        {
            "name": "副本-测试版本-出国销售计划表",
            "url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
            "enabled": true
        },
        {
            "name": "测试版本-小红书部门",
            "url": "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs",
            "enabled": true
        }
    ],
    "download_format": "csv",
    "schedule": {
        "enabled": false,
        "interval": "weekly"
    }
}
```

## 五、URL获取路径

### 5.1 数据流向
```
用户输入URL → 8089界面 → /api/save-download-links
    ↓
保存到 download_config.json
    ↓
8093批处理读取 → 提取doc_id → 生成文件名 → 下载文件
```

### 5.2 关键API端点

#### 保存链接配置
- **端点**: `/api/save-download-links`
- **方法**: POST
- **功能**: 保存URL配置，支持软删除

#### 获取链接配置
- **端点**: `/api/get-download-links`
- **方法**: GET
- **功能**: 读取当前配置的URL列表

#### 文档链接映射
- **端点**: `/api/document-links`
- **方法**: GET
- **功能**: 获取文档名到URL的映射关系

## 六、文件查找规则

### 6.1 基线文件查找
```python
def find_baseline_files(self, max_weeks_back: int = 4):
    """查找基线文件，支持向前查找历史周"""
    patterns = [
        f"*_baseline_W{week_num:02d}.csv",
        f"*_baseline_W{week_num:02d}.xlsx",
        f"*_baseline_W{week_num:02d}.xls"
    ]
```

### 6.2 目标文件查找
根据当前时间动态选择版本类型：
- 周一至周三：查找上周weekend版本
- 周四至周五：查找本周midweek版本
- 周六至周日：查找本周weekend版本

### 6.3 文件匹配优先级
1. 精确匹配doc_id
2. 匹配文档名称
3. 按时间戳排序（最新优先）

## 七、目录结构

```
csv_versions/
├── {YEAR}_W{周数}/
│   ├── baseline/           # 基线版本
│   │   └── tencent_*_baseline_W{周数}.*
│   ├── midweek/           # 中期版本
│   │   └── tencent_*_midweek_W{周数}.*
│   └── weekend/           # 周末版本
│       └── tencent_*_weekend_W{周数}.*
└── current_week -> {YEAR}_W{周数}  # 软链接
```

## 八、核心实现模块

### 8.1 WeekTimeManager
**路径**: `/production/core_modules/week_time_manager.py`
- 生成标准文件名
- 管理周数和版本
- 文件查找逻辑

### 8.2 TencentDocAutoExporter
**路径**: `/production/core_modules/tencent_export_automation.py`
- URL解析和doc_id提取
- 文件下载和保存

### 8.3 URLMapper
**路径**: `/production/core_modules/url_mapper.py`
- URL到本地文件的映射
- 多源URL管理

## 九、关键约束和规则

### 9.1 强制要求
1. **doc_id必须存在**: 新版本不再支持无doc_id的文件名
2. **扩展名灵活**: 支持csv、xlsx、xls等多种格式
3. **字符清理**: 必须移除文件名中的非法字符

### 9.2 向后兼容
- 支持旧格式文件名的读取（带_csv_标记）
- 旧文件会在处理时自动迁移到新格式

### 9.3 唯一性保证
- 使用doc_id确保文件唯一性
- 时间戳精确到分钟避免重复
- 版本类型和周数提供额外区分

## 十、错误处理

### 10.1 常见错误
| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| doc_id缺失 | URL解析失败 | 检查URL格式是否正确 |
| 文件名重复 | 时间戳相同 | 等待1分钟或手动添加序号 |
| 非法字符 | 文档名含特殊字符 | 自动清理或手动编辑 |

### 10.2 降级策略
1. 如果无法提取doc_id，拒绝生成文件名
2. 如果找不到基线文件，向前查找4周
3. 如果配置文件损坏，使用默认配置

## 十一、最佳实践

### 11.1 添加新文档
1. 在8089界面输入完整URL
2. 系统自动提取doc_id
3. 生成符合规范的文件名
4. 保存到对应版本目录

### 11.2 文件管理
1. 定期清理过期文件（超过4周）
2. 保持基线文件完整性
3. 使用软链接访问当前周数据

### 11.3 配置维护
1. 定期备份download_config.json
2. 清理deleted_links中的过期记录
3. 验证URL的有效性

## 十二、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v1.0 | 2025-09-27 | 初始版本，完整规范文档 |

---

**维护者**: 系统架构组
**最后更新**: 2025-09-27 20:50