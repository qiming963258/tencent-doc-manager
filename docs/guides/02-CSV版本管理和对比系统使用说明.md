# CSV版本管理和对比系统使用说明

## 🎯 系统概述

完整的CSV文件版本管理系统，包含自动化命名、版本控制、智能对比分析功能。

---

## 📁 目录结构

```
csv_versions/
├── current/           # 当前最新版本文件
├── archive/          # 历史版本归档
└── comparison/       # 对比分析工作区
```

---

## 🏷️ 文件命名规范

### 标准格式
```
{表格名称}_{YYYYMMDD}_{HHMM}_{版本号}.csv
```

### 示例文件名
- `小红书部门工作表2_20250814_1640_v002.csv`
- `回国销售计划表工作表1_20250813_1200_v001.csv`

### 命名规则说明
| 部分 | 说明 | 示例 |
|-----|------|------|
| 表格名称 | 去除特殊字符的清洁名称 | `小红书部门工作表2` |
| 日期 | YYYYMMDD格式 | `20250814` |
| 时间 | HHMM格式 | `1640` |
| 版本号 | v001递增格式 | `v002` |

---

## 🚀 集成使用方式

### 自动下载并版本管理
```bash
# 标准下载命令（自动版本管理）
python3 tencent_export_automation.py "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs" --format=csv --cookies="your_cookies"

# 禁用版本管理（仅下载）
python3 tencent_export_automation.py "URL" --format=csv --cookies="cookies" --disable-version-management
```

### 执行流程说明
1. **下载文件** → downloads目录
2. **版本检测** → 检查是否重复内容
3. **版本归档** → 旧版本移到archive
4. **新版本存储** → current目录
5. **对比准备** → comparison目录准备对比文件
6. **自动分析** → 生成对比报告

---

## 🛠️ 独立工具使用

### 版本管理器工具
```bash
# 添加新版本
python3 csv_version_manager.py add --file="/path/to/file.csv" --table="表格名称"

# 查看所有版本
python3 csv_version_manager.py list

# 查看特定表格版本
python3 csv_version_manager.py list --table="小红书部门工作表2"

# 准备对比文件
python3 csv_version_manager.py compare --table="小红书部门工作表2"
```

### CSV对比分析器
```bash
# 基础对比分析
python3 csv_comparator.py "旧文件.csv" "新文件.csv"

# 生成详细报告
python3 csv_comparator.py "旧文件.csv" "新文件.csv" --output="report.json"

# 设置数值比较精度
python3 csv_comparator.py "旧文件.csv" "新文件.csv" --precision=0.001
```

---

## 📊 对比分析功能

### 分析维度
1. **结构变化**: 行数、列数、新增/删除列
2. **单元格变更**: 逐个单元格内容对比
3. **数据质量**: 空值、重复值分析
4. **变更摘要**: 智能生成变更级别和建议

### 变更级别分类
| 级别 | 判断标准 | 说明 |
|-----|---------|------|
| 无变化 | 完全相同 | 文件内容完全一致 |
| 轻微变更 | <1%单元格变更 | 少量数据修正 |
| 中等变更 | 1-10%单元格变更 | 中等规模数据更新 |
| 重大变更 | >10%单元格变更 | 大量数据修改 |
| 结构变更 | 行列结构改变 | 表格结构调整 |

### 输出报告格式
```json
{
  "success": true,
  "file_info": {
    "old_file": "文件名",
    "new_file": "文件名",
    "old_size": 71853,
    "new_size": 71722
  },
  "structure_analysis": {
    "row_changes": {...},
    "column_changes": {...}
  },
  "cell_analysis": {
    "modified_cells": [...],
    "statistics": {...}
  },
  "data_quality": {
    "completeness": {...},
    "consistency": {...}
  },
  "summary": {
    "change_level": "轻微变更",
    "key_changes": [...],
    "recommendations": [...]
  }
}
```

---

## 📈 实际使用案例

### 示例：小红书部门工作表2对比
```bash
# 自动执行流程
python3 tencent_export_automation.py "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs" --format=csv --cookies="cookies"
```

**执行结果输出：**
```
✅ 新版本已添加: 小红书部门工作表2_20250814_1640_v002.csv
📁 已归档旧版本: 小红书部门工作表2_20250813_1200_v001.csv
📊 对比文件已准备: 对比文件已准备完成: 小红书部门工作表2
📄 当前版本: current_小红书部门工作表2_20250814_1640_v002.csv
📄 对比版本: previous_小红书部门工作表2_20250813_1200_v001.csv
```

**对比分析结果：**
- 🎯 变更级别: 轻微变更
- 📈 结构变化: 94行 → 94行 (无结构变化)
- 🔄 单元格变化: 18个单元格变更 (变更率0.96%)
- 📋 关键变更: 修改18个单元格

---

## 🔧 高级配置

### 版本管理配置
- **重复内容检测**: MD5哈希值比较
- **自动归档**: 旧版本自动移动到archive目录
- **文件名清理**: 自动去除特殊字符和前缀

### 对比分析配置
- **数值精度**: 默认0.01，可调整
- **编码支持**: UTF-8, GBK, GB2312自动检测
- **空值处理**: 自动填充和标准化

---

## ⚠️ 注意事项

### 文件要求
1. CSV格式文件
2. UTF-8或GBK编码
3. 表格结构相对稳定

### 性能限制
1. 建议文件大小<100MB
2. 行数建议<50,000行
3. 列数建议<100列

### 错误处理
1. **重复内容**: 自动跳过，不创建新版本
2. **文件损坏**: 报告加载错误，提供详细信息
3. **权限问题**: 检查文件读写权限

---

## 📝 下一步操作指南

### 第一次使用
1. 下载CSV文件并自动创建版本
2. 查看version列表确认文件正确
3. 检查对比分析结果

### 日常使用流程
1. **定期下载**: 按需下载最新版本
2. **版本检查**: 使用list命令查看版本历史  
3. **对比分析**: 分析变更内容和影响
4. **决策支持**: 基于对比结果做业务决策

### 故障排除
```bash
# 检查版本状态
python3 csv_version_manager.py list --table="表格名称"

# 重新对比分析
python3 csv_comparator.py "旧文件" "新文件" -o "new_report.json"

# 清理对比目录
rm -rf csv_versions/comparison/*
```

---

**版本**: v1.0  
**更新时间**: 2025-08-14  
**功能状态**: ✅ 完全可用