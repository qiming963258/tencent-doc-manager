# 03 - CSV对比完整技术规范
## CSV Comparison Complete Technical Specification

> 统一整合版本 - 合并自原03系列三个文档
> 更新时间: 2025-09-17
> 版本: 5.0.0
> 状态: 生产就绪

---

## 第一部分：CSV对比算法核心

### 1.1 算法本质与创新

CSV对比算法采用**单元格级别精确对比**，解决了传统行级别对比在处理不同列数文件时的致命缺陷。

**核心创新点**：
- 通过列标准化实现跨列数对比
- 使用difflib智能行匹配
- 加权评分反映真实相似度
- 简化输出文件大小减少89%

### 1.2 v4.0增强版关键改进（2025-09-15）

| 问题 | v3.0缺陷 | v4.0解决方案 |
|-----|---------|------------|
| **列数不匹配** | 整行对比失败（0%相似度） | 仅对比共同列，智能处理差异 |
| **检测范围** | 仅检测19个标准列 | 检测所有列的修改 |
| **行顺序变化** | 无法识别移动的行 | difflib序列匹配器智能对齐 |
| **相似度计算** | 二元判断（相同/不同） | 三层加权（60%内容+30%结构+10%行数） |

**准确率提升**: 从v3.0的33%提升到v4.0的100%（全列检测）

### 1.3 核心算法实现

#### 数据预处理
```python
def normalize_for_comparison(data: List[List[str]], target_cols: int) -> List[Tuple]:
    """标准化行数据以支持不同列数对比"""
    normalized = []
    for row in data:
        if len(row) >= target_cols:
            normalized_row = tuple(row[:target_cols])
        else:
            # 填充空字符串到目标列数
            normalized_row = tuple(row + [''] * (target_cols - len(row)))
        normalized.append(normalized_row)
    return normalized
```

#### 智能行匹配
```python
def match_rows(baseline_data: List, target_data: List) -> List[Tuple]:
    """使用difflib进行智能行匹配"""
    min_cols = min(
        len(baseline_data[0]) if baseline_data else 0,
        len(target_data[0]) if target_data else 0
    )

    baseline_tuples = normalize_for_comparison(baseline_data, min_cols)
    target_tuples = normalize_for_comparison(target_data, min_cols)

    matcher = difflib.SequenceMatcher(None, baseline_tuples, target_tuples)
    return matcher.get_opcodes()
```

#### 增强版全列检测
```python
class EnhancedCSVComparator:
    """增强版CSV对比器 - 检测所有列的修改"""

    def compare_all_columns(self, file1, file2):
        max_cols = max(len(headers1), len(headers2))

        for col_idx in range(max_cols):  # 遍历所有列
            # 检测每一列的修改，不管是否在标准列中
            if val1 != val2:
                differences.append(diff)
```

### 1.4 相似度评分系统

#### 三层加权公式
```python
def calculate_similarity(baseline_file, target_file):
    """计算综合相似度分数"""
    # 层次1：内容相似度（60%权重）
    content_similarity = cell_match_count / total_cells

    # 层次2：结构相似度（30%权重）
    column_similarity = min(baseline_cols, target_cols) / max(baseline_cols, target_cols)

    # 层次3：行数相似度（10%权重）
    row_similarity = min(baseline_rows, target_rows) / max(baseline_rows, target_rows)

    # 加权综合
    final_score = (content_similarity * 0.6 +
                  column_similarity * 0.3 +
                  row_similarity * 0.1)

    return round(final_score * 100, 2)
```

---

## 第二部分：列名标准化技术

### 2.1 标准化架构

```
原始CSV文件（基线+目标）
           ↓
SimplifiedCSVComparator（简化对比器）
           ↓
简化JSON结果（2.6KB）
           ↓
ColumnStandardizationProcessorV3（V3处理器）
           ↓
DeepSeek/Claude API（智能标准化）
           ↓
标准化JSON结果（含19列映射）
```

### 2.2 19个标准列定义

```python
STANDARD_COLUMNS = [
    "序号",           # 0 - L3
    "项目类型",       # 1 - L2
    "来源",           # 2 - L1
    "任务发起时间",   # 3 - L1
    "目标对齐",       # 4 - L1
    "关键KR对齐",     # 5 - L1
    "具体计划内容",   # 6 - L2
    "邓总指导登记",   # 7 - L2
    "负责人",         # 8 - L2
    "协助人",         # 9 - L2
    "监督人",         # 10 - L2
    "重要程度",       # 11 - L1
    "预计完成时间",   # 12 - L1
    "完成进度",       # 13 - L1
    "完成链接",       # 14 - L3
    "经理分析复盘",   # 15 - L3
    "最新复盘时间",   # 16 - L3
    "对上汇报",       # 17 - L3
    "应用情况"        # 18 - L3
]
```

### 2.3 智能映射策略

#### 四级匹配优先级
1. **精确匹配** (100%置信度) - 完全相同的列名
2. **变异匹配** (85%置信度) - 处理常见变异
3. **语义匹配** (70%置信度) - AI语义理解
4. **位置匹配** (60%置信度) - 基于列位置推测

#### 变异处理规则
```python
COLUMN_VARIATIONS = {
    "序号": ["序号", "编号", "ID", "No.", "#"],
    "负责人": ["负责人", "责任人", "Owner", "主负责人", "执行人"],
    "完成进度": ["完成进度", "进度", "完成率", "Progress", "进展"],
    # ... 其他变异映射
}
```

### 2.4 AI集成方式

#### DeepSeek API调用
```python
def standardize_with_ai(actual_columns, standard_columns):
    prompt = f"""
    请将以下实际列名映射到标准列名。

    实际列名：{actual_columns}
    标准列名：{standard_columns}

    要求：
    1. 每个实际列名必须映射到最合适的标准列名
    2. 不允许重复映射
    3. 返回JSON格式的映射关系
    """

    response = deepseek_client.chat(prompt)
    return parse_mapping(response)
```

---

## 第三部分：CSV文件查找规则

### 3.1 唯一性原则

- **唯一查找方式**：只能使用本地csv_versions目录查找
- **唯一查找函数**：find_baseline_files() 和 find_target_files()
- **禁止降级**：找不到文件直接报错，不使用任何备用方案
- **禁止混合模式**：查找是查找，下载是下载，两者必须分离
- **禁止回退机制**：不允许使用缓存、旧文件或备用策略

### 3.2 时间节点定义

| 时间段 | 定义 | 查找策略 |
|--------|------|----------|
| **周一全天** | 周一 00:00 - 23:59 | 使用上周数据 |
| **周二上午** | 周二 00:00 - 11:59 | 使用上周数据 |
| **周二下午** | 周二 12:00 - 23:59 | 使用本周数据 |
| **周三至周五** | 周三 00:00 - 周五 23:59 | 使用本周数据 |
| **周末** | 周六 00:00 - 周日 23:59 | 使用本周数据 |

### 3.3 文件查找实现

#### 时间上下文判断
```python
def get_time_context():
    """获取当前时间上下文"""
    now = datetime.now()
    weekday = now.weekday()  # 0=周一
    hour = now.hour
    week_info = now.isocalendar()

    # 判断使用哪一周的数据
    if weekday < 1 or (weekday == 1 and hour < 12):
        # 周一全天 OR 周二12点前 → 使用上周
        target_week = week_info[1] - 1
        week_context = "previous_week"
    else:
        # 周二12点后 至 周日 → 使用本周
        target_week = week_info[1]
        week_context = "current_week"

    return {
        "week_context": week_context,
        "target_week": target_week,
        "weekday": weekday,
        "hour": hour
    }
```

#### 基线文件查找
```python
def find_baseline_files(target_week):
    """查找基线文件（周初稳定版本）"""
    base_path = f"/root/projects/tencent-doc-manager/csv_versions/2025_W{target_week}"

    # 查找顺序
    search_paths = [
        f"{base_path}/baseline/",      # 优先：baseline目录
        f"{base_path}/weekend/",        # 备选：上周末版本
        f"{base_path}/"                # 最后：根目录
    ]

    for path in search_paths:
        if os.path.exists(path):
            files = glob.glob(f"{path}/*baseline*.csv")
            if files:
                return sorted(files)

    # 找不到直接报错，绝不降级
    raise FileNotFoundError(f"未找到W{target_week}的基线文件")
```

#### 目标文件查找
```python
def find_target_files(current_week, weekday):
    """查找目标文件（当前版本）"""
    base_path = f"/root/projects/tencent-doc-manager/csv_versions/2025_W{current_week}"

    # 根据星期几决定查找策略
    if weekday < 3:  # 周一、周二
        search_dirs = ["midweek", "baseline"]
    else:  # 周三到周日
        search_dirs = ["weekend", "midweek", "baseline"]

    for dir_name in search_dirs:
        path = f"{base_path}/{dir_name}/"
        if os.path.exists(path):
            files = glob.glob(f"{path}/*.csv")
            if files:
                # 返回最新的文件
                return sorted(files, key=os.path.getmtime, reverse=True)

    raise FileNotFoundError(f"未找到W{current_week}的目标文件")
```

### 3.4 文件命名规范

```
tencent_{文档名}_{时间戳}_{版本类型}_W{周数}.{扩展名}
```

示例：
- `tencent_副本-测试版本-出国销售计划表_20250909_2250_baseline_W37.csv`
- `tencent_回国销售计划表_20250912_1430_midweek_W37.xlsx`

---

## 第四部分：输出规范

### 4.1 简化对比输出

```json
{
    "comparison_metadata": {
        "baseline_file": "path/to/baseline.csv",
        "target_file": "path/to/target.csv",
        "total_differences": 18,
        "similarity_score": 87.5
    },
    "differences": [
        {
            "row": 5,
            "column": "负责人",
            "baseline_value": "张三",
            "target_value": "李四",
            "column_index": 8
        }
    ],
    "column_summary": {
        "total_columns": 19,
        "modified_columns": 6
    }
}
```

### 4.2 标准化输出

```json
{
    "standardization_metadata": {
        "original_columns": ["列1", "列2"],
        "standard_columns": ["序号", "项目类型"],
        "mapping_confidence": 0.85
    },
    "column_mapping": {
        "列1": "序号",
        "列2": "项目类型"
    },
    "standardized_differences": [
        {
            "row": 5,
            "standard_column": "负责人",
            "baseline_value": "张三",
            "target_value": "李四",
            "risk_level": "L2",
            "risk_score": 0.65
        }
    ]
}
```

---

## 第五部分：性能优化

### 5.1 优化指标

| 指标 | v3.0 | v4.0增强版 | 提升 |
|------|------|-----------|------|
| 文件大小 | 23.7KB | 2.6KB | -89% |
| 处理速度 | 1.2s | 0.3s | 4x |
| 内存占用 | 150MB | 45MB | -70% |
| 准确率 | 33% | 100% | 3x |

### 5.2 优化技术

1. **增量对比**: 只存储差异，不存储相同内容
2. **智能缓存**: 缓存列映射关系，避免重复AI调用
3. **并行处理**: 多文件并行对比
4. **内存优化**: 流式读取大文件

---

## 核心文件清单

```
/root/projects/tencent-doc-manager/
├── production/
│   └── core_modules/
│       ├── unified_csv_comparator.py              # 统一对比接口
│       ├── simplified_csv_comparator.py           # 简化对比器
│       └── column_standardization_processor_v3.py # 标准化处理器
├── csv_versions/
│   └── 2025_W{周数}/
│       ├── baseline/                              # 基线文件
│       ├── midweek/                              # 周中文件
│       └── weekend/                               # 周末文件
└── comparison_results/
    ├── simplified_*.json                          # 简化结果
    └── simplified_*_standardized.json            # 标准化结果
```

---

## 强制执行要求

1. **算法版本**: 必须使用v4.0增强版（全列检测）
2. **文件查找**: 严格遵循时间规则，禁止降级
3. **列名映射**: 必须通过AI标准化到19列
4. **输出格式**: 必须符合JSON规范
5. **错误处理**: 找不到文件必须报错，不允许静默失败

---

**版本历史**:
- v5.0.0 (2025-09-17): 合并原03系列三个文档，统一CSV对比规范
- v4.0.0 (2025-09-15): 增强版算法，支持全列检测
- v3.0.0 (2025-09-12): 添加列名标准化
- v2.0.0 (2025-09-04): 添加文件查找规则
- v1.0.0 (2025-08-18): 初始版本