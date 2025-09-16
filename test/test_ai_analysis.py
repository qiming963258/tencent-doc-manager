#!/usr/bin/env python3
"""
测试Claude AI分析功能
验证8081端口服务的实际分析能力
"""

import requests
import json
from datetime import datetime

def test_csv_change_analysis():
    """测试CSV变更的AI分析"""
    
    print("="*60)
    print("Claude AI CSV变更分析测试")
    print("="*60)
    
    # 测试案例：模拟实际的CSV变更
    test_cases = [
        {
            "column": "负责人",
            "old_value": "张三",
            "new_value": "李四",
            "description": "负责人变更（L2级别）"
        },
        {
            "column": "完成进度",
            "old_value": "80%",
            "new_value": "95%",
            "description": "进度更新（L3级别）"
        },
        {
            "column": "重要程度",
            "old_value": "高",
            "new_value": "低",
            "description": "重要程度降级（L1级别）"
        }
    ]
    
    api_url = "http://localhost:8081/chat"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 测试案例 {i}: {test_case['description']}")
        print("-"*40)
        
        # 构建分析请求
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": f"""请分析以下CSV表格的修改是否合理：

列名: {test_case['column']}
原值: {test_case['old_value']}
新值: {test_case['new_value']}

请从以下角度分析：
1. 修改的合理性（是否符合业务逻辑）
2. 风险等级评估（L1=高风险不可修改, L2=需审核, L3=低风险）
3. 给出审批建议（批准/拒绝/需要进一步审核）

请用JSON格式返回：
{{
  "risk_level": "L1/L2/L3",
  "recommendation": "APPROVE/REJECT/REVIEW",
  "reasoning": "分析原因",
  "confidence": 0.8
}}"""
                }
            ],
            "max_tokens": 500
        }
        
        try:
            # 发送请求
            response = requests.post(api_url, json=request_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ AI分析成功")
                
                # 提取AI响应
                ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # 尝试解析JSON响应
                try:
                    # 查找JSON部分
                    import re
                    json_match = re.search(r'\{[^}]+\}', ai_response, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        print(f"   风险等级: {analysis.get('risk_level', 'N/A')}")
                        print(f"   建议: {analysis.get('recommendation', 'N/A')}")
                        print(f"   原因: {analysis.get('reasoning', 'N/A')}")
                        print(f"   置信度: {analysis.get('confidence', 0):.1%}")
                    else:
                        print(f"   AI响应: {ai_response[:200]}")
                except:
                    print(f"   AI响应: {ai_response[:200]}")
                
                # 显示Token使用情况
                usage = result.get('usage', {})
                print(f"   Token使用: 输入={usage.get('input_tokens', 0)}, 输出={usage.get('output_tokens', 0)}")
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"   错误: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 发生错误: {e}")

def test_batch_analysis():
    """测试批量分析功能"""
    
    print("\n" + "="*60)
    print("批量分析测试")
    print("="*60)
    
    # 构建批量分析请求
    batch_request = {
        "messages": [
            {
                "role": "user", 
                "content": """以下是CSV表格的多个修改，请评估整体风险：

1. 负责人: 张三 → 李四
2. 监督人: 王五 → 赵六
3. 完成进度: 60% → 90%
4. 预计完成时间: 2025-01-01 → 2025-02-01

请评估：
- 整体风险等级
- 是否存在关联风险
- 综合审批建议"""
            }
        ],
        "max_tokens": 800
    }
    
    try:
        response = requests.post("http://localhost:8081/chat", json=batch_request, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 批量分析成功")
            
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"\nAI分析结果:")
            print("-"*40)
            print(ai_response[:800])
            
        else:
            print(f"❌ 批量分析失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

def main():
    """主测试函数"""
    
    # 首先检查服务状态
    print("🔍 检查8081端口服务状态...")
    try:
        health = requests.get("http://localhost:8081/health", timeout=5)
        if health.status_code == 200:
            print("✅ Claude服务正常运行")
            health_data = health.json()
            print(f"   运行时间: {health_data.get('uptime_formatted', 'N/A')}")
            print(f"   成功率: {health_data.get('api_stats', {}).get('success_rate', 0):.1f}%")
        else:
            print("❌ 服务响应异常")
            return
    except:
        print("❌ 无法连接到8081端口服务")
        return
    
    # 执行测试
    test_csv_change_analysis()
    test_batch_analysis()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n💡 结论：")
    print("如果以上测试都成功，说明AI分析功能可以正常工作")
    print("可以将其集成到CSV对比流程中，实现智能风险评估")

if __name__ == "__main__":
    main()