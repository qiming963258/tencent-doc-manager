#!/usr/bin/env python3
"""
测试L2列AI语义分析和打分功能
验证L2列变更是否能正确触发橙色警告（>=0.6分）
"""

import os
import sys
import json
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from production.scoring_engine.integrated_scorer import IntegratedScorer

def test_l2_scoring():
    """测试L2列打分"""
    print("=" * 60)
    print("测试L2列AI语义分析和打分功能")
    print("=" * 60)
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ DEEPSEEK_API_KEY未设置")
        return False
    else:
        print(f"✅ DEEPSEEK_API_KEY已加载: {api_key[:10]}...")
    
    # 初始化打分器（使用AI）
    try:
        scorer = IntegratedScorer(use_ai=True, cache_enabled=False)
        print("✅ IntegratedScorer初始化成功（AI模式）")
    except Exception as e:
        print(f"❌ IntegratedScorer初始化失败: {e}")
        return False
    
    # 测试L2列修改
    test_modifications = [
        {
            "mod_id": "test_1",
            "column_name": "负责人",  # L2列
            "old_value": "张三",
            "new_value": "李四",
            "row": 5,
            "cell": "D5"
        },
        {
            "mod_id": "test_2", 
            "column_name": "具体计划内容",  # L2列
            "old_value": "开发新功能",
            "new_value": "市场推广活动",
            "row": 10,
            "cell": "B10"
        },
        {
            "mod_id": "test_3",
            "column_name": "邓总指导登记（日更新）",  # L2列
            "old_value": "已审批",
            "new_value": "待修改",
            "row": 15,
            "cell": "E15"
        }
    ]
    
    print("\n开始测试L2列打分...")
    print("-" * 40)
    
    all_passed = True
    for mod in test_modifications:
        try:
            # 调用打分（需要单独传入mod_id）
            mod_id = mod.pop('mod_id')  # 提取mod_id
            result = scorer.score_modification(mod, mod_id)
            
            # 从正确的嵌套结构中提取数据
            scoring_details = result.get('scoring_details', {})
            score = scoring_details.get('final_score', 0)
            
            risk_assessment = result.get('risk_assessment', {})
            risk_level = risk_assessment.get('risk_level', 'unknown')
            color = risk_assessment.get('risk_color', 'unknown')
            level = result.get('column_level', 'unknown')
            
            # 检查是否满足L2最低要求（>=0.6，橙色）
            passed = score >= 0.6 and (color == 'orange' or color == 'red')
            status = "✅" if passed else "❌"
            
            print(f"\n{status} 列: {mod['column_name']}")
            print(f"   变更: '{mod['old_value']}' → '{mod['new_value']}'")
            print(f"   得分: {score:.2f}")
            print(f"   等级: {level}")
            print(f"   风险: {risk_level}")
            print(f"   颜色: {color}")
            
            if not passed:
                print(f"   ⚠️ 未达到L2最低要求（应>=0.6，橙色）")
                all_passed = False
                
        except Exception as e:
            print(f"\n❌ 测试失败 - 列: {mod['column_name']}")
            print(f"   错误: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有L2列测试通过！L2列正确触发橙色警告（>=0.6分）")
    else:
        print("❌ 部分L2列测试失败，请检查配置")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_l2_scoring()
    sys.exit(0 if success else 1)