#!/usr/bin/env python3
"""
简化版实际提问测试
快速验证Claude AI的实际问题处理能力
"""

import requests
import json
import time

def quick_real_test():
    """快速实际问题测试"""
    base_url = "http://localhost:8081"
    
    print("🧪 开始实际提问测试（简化版）")
    print("=" * 50)
    
    # 精选3个真实业务问题
    test_questions = [
        {
            "name": "项目延期风险评估",
            "content": "我们的APP开发项目原计划8月底上线，但现在发现核心功能的API接口开发进度滞后，预计要延期到9月中旬。这个延期对业务的影响风险如何？",
            "type": "risk_assessment"
        },
        {
            "name": "预算增加合理性",
            "content": "市场部申请将本季度广告投放预算从30万增加到45万，理由是竞争对手投放力度加大。这个预算调整请求是否合理？",
            "type": "content_analysis"
        },
        {
            "name": "人员变动影响分析",
            "content": "技术团队的架构师李工要离职，HR建议内部提拔一位高级开发来接替。这种人员变动对项目的影响如何评估？",
            "type": "risk_assessment"
        }
    ]
    
    results = []
    
    for i, question in enumerate(test_questions):
        print(f"\n📋 问题 {i+1}: {question['name']}")
        print(f"内容: {question['content'][:80]}...")
        
        try:
            start_time = time.time()
            
            response = requests.post(f"{base_url}/analyze", json={
                "content": question["content"],
                "analysis_type": question["type"]
            }, timeout=30)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 分析完成 ({response_time:.1f}s)")
                print(f"   风险等级: {result.get('risk_level', 'N/A')}")
                print(f"   置信度: {result.get('confidence', 0):.2f}")
                print(f"   结果预览: {result.get('result', '')[:100]}...")
                
                results.append({
                    "question": question["name"],
                    "success": True,
                    "response_time": response_time,
                    "risk_level": result.get('risk_level'),
                    "confidence": result.get('confidence')
                })
            else:
                print(f"❌ 分析失败: {response.status_code}")
                results.append({"question": question["name"], "success": False})
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)[:50]}...")
            results.append({"question": question["name"], "success": False, "error": str(e)})
        
        time.sleep(1)  # 短暂间隔
    
    # 简单的结果统计
    successful = [r for r in results if r.get("success")]
    print(f"\n📊 测试结果:")
    print(f"   成功: {len(successful)}/{len(results)}")
    print(f"   成功率: {len(successful)/len(results)*100:.0f}%")
    
    if successful:
        avg_time = sum(r["response_time"] for r in successful) / len(successful)
        avg_confidence = sum(r.get("confidence", 0) for r in successful) / len(successful)
        print(f"   平均响应时间: {avg_time:.1f}秒")
        print(f"   平均置信度: {avg_confidence:.2f}")
    
    return results

def test_simple_chat():
    """测试简单对话"""
    print(f"\n💬 简单对话测试:")
    
    try:
        response = requests.post("http://localhost:8081/chat", json={
            "messages": [{"role": "user", "content": "你好，请简单介绍一下你在文档风险分析方面的能力。"}],
            "max_tokens": 150
        }, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ 对话成功")
            print(f"   回复: {content[:200]}...")
            return True
        else:
            print(f"❌ 对话失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 对话异常: {str(e)[:50]}...")
        return False

if __name__ == "__main__":
    print("🚀 Claude AI实际应用能力验证")
    
    # 智能分析测试
    analysis_results = quick_real_test()
    
    # 对话测试  
    chat_success = test_simple_chat()
    
    # 总结
    analysis_success_rate = len([r for r in analysis_results if r.get("success")]) / len(analysis_results)
    
    print(f"\n🎯 总体评价:")
    print(f"   智能分析能力: {analysis_success_rate*100:.0f}%")
    print(f"   对话交互能力: {'✅' if chat_success else '❌'}")
    
    overall_score = (analysis_success_rate + (1 if chat_success else 0)) / 2
    if overall_score >= 0.8:
        status = "✅ 优秀 - 可用于生产环境"
    elif overall_score >= 0.6:
        status = "🟡 良好 - 基本满足需求"
    else:
        status = "❌ 需改进"
    
    print(f"   综合评价: {status}")
    print(f"\n🎉 实际提问测试完成!")