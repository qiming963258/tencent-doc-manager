#!/usr/bin/env python3
"""
Claude AI封装程序实际提问测试
模拟真实业务场景的AI分析请求
"""

import requests
import json
import time
from datetime import datetime

class RealWorldTestClient:
    """真实场景测试客户端"""
    
    def __init__(self):
        self.base_url = "http://localhost:8081"
        self.session = requests.Session()
        
    def test_real_questions(self):
        """测试实际业务问题"""
        print("🧪 开始实际提问测试")
        print("=" * 60)
        
        # 真实业务场景测试用例
        test_cases = [
            {
                "name": "项目负责人变更风险评估",
                "content": "在我们的软件开发项目中，原负责人张三因为要去新部门，项目负责人要改成李四。李四之前负责过类似项目，但对这个项目的具体技术栈还不太熟悉。这个变更的风险如何评估？",
                "analysis_type": "risk_assessment",
                "context": {"domain": "项目管理", "urgency": "高"}
            },
            {
                "name": "预算调整合理性分析", 
                "content": "市场部提出将Q4营销预算从50万增加到80万，理由是竞争对手加大了投入，我们需要保持市场份额。这个预算调整是否合理？",
                "analysis_type": "content_analysis",
                "context": {"domain": "财务管理", "quarter": "Q4"}
            },
            {
                "name": "技术方案变更影响评估",
                "content": "技术团队建议将后端架构从单体应用改为微服务架构，预计需要3个月时间，会暂停新功能开发。产品团队担心影响业务进度。",
                "analysis_type": "risk_assessment", 
                "context": {"domain": "技术决策", "impact": "高"}
            },
            {
                "name": "人员调动合规性检查",
                "content": "HR部门计划将销售部的王五调到客服部，王五在销售部工作了2年，客户满意度一直很高。这个调动安排如何？",
                "analysis_type": "content_analysis",
                "context": {"domain": "人力资源", "type": "内部调动"}
            },
            {
                "name": "供应商变更风险分析",
                "content": "采购部门建议更换主要原料供应商，新供应商价格便宜20%，但是一家新成立的公司，没有长期合作历史。",
                "analysis_type": "risk_assessment",
                "context": {"domain": "供应链管理", "cost_impact": "高"}
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            print(f"\n📋 测试案例 {i+1}: {test_case['name']}")
            print("-" * 40)
            print(f"问题: {test_case['content'][:100]}...")
            
            try:
                start_time = time.time()
                
                # 发送请求到Claude AI封装程序
                response = self.session.post(f"{self.base_url}/analyze", json={
                    "content": test_case["content"],
                    "analysis_type": test_case["analysis_type"],
                    "context": test_case.get("context", {})
                }, timeout=60)
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    
                    print(f"✅ 分析成功:")
                    print(f"   响应时间: {response_time:.2f}秒")
                    print(f"   分析类型: {result.get('analysis_type', 'N/A')}")
                    print(f"   风险等级: {result.get('risk_level', 'N/A')}")
                    print(f"   置信度: {result.get('confidence', 0):.2f}")
                    print(f"   分析结果: {result.get('result', '')[:200]}...")
                    
                    results.append({
                        "test_case": test_case["name"],
                        "success": True,
                        "response_time": response_time,
                        "analysis_type": result.get("analysis_type"),
                        "risk_level": result.get("risk_level"),
                        "confidence": result.get("confidence"),
                        "result_preview": result.get("result", "")[:200]
                    })
                    
                else:
                    print(f"❌ 分析失败: HTTP {response.status_code}")
                    print(f"   错误信息: {response.text}")
                    results.append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "response_time": response_time
                    })
                    
            except Exception as e:
                print(f"❌ 请求异常: {str(e)}")
                results.append({
                    "test_case": test_case["name"],
                    "success": False,
                    "error": str(e),
                    "response_time": None
                })
            
            # 短暂等待避免API限制
            time.sleep(2)
        
        return results
    
    def test_interactive_questions(self):
        """测试交互式问题"""
        print(f"\n🎯 交互式问题测试")
        print("-" * 40)
        
        interactive_tests = [
            {
                "question": "你好，我是一家科技公司的项目经理，请帮我分析一下团队绩效问题。",
                "follow_up": "我们团队最近项目延期了，主要是因为技术难度超出预期，你觉得这种情况应该如何处理？"
            },
            {
                "question": "我想了解一下文档变更的风险评估标准是什么？",
                "follow_up": "如果是涉及核心业务流程的文档修改，风险等级会如何评定？"
            }
        ]
        
        interactive_results = []
        
        for i, test in enumerate(interactive_tests):
            print(f"\n💬 交互测试 {i+1}:")
            print(f"初始问题: {test['question']}")
            
            try:
                # 第一轮对话
                response1 = self.session.post(f"{self.base_url}/chat", json={
                    "messages": [
                        {"role": "user", "content": test["question"]}
                    ],
                    "max_tokens": 300
                }, timeout=45)
                
                if response1.status_code == 200:
                    result1 = response1.json()
                    first_response = result1["choices"][0]["message"]["content"]
                    print(f"✅ AI回复: {first_response[:150]}...")
                    
                    # 追问
                    print(f"追问: {test['follow_up']}")
                    
                    response2 = self.session.post(f"{self.base_url}/chat", json={
                        "messages": [
                            {"role": "user", "content": test["question"]},
                            {"role": "assistant", "content": first_response},
                            {"role": "user", "content": test["follow_up"]}
                        ],
                        "max_tokens": 300
                    }, timeout=45)
                    
                    if response2.status_code == 200:
                        result2 = response2.json()
                        second_response = result2["choices"][0]["message"]["content"]
                        print(f"✅ AI追问回复: {second_response[:150]}...")
                        
                        interactive_results.append({
                            "test_id": i+1,
                            "success": True,
                            "first_response_length": len(first_response),
                            "second_response_length": len(second_response)
                        })
                    else:
                        print(f"❌ 追问失败: {response2.status_code}")
                        interactive_results.append({"test_id": i+1, "success": False})
                else:
                    print(f"❌ 初始问题失败: {response1.status_code}")
                    interactive_results.append({"test_id": i+1, "success": False})
                    
            except Exception as e:
                print(f"❌ 交互测试异常: {e}")
                interactive_results.append({"test_id": i+1, "success": False, "error": str(e)})
            
            time.sleep(3)
        
        return interactive_results
    
    def generate_real_test_report(self, analysis_results, interactive_results):
        """生成实际测试报告"""
        print(f"\n" + "=" * 60)
        print("📊 实际提问测试结果汇总")
        print("=" * 60)
        
        # 分析测试统计
        successful_analysis = [r for r in analysis_results if r["success"]]
        failed_analysis = [r for r in analysis_results if not r["success"]]
        
        print(f"📈 智能分析测试:")
        print(f"   总测试数: {len(analysis_results)}")
        print(f"   成功数: {len(successful_analysis)}")
        print(f"   失败数: {len(failed_analysis)}")
        print(f"   成功率: {len(successful_analysis)/len(analysis_results)*100:.1f}%")
        
        if successful_analysis:
            avg_time = sum(r["response_time"] for r in successful_analysis) / len(successful_analysis)
            avg_confidence = sum(r.get("confidence", 0) for r in successful_analysis) / len(successful_analysis)
            print(f"   平均响应时间: {avg_time:.2f}秒")
            print(f"   平均置信度: {avg_confidence:.2f}")
            
            # 风险等级统计
            risk_levels = [r.get("risk_level") for r in successful_analysis if r.get("risk_level")]
            l1_count = risk_levels.count("L1")
            l2_count = risk_levels.count("L2") 
            l3_count = risk_levels.count("L3")
            print(f"   风险等级分布: L1({l1_count}) L2({l2_count}) L3({l3_count})")
        
        # 交互测试统计
        successful_interactive = [r for r in interactive_results if r.get("success")]
        print(f"\n💬 交互式测试:")
        print(f"   总测试数: {len(interactive_results)}")
        print(f"   成功数: {len(successful_interactive)}")
        print(f"   成功率: {len(successful_interactive)/len(interactive_results)*100:.1f}%")
        
        # 整体评价
        overall_success_rate = (len(successful_analysis) + len(successful_interactive)) / (len(analysis_results) + len(interactive_results))
        
        print(f"\n🎯 整体评价:")
        print(f"   综合成功率: {overall_success_rate*100:.1f}%")
        print(f"   系统状态: {'✅ 优秀' if overall_success_rate > 0.9 else '🟡 良好' if overall_success_rate > 0.7 else '❌ 需改进'}")
        
        # 保存详细报告
        detailed_report = {
            "timestamp": datetime.now().isoformat(),
            "analysis_results": analysis_results,
            "interactive_results": interactive_results,
            "summary": {
                "total_analysis_tests": len(analysis_results),
                "successful_analysis": len(successful_analysis),
                "analysis_success_rate": len(successful_analysis)/len(analysis_results),
                "total_interactive_tests": len(interactive_results),
                "successful_interactive": len(successful_interactive),
                "interactive_success_rate": len(successful_interactive)/len(interactive_results) if interactive_results else 0,
                "overall_success_rate": overall_success_rate
            }
        }
        
        report_filename = f"real_world_test_report_{int(time.time())}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 详细报告已保存: {report_filename}")
        return detailed_report
    
    def run_comprehensive_real_test(self):
        """运行完整的实际测试"""
        print("🚀 开始Claude AI封装程序实际提问测试")
        print("🎯 模拟真实业务场景验证AI分析能力")
        print("=" * 60)
        
        # 执行测试
        analysis_results = self.test_real_questions()
        interactive_results = self.test_interactive_questions()
        
        # 生成报告
        report = self.generate_real_test_report(analysis_results, interactive_results)
        
        return report

if __name__ == "__main__":
    tester = RealWorldTestClient()
    results = tester.run_comprehensive_real_test()
    print("\n🎉 实际提问测试完成!")