#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试解析带小括号注释的JSON文件"""

import re
import json

def parse_annotated_json(content):
    """解析带小括号注释的JSON文件"""
    # 逐行处理，移除注释
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        # 更智能地检测注释
        # 跳过字符串中的 //
        in_string = False
        cleaned_line = ""
        i = 0
        while i < len(line):
            if line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                in_string = not in_string
                cleaned_line += line[i]
            elif not in_string and i < len(line) - 1 and line[i:i+2] == '//':
                # 找到注释，停止处理此行
                break
            else:
                cleaned_line += line[i]
            i += 1

        # 保留处理后的行
        cleaned_lines.append(cleaned_line)

    # 重新组合成字符串
    clean_content = '\n'.join(cleaned_lines)

    # 移除多余的逗号（最后一个元素后的逗号）
    # 处理对象中的逗号
    clean_content = re.sub(r',\s*}', '}', clean_content)
    # 处理数组中的逗号
    clean_content = re.sub(r',\s*\]', ']', clean_content)

    # 输出清理后的内容进行调试
    # print("清理后的内容：")
    # print(clean_content)
    # print("=" * 50)

    # 解析清理后的JSON
    try:
        return json.loads(clean_content)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误：{e}")
        print(f"错误位置附近的内容：")
        lines = clean_content.split('\n')
        for i, line in enumerate(lines[10:15], start=11):
            print(f"Line {i}: {repr(line)}")
        raise

# 测试数据
test_json = """
{
  "metadata": {  // （元数据部分：记录文件生成的基本信息）
    "week": "W37",  // （周数标识：使用ISO 8601标准的第37周）
    "generation_time": "2025-09-09 13:38:57",  // （生成时间：综合报告创建的具体时间戳）
    "total_tables": 1,  // （处理表格数：本次分析涉及的腾讯文档表格总数）
    "total_modifications": 6  // （总修改数：所有表格中检测到的修改项总计）
  },
  "table_scores": [  // （表格评分数组：包含每个表格的详细评分数据）
    {
      "table_name": "测试表格",  // （表格名称：包含对比双方信息）
      "table_url": "https://docs.qq.com/sheet/test",  // （腾讯文档URL）
      "modifications_count": 6,  // （修改计数）
      "column_scores": {  // （列级评分）
        "项目类型": {  // （列名）
          "column_level": "L2",  // （列级别：L2表示中风险）
          "scores": [0.54]  // （风险分数）
        }
      }
    }
  ]
}
"""

# 测试解析
try:
    result = parse_annotated_json(test_json)
    print("✅ 成功解析带小括号注释的JSON！")
    print("\n解析结果：")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 验证关键字段
    assert "metadata" in result
    assert result["metadata"]["week"] == "W37"
    assert result["metadata"]["total_tables"] == 1
    assert "table_scores" in result
    assert len(result["table_scores"]) == 1

    print("\n✅ 所有字段验证通过！")

    # 测试实际文件
    print("\n测试实际带注释文件...")
    with open("/root/projects/tencent-doc-manager/演示讲解_详细打分系统/综合打分结果_带注释版_W37.json", "r", encoding="utf-8") as f:
        actual_content = f.read()

    actual_result = parse_annotated_json(actual_content)
    print(f"✅ 成功解析实际文件！")
    print(f"  - metadata.week: {actual_result['metadata']['week']}")
    print(f"  - table_scores数量: {len(actual_result['table_scores'])}")
    print(f"  - 第一个表格修改数: {actual_result['table_scores'][0]['modifications_count']}")

except Exception as e:
    print(f"❌ 解析失败：{e}")
    import traceback
    traceback.print_exc()