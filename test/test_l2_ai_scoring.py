#!/usr/bin/env python3
"""
测试脚本：验证L2列确实使用AI语义分析
"""

import os
import sys
import json
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'production'))

def test_l2_scoring():
    """测试L2列的打分是否使用AI"""
    
    print("="*60)
    print("L2 AI语义分析测试")
    print("="*60)
    
    # 创建测试数据
    test_data = {
        "metadata": {
            "source_file": "test_baseline.csv",
            "target_file": "test_target.csv",
            "comparison_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "modifications": [
            {
                "cell": "A1",
                "column_name": "项目类型",  # L2列
                "old_value": "目标管理",
                "new_value": "体系建设",
                "row_index": 1
            },
            {
                "cell": "B1", 
                "column_name": "重要程度",  # L1列
                "old_value": "高",
                "new_value": "中",
                "row_index": 1
            },
            {
                "cell": "C1",
                "column_name": "其他信息",  # L3列
                "old_value": "备注1",
                "new_value": "备注2",
                "row_index": 1
            }
        ]
    }
    
    # 保存测试文件
    test_file = "/tmp/test_l2_scoring.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 创建测试文件: {test_file}")
    
    # 导入打分器
    try:
        from scoring_engine.integrated_scorer import IntegratedScorer
        print("✓ 成功导入IntegratedScorer")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return
    
    # 测试场景1：无AI时L2应该报错
    print("\n场景1：测试L2列在无AI时必须失败")
    print("-"*40)
    
    try:
        scorer_no_ai = IntegratedScorer(use_ai=False)
        result = scorer_no_ai.process_file(test_file)
        print("✗ 错误：L2列在无AI时应该报错，但却成功了！")
    except Exception as e:
        if "L2列必须使用AI" in str(e):
            print(f"✓ 正确：L2列无AI时报错: {e}")
        else:
            print(f"? 其他错误: {e}")
    
    # 测试场景2：有AI时L2应该成功
    print("\n场景2：测试L2列使用AI分析（使用集成的API密钥）")
    print("-"*40)
    
    # 系统现在使用集成的API密钥，无需检查环境变量
    print("✓ 使用集成的API密钥（来自8098端口服务）")
    
    try:
        scorer_with_ai = IntegratedScorer(use_ai=True)
        output_file = scorer_with_ai.process_file(test_file)
        print(f"✓ 成功生成打分文件: {output_file}")
        
        # 读取并分析结果
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        print("\n分析结果：")
        print("-"*40)
        
        for score in result['scores']:
            col_name = score['column_name']
            col_level = score['column_level']
            ai_used = score['ai_analysis']['ai_used']
            final_score = score['scoring_details']['final_score']
            
            print(f"\n列名: {col_name}")
            print(f"  级别: {col_level}")
            print(f"  使用AI: {ai_used}")
            print(f"  最终得分: {final_score:.3f}")
            
            # 验证L2列必须使用AI
            if col_level == 'L2':
                if ai_used:
                    ai_detail = score['ai_analysis'].get('ai_analysis', {})
                    if ai_detail:
                        print(f"  ✓ L2列正确使用了AI分析")
                        print(f"    - 最终决策: {ai_detail.get('final_decision')}")
                        print(f"    - 需要审批: {ai_detail.get('approval_required')}")
                        
                        # 检查是否有layer1_result
                        if ai_detail.get('layer1_result'):
                            layer1 = ai_detail['layer1_result']
                            print(f"    - 第一层判断: {layer1.get('judgment')} (置信度: {layer1.get('confidence')}%)")
                        
                        # 检查是否有layer2_result
                        if ai_detail.get('layer2_result'):
                            layer2 = ai_detail['layer2_result']
                            print(f"    - 第二层分析: {layer2.get('decision')} (风险: {layer2.get('risk_level')})")
                    else:
                        print(f"  ⚠️  L2列标记为使用AI但缺少详细结果")
                else:
                    print(f"  ✗ 错误：L2列未使用AI分析！")
            
            # 验证L1和L3列不使用AI
            elif col_level in ['L1', 'L3']:
                if not ai_used:
                    print(f"  ✓ {col_level}列正确地未使用AI")
                else:
                    print(f"  ✗ 错误：{col_level}列不应该使用AI！")
        
        # 统计汇总
        print("\n" + "="*60)
        print("测试汇总")
        print("="*60)
        
        summary = result.get('summary', {})
        ai_usage = summary.get('ai_usage', {})
        
        print(f"总修改数: {summary.get('total_modifications', 0)}")
        print(f"AI调用次数: {ai_usage.get('total_ai_calls', 0)}")
        print(f"第一层通过: {ai_usage.get('layer1_passes', 0)}")
        print(f"第二层分析: {ai_usage.get('layer2_analyses', 0)}")
        print(f"Token消耗: {ai_usage.get('total_tokens', 0)}")
        
        # 风险分布
        risk_dist = summary.get('risk_distribution', {})
        if risk_dist:
            print("\n风险分布:")
            for level, count in risk_dist.items():
                print(f"  {level}: {count}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_l2_scoring()