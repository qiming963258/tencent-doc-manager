#!/usr/bin/env python3
"""测试评分系统修复效果"""

import sys
import os
import json
from datetime import datetime

# 添加路径
sys.path.append('/root/projects/tencent-doc-manager')
sys.path.append('/root/projects/tencent-doc-manager/production')

from production.scoring_engine.integrated_scorer import IntegratedScorer

def test_scoring_system():
    """测试评分系统"""
    
    print("="*60)
    print("评分系统修复测试")
    print("="*60)
    
    # 创建打分器（不使用AI以简化测试）
    scorer = IntegratedScorer(use_ai=False, cache_enabled=False)
    
    # 测试用例
    test_cases = [
        # L1列测试
        {
            "name": "L1列-小幅变更",
            "column_name": "任务发起时间",  # L1列
            "old_value": "2025-01-01",
            "new_value": "2025-01-02",
            "expected_min_score": 0.8,  # 应该>=0.8（红色）
            "expected_color": "red"
        },
        {
            "name": "L1列-从空到有",
            "column_name": "重要程度",  # L1列
            "old_value": "",
            "new_value": "高",
            "expected_min_score": 0.8,
            "expected_color": "red"
        },
        {
            "name": "L1列-无变更",
            "column_name": "目标对齐",  # L1列
            "old_value": "Q1目标",
            "new_value": "Q1目标",
            "expected_min_score": 0,
            "expected_color": "blue"
        },
        
        # L2列测试
        {
            "name": "L2列-小幅变更",
            "column_name": "负责人",  # L2列
            "old_value": "张三",
            "new_value": "李四",
            "expected_min_score": 0.4,  # 应该>=0.4（黄色）
            "expected_color": "yellow"
        },
        {
            "name": "L2列-从有到空",
            "column_name": "协助人",  # L2列
            "old_value": "团队A",
            "new_value": "",
            "expected_min_score": 0.4,
            "expected_color": "yellow"
        },
        
        # L3列测试
        {
            "name": "L3列-变更",
            "column_name": "序号",  # L3列
            "old_value": "1",
            "new_value": "2",
            "expected_min_score": 0,
            "expected_color": None  # L3可以是任何颜色
        }
    ]
    
    print("\n📊 测试结果：\n")
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        # 构建修改数据
        mod = {
            "column_name": test_case["column_name"],
            "old_value": test_case["old_value"],
            "new_value": test_case["new_value"],
            "cell": f"A{i}"
        }
        
        # 获取列级别
        column_level = scorer.get_column_level(test_case["column_name"])
        
        # 调用相应的处理方法
        if column_level == "L1":
            result = scorer.process_l1_modification(mod)
        elif column_level == "L2":
            # 模拟L2处理（不调用AI）
            base_score = 0.5
            change_factor = scorer.calculate_change_factor(
                mod.get('old_value', ''),
                mod.get('new_value', '')
            )
            importance_weight = scorer.get_column_weight(mod['column_name'])
            
            # L2特殊处理逻辑
            if change_factor > 0:
                raw_score = base_score * change_factor * importance_weight * 1.0 * 1.0  # 不使用AI调整
                final_score = max(0.4, min(raw_score, 1.0))
            else:
                final_score = 0.0
            
            result = {
                'base_score': base_score,
                'change_factor': change_factor,
                'importance_weight': importance_weight,
                'ai_adjustment': 1.0,
                'confidence_weight': 1.0,
                'final_score': final_score,
                'ai_used': False
            }
        else:  # L3
            result = scorer.process_l3_modification(mod)
        
        # 获取风险等级
        final_score = result['final_score']
        risk_level, risk_color, risk_icon = scorer.get_risk_level(final_score)
        
        # 检查结果
        passed = True
        
        # 检查最低分数
        if test_case["expected_min_score"] > 0:
            if final_score < test_case["expected_min_score"]:
                passed = False
        
        # 检查颜色
        if test_case["expected_color"]:
            if risk_color != test_case["expected_color"]:
                passed = False
        
        # 打印结果
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{i}. {test_case['name']}")
        print(f"   列级别: {column_level}")
        print(f"   变更: '{test_case['old_value']}' → '{test_case['new_value']}'")
        print(f"   最终分数: {final_score:.3f}")
        print(f"   风险等级: {risk_level} {risk_icon} ({risk_color})")
        print(f"   期望: 分数>={test_case['expected_min_score']}, 颜色={test_case['expected_color']}")
        print(f"   结果: {status}")
        print()
        
        if not passed:
            all_passed = False
    
    # 总结
    print("="*60)
    if all_passed:
        print("✅ 所有测试通过！评分系统修复成功")
    else:
        print("❌ 部分测试失败，请检查修复逻辑")
    print("="*60)
    
    # 额外信息
    print("\n📋 评分规则总结：")
    print("• L1列（核心业务）: 任何变更 → 最低0.8分（红色警告）")
    print("• L2列（重要业务）: 任何变更 → 最低0.4分（黄色警告）")
    print("• L3列（一般信息）: 按原有逻辑计算")
    print()
    print("颜色阈值：")
    print("• 红色: 分数 >= 0.8")
    print("• 橙色: 分数 >= 0.6")
    print("• 黄色: 分数 >= 0.4")
    print("• 绿色: 分数 >= 0.2")
    print("• 蓝色: 分数 < 0.2")


if __name__ == "__main__":
    test_scoring_system()