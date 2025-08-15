# 🤖 AI助手快速参考卡片

## ⚡ 一页式AI导航 (打印/屏幕常驻版)

### 🔴 核心6大文档路径
```
1. CLAUDE.md                                    → 系统配置基础
2. 项目综合状态报告-更新版.md                      → 最新项目状态(85%完成)
3. docs/guides/01-腾讯文档自动化下载使用说明.md      → 下载工具详细使用(269行)
4. docs/guides/快速参考.md                       → 10步完整流程操作
5. docs/specifications/01-系统总体架构规格.md       → 系统架构设计(424行)
6. docs/specifications/05-AI语义分析集成规格.md     → Claude AI技术规格
```

### 🚨 应急4大处理路径
```
🔥 系统启动失败    → CLAUDE.md → docs/guides/01-下载使用说明.md(故障排除)
🔥 Cookie认证问题  → docs/guides/01-下载使用说明.md(第64-93行)
🔥 版本管理问题    → csv_version_manager.py → 项目状态报告(版本管理部分)
🔥 AI功能问题      → claude_mini_wrapper/ → docs/specifications/05-AI集成规格.md
```

### 🎯 问题分类快速决策
```
"怎么配置/设置"     → CLAUDE.md
"项目状态/进度"     → 项目综合状态报告-更新版.md  
"如何操作/使用"     → docs/guides/快速参考.md
"技术架构/设计"     → docs/specifications/01-系统架构.md
"代码在哪/实现"     → production/core_modules/
"如何测试/验证"     → refer/测试数据 + docs/specifications/09-测试规范.md
```

### 📂 核心代码文件位置
```
📊 表格对比: production/core_modules/adaptive_table_comparator.py
📈 变更分析: production/core_modules/document_change_analyzer.py  
🤖 AI集成: production/core_modules/claude_wrapper_integration.py
📝 Excel处理: production/core_modules/excel_mcp_visualizer.py
🌐 主服务器: production/servers/enhanced_flask_api_server.py (5000端口)
🔥 热力图: production/servers/final_heatmap_server.py (8089端口)
🤖 AI服务: claude_mini_wrapper/main.py (8081端口)
📥 下载工具: 测试版本-性能优化开发-20250811-001430/tencent_export_automation.py
🔄 版本管理: 测试版本-性能优化开发-20250811-001430/csv_version_manager.py
```

### 💾 重要数据文件
```
🎯 测试基准: refer/测试版本-小红书部门-工作表2.csv
💾 数据库: tencent_docs_enhanced.db  
📋 当前版本: 测试版本-.../csv_versions/current/
📊 对比结果: 测试版本-.../csv_versions/comparison/
```

### 🏷️ 系统状态关键信息
```
✅ AI服务: 8081端口, 92.04%成功率, 运行200,422秒
✅ 热力图UI: 8089端口, 30×19矩阵, 高斯平滑算法
✅ 主系统: 5000端口, Flask API, 全功能集成
⚠️ Excel MCP: 状态待确认, 半填充功能需验证
⚠️ Cookie管理: 手动输入, 无持久化存储
⚠️ 版本识别: 基于时间戳, 可能出现混乱
```

### 📋 AI回答检查点
```
✅ 引用具体文档路径
✅ 提供操作步骤/命令  
✅ 考虑85%完成度状态
✅ 提及风险和注意事项
✅ 给出文件位置
❌ 避免无依据推测
❌ 避免推荐废弃方法
```

---
**小红书部门测试URL**: `https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs`  
**主要测试场景**: Cookie存储→CSV下载→版本管理→AI分析→热力图→Excel输出  
**系统评级**: 🏆 优秀级企业AI系统(85%完成度)