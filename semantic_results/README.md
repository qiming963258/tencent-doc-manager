# AI语义分析输出文件说明

## 📁 输出文件结构

### 1. 语义分析结果文件
**路径**: `/semantic_results/2025_W36/`
**格式**: JSON
**命名**: `semantic_analysis_[表名]_[时间戳].json`

包含内容：
- 元数据（源文件、处理时间、Token消耗）
- 每个修改的详细分析结果
- 第一层和第二层的判断结果
- 最终决策和审批要求
- 风险分布统计

### 2. 审批工作流文件
**路径**: `/approval_workflows/pending/`
**格式**: JSON
**命名**: `workflow_[WF-ID]_[表名]_[日期].json`

包含内容：
- 待审批项详细信息
- 自动通过项列表
- 审批要求和截止时间
- 工作流历史记录
- 通知发送记录

### 3. Excel标记文件（待实现）
**路径**: `/marked_excels/2025_W36/`
**格式**: XLSX
**命名**: `marked_[表名]_semantic_[时间戳].xlsx`

标记规则：
- 🟢 绿色: SAFE/APPROVE（低风险）
- 🟡 黄色: CONDITIONAL（有条件通过）
- 🟠 橙色: REVIEW（需要审核）
- 🔴 红色: REJECT（高风险拒绝）

## 📊 示例文件

### 语义分析结果示例
```json
{
  "metadata": {
    "total_modifications": 6,
    "layer1_passed": 4,
    "layer2_analyzed": 2
  },
  "results": [...],
  "summary": {
    "approved": 4,
    "review_required": 2
  }
}
```

### 审批工作流示例
```json
{
  "workflow_id": "WF-20250907-001",
  "pending_approvals": [
    {
      "column": "项目类型",
      "risk_level": "MEDIUM",
      "approver_role": "项目经理"
    }
  ]
}
```

## 🔄 处理流程

1. **输入**: CSV对比结果JSON文件
2. **第一层分析**: 快速筛选（67%通过）
3. **第二层分析**: 深度分析（33%需要）
4. **输出生成**:
   - 语义分析结果JSON
   - 审批工作流JSON
   - Excel标记文件（可选）
5. **通知发送**: 邮件/系统通知

## 📈 性能指标

- 处理速度: 1.1秒/表
- Token消耗: 1300 tokens/表
- 准确率: >85%
- 自动通过率: 67%

## 🔗 相关文档

- [AI语义分析集成规格](../docs/specifications/05-AI语义分析集成规格.md)
- [测试脚本](../test_8098_complete.sh)
- [8098服务API](http://202.140.143.88:8098)