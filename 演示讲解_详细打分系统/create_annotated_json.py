#!/usr/bin/env python3
"""
创建带行内注释的综合打分JSON文件
模仿W37格式，每个字段后面都有详细的中文解释
"""

def create_annotated_json():
    """生成带注释的JSON内容"""

    # 这是一个带注释的JSON模板，使用Python字符串保存
    content = '''{
  "generation_time": "2025-09-13T15:30:00.000000",  // （生成时间：ISO 8601格式时间戳，记录综合打分数据生成的精确时刻，用于版本控制和审计追踪）
  "scoring_version": "3.0",  // （打分版本：综合打分系统的版本号，3.0表示第三代算法，支持AI智能评估和多维度风险分析）
  "scoring_standard": "0000-颜色和级别打分标准",  // （打分标准：引用的核心标准文档，定义了L1/L2/L3级别和颜色映射规则）

  "table_names": [  // （关键内容1 - 所有表名列表：UI热力图左侧Y轴显示的表格名称数组，决定了热力图的行数）
    "小红书内容审核记录表",  // （第1个表格：小红书业务线的内容审核数据表）
    "企业风险评估矩阵表",  // （第2个表格：企业级风险管理评估矩阵）
    "财务月度报表汇总表"  // （第3个表格：财务部门月度数据汇总）
  ],

  "column_avg_scores": {  // （关键内容2 - 每标准列平均加权修改打分：UI热力图顶部X轴显示的19个标准列的整体风险水平）
    "序号": 0.85,  // （序号列：L1级别核心列，最低分0.8，0.85表示高风险，UI显示红色）
    "项目类型": 0.92,  // （项目类型列：L1级别核心列，0.92表示极高风险，UI热力图显示深红色）
    "来源": 0.25,  // （来源列：L3级别一般信息列，0.25表示低风险，UI显示绿色）
    "任务发起时间": 0.28,  // （任务发起时间列：L3级别时间记录列，低风险绿色显示）
    "目标对齐": 0.88,  // （目标对齐列：L1级别战略关键列，0.88极高风险红色预警）
    "关键KR对齐": 0.91,  // （关键KR对齐列：L1级别OKR核心数据，0.91最高风险深红色）
    "具体计划内容": 0.22,  // （具体计划内容列：L3级别文本描述列，低风险绿色）
    "邓总指导登记": 0.27,  // （邓总指导登记列：L3级别记录类信息，低风险绿色）
    "负责人": 0.55,  // （负责人列：L2级别需AI评估，0.55中等风险黄色警示）
    "协助人": 0.58,  // （协助人列：L2级别人员变更需评估，中高风险黄橙色）
    "监督人": 0.59,  // （监督人列：L2级别管理链条关键，中高风险黄橙色）
    "重要程度": 0.56,  // （重要程度列：L2级别优先级判断，中等风险黄色）
    "预计完成时间": 0.54,  // （预计完成时间列：L2级别时间承诺关键，中等风险黄色）
    "完成进度": 0.53,  // （完成进度列：L2级别执行状态监控，中等风险黄色）
    "形成计划清单": 0.28,  // （形成计划清单列：L3级别过程记录，低风险绿色）
    "复盘时间": 0.24,  // （复盘时间列：L3级别时间记录，低风险绿色）
    "对上汇报": 0.25,  // （对上汇报列：L3级别沟通记录，低风险绿色）
    "应用情况": 0.22,  // （应用情况列：L3级别效果记录，低风险绿色）
    "进度分析总结": 0.23  // （进度分析总结列：L3级别文本总结，低风险绿色）
  },

  "table_scores": [  // （关键内容3&4 - 表格详细数据数组：包含每个表格的修改详情、URL和列级别打分，是UI热力图矩阵的核心数据源）
    {
      "table_id": 0,  // （表格ID：唯一标识符，从0开始的索引，用于数组定位和数据关联）
      "table_name": "小红书内容审核记录表",  // （表格名称：与table_names数组对应，用于UI显示和日志记录）
      "table_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",  // （关键内容4 - 表格URL：真实的腾讯文档链接，点击表格名称时新标签页打开）
      "total_rows": 92,  // （总行数：CSV文件的实际数据行数，用于计算修改密度和风险权重）
      "total_modifications": 15,  // （表格总修改数：该表格所有列的修改总和，用于右侧横条图显示）
      "overall_risk_score": 0.65,  // （整体风险分数：表格级别的加权平均风险值，决定表格名称的颜色强度）

      "column_scores": {  // （关键内容3 - 每列具体修改详情：UI热力图单元格颜色和鼠标悬停信息的数据源）
        "项目类型": {  // （项目类型列的修改详情）
          "column_level": "L1",  // （列级别：L1表示核心关键列，任何修改都是高风险，最低分0.8）
          "avg_score": 0.98,  // （平均分数：该列所有修改的平均风险分，0.98决定热力图显示深红色）
          "modified_rows": [5, 12, 28],  // （修改行号列表：具体哪些行发生了修改，行号从1开始，用于悬停详情显示）
          "row_scores": [0.95, 0.99, 1.0],  // （行打分列表：每个修改行对应的风险打分，与modified_rows一一对应）
          "modifications": 3,  // （修改次数：该列的修改总数，等于modified_rows数组长度）
          "risk_level": "HIGH"  // （风险级别：HIGH/MEDIUM/LOW，用于快速分类和过滤）
        },
        "负责人": {  // （负责人列的修改详情）
          "column_level": "L2",  // （列级别：L2表示重要业务列，最低分0.4，需要AI智能评估）
          "avg_score": 0.55,  // （平均分数：0.55表示中等风险，UI热力图显示黄色）
          "modified_rows": [8, 15, 22, 35, 67],  // （修改的5个行号）
          "row_scores": [0.45, 0.52, 0.58, 0.61, 0.59],  // （对应的5个风险分数）
          "modifications": 5,  // （总共修改5次）
          "risk_level": "MEDIUM",  // （中等风险级别）
          "ai_decisions": ["APPROVE", "APPROVE", "REVIEW", "REVIEW", "REVIEW"],  // （AI审批建议：2个批准，3个需要复审）
          "ai_confidence": [0.85, 0.82, 0.75, 0.73, 0.76]  // （AI置信度：表示AI对决策的把握程度，范围0-1）
        },
        "来源": {  // （来源列的修改详情）
          "column_level": "L3",  // （列级别：L3表示一般信息列，最低分0.1，风险较低）
          "avg_score": 0.21,  // （平均分数：0.21表示低风险，UI热力图显示绿色）
          "modified_rows": [2, 45],  // （只有2行被修改）
          "row_scores": [0.18, 0.24],  // （对应的低风险分数）
          "modifications": 2,  // （修改2次）
          "risk_level": "LOW"  // （低风险级别）
        }
      }
    },
    {
      "table_id": 1,  // （第二个表格）
      "table_name": "企业风险评估矩阵表",  // （风险管理表）
      "table_url": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",  // （关键内容4 - 第二个真实URL）
      "total_rows": 75,  // （75行数据）
      "total_modifications": 8,  // （8个修改）
      "overall_risk_score": 0.48,  // （中等风险）
      "column_scores": {  // （列修改详情）
        "目标对齐": {  // （目标对齐列）
          "column_level": "L1",  // （L1级别）
          "avg_score": 0.88,  // （高风险）
          "modified_rows": [10, 25],  // （2行修改）
          "row_scores": [0.85, 0.91],  // （高风险分数）
          "modifications": 2,  // （2次修改）
          "risk_level": "HIGH"  // （高风险）
        },
        "预计完成时间": {  // （预计完成时间列）
          "column_level": "L2",  // （L2级别）
          "avg_score": 0.54,  // （中等风险）
          "modified_rows": [30, 42, 58],  // （3行修改）
          "row_scores": [0.52, 0.55, 0.55],  // （中等风险分数）
          "modifications": 3,  // （3次修改）
          "risk_level": "MEDIUM",  // （中等风险）
          "ai_decisions": ["APPROVE", "REVIEW", "REVIEW"],  // （1批准2复审）
          "ai_confidence": [0.81, 0.72, 0.74]  // （AI置信度）
        },
        "进度分析总结": {  // （进度分析总结列）
          "column_level": "L3",  // （L3级别）
          "avg_score": 0.23,  // （低风险）
          "modified_rows": [5, 18, 66],  // （3行修改）
          "row_scores": [0.22, 0.24, 0.23],  // （低风险分数）
          "modifications": 3,  // （3次修改）
          "risk_level": "LOW"  // （低风险）
        }
      }
    },
    {
      "table_id": 2,  // （第三个表格）
      "table_name": "财务月度报表汇总表",  // （财务汇总表）
      "table_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",  // （关键内容4 - 第三个真实URL）
      "total_rows": 120,  // （120行数据）
      "total_modifications": 12,  // （12个修改）
      "overall_risk_score": 0.72,  // （较高风险）
      "column_scores": {  // （列修改详情）
        "关键KR对齐": {  // （KR对齐列）
          "column_level": "L1",  // （L1级别）
          "avg_score": 0.91,  // （极高风险）
          "modified_rows": [3, 15, 45, 78],  // （4行修改）
          "row_scores": [0.89, 0.92, 0.91, 0.92],  // （高风险分数）
          "modifications": 4,  // （4次修改）
          "risk_level": "HIGH"  // （高风险）
        },
        "监督人": {  // （监督人列）
          "column_level": "L2",  // （L2级别）
          "avg_score": 0.59,  // （中高风险）
          "modified_rows": [20, 35, 50, 65, 80, 95],  // （6行修改）
          "row_scores": [0.58, 0.60, 0.59, 0.61, 0.57, 0.59],  // （中高风险分数）
          "modifications": 6,  // （6次修改）
          "risk_level": "MEDIUM",  // （中等风险）
          "ai_decisions": ["REVIEW", "REVIEW", "APPROVE", "REVIEW", "REVIEW", "APPROVE"],  // （2批准4复审）
          "ai_confidence": [0.73, 0.74, 0.82, 0.72, 0.73, 0.81]  // （AI置信度）
        },
        "复盘时间": {  // （复盘时间列）
          "column_level": "L3",  // （L3级别）
          "avg_score": 0.24,  // （低风险）
          "modified_rows": [12, 88],  // （2行修改）
          "row_scores": [0.23, 0.25],  // （低风险分数）
          "modifications": 2,  // （2次修改）
          "risk_level": "LOW"  // （低风险）
        }
      }
    }
  ],

  "total_modifications": 35,  // （关键内容5 - 全部修改数：所有表格修改的总和15+8+12=35，UI右上角显示的总统计）

  "risk_summary": {  // （风险统计汇总：UI风险分布饼图或柱状图的数据源）
    "high_risk_count": 12,  // （高风险修改数：打分≥0.6的修改总数，显示红色或橙色）
    "medium_risk_count": 15,  // （中风险修改数：0.4≤打分<0.6的修改总数，显示黄色）
    "low_risk_count": 8,  // （低风险修改数：打分<0.4的修改总数，显示绿色或蓝色）
    "risk_distribution_by_level": {  // （按列级别的风险分布）
      "L1": 9,  // （L1列的修改数：核心列修改，需要最高优先级处理）
      "L2": 14,  // （L2列的修改数：需要AI评估的修改）
      "L3": 12  // （L3列的修改数：一般信息的修改）
    }
  },

  "ai_analysis_summary": {  // （AI分析汇总：L2列的AI评估结果统计）
    "total_ai_evaluations": 14,  // （AI评估总数：所有L2列的修改都经过AI评估）
    "approvals": 5,  // （批准数：AI判断可以直接通过的修改）
    "reviews": 9,  // （复审数：AI建议人工复审的修改）
    "rejects": 0,  // （拒绝数：AI判断必须拒绝的修改，本批次无拒绝）
    "average_confidence": 0.77  // （平均置信度：AI决策的平均把握程度）
  },

  "ui_mapping_guide": {  // （UI映射指南：说明UI组件如何使用这些数据）
    "heatmap_matrix": {  // （热力图矩阵映射）
      "y_axis": "table_names",  // （Y轴：使用table_names数组）
      "x_axis": "19_standard_columns",  // （X轴：19个标准列）
      "cell_color": "table_scores[i].column_scores[col].avg_score",  // （单元格颜色：基于avg_score）
      "color_mapping": {  // （颜色映射规则）
        "red": "score >= 0.8",  // （红色：极高风险）
        "orange": "0.6 <= score < 0.8",  // （橙色：高风险）
        "yellow": "0.4 <= score < 0.6",  // （黄色：中风险）
        "green": "0.1 <= score < 0.4",  // （绿色：低风险）
        "blue": "score < 0.1"  // （蓝色：极低风险）
      }
    },
    "hover_tooltip": {  // （悬停提示框映射）
      "table_name": "table_scores[i].table_name",  // （表格名称）
      "column_name": "column_key",  // （列名）
      "modified_rows": "column_scores[col].modified_rows",  // （修改行号）
      "risk_scores": "column_scores[col].row_scores",  // （风险分数）
      "ai_decision": "column_scores[col].ai_decisions"  // （AI决策，仅L2列）
    },
    "right_panel": {  // （右侧面板映射）
      "bar_width": "based_on_avg_score",  // （横条宽度：基于平均分数）
      "bar_color": "based_on_risk_level",  // （横条颜色：基于风险级别）
      "modification_count": "modifications"  // （修改数显示）
    },
    "table_links": {  // （表格链接映射）
      "click_action": "open_new_tab",  // （点击动作：新标签页打开）
      "url_source": "table_scores[i].table_url"  // （URL来源：table_url字段）
    }
  }
}'''

    return content

def save_annotated_json():
    """保存带注释的JSON文件"""
    content = create_annotated_json()

    # 保存带注释版本（供查看和学习）
    output_file = "/root/projects/tencent-doc-manager/演示讲解_详细打分系统/综合打分结果_完整注释版_W36.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已生成带完整注释的综合打分文件: {output_file}")

    # 统计注释信息
    lines = content.split('\n')
    comment_lines = sum(1 for line in lines if '//' in line)
    total_lines = len(lines)

    print(f"\n📊 文件统计：")
    print(f"  - 总行数: {total_lines}")
    print(f"  - 包含注释的行数: {comment_lines}")
    print(f"  - 注释覆盖率: {comment_lines/total_lines*100:.1f}%")

    # 生成纯净版（去除注释）
    clean_content = '\n'.join([line.split('  //')[0].rstrip() for line in lines])
    clean_file = "/root/projects/tencent-doc-manager/演示讲解_详细打分系统/综合打分结果_纯净版_W36.json"
    with open(clean_file, 'w', encoding='utf-8') as f:
        f.write(clean_content)

    # 验证纯净版JSON格式
    import json
    try:
        with open(clean_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n✅ 纯净版JSON格式验证通过: {clean_file}")
        print(f"  - 表格数量: {len(data.get('table_names', []))}")
        print(f"  - 总修改数: {data.get('total_modifications')}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")

if __name__ == "__main__":
    save_annotated_json()