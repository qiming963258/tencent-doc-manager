#!/bin/bash

# 第三步批量列名标准化处理脚本
# 处理30个表格的标准化映射任务

echo "🚀 开始批量列名标准化处理..."

# 设置基本路径
INPUT_DIR="/root/projects/tencent-doc-manager/csv_versions/standard_outputs"
API_URL="http://localhost:8081/api/ai-column-mapping"
OUTPUT_SUFFIX="_column_mapping.json"
LOG_FILE="/root/projects/tencent-doc-manager/batch_column_mapping.log"

# 清空日志文件
> "$LOG_FILE"

# 统计变量
TOTAL_COUNT=0
SUCCESS_COUNT=0
FAILED_COUNT=0

echo "📊 扫描输入目录: $INPUT_DIR"
echo "🔗 API服务地址: $API_URL"
echo "📝 日志文件: $LOG_FILE"
echo "----------------------------------------"

# 验证Claude API服务状态
echo "🔍 检查Claude API服务状态..."
if curl -s "$API_URL/../health" > /dev/null 2>&1; then
    echo "✅ Claude API服务正常运行"
else
    echo "❌ Claude API服务不可用，请先启动服务"
    echo "启动命令: cd claude_mini_wrapper && python3 main.py"
    exit 1
fi

# 查找所有table_XXX_diff.json文件
for input_file in "$INPUT_DIR"/table_*_diff.json; do
    if [ -f "$input_file" ]; then
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        
        # 获取文件名（不包含路径和扩展名）
        filename=$(basename "$input_file" .json)
        output_file="${INPUT_DIR}/${filename}${OUTPUT_SUFFIX}"
        
        echo "📋 处理文件: $filename"
        echo "   输入: $input_file"
        echo "   输出: $output_file"
        
        # 记录开始时间
        start_time=$(date +%s.%N)
        
        # 调用API进行列名标准化
        if curl -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -d "@$input_file" \
            -o "$output_file" \
            --silent \
            --show-error \
            --max-time 120; then
            
            # 计算处理时间
            end_time=$(date +%s.%N)
            duration=$(echo "$end_time - $start_time" | bc)
            
            # 验证输出文件
            if [ -s "$output_file" ] && grep -q '"success"' "$output_file"; then
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                echo "   ✅ 成功 (耗时: ${duration}s)"
                echo "$(date '+%Y-%m-%d %H:%M:%S') SUCCESS: $filename (${duration}s)" >> "$LOG_FILE"
            else
                FAILED_COUNT=$((FAILED_COUNT + 1))
                echo "   ❌ 失败 - 输出文件无效或为空"
                echo "$(date '+%Y-%m-%d %H:%M:%S') FAILED: $filename - Invalid output" >> "$LOG_FILE"
                # 删除无效的输出文件
                rm -f "$output_file"
            fi
        else
            FAILED_COUNT=$((FAILED_COUNT + 1))
            echo "   ❌ 失败 - API调用失败"
            echo "$(date '+%Y-%m-%d %H:%M:%S') FAILED: $filename - API call failed" >> "$LOG_FILE"
        fi
        
        echo "----------------------------------------"
        
        # 避免API请求过于频繁，添加短暂延迟
        sleep 1
    fi
done

# 处理结果统计
echo "📊 批量处理完成统计:"
echo "   总文件数: $TOTAL_COUNT"
echo "   成功处理: $SUCCESS_COUNT"
echo "   失败数量: $FAILED_COUNT"
echo "   成功率: $(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_COUNT" | bc)%"

# 生成汇总报告
SUMMARY_FILE="${INPUT_DIR}/batch_column_mapping_summary_$(date '+%Y%m%d_%H%M%S').json"
cat > "$SUMMARY_FILE" << EOF
{
  "batch_processing_summary": {
    "processing_time": "$(date '+%Y-%m-%d %H:%M:%S')",
    "input_directory": "$INPUT_DIR",
    "api_endpoint": "$API_URL",
    "total_files": $TOTAL_COUNT,
    "successful_mappings": $SUCCESS_COUNT,
    "failed_mappings": $FAILED_COUNT,
    "success_rate": $(echo "scale=4; $SUCCESS_COUNT / $TOTAL_COUNT" | bc),
    "output_pattern": "*${OUTPUT_SUFFIX}"
  },
  "processed_files": [
$(for input_file in "$INPUT_DIR"/table_*_diff.json; do
    if [ -f "$input_file" ]; then
        filename=$(basename "$input_file" .json)
        output_file="${INPUT_DIR}/${filename}${OUTPUT_SUFFIX}"
        if [ -f "$output_file" ]; then
            echo "    \"$filename\": \"success\","
        else
            echo "    \"$filename\": \"failed\","
        fi
    fi
done | sed '$ s/,$//')
  ]
}
EOF

echo "📄 汇总报告已生成: $SUMMARY_FILE"
echo "📝 详细日志: $LOG_FILE"

if [ $FAILED_COUNT -eq 0 ]; then
    echo "🎉 批量列名标准化处理全部成功！"
    exit 0
else
    echo "⚠️ 有 $FAILED_COUNT 个文件处理失败，请检查日志文件"
    exit 1
fi