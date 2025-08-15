# 评分程序审查报告
**生成时间**: 2025-08-14 01:24:40

## 🏋️ 权重配置审查

### 当前权重配置
- **modificationCount**: 0.3 (30.0%)
- **changeComplexity**: 0.25 (25.0%)
- **riskLevel**: 0.35 (35.0%)
- **timeRecency**: 0.1 (10.0%)

### 优化建议
- 调整riskLevel权重从0.35到0.4，更符合业务优先级

## 🎯 风险分级体系审查

### 发现的问题
#### 🔴 高优先级问题
- **duplicate_column**: 列'序号'同时出现在L1和L3级别中
- **duplicate_column**: 列'复盘时间'同时出现在L1和L3级别中
- **score_range_overlap**: L2和L3的分数范围有重叠
- **score_range_overlap**: L3和L2的分数范围有重叠

#### 🟡 中优先级问题
- **test_missing_columns**: L1级别测试代码缺失列定义
- **test_missing_columns**: L2级别测试代码缺失列定义
- **test_missing_columns**: L3级别测试代码缺失列定义
