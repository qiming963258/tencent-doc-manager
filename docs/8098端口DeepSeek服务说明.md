# 8098端口 DeepSeek增强服务说明

## 服务概述

8098端口提供了DeepSeek AI增强的列名标准化服务，是整个系统的智能处理核心。

**访问地址**: http://localhost:8098

## 🔑 API密钥配置（重要）

### 密钥存储位置

系统使用共享的DeepSeek API密钥，存储在多个位置：

| 文件路径 | 行号 | 变量名 | 说明 |
|----------|------|--------|------|
| `/deepseek_enhanced_server_complete.py` | 34 | `API_KEY` | 8098服务主密钥 |
| `/production/core_modules/deepseek_client.py` | 156 | `SHARED_API_KEY` | 详细打分系统共享密钥 |
| `/deepseek_enhanced_server.py` | 34 | `API_KEY` | 备份服务密钥 |
| `/deepseek_enhanced_server_fixed.py` | 34 | `API_KEY` | 修复版服务密钥 |

### 当前使用的API密钥
```
sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb
```

### 密钥更新方法

如需更新API密钥，请同时修改以下文件：

1. **主服务器文件** (必须更新)
   ```python
   # /deepseek_enhanced_server_complete.py 第34行
   API_KEY = "your_new_api_key_here"
   ```

2. **详细打分系统** (必须更新)
   ```python
   # /production/core_modules/deepseek_client.py 第156行
   SHARED_API_KEY = "your_new_api_key_here"
   ```

3. **其他服务器版本** (建议更新)
   - `/deepseek_enhanced_server.py`
   - `/deepseek_enhanced_server_fixed.py`
   - `/deepseek_enhanced_server_final.py`

## 核心功能

### 1. 列名标准化 API

**端点**: `POST /api/standardize_columns`

**功能**: 将不规范的列名映射到19个标准列名

**请求示例**:
```json
{
  "columns": ["序号", "项目分类", "来源地", "任务开始时间"],
  "use_numbering": false
}
```

**响应示例**:
```json
{
  "success": true,
  "standardized": {
    "序号": "序号",
    "项目分类": "项目类型",
    "来源地": "来源",
    "任务开始时间": "任务发起时间"
  },
  "token_count": 245
}
```

### 2. 文件处理 API

**端点**: `POST /api/process_file`

**功能**: 处理完整的CSV对比文件，执行列名标准化

**输入文件格式**:
- 简化对比JSON文件
- 包含modifications数组
- 每个修改包含column_name字段

**输出**:
- 标准化后的JSON文件
- 保存位置: `/comparison_results/*_standardized.json`

## 与其他系统的集成

### L2语义分析集成

8098端口的API密钥被以下系统共享使用：

1. **详细打分系统** (端口8100)
   - 使用相同的API密钥进行L2列语义分析
   - 调用路径: `integrated_scorer.py` → `l2_semantic_analysis_two_layer.py` → `deepseek_client.py`

2. **列名标准化处理器**
   - 文件: `column_standardization_processor_v3.py`
   - 直接使用API_KEY变量

3. **语义分析生成器**
   - 文件: `generate_semantic_report.py`
   - 共享同一API密钥

## 服务架构

```
8098端口服务
    ├── deepseek_enhanced_server_complete.py (主服务)
    ├── column_standardization_processor_v3.py (处理器)
    └── deepseek_client.py (API客户端)
            ↓
        DeepSeek API
            ↓
        标准化结果
```

## 19个标准列名

系统识别并映射到以下标准列名：

1. 序号
2. 项目类型
3. 来源
4. 任务发起时间
5. 目标对齐
6. 关键KR对齐
7. 具体计划内容
8. 邓总指导登记（日更新）
9. 负责人
10. 协助人
11. 监督人
12. 重要程度
13. 预计完成时间
14. 完成进度（%）
15. 形成计划清单
16. 复盘时间
17. 对上汇报
18. 应用情况
19. 进度分析总结

## 启动服务

```bash
# 启动8098端口服务
python3 deepseek_enhanced_server_complete.py

# 或使用后台运行
nohup python3 deepseek_enhanced_server_complete.py > /tmp/8098_server.log 2>&1 &
```

## 故障排查

### API密钥问题

**症状**: "DeepSeek API密钥未配置"错误

**解决方案**:
1. 检查密钥配置文件是否正确
2. 确认密钥没有过期
3. 验证密钥格式（应以"sk-"开头）

### 服务连接问题

**症状**: 无法连接到8098端口

**解决方案**:
```bash
# 检查端口占用
lsof -i:8098

# 查看服务日志
tail -f /tmp/8098_server.log

# 重启服务
pkill -f "deepseek_enhanced_server"
python3 deepseek_enhanced_server_complete.py
```

## 性能优化

- **批量处理**: 支持一次性处理多个列名
- **缓存机制**: 相同的列名映射会被缓存
- **Token优化**: 使用精简的提示词减少API消耗

## 监控指标

- API调用成功率
- 平均响应时间
- Token消耗统计
- 列名映射准确率

## 更新历史

- **2025-09-08**: 集成共享API密钥到详细打分系统
- **2025-08-15**: 实现列名标准化服务
- **2025-08-13**: 初始版本发布