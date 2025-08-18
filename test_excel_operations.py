#!/usr/bin/env python3
"""
测试Excel MCP操作的脚本
"""

import pandas as pd
import os

# 创建测试数据
test_data = {
    '序号': [1, 2, 3],
    '项目类型': ['内容优化', '用户运营', '品牌推广'],
    '负责人': ['张三', '李四', '王五'],
    '状态': ['进行中', '已完成', '待开始']
}

# 创建DataFrame
df = pd.DataFrame(test_data)

# 保存为Excel文件
output_path = '/root/projects/tencent-doc-manager/test_excel_mcp.xlsx'
df.to_excel(output_path, index=False, sheet_name='测试工作表')

print(f"测试Excel文件已创建: {output_path}")
print(f"文件大小: {os.path.getsize(output_path)} bytes")
print("数据内容:")
print(df)