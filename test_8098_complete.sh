#!/bin/bash
# 8098服务完整功能测试脚本

echo "========================================="
echo "8098服务完整功能测试"
echo "========================================="

# 检查服务是否运行
echo -e "\n1. 检查服务状态..."
if ps aux | grep -q "[d]eepseek_enhanced_server_with_semantic.py"; then
    echo "✓ 服务正在运行"
else
    echo "✗ 服务未运行，请先启动服务"
    exit 1
fi

# 测试主页访问
echo -e "\n2. 测试主页访问..."
if curl -s http://localhost:8098/ | grep -q "AI语义分析两层架构测试"; then
    echo "✓ 主页包含语义分析模块"
else
    echo "✗ 主页缺少语义分析模块"
fi

# 测试列名标准化API
echo -e "\n3. 测试列名标准化API..."
response=$(curl -s -X POST http://localhost:8098/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"columns": ["A: 项目类型", "B: 任务发起时间", "C: 负责人"]}')
if echo "$response" | grep -q "success"; then
    echo "✓ 列名标准化API正常"
else
    echo "✗ 列名标准化API异常"
fi

# 测试语义分析API
echo -e "\n4. 测试语义分析API..."
test_file="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"
if [ -f "$test_file" ]; then
    response=$(curl -s -X POST http://localhost:8098/api/semantic_analysis \
      -H "Content-Type: application/json" \
      -d "{\"file_path\": \"$test_file\"}")
    
    if echo "$response" | grep -q "layer1_passed"; then
        echo "✓ 语义分析API正常"
        echo "  - 第一层通过: $(echo "$response" | grep -o '"layer1_passed":[0-9]*' | cut -d: -f2)个"
        echo "  - 第二层分析: $(echo "$response" | grep -o '"layer2_analyzed":[0-9]*' | cut -d: -f2)个"
    else
        echo "✗ 语义分析API异常"
    fi
else
    echo "✗ 测试文件不存在"
fi

# 测试提示词显示API
echo -e "\n5. 测试提示词显示API..."
if curl -s http://localhost:8098/api/get_prompt | python3 -c "import json, sys; data = json.load(sys.stdin); exit(0 if 'CSV' in data.get('prompt', '') else 1)" 2>/dev/null; then
    echo "✓ 提示词显示API正常"
else
    echo "✗ 提示词显示API异常"
fi

echo -e "\n========================================="
echo "测试完成！"
echo "访问 http://202.140.143.88:8098 查看完整界面"
echo "========================================="