用中文回复我
不要输出简化版本
因对复杂任务请：1先阅读相关spec文档，如果文档内容不清晰向我说出需求；2合理分配agents用于不同计划，给出精要全面的agents工作配合计划。

## 腾讯文档智能监控系统 - 项目总览

🎯 **企业级智能文档变更监控与风险评估系统**

### 📋 系统架构概述

本系统是一个完整的企业级文档监控解决方案，包含10个主要处理步骤，支持5200+参数配置，实现从CSV对比分析到Excel半填充标记的完整链路。系统已升级为配置驱动架构，支持动态文档数量管理。

### 🚀 核心功能模块

1. **📊 智能变更检测系统**
   - CSV/Excel格式表格对比分析
   - AI驱动的列名标准化
   - 自适应表格结构处理
   - 风险等级智能分类（L1/L2/L3）
   - **文件命名规范**：`tencent_{文档名}_{时间戳}_{版本类型}_W{周数}.{扩展名}`
     - 扩展名根据实际格式动态决定（csv/xlsx）
     - 不再强制使用.csv扩展名

2. **🔥 科学热力图可视化**
   - 动态N×19矩阵显示（N根据文档数量自动调整）
   - 高斯平滑算法处理
   - 5级色彩分段映射（蓝→青→绿→黄→血红）
   - 实时统计和热点识别

3. **📝 专业Excel半填充标记**
   - lightUp图案对角线纹理
   - 企业级颜色编码
   - 详细AI分析批注
   - 自动上传腾讯文档（Cookie认证，成功率95%+）

4. **🤖 Claude AI语义分析**
   - 变更合理性评估
   - 风险等级智能判断
   - 审批建议生成
   - 置信度评分

5. **🔧 配置驱动架构**
   - RealDocumentLoader动态文档管理
   - real_documents.json配置文件
   - 支持任意数量腾讯文档
   - 独立URL映射系统

6. **⚙️ 配置中心统一管理**
   - **位置**: `/production/config/` - 所有配置的单一真相源
   - **价值**: 解决20个文件配置分散问题，统一管理
   - **文件结构**:
     ```
     production/config/
     ├── config_center.py       # 配置中心（单例模式）
     ├── column_definitions.py  # 标准19列定义
     ├── risk_classification.py # L1/L2/L3风险分级
     └── scoring_parameters.py  # 权重和打分参数
     ```
   - **快速使用**:
     ```python
     from production.config import (
         STANDARD_COLUMNS,     # 标准19列
         L1_COLUMNS,          # 高风险列（7列）
         L2_COLUMNS,          # 中风险列（6列）
         L3_COLUMNS,          # 低风险列（6列）
         get_column_weight    # 获取列权重
     )

     # ⚠️ 关键：第14-16列已统一为：
     # 14: 完成链接（非"形成计划清单"）
     # 15: 经理分析复盘（非"进度分析总结"）
     # 16: 最新复盘时间（非"复盘时间"）
     ```
   - **重要提醒**:
     - ✅ 向后兼容：`standard_columns_config.py`仍可用（已成为适配器）
     - ⚠️ 配置只影响新生成数据，已有缓存需清理
     - 📖 详细说明见：`docs/配置中心使用指南.md`

### 📊 完整处理流程

**步骤1-3**: CSV数据采集与初步对比
**步骤4**: AI列名标准化处理
**步骤5**: 数据清洗与重新打分
**步骤6**: 5200+参数UI数据生成
**步骤7**: 复杂热力图UI显示（支持动态行数）
**步骤8**: Excel MCP专业半填充
**步骤9**: 自动上传腾讯文档
**步骤10**: UI链接绑定与交互

### 🎯 核心技术特性
- **自适应列匹配**: 智能处理不同表格结构
- **数据清洗算法**: 标准化评分权重计算
- **热力图算法**: 高斯平滑+科学色彩映射
- **Excel MCP集成**: 专业文档标记
- **实时UI更新**: WebSocket实时数据同步

## 项目完成状态

✅ **腾讯文档智能监控系统已全面完成**

### 🎯 核心成果
- 完整10步处理流程 - 全部实现并测试通过
- Claude封装程序 (端口8081) - 正常运行，API成功率88.9%
- 智能热力图UI (端口8089) - 完整功能，动态N×19矩阵显示
- Excel MCP半填充 - 专业标记，自动上传
- AI语义分析功能 - 100%测试通过，平均置信度0.85

### 📊 实际测试结果
**完整流程测试**: 10/10步骤全部通过 ✅  
**5200+参数处理**: 100%正确解析 ✅  
**热力图渲染**: 高斯平滑+科学色彩 ✅  
**Excel半填充**: lightUp纹理+AI批注 ✅  
**系统评级**: 企业级生产就绪 🏅

### 📁 完整文件清单
详见: `系统功能组件完整清单.md`

## 🔧 8089端口热力图UI服务配置

### ⚠️ 访问问题解决方案
**问题症状**: http://202.140.143.88:8089/ 被nginx防火墙阻拦  
**解决方案**: 
```bash
sudo ufw allow 8089
```

### 🚀 正确启动服务器
**错误启动**: `python3 debug_ui_server.py` - 只显示加载页面  
**正确启动**: `python3 final_heatmap_server.py` - 完整功能UI

### 📊 服务器功能对比
| 服务器文件 | 功能 | 用途 |
|-----------|------|------|
| `debug_ui_server.py` | 测试页面 | React组件测试 |
| `final_heatmap_server.py` | 完整热力图UI + 增强功能 | **生产使用** |
| `simple_ui_server.py` | 简化版UI | 基础功能测试 |

### 🔥 热力图UI特色功能
- ✅ 高斯平滑算法
- ✅ 科学热力图颜色映射  
- ✅ 智能数据排序
- ✅ 动态N×19矩阵（支持任意数量文档）
- ✅ 真实风险统计

### 🆕 增强功能
#### 1. **详细日志显示（8093格式）**
- 图标系统自动匹配（✅成功、❌错误、📋处理、🔥开始等）
- 实时工作流状态追踪
- 彩色日志输出，易于识别问题

#### 2. **URL软删除管理**
- 链接配置支持软删除机制
- 已删除链接保留历史记录（deleted_links数组）
- 前端实时显示当前存储的所有URL
- "导入链接"按钮已更名为"更新链接"

#### 3. **基线文件管理界面**
- 可折叠的管理界面，显示当前周数和存储路径
- 支持腾讯文档URL直接下载为基线文件
- 文件列表显示（包含大小、修改时间）
- 每个文件独立删除按钮（软删除到.deleted文件夹）
- 自动归档到当前周的baseline文件夹

### 📁 相关API端点
- `/api/save-download-links` - URL配置保存（支持软删除）
- `/api/baseline-files` - 基线文件管理（GET/POST/DELETE）
- `/api/get-download-links` - 获取活跃的URL配置

## Excel MCP 使用规范

⚠️ **重要**: 在使用Excel MCP进行任何Excel文件操作前，必须先阅读以下使用指南：

📖 **完整使用指南**: [docs/Excel-MCP-AI-使用指南.md](docs/Excel-MCP-AI-使用指南.md)

### 快速参考

1. **推荐使用**: `mcp__excel__*` 函数系列
2. **文件路径**: 必须使用绝对路径，如 `/root/projects/file.xlsx`
3. **内存限制**: 单次操作不超过2000单元格
4. **中文支持**: 直接使用中文工作表名和数据内容
5. **数据格式**: 写入时使用二维数组 `[[row1], [row2]]`

### 错误处理
- 文件不存在 → 检查绝对路径
- 内存超限 → 使用分页处理
- 格式错误 → 检查二维数组格式

## 🚀 系统架构特性

### 📊 架构升级：从虚拟到真实
系统已完成重大架构升级，从虚拟测试数据迁移到真实腾讯文档：

#### 核心变更
- **数据源**: 从9个虚拟表格 → 3个真实腾讯文档
- **热力图**: 从固定30×19矩阵 → 动态N×19矩阵
- **URL映射**: 每个文档独立URL（修复了全部链接到小红书的问题）
- **架构模式**: 配置驱动架构，支持动态扩展

#### 当前配置的真实文档
1. **副本-测试版本-出国销售计划表**
   - URL: https://docs.qq.com/sheet/DWEFNU25TemFnZXJN
   - 用途: 出国销售数据监控

2. **副本-测试版本-回国销售计划表**
   - URL: https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr
   - 用途: 回国销售数据监控

3. **测试版本-小红书部门**
   - URL: https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R
   - 用途: 小红书部门数据监控

#### 技术实现
- **核心模块**: `/production/core_modules/real_doc_loader.py`
- **配置文件**: `/production/config/real_documents.json`
- **动态加载**: RealDocumentLoader类统一管理
- **API同步**: document-links与real_csv_data完全一致

#### 扩展方法
如需添加更多文档，只需编辑配置文件：
```json
{
  "documents": [
    {
      "name": "文档名称",
      "url": "腾讯文档URL",
      "doc_id": "文档ID",
      "csv_pattern": "CSV文件模式",
      "description": "文档描述"
    }
  ]
}
```

## 📋 已修复问题

### 文件扩展名问题 (已修复)
- **问题**: xlsx文件错误使用.csv扩展名
- **解决**: 文件命名支持动态扩展名 `{文档名}_{时间戳}_{版本}_W{周}.{ext}`
- **状态**: ✅ 已完成

---

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

