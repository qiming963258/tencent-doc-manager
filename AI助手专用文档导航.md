# 🤖 AI助手专用文档导航 - 腾讯文档智能监控系统

## 🎯 AI使用说明

**本导航专为AI助手设计**，提供快速、精确的文档路径指引，确保AI能够高效地找到所需信息并提供准确的帮助。

---

## 📋 核心参考路径图

### 🔴 系统配置和基础操作类问题
```
用户问题类型: "如何配置系统", "Cookie怎么设置", "基础使用方法"
AI应优先参考:
├── CLAUDE.md                                    # 系统基础配置规范
├── 测试版本-性能优化开发-20250811-001430/CLAUDE.md  # 下载工具配置
└── docs/guides/01-腾讯文档自动化下载使用说明.md    # 详细操作手册
```

### 🔴 系统状态和项目概览类问题
```
用户问题类型: "项目进度如何", "系统现状", "有什么功能"
AI应优先参考:
├── 项目综合状态报告-更新版.md                      # 最新状态评估
├── 项目文档使用指南.md                           # 文档结构概览
└── 项目整理总结报告.md                           # 整理成果总结
```

### 🔴 具体功能操作类问题
```
用户问题类型: "如何下载文档", "怎么运行流程", "命令怎么执行"
AI应优先参考:
├── docs/guides/快速参考.md                       # 10步完整流程
├── docs/guides/01-腾讯文档自动化下载使用说明.md      # 下载工具详细使用
└── docs/guides/Excel-MCP-AI-使用指南.md          # Excel处理规范
```

### 🔴 技术架构和设计类问题
```
用户问题类型: "系统怎么设计的", "架构是什么", "技术栈"
AI应优先参考:
├── docs/specifications/01-系统总体架构规格.md       # 系统架构设计(424行)
├── docs/specifications/05-AI语义分析集成规格.md     # AI集成技术规格
└── docs/guides/完整流程架构文档.md                 # 架构说明补充
```

### 🟡 代码实现和开发类问题
```
用户问题类型: "代码在哪里", "怎么实现的", "如何修改"
AI应优先参考:
├── production/core_modules/                      # 核心业务逻辑代码
│   ├── adaptive_table_comparator.py             # 表格对比算法
│   ├── document_change_analyzer.py              # 变更分析逻辑
│   ├── claude_wrapper_integration.py            # AI集成代码
│   └── excel_mcp_visualizer.py                 # Excel可视化代码
├── production/servers/                          # 服务器程序
└── claude_mini_wrapper/                         # AI封装服务代码
```

### 🟡 测试和验证类问题
```
用户问题类型: "怎么测试", "测试数据在哪", "如何验证功能"
AI应优先参考:
├── docs/specifications/09-腾讯文档智能监控系统综合测试规范.md  # 测试规范
├── refer/测试版本-小红书部门-工作表2.csv                        # 基准测试数据
├── docs/reports/实际测试结果报告.md                            # 测试结果参考
└── development/testing/                                       # 测试代码集合
```

---

## 🚨 应急问题处理路径

### ❌ 系统无法启动/运行问题
```
用户症状: "服务启动失败", "程序报错", "无法连接"
AI处理步骤:
1. 首先检查: CLAUDE.md (基础配置)
2. 然后参考: docs/guides/01-腾讯文档自动化下载使用说明.md (故障排除章节)
3. 如果是AI服务: claude_mini_wrapper/README.md
4. 最后检查: 项目综合状态报告-更新版.md (系统状态)
```

### ❌ Cookie和认证问题
```
用户症状: "Cookie过期", "认证失败", "无法下载"
AI处理步骤:
1. 优先参考: docs/guides/01-腾讯文档自动化下载使用说明.md (第64-93行Cookie详细说明)
2. 配置参考: 测试版本-性能优化开发-20250811-001430/CLAUDE.md
3. 问题分析: 项目综合状态报告-更新版.md (Cookie存储机制问题部分)
```

### ❌ 版本管理和文件问题
```
用户症状: "文件找不到", "版本混乱", "对比失败"
AI处理步骤:
1. 首先了解: 测试版本-性能优化开发-20250811-001430/csv_version_manager.py
2. 使用参考: docs/guides/02-CSV版本管理和对比系统使用说明.md
3. 问题诊断: 项目综合状态报告-更新版.md (版本管理现状分析)
```

### ❌ AI功能问题
```
用户症状: "AI分析失败", "语义识别错误", "风险等级问题"
AI处理步骤:
1. 服务状态: claude_mini_wrapper/main.py 和 test_client.py
2. 技术规格: docs/specifications/05-AI语义分析集成规格.md
3. 集成代码: production/core_modules/claude_wrapper_integration.py
```

---

## 🎯 AI回答用户问题的标准流程

### 步骤1: 问题分类
```
根据用户问题，快速分类到以上6个主要类别：
🔴 系统配置 → 🔴 项目概览 → 🔴 功能操作 → 🔴 技术架构 → 🟡 代码开发 → 🟡 测试验证
```

### 步骤2: 文档定位
```
根据分类，按优先级顺序参考对应文档：
1. 先查看🔴高优先级核心文档
2. 需要时补充🟡中优先级文档
3. 特殊情况参考🟢低优先级文档
```

### 步骤3: 信息整合
```
从多个文档中整合信息时的优先级：
1. CLAUDE.md (配置规范) > 其他配置文档
2. 项目综合状态报告-更新版.md (最新状态) > 历史报告
3. docs/guides/ (使用指南) > docs/specifications/ (技术规格)
4. production/ (生产代码) > development/ (开发测试代码)
```

### 步骤4: 回答输出
```
AI回答应包含：
✅ 引用的具体文档路径 (方便用户查看)
✅ 相关的代码文件位置 (如果涉及代码)
✅ 具体的操作步骤或命令 (如果需要执行)
✅ 风险提醒和注意事项 (基于项目状态报告)
```

---

## 📂 核心文件路径速查表

### 🔴 必备参考文件 (AI必须熟悉)
| 文档用途 | 文件路径 | 关键信息 |
|---------|----------|----------|
| 系统配置 | `CLAUDE.md` | 基础配置、使用规范 |
| 项目状态 | `项目综合状态报告-更新版.md` | 85%完成度、风险分析 |
| 下载工具 | `docs/guides/01-腾讯文档自动化下载使用说明.md` | 269行详细使用说明 |
| 操作流程 | `docs/guides/快速参考.md` | 10步完整流程 |
| 系统架构 | `docs/specifications/01-系统总体架构规格.md` | 424行架构设计 |
| AI集成 | `docs/specifications/05-AI语义分析集成规格.md` | Claude AI技术规格 |

### 🟡 重要代码文件 (按需参考)
| 功能模块 | 文件路径 | 作用说明 |
|---------|----------|----------|
| 表格对比 | `production/core_modules/adaptive_table_comparator.py` | 智能表格对比算法 |
| 变更分析 | `production/core_modules/document_change_analyzer.py` | 文档变更检测分析 |
| AI集成 | `production/core_modules/claude_wrapper_integration.py` | Claude AI调用接口 |
| Excel处理 | `production/core_modules/excel_mcp_visualizer.py` | Excel可视化标记 |
| 主服务器 | `production/servers/enhanced_flask_api_server.py` | Flask主服务(5000端口) |
| 热力图UI | `production/servers/final_heatmap_server.py` | 热力图服务(8089端口) |
| AI服务 | `claude_mini_wrapper/main.py` | AI封装服务(8081端口) |
| 下载工具 | `测试版本-性能优化开发-20250811-001430/tencent_export_automation.py` | 文档下载主程序 |
| 版本管理 | `测试版本-性能优化开发-20250811-001430/csv_version_manager.py` | 版本管理核心 |

### 🟢 数据文件 (测试参考)
| 数据类型 | 文件路径 | 用途说明 |
|---------|----------|----------|
| 测试基准 | `refer/测试版本-小红书部门-工作表2.csv` | 小红书部门基准数据 |
| 数据库 | `tencent_docs_enhanced.db` | SQLite生产数据库 |
| 当前版本 | `测试版本-性能优化开发-20250811-001430/csv_versions/current/` | 最新版本文件 |
| 对比结果 | `测试版本-性能优化开发-20250811-001430/csv_versions/comparison/` | 版本对比报告 |

---

## ⚡ AI快速决策树

```
用户提问 → AI分析问题类型
    ├─ 配置问题 → CLAUDE.md
    ├─ 状态询问 → 项目综合状态报告-更新版.md  
    ├─ 操作指导 → docs/guides/快速参考.md
    ├─ 技术细节 → docs/specifications/01-系统总体架构规格.md
    ├─ 代码相关 → production/core_modules/
    ├─ 测试验证 → refer/ + docs/specifications/09-测试规范.md
    ├─ 故障排除 → docs/guides/01-下载使用说明.md (故障排除章节)
    └─ 不确定 → 项目文档使用指南.md (获取完整导航)
```

---

## 📝 AI回答质量检查清单

### ✅ 每次回答AI应确认：
- [ ] 是否引用了正确的文档路径？
- [ ] 是否提供了具体的操作步骤？
- [ ] 是否考虑了项目当前状态(85%完成度)？
- [ ] 是否提及了相关的风险或注意事项？
- [ ] 是否给出了文件的具体位置？
- [ ] 是否使用了最新的项目状态信息？

### 🚨 AI应避免的回答方式：
- ❌ 不要基于假设回答，必须基于文档内容
- ❌ 不要推荐已废弃的文档或方法  
- ❌ 不要忽略项目状态报告中的风险提醒
- ❌ 不要给出没有文档支撑的操作建议

---

**AI专用导航更新时间**: 2025-08-14 24:00  
**适用AI类型**: Claude, GPT, 及其他大语言模型助手  
**文档覆盖率**: 100% (50+文档全覆盖)  
**决策路径数**: 6个主要类别 + 4个应急路径