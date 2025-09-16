#!/bin/bash
# 8098完整版服务测试脚本

echo "========================================="
echo "8098完整版服务功能测试"
echo "========================================="

# 检查服务是否运行
echo -e "\n1. 检查服务状态..."
if ps aux | grep -q "[d]eepseek_enhanced_server_final.py"; then
    echo "✓ 服务正在运行"
else
    echo "✗ 服务未运行，请先启动服务"
    exit 1
fi

# 测试主页访问
echo -e "\n2. 测试主页访问..."
if curl -s http://localhost:8098/ | grep -q "完整报告生成"; then
    echo "✓ 主页包含完整功能"
else
    echo "✗ 主页加载失败"
fi

# 测试语义分析和文件生成
echo -e "\n3. 测试语义分析和报告生成..."
test_file="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"
response=$(curl -s -X POST http://localhost:8098/api/semantic_analysis \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"$test_file\"}")

if echo "$response" | grep -q "semantic_report"; then
    echo "✓ 语义分析成功"
    echo "  生成的文件："
    echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'data' in data and 'files_generated' in data['data']:
    files = data['data']['files_generated']
    print(f'    - 语义报告: {files.get(\"semantic_report\", \"N/A\")}')
    print(f'    - 工作流文件: {files.get(\"workflow_file\", \"N/A\")}')
"
else
    echo "✗ 语义分析失败"
fi

# 测试历史报告列表
echo -e "\n4. 测试历史报告列表..."
reports=$(curl -s http://localhost:8098/api/list_reports)
if echo "$reports" | grep -q "semantic_reports"; then
    count=$(echo "$reports" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(len(data.get('semantic_reports', [])))
")
    echo "✓ 历史报告API正常"
    echo "  - 找到 $count 个语义分析报告"
else
    echo "✗ 历史报告API异常"
fi

# 测试文件下载
echo -e "\n5. 测试文件下载功能..."
# 获取第一个报告文件名
filename=$(echo "$reports" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('semantic_reports'):
    print(data['semantic_reports'][0]['filename'])
" 2>/dev/null)

if [ ! -z "$filename" ]; then
    # URL编码文件名
    encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$filename'))")
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8098/download/report/$encoded")
    if [ "$status" = "200" ]; then
        echo "✓ 文件下载功能正常"
        echo "  - 测试文件: $filename"
    else
        echo "✗ 文件下载失败 (HTTP $status)"
    fi
else
    echo "✗ 无法获取测试文件名"
fi

# 检查生成的文件目录
echo -e "\n6. 检查文件存储目录..."
echo "语义分析报告目录："
ls -la /root/projects/tencent-doc-manager/semantic_results/2025_W36/ 2>/dev/null | head -3 || echo "  目录不存在"
echo ""
echo "审批工作流目录："
ls -la /root/projects/tencent-doc-manager/approval_workflows/pending/ 2>/dev/null | head -3 || echo "  目录不存在"

echo -e "\n========================================="
echo "测试完成！"
echo "访问 http://202.140.143.88:8098 查看完整界面"
echo "主要功能："
echo "  ✨ 语义分析生成实际报告文件"
echo "  📁 报告存储在指定目录结构"
echo "  📥 支持文件下载"
echo "  📚 查看历史报告列表"
echo "========================================="