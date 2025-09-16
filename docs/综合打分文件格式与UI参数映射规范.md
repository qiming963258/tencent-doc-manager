# 综合打分文件格式与UI参数映射规范 v1.0

生成时间: 2025-09-15
作者: Claude Assistant
状态: 🔍 深度分析完成

---

## 📊 UI需要的7种核心参数

### 1. 热力图主体数据
- **参数名**: 列名 + 表名 + 修改值
- **用途**: 渲染30×19的热力图矩阵
- **数据源字段**:
  ```json
  {
    "tables": ["出国销售计划表", "回国销售计划表", "小红书部门"],
    "ui_data": [{
      "table_name": "出国销售计划表",
      "row_data": [
        {
          "column": "任务发起时间",
          "heat_value": 0.7,
          "color": "#FFA500"
        }
      ],
      "heat_values": [0.7, 0.7, 0.7, ...]  // 19个值
    }]
  }
  ```

### 2. 鼠标悬浮窗数据
- **参数名**: 每个表每列发生的总修改行数
- **用途**: 显示悬浮提示信息
- **数据源字段**:
  ```json
  {
    "ui_data": [{
      "row_data": [{
        "column": "任务发起时间",
        "modified_rows": [7]  // 修改的行号列表
      }]
    }]
  }
  ```

### 3. 右侧统计UI数据
- **参数名**: 每个表总修改数
- **用途**: 显示表格修改统计
- **数据源字段**:
  ```json
  {
    "table_scores": [{
      "table_name": "出国销售计划表",
      "total_modifications": 18
    }]
  }
  ```

### 4. 右侧一维图数据(1)
- **参数名**: 每个表总行数
- **用途**: 计算修改密度
- **数据源字段**:
  ```json
  {
    "table_scores": [{
      "total_rows": 270
    }]
  }
  ```

### 5. 右侧一维图数据(2)
- **参数名**: 每列的发生修改的行位置
- **用途**: 显示行级修改分布
- **数据源字段**:
  ```json
  {
    "ui_data": [{
      "row_level_data": {
        "column_modifications": {
          "任务发起时间": {
            "modified_rows": [7],
            "count": 1
          }
        }
      }
    }]
  }
  ```

### 6. 右侧一维图行级数据
- **参数名**: 修改的行列表
- **用途**: 显示整体修改分布
- **数据源字段**:
  ```json
  {
    "ui_data": [{
      "row_level_data": {
        "modified_rows": [1, 2, 3, 4, 5, 6, 7, ...],
        "total_differences": 18
      }
    }]
  }
  ```

### 7. 热力图颜色映射
- **参数名**: 颜色值
- **用途**: 根据风险等级显示颜色
- **数据源字段**:
  ```json
  {
    "ui_data": [{
      "row_data": [{
        "color": "#FFA500"  // 橙色表示中等风险
      }]
    }]
  }
  ```

---

## ✅ 当前系统参数提供状态

| 参数 | 后端提供 | UI接收 | 状态 | 问题 |
|------|---------|--------|------|------|
| 1. 表名 | ✅ `tables` + `ui_data[].table_name` | ✅ 正确接收 | ✅ 正常 | - |
| 2. 列名 | ✅ `ui_data[].row_data[].column` | ✅ 正确接收 | ✅ 正常 | - |
| 3. 修改值 | ✅ `ui_data[].heat_values` | ✅ 正确接收 | ✅ 正常 | - |
| 4. 每列修改行数 | ✅ `ui_data[].row_data[].modified_rows` | ❌ 查找 `colMods?.rows` | ⚠️ 字段名不匹配 | UI使用错误字段名 |
| 5. 表总修改数 | ✅ `table_scores[].total_modifications` | ✅ 正确接收 | ✅ 正常 | - |
| 6. 表总行数 | ✅ `table_scores[].total_rows` | ✅ 正确接收 | ✅ 正常 | - |
| 7. 行位置数据 | ✅ `row_level_data.modified_rows` | ✅ 正确接收 | ✅ 正常 | - |

---

## 🔴 发现的问题

### 问题1: UI字段映射错误
**位置**: `final_heatmap_server.py` 第8774行
```javascript
// 错误代码
{colMods?.rows && colMods.rows.length > 0 && (

// 应该改为
{colMods?.modified_rows && colMods.modified_rows.length > 0 && (
```

### 问题2: 数据源混淆
**现象**: UI同时从多个地方获取数据
- `detailedScores` - 详细打分数据
- `tableScores` - 表格打分数据
- `colMods` - 列修改数据
- `hoveredCell` - 悬浮单元格数据

**建议**: 统一从 `ui_data` 获取所有UI展示数据

---

## 📐 完整的综合打分文件JSON结构

```json
{
  "timestamp": "2025-09-15T12:28:01",
  "week": "W38",
  "total_modifications": 18,

  // 表格列表
  "tables": [
    "出国销售计划表",
    "回国销售计划表",
    "小红书部门"
  ],

  // 表格打分数据（用于统计）
  "table_scores": [
    {
      "table_name": "出国销售计划表",
      "total_rows": 270,
      "total_modifications": 18,
      "risk_score": 0.6,
      "column_scores": {
        "任务发起时间": {
          "modified_rows": [4],
          "avg_score": 0.7,
          "modification_count": 1,
          "total_rows": 270
        }
        // ... 其他18列
      },
      "row_level_data": {
        "total_rows": 270,
        "total_differences": 18,
        "column_modifications": {
          "任务发起时间": {"modified_rows": [7], "count": 1}
          // ... 其他列
        },
        "modified_rows": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
      }
    }
    // ... 其他2个表格
  ],

  // UI展示数据（用于渲染）
  "ui_data": [
    {
      "table_name": "出国销售计划表",
      "heat_values": [0.7, 0.7, 0.7, ...],  // 19个值
      "row_data": [
        {
          "column": "任务发起时间",
          "heat_value": 0.7,
          "color": "#FFA500",
          "modified_rows": [7]  // 修改的行号
        }
        // ... 其他18列
      ],
      "row_level_data": {
        "total_rows": 270,
        "total_differences": 18,
        "column_modifications": {
          "任务发起时间": {"modified_rows": [7], "count": 1}
        },
        "modified_rows": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
      }
    }
    // ... 其他2个表格
  ]
}
```

---

## 🎯 数据流向图

```
综合打分文件
    ├── tables[] ─────────────────> 热力图Y轴（表名）
    ├── ui_data[]
    │   ├── table_name ───────────> 表格标题
    │   ├── heat_values[] ────────> 热力图颜色强度
    │   ├── row_data[]
    │   │   ├── column ──────────> 热力图X轴（列名）
    │   │   ├── heat_value ──────> 单元格热力值
    │   │   ├── color ───────────> 单元格颜色
    │   │   └── modified_rows[] ─> 悬浮窗显示行号
    │   └── row_level_data
    │       ├── total_rows ──────> 右侧统计总行数
    │       ├── total_differences > 右侧统计总修改
    │       ├── column_modifications
    │       │   └── {列名}
    │       │       └── modified_rows[] > 一维图行分布
    │       └── modified_rows[] ─> 整体修改行列表
    └── table_scores[]
        ├── total_modifications ─> 右侧统计修改数
        └── total_rows ──────────> 右侧统计总行数
```

---

## 📋 修复建议

### 1. 立即修复UI字段映射
```javascript
// 在 final_heatmap_server.py 第8701-8704行
const colMods = tableScores?.column_modifications?.[hoveredCell.columnName];
const modCount = colMods?.modified_rows?.length || 0;  // 改为modified_rows

// 第8774行
{colMods?.modified_rows && colMods.modified_rows.length > 0 && (
```

### 2. 统一数据源
- 所有UI展示数据统一从 `ui_data` 获取
- 避免混用 `table_scores` 和 `ui_data`

### 3. 增加数据验证
```javascript
// 在数据加载时验证必要字段
if (!result.ui_data || !result.table_scores) {
  console.error('综合打分数据格式不完整');
}
```

---

## 🔍 深度分析结论

### ✅ 数据完整性
- **后端**: 提供了UI需要的全部7种参数 ✅
- **格式**: JSON结构清晰，层次分明 ✅
- **内容**: 包含真实的修改数据（18个对角线修改）✅

### ⚠️ 需要优化
1. **UI字段映射**: `colMods.rows` → `colMods.modified_rows`
2. **数据源统一**: 避免从多个地方获取相同数据
3. **错误处理**: 增加数据格式验证

### 📊 实际效果
当前系统**能够**提供UI需要的全部7种参数，数据是**真实准确**的。但UI在接收数据时存在**字段映射错误**，需要修复才能完全正确显示。

---

## 📝 版本历史
- v1.0 (2025-09-15): 初始版本，完成7种参数映射分析