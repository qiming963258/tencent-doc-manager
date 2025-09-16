# UI与综合打分适配规范说明 v1.0

## 📊 核心原则

**唯一数据源原则**：UI只能从综合打分JSON文件（`/tmp/comprehensive_scoring_data.json`）获取数据，这是强制要求，不允许直接访问CSV文件或其他中间文件。

## 🎯 综合打分文件的五个关键内容

### 1️⃣ 所有表名列表 (`table_names`)
- **用途**：UI热力图左侧Y轴显示
- **格式**：字符串数组
- **示例**：
```json
"table_names": [
  "小红书内容审核记录表",
  "企业风险评估矩阵表",
  "财务月度报表汇总表"
]
```

### 2️⃣ 每标准列平均加权修改打分 (`column_avg_scores`)
- **用途**：UI热力图顶部显示列的整体风险水平
- **格式**：包含19个标准列的对象
- **说明**：每个值代表该列在所有表格中的平均风险分数
- **示例**：
```json
"column_avg_scores": {
  "序号": 0.85,        // L1列，高风险
  "负责人": 0.55,      // L2列，中风险
  "来源": 0.25         // L3列，低风险
}
```

### 3️⃣ 每列具体修改行数和打分 (`table_scores[].column_scores`)
- **用途**：UI热力图单元格颜色渲染和悬停详情
- **关键字段**：
  - `modified_rows`: 修改的行号数组
  - `row_scores`: 对应行的风险打分数组
  - `column_level`: 列级别（L1/L2/L3）
  - `avg_score`: 平均分数（决定单元格颜色）
- **示例**：
```json
"column_scores": {
  "项目类型": {
    "column_level": "L1",
    "avg_score": 0.98,
    "modified_rows": [5, 12, 28],
    "row_scores": [0.95, 0.99, 1.0],
    "modifications": 3
  }
}
```

### 4️⃣ 表格URL列表 (`table_scores[].table_url`)
- **用途**：点击表格名称跳转到腾讯文档
- **格式**：标准腾讯文档URL
- **示例**：`"https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"`

### 5️⃣ 全部修改数 (`total_modifications`)
- **用途**：UI右上角显示总修改统计
- **格式**：整数
- **计算**：所有表格修改数之和

## 🎨 颜色映射规范（0000标准）

| 打分范围 | 颜色 | 颜色代码 | 风险等级 | UI表现 |
|---------|------|---------|---------|--------|
| score ≥ 0.8 | 红色 | #FF0000 | 极高风险 | 热力图深红色块 |
| 0.6 ≤ score < 0.8 | 橙色 | #FFA500 | 高风险 | 热力图橙色块 |
| 0.4 ≤ score < 0.6 | 黄色 | #FFFF00 | 中风险 | 热力图黄色块 |
| 0.1 ≤ score < 0.4 | 绿色 | #00FF00 | 低风险 | 热力图绿色块 |
| score < 0.1 | 蓝色 | #0000FF | 极低风险 | 热力图蓝色块 |

## 📐 列级别定义（L1/L2/L3）

### L1级别列（核心关键）
- **最低分**：0.8
- **特点**：任何修改都是高风险
- **包含列**：序号、项目类型、目标对齐、关键KR对齐
- **UI表现**：通常显示为红色或橙色

### L2级别列（重要业务）
- **最低分**：0.4
- **特点**：需要AI智能评估
- **包含列**：负责人、协助人、监督人、重要程度、预计完成时间、完成进度
- **UI表现**：通常显示为黄色或橙色
- **特殊处理**：包含AI决策建议（APPROVE/REVIEW/REJECT）

### L3级别列（一般信息）
- **最低分**：0.1
- **特点**：风险较低，仅做基础对比
- **包含列**：来源、任务发起时间、具体计划内容、邓总指导登记等
- **UI表现**：通常显示为绿色或蓝色

## 🖥️ UI组件数据映射

### 热力图矩阵
```javascript
// Y轴（行）
rows = comprehensive_data.table_names

// X轴（列）
columns = ["序号", "项目类型", "来源", ...] // 19个标准列

// 单元格颜色
cellColor = comprehensive_data.table_scores[rowIndex]
            .column_scores[columnName].avg_score

// 应用颜色映射
if (cellColor >= 0.8) color = "#FF0000"
else if (cellColor >= 0.6) color = "#FFA500"
// ... 依此类推
```

### 右侧列分布图（鼠标悬停时显示）
```javascript
onHover(columnName) {
  for (table of comprehensive_data.table_scores) {
    columnData = table.column_scores[columnName]
    if (columnData) {
      // 显示条形图
      barWidth = columnData.avg_score * maxWidth
      barColor = getColorByScore(columnData.avg_score)
      modificationCount = columnData.modifications
      riskLevel = columnData.column_level
    }
  }
}
```

### 悬停详情弹窗
```javascript
showDetails(tableIndex, columnName) {
  table = comprehensive_data.table_scores[tableIndex]
  column = table.column_scores[columnName]

  details = {
    表格名: table.table_name,
    修改行: column.modified_rows,  // [5, 12, 28]
    行打分: column.row_scores,     // [0.95, 0.99, 1.0]
    列级别: column.column_level,   // "L1"
    平均分: column.avg_score,      // 0.98
    AI建议: column.ai_decisions    // 仅L2列有
  }
}
```

### 表格链接跳转
```javascript
onTableNameClick(tableIndex) {
  url = comprehensive_data.table_scores[tableIndex].table_url
  window.open(url, '_blank')  // 新标签页打开腾讯文档
}
```

## ✅ 数据完整性验证

服务器启动时必须验证：

1. **必需字段存在**
   - `table_names` 是数组
   - `column_avg_scores` 包含19个键
   - `table_scores` 数组长度与 `table_names` 一致
   - 每个 `table_score` 包含 `table_url`
   - `total_modifications` 是数字

2. **打分规则符合标准**
   - L1列打分 ≥ 0.8
   - L2列打分 ≥ 0.4
   - L3列打分 > 0.1
   - 所有打分在 0-1 范围内

3. **数据一致性**
   - `modified_rows` 和 `row_scores` 长度相同
   - `modifications` 等于 `modified_rows` 长度
   - `total_modifications` 等于所有表格修改数之和

## 📁 文件位置

- **生产环境数据**：`/tmp/comprehensive_scoring_data.json`
- **带注释示例**：`/root/projects/tencent-doc-manager/演示讲解_详细打分系统/综合打分结果_带注释版_W36.json`
- **生产版本示例**：`/root/projects/tencent-doc-manager/演示讲解_详细打分系统/综合打分结果_生产版_W36.json`

## 🔧 服务器配置

```python
# 强制使用综合打分模式
COMPREHENSIVE_MODE = True

# 数据源设置（只能是comprehensive）
DATA_SOURCE = 'comprehensive'

# 启动时加载综合打分数据
comprehensive_scoring_data = load_json('/tmp/comprehensive_scoring_data.json')
```

## 📝 注意事项

1. **禁止绕过**：不允许提供切换到CSV模式的选项
2. **实时更新**：修改综合打分文件后需重启服务器
3. **URL真实性**：表格URL必须是真实有效的腾讯文档链接
4. **性能优化**：可以缓存综合打分数据5分钟
5. **错误处理**：如果综合打分文件不存在或格式错误，服务器应拒绝启动

---

**文档版本**：1.0
**更新日期**：2025-09-13
**维护团队**：热力图开发组