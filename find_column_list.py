#!/usr/bin/env python3
"""找到右侧列名列表的代码位置"""

with open('/root/projects/tencent-doc-manager/production/servers/final_heatmap_server.py', 'r') as f:
    lines = f.readlines()

# 搜索包含"改"字并且可能是数字显示的模式
for i, line in enumerate(lines, 1):
    if '改' in line and ('{' in line or 'span' in line):
        # 打印前后5行上下文
        start = max(0, i-5)
        end = min(len(lines), i+5)
        print(f"\n===== 位置 {i} 行 =====")
        for j in range(start, end):
            prefix = ">>> " if j == i-1 else "    "
            print(f"{prefix}{j+1}: {lines[j].rstrip()}")