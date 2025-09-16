#!/bin/bash
# 模拟8098 Web界面的完整处理流程

echo "=========================================="
echo "模拟8098 Web界面处理流程"
echo "=========================================="

FILE_PATH="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"

echo ""
echo "📁 文件路径: $FILE_PATH"
echo ""

# Step 1: 读取文件
echo "Step 1: 读取文件..."
READ_RESPONSE=$(curl -s -X POST http://localhost:8098/api/read_file \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"$FILE_PATH\"}")

SUCCESS=$(echo $READ_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])")

if [ "$SUCCESS" = "True" ]; then
    echo "✅ 文件读取成功"
    
    # 提取修改的列
    COLUMNS=$(echo $READ_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
cols = list(data['content']['modified_columns'].values())
print(json.dumps(cols))
")
    
    echo "   找到修改列: $COLUMNS"
    
    # Step 2: 执行AI标准化
    echo ""
    echo "Step 2: 执行AI标准化..."
    
    ANALYZE_RESPONSE=$(curl -s -X POST http://localhost:8098/api/analyze \
      -H "Content-Type: application/json" \
      -d "{
        \"columns\": $COLUMNS,
        \"csv_path\": \"$FILE_PATH\",
        \"use_numbering\": true,
        \"filter_modified\": true
      }")
    
    ANALYZE_SUCCESS=$(echo $ANALYZE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))")
    
    if [ "$ANALYZE_SUCCESS" = "True" ]; then
        echo "✅ AI标准化成功"
        
        # 显示部分结果
        echo ""
        echo "📊 标准化结果预览:"
        echo $ANALYZE_RESPONSE | python3 -m json.tool | head -20
    else
        echo "❌ AI标准化失败"
        echo $ANALYZE_RESPONSE | python3 -m json.tool
    fi
else
    echo "❌ 文件读取失败"
    echo $READ_RESPONSE | python3 -m json.tool
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="