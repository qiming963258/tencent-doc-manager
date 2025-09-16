# 🤖 腾讯文档智能监控系统 - AI助手参考指引

## 📋 系统概述

**腾讯文档智能监控系统**是一个企业级智能文档变更监控与风险评估系统，支持完整的11步处理流程，实现从CSV对比分析到Excel半填充标记和定时调度的全自动化监控。

**当前服务器**: 202.140.143.88  
**系统状态**: ✅ 生产就绪，核心功能完成  
**完成度**: 90% (优秀级企业AI系统)

## 🎯 核心功能

- **📊 智能变更检测**: CSV对比分析 + AI列名标准化
- **🔥 科学热力图**: 30×19矩阵 + 高斯平滑算法  
- **📝 专业Excel标记**: lightUp纹理 + AI批注系统
- **🤖 Claude AI集成**: 语义分析 + 风险评估
- **⏰ 智能定时调度**: 周二、四、六三级定时下载系统

## 🌟 最新功能更新状态 (2025-08-18)

✅ **服务器迁移完成** - 已成功迁移至 202.140.143.88  
✅ **Claude API服务** - 8081端口正常运行，配置已更新  
✅ **Excel MCP轻量版** - 已安装并测试通过，完全符合文档描述  
✅ **热力图UI** - 8089端口正常服务，防火墙已配置  
✅ **定时下载系统** - 完整的调度器和预设任务管理功能已实现  
✅ **项目结构优化** - 清理废弃文档，优化目录结构，保留核心功能  
✅ **CSV版本管理** - 新规格目录结构就绪，支持基准版管理  

## 🌐 主要服务

| 服务 | 端口 | 状态 | 访问地址 |
|------|------|------|----------|
| 热力图UI | 8089 | ✅ 运行中 | http://202.140.143.88:8089 |
| Claude AI | 8081 | ✅ 已配置 | http://202.140.143.88:8081 |
| 主系统API | 5000 | ⚠️ 需配置 | http://202.140.143.88:5000 |

## 📚 文档导航索引

### 🔴 高优先级 - AI必读核心文档

#### 使用指南 (docs/guides/)
- **[快速参考](docs/guides/快速参考.md)** - 10步完整操作流程
- **[腾讯文档下载使用说明](docs/guides/01-腾讯文档自动化下载使用说明.md)** - 下载工具详细使用(269行)
- **[Excel-MCP使用指南](docs/guides/Excel-MCP-AI-使用指南.md)** - Excel处理规范
- **[系统部署实施计划](docs/guides/系统部署实施计划.md)** - 部署和集成计划
- **[API文档](docs/guides/API文档.md)** - API接口说明

#### 技术规格 (docs/specifications/)
- **[系统总体架构规格](docs/specifications/01-系统总体架构规格.md)** - 系统架构设计(424行)
- **[AI语义分析集成规格](docs/specifications/05-AI语义分析集成规格.md)** - Claude AI技术规格
- **[部署运维和监控规格](docs/specifications/07-部署运维和监控规格.md)** - 部署运维规格

### 🟡 中优先级 - 项目状态报告

#### 项目报告 (docs/reports/)
- **[项目最新状态报告](docs/reports/项目最新状态报告.md)** - 85%完成度，最新项目状态
- **[项目完成总结](docs/reports/项目完成总结.md)** - 项目交付成果
- **[实际测试结果报告](docs/reports/实际测试结果报告.md)** - 测试验证结果

### 🟢 低优先级 - 详细技术文档

#### 完整技术规格 (docs/specifications/)
- **[数据流和API接口规格](docs/specifications/02-数据流和API接口规格.md)** - 数据流程设计
- **[Excel-MCP可视化标记规格](docs/specifications/06-Excel-MCP可视化标记规格.md)** - Excel处理规格
- **[综合测试规范](docs/specifications/09-腾讯文档智能监控系统综合测试规范.md)** - 测试规范

## ⏰ 定时下载系统使用指南

### 🎯 核心功能
**智能定时调度器**支持自动化的文档下载和处理，包含三个预设业务任务：

1. **周二基准下载** (每周二12:00) - 下载基准CSV文件
2. **周四中期更新** (每周四09:00) - 下载全部表格CSV并更新系统  
3. **周六完整更新** (每周六19:00) - 全流程更新系统

### 🚀 快速使用步骤

1. **访问管理界面**
   ```
   http://202.140.143.88:8089
   ```

2. **配置基础设置**
   - 点击"监控设置"按钮
   - 配置有效的腾讯文档Cookie
   - 导入要监控的文档链接

3. **启用定时任务**
   - 在"定时下载任务"区域中
   - 点击"启动调度器"
   - 选择要加载的预设任务（周二/周四/周六）
   - 点击"加载任务"

4. **监控执行状态**
   - 查看调度器运行状态
   - 监控活动任务列表
   - 查看最近执行记录

### 📋 支持的调度格式
- **Simple格式**: `weekly:tuesday:12:00`, `daily:09:00`, `hourly:30`
- **Cron格式**: `0 12 * * 2` (每周二12:00)

### 🔧 API接口
定时调度系统提供完整的REST API接口：
- `GET /api/schedule/status` - 获取调度器状态
- `POST /api/schedule/start` - 启动调度器
- `GET /api/schedule/list-tasks` - 获取任务列表
- `POST /api/schedule/load-preset-task` - 加载预设任务

**详细API文档**: [API文档.md](docs/guides/API文档.md#热力图ui服务器api-端口8089)

## 🚨 AI应急处理路径

### 系统配置问题
1. **CLAUDE.md** - 基础配置规范
2. **docs/guides/01-腾讯文档自动化下载使用说明.md** - 故障排除

### 功能操作问题  
1. **docs/guides/快速参考.md** - 10步流程
2. **docs/guides/Excel-MCP-AI-使用指南.md** - Excel处理

### 技术架构问题
1. **docs/specifications/01-系统总体架构规格.md** - 架构设计
2. **production/core_modules/** - 核心代码

## 📁 项目目录结构

```
/root/projects/tencent-doc-manager/
├── 📄 CLAUDE.md                           # Claude系统配置规范
├── 📄 README.md                           # 项目说明文档
├── 📂 claude_mini_wrapper/                # Claude AI服务 (8081端口)
│   ├── main.py                            # FastAPI主服务
│   ├── claude_client.py                   # Claude客户端
│   ├── config.py                          # 配置管理
│   └── README.md                          # AI服务使用说明
├── 📂 config/                             # 系统配置文件
│   ├── cookies.json                       # Cookie存储配置
│   ├── download_settings.json             # 下载配置管理
│   └── schedule_tasks.json                # 定时任务配置
├── 📂 csv_versions/                       # CSV版本管理目录
│   ├── 2025_W34/                          # 周版本目录
│   │   ├── baseline/                      # 基准版文件
│   │   ├── midweek/                       # 周中版文件
│   │   └── weekend/                       # 周末版文件
│   ├── comparison_cache/                  # 对比结果缓存
│   ├── current_week -> 2025_W34/          # 当周软链接
│   └── *.csv                              # 当前版本文件
├── 📂 docs/                               # 技术文档目录
│   ├── guides/                            # 使用指南
│   │   ├── 01-腾讯文档自动化下载使用说明.md
│   │   ├── 02-CSV版本管理和对比系统使用说明.md
│   │   ├── API文档.md
│   │   ├── Excel-MCP-AI-使用指南.md
│   │   ├── 快速参考.md
│   │   └── 系统部署实施计划.md
│   ├── plans/                             # 项目计划
│   │   └── 腾讯文档智能监控系统-实施计划.md
│   └── specifications/                    # 技术规格
│       ├── 01-系统总体架构规格.md
│       ├── 02-时间管理和文件版本规格.md
│       ├── 04-自适应表格对比算法规格.md
│       ├── 05-AI语义分析集成规格.md
│       ├── 06-Excel-MCP可视化标记规格.md
│       └── ...更多规格文档
├── 📂 downloads/                          # 下载文件存储
│   └── *.xlsx                             # 下载的Excel文件
├── 📂 production/                         # 生产环境代码
│   ├── core_modules/                      # 核心业务模块
│   │   ├── adaptive_table_comparator.py  # 自适应表格对比算法
│   │   ├── baseline_manager.py           # 基准版管理器
│   │   ├── week_time_manager.py          # 时间管理器
│   │   ├── auto_comparison_task.py       # 自动对比任务
│   │   ├── claude_wrapper_integration.py # Claude集成封装
│   │   ├── claude_semantic_analysis.py   # AI语义分析
│   │   ├── document_change_analyzer.py   # 文档变更分析
│   │   └── excel_mcp_visualizer.py       # Excel可视化处理
│   └── servers/                           # 服务器程序
│       ├── enhanced_flask_api_server.py  # 增强版API服务器
│       ├── final_heatmap_server.py       # 热力图UI服务器 (8089端口)
│       ├── fixed_heatmap_server.py       # 备用热力图服务
│       └── simple_scheduler.py           # 简化调度器
└── 📂 测试版本-性能优化开发-20250811-001430/ # 旧版本目录（待清理）
    ├── tencent_export_automation.py      # 腾讯文档下载器
    ├── csv_version_manager.py            # 旧版本管理器
    └── ...其他旧版本文件
```

## 🎯 AI使用建议

1. **问题分类**: 按照配置/状态/操作/架构/代码/测试分类
2. **文档优先级**: 🔴 > 🟡 > 🟢 顺序查看
3. **路径引用**: 引用具体文档路径和行号
4. **状态考虑**: 基于85%完成度状态回答
5. **风险提醒**: 参考项目状态报告中的风险提示

---

**系统版本**: v2.2 (优化版)  
**服务器**: 202.140.143.88  
**文档更新**: 2025-08-18  
**迁移状态**: ✅ 完成，服务正常  
**维护状态**: ✅ 持续监控中  
**项目结构**: ✅ 已优化清理