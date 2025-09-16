#!/bin/bash
# 8098增强版服务测试脚本 - 验证报告生成和路径展示

echo "========================================="
echo "8098增强版服务测试"
echo "测试内容：报告生成和路径展示"
echo "========================================="

# 检查服务是否运行
echo -e "\n1. 检查服务状态..."
if ps aux | grep -q "[d]eepseek_enhanced_server_with_semantic.py"; then
    echo "✓ 服务正在运行"
else
    echo "✗ 服务未运行，请先启动服务"
    exit 1
fi

# 测试语义分析API并生成报告
echo -e "\n2. 测试语义分析并生成报告..."
test_file="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"

response=$(curl -s -X POST http://localhost:8098/api/semantic_analysis \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"$test_file\"}")

# 检查返回结果
if echo "$response" | grep -q "files_generated"; then
    echo "✓ API返回成功，包含文件路径信息"
    
    # 提取文件路径
    semantic_report=$(echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'data' in data and 'files_generated' in data['data']:
    print(data['data']['files_generated']['semantic_report'])
")
    
    workflow_file=$(echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'data' in data and 'files_generated' in data['data']:
    print(data['data']['files_generated']['workflow_file'])
")
    
    echo "  - 语义报告: $semantic_report"
    echo "  - 工作流文件: $workflow_file"
else
    echo "✗ API未返回文件路径信息"
fi

# 验证文件是否真实存在
echo -e "\n3. 验证生成的文件..."
if [ ! -z "$semantic_report" ] && [ -f "$semantic_report" ]; then
    echo "✓ 语义分析报告文件存在"
    file_size=$(stat -c%s "$semantic_report")
    echo "  - 文件大小: $file_size 字节"
else
    echo "✗ 语义分析报告文件不存在"
fi

if [ ! -z "$workflow_file" ] && [ -f "$workflow_file" ]; then
    echo "✓ 审批工作流文件存在"
    file_size=$(stat -c%s "$workflow_file")
    echo "  - 文件大小: $file_size 字节"
else
    echo "✗ 审批工作流文件不存在"
fi

# 检查结果汇总
echo -e "\n4. 检查结果汇总信息..."
if echo "$response" | grep -q "summary"; then
    echo "✓ 包含结果汇总"
    echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'data' in data and 'summary' in data['data']:
    summary = data['data']['summary']
    print(f'  - 自动通过: {summary.get(\"approved\", 0)}')
    print(f'  - 需要审核: {summary.get(\"review_required\", 0)}')
    print(f'  - 已拒绝: {summary.get(\"rejected\", 0)}')
"
else
    echo "✗ 缺少结果汇总信息"
fi

# 检查网页界面是否包含文件路径展示部分
echo -e "\n5. 检查网页界面展示..."
if curl -s http://localhost:8098/ | grep -q "生成的报告文件"; then
    echo "✓ 网页包含报告文件展示部分"
else
    echo "✗ 网页缺少报告文件展示部分"
fi

# 统计所有生成的文件
echo -e "\n6. 统计所有生成的文件..."
semantic_count=$(ls /root/projects/tencent-doc-manager/semantic_results/2025_W36/*.json 2>/dev/null | wc -l)
workflow_count=$(ls /root/projects/tencent-doc-manager/approval_workflows/pending/*.json 2>/dev/null | wc -l)

echo "📊 文件统计："
echo "  - 语义分析报告: $semantic_count 个"
echo "  - 审批工作流: $workflow_count 个"

echo -e "\n========================================="
echo "测试完成！"
echo "访问 http://202.140.143.88:8098 查看完整界面"
echo ""
echo "主要增强功能："
echo "  ✨ 生成实际的报告文件"
echo "  📁 在网页中展示文件路径"
echo "  📊 显示结果汇总统计"
echo "  💾 报告持久化存储"
echo "========================================="