#!/usr/bin/env python3
"""
Claude封装程序轻量化性能测试
优化版本：快速验证核心功能和性能指标
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime

class LightweightPerformanceTest:
    """轻量级性能测试"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.results = {}
        
    async def test_basic_functionality(self):
        """基础功能测试"""
        print("🧪 基础功能测试...")
        
        async with aiohttp.ClientSession() as session:
            # 1. 健康检查
            start_time = time.time()
            async with session.get(f"{self.base_url}/health") as resp:
                health_data = await resp.json()
                health_time = time.time() - start_time
            
            # 2. 单次分析测试
            start_time = time.time()
            async with session.post(
                f"{self.base_url}/analyze",
                json={
                    "content": "项目负责人从王五改为赵六",
                    "analysis_type": "risk_assessment"
                }
            ) as resp:
                analysis_data = await resp.json()
                analysis_time = time.time() - start_time
        
        return {
            "health_check": {
                "status": health_data.get("status"),
                "response_time": health_time,
                "success_rate": health_data.get("api_stats", {}).get("success_rate", 0),
                "models_available": len(health_data.get("models_available", []))
            },
            "single_analysis": {
                "success": "result" in analysis_data,
                "response_time": analysis_time,
                "result_quality": len(analysis_data.get("result", "")),
                "confidence": analysis_data.get("confidence", 0),
                "risk_level": analysis_data.get("risk_level")
            }
        }
    
    async def test_concurrent_requests(self, concurrent_count: int = 3):
        """并发请求测试"""
        print(f"⚡ {concurrent_count}并发请求测试...")
        
        test_cases = [
            {"content": "具体计划内容从A项目修改为B项目", "analysis_type": "risk_assessment"},
            {"content": "协助人从李四改为王五", "analysis_type": "risk_assessment"},
            {"content": "邓总指导登记增加新的备注信息", "analysis_type": "risk_assessment"}
        ]
        
        async def single_request(session, case):
            start_time = time.time()
            try:
                async with session.post(
                    f"{self.base_url}/analyze",
                    json=case
                ) as resp:
                    result = await resp.json()
                    response_time = time.time() - start_time
                    return {
                        "success": True,
                        "response_time": response_time,
                        "confidence": result.get("confidence", 0),
                        "risk_level": result.get("risk_level")
                    }
            except Exception as e:
                return {
                    "success": False,
                    "response_time": time.time() - start_time,
                    "error": str(e)
                }
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            tasks = [single_request(session, case) for case in test_cases[:concurrent_count]]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
        
        successful_requests = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]
        
        return {
            "concurrent_level": concurrent_count,
            "total_time": total_time,
            "successful_requests": len(successful_requests),
            "failed_requests": len(results) - len(successful_requests),
            "success_rate": len(successful_requests) / len(results) if results else 0,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0
        }
    
    async def test_memory_and_stability(self):
        """内存和稳定性测试"""
        print("💾 内存和稳定性测试...")
        
        # 连续5个请求测试稳定性
        test_case = {
            "content": "监督人职位变更需要重新分配责任",
            "analysis_type": "risk_assessment"
        }
        
        results = []
        async with aiohttp.ClientSession() as session:
            for i in range(5):
                start_time = time.time()
                try:
                    async with session.post(
                        f"{self.base_url}/analyze",
                        json=test_case
                    ) as resp:
                        result = await resp.json()
                        response_time = time.time() - start_time
                        results.append({
                            "success": True,
                            "response_time": response_time,
                            "result_length": len(result.get("result", "")),
                            "confidence": result.get("confidence", 0)
                        })
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e),
                        "response_time": time.time() - start_time
                    })
                
                # 间隔1秒
                await asyncio.sleep(1)
        
        successful_results = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_results]
        
        return {
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "stability_rate": len(successful_results) / len(results),
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "response_time_std": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "avg_result_quality": statistics.mean([r["result_length"] for r in successful_results]) if successful_results else 0
        }
    
    def generate_performance_summary(self, results: dict) -> dict:
        """生成性能总结"""
        
        basic = results.get("basic_functionality", {})
        concurrent = results.get("concurrent_requests", {})
        stability = results.get("memory_stability", {})
        
        # 计算综合评分
        health_score = 100 if basic.get("health_check", {}).get("status") == "healthy" else 0
        
        response_time_score = max(0, 100 - (basic.get("single_analysis", {}).get("response_time", 0) - 5) * 10)
        response_time_score = min(100, response_time_score)
        
        concurrent_score = concurrent.get("success_rate", 0) * 100
        
        stability_score = stability.get("stability_rate", 0) * 100
        
        overall_score = (health_score + response_time_score + concurrent_score + stability_score) / 4
        
        return {
            "overall_performance_score": round(overall_score, 1),
            "health_status": "excellent" if health_score >= 90 else "good" if health_score >= 70 else "poor",
            "response_performance": "excellent" if response_time_score >= 90 else "good" if response_time_score >= 70 else "slow",
            "concurrent_performance": "excellent" if concurrent_score >= 90 else "good" if concurrent_score >= 70 else "poor",
            "stability": "excellent" if stability_score >= 90 else "good" if stability_score >= 70 else "unstable",
            "key_metrics": {
                "avg_response_time": basic.get("single_analysis", {}).get("response_time", 0),
                "concurrent_success_rate": concurrent.get("success_rate", 0),
                "stability_rate": stability.get("stability_rate", 0),
                "api_success_rate": basic.get("health_check", {}).get("success_rate", 0)
            },
            "recommendations": self._generate_recommendations(results)
        }
    
    def _generate_recommendations(self, results: dict) -> list:
        """生成优化建议"""
        recommendations = []
        
        basic = results.get("basic_functionality", {})
        concurrent = results.get("concurrent_requests", {})
        stability = results.get("memory_stability", {})
        
        # 响应时间建议
        avg_time = basic.get("single_analysis", {}).get("response_time", 0)
        if avg_time > 15:
            recommendations.append("响应时间较长，建议优化Claude API调用或增加缓存")
        elif avg_time > 10:
            recommendations.append("响应时间适中，可考虑在高并发场景下增加优化")
        
        # 并发性能建议
        concurrent_rate = concurrent.get("success_rate", 0)
        if concurrent_rate < 0.8:
            recommendations.append("并发处理成功率较低，建议检查连接池配置和限流设置")
        
        # 稳定性建议
        stability_rate = stability.get("stability_rate", 0)
        if stability_rate < 0.9:
            recommendations.append("系统稳定性有待提升，建议加强错误处理和重试机制")
        
        # 通用建议
        if not recommendations:
            recommendations.append("系统运行良好，可以投入生产环境使用")
        
        return recommendations

async def main():
    """主测试函数"""
    print("🚀 启动Claude封装程序轻量化性能测试")
    print("=" * 60)
    
    tester = LightweightPerformanceTest()
    all_results = {}
    
    try:
        # 基础功能测试
        all_results["basic_functionality"] = await tester.test_basic_functionality()
        print("✅ 基础功能测试完成")
        
        # 并发请求测试
        all_results["concurrent_requests"] = await tester.test_concurrent_requests(3)
        print("✅ 并发请求测试完成")
        
        # 稳定性测试
        all_results["memory_stability"] = await tester.test_memory_and_stability()
        print("✅ 稳定性测试完成")
        
        # 生成性能总结
        summary = tester.generate_performance_summary(all_results)
        all_results["performance_summary"] = summary
        
        # 输出详细结果
        print("\n" + "=" * 60)
        print("📊 性能测试结果详情")
        print("=" * 60)
        
        # 基础功能
        basic = all_results["basic_functionality"]
        print(f"🏥 健康检查: {basic['health_check']['status']}")
        print(f"⏱️  健康检查响应时间: {basic['health_check']['response_time']:.2f}秒")
        print(f"📈 API历史成功率: {basic['health_check']['success_rate']:.1%}")
        print(f"🤖 可用模型数量: {basic['health_check']['models_available']}")
        
        print(f"\n🔍 单次分析测试:")
        print(f"✅ 分析成功: {basic['single_analysis']['success']}")
        print(f"⏱️  响应时间: {basic['single_analysis']['response_time']:.2f}秒")
        print(f"🎯 置信度: {basic['single_analysis']['confidence']:.2f}")
        print(f"⚠️  风险等级: {basic['single_analysis']['risk_level']}")
        
        # 并发测试
        concurrent = all_results["concurrent_requests"]
        print(f"\n⚡ 并发测试 (3个请求):")
        print(f"✅ 成功请求: {concurrent['successful_requests']}/{concurrent['concurrent_level']}")
        print(f"📊 成功率: {concurrent['success_rate']:.1%}")
        print(f"⏱️  平均响应时间: {concurrent['avg_response_time']:.2f}秒")
        print(f"⏰ 最大响应时间: {concurrent['max_response_time']:.2f}秒")
        
        # 稳定性测试
        stability = all_results["memory_stability"]
        print(f"\n💾 稳定性测试 (5个连续请求):")
        print(f"✅ 成功率: {stability['stability_rate']:.1%}")
        print(f"⏱️  平均响应时间: {stability['avg_response_time']:.2f}秒")
        print(f"📏 响应时间标准差: {stability['response_time_std']:.2f}")
        
        # 性能总结
        print(f"\n" + "=" * 60)
        print("🎯 性能总结")
        print("=" * 60)
        print(f"🏆 综合性能评分: {summary['overall_performance_score']}/100")
        print(f"🏥 健康状态: {summary['health_status']}")
        print(f"⚡ 响应性能: {summary['response_performance']}")
        print(f"🔄 并发性能: {summary['concurrent_performance']}")
        print(f"💪 系统稳定性: {summary['stability']}")
        
        print(f"\n📋 优化建议:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"{i}. {rec}")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"performance_test_result_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细结果已保存到: {result_file}")
        print("\n🎉 轻量化性能测试完成!")
        
        return all_results
        
    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())