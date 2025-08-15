#!/usr/bin/env python3
"""
Claude封装服务快速性能测试
针对实际响应时间优化的轻量级压力测试
"""

import asyncio
import aiohttp
import time
import statistics
import json
from datetime import datetime
import psutil

class QuickPerformanceBenchmark:
    """快速性能基准测试"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        
    async def test_response_times(self, concurrent_count: int = 3) -> dict:
        """测试响应时间（轻量级）"""
        print(f"📊 测试 {concurrent_count} 并发响应时间...")
        
        async def single_request(session, request_id):
            try:
                start_time = time.time()
                async with session.post(f"{self.base_url}/analyze", json={
                    "content": f"测试请求 #{request_id}: 负责人从张三改为李四",
                    "analysis_type": "risk_assessment",
                    "context": {"test_id": request_id}
                }) as response:
                    result = await response.json()
                    response_time = time.time() - start_time
                    return {
                        "success": response.status == 200,
                        "response_time": response_time,
                        "request_id": request_id
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "request_id": request_id
                }
        
        # 执行并发测试
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            tasks = [single_request(session, i) for i in range(concurrent_count)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
        
        # 统计结果
        successful = [r for r in results if r["success"]]
        failed = len(results) - len(successful)
        
        if successful:
            response_times = [r["response_time"] for r in successful]
            return {
                "concurrent_level": concurrent_count,
                "total_requests": concurrent_count,
                "successful_requests": len(successful),
                "failed_requests": failed,
                "success_rate": len(successful) / concurrent_count * 100,
                "total_time": total_time,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "throughput": len(successful) / total_time
            }
        else:
            return {"error": "所有请求失败", "failed_requests": concurrent_count}
    
    async def test_sustained_load(self, duration_seconds: int = 30, request_interval: int = 15) -> dict:
        """持续负载测试（轻量级）"""
        print(f"⏱️ 持续负载测试 ({duration_seconds}秒, 每{request_interval}秒1个请求)...")
        
        results = []
        start_time = time.time()
        request_id = 0
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                try:
                    req_start = time.time()
                    async with session.post(f"{self.base_url}/analyze", json={
                        "content": f"持续测试 #{request_id}: 进度从60%更新为85%",
                        "analysis_type": "content_analysis",
                        "context": {"sustained_test": True}
                    }) as response:
                        result = await response.json()
                        response_time = time.time() - req_start
                        
                        results.append({
                            "timestamp": time.time(),
                            "success": response.status == 200,
                            "response_time": response_time,
                            "request_id": request_id
                        })
                        
                        request_id += 1
                        
                        # 等待间隔
                        elapsed = time.time() - req_start
                        if elapsed < request_interval:
                            await asyncio.sleep(request_interval - elapsed)
                            
                except Exception as e:
                    results.append({
                        "timestamp": time.time(),
                        "success": False,
                        "error": str(e),
                        "request_id": request_id
                    })
                    request_id += 1
                    await asyncio.sleep(request_interval)
        
        # 分析结果
        successful = [r for r in results if r["success"]]
        if successful:
            response_times = [r["response_time"] for r in successful]
            return {
                "duration_seconds": duration_seconds,
                "total_requests": len(results),
                "successful_requests": len(successful),
                "failed_requests": len(results) - len(successful),
                "success_rate": len(successful) / len(results) * 100,
                "avg_response_time": statistics.mean(response_times),
                "max_response_time": max(response_times),
                "min_response_time": min(response_times)
            }
        else:
            return {"error": "所有持续请求失败"}
    
    def get_system_stats(self) -> dict:
        """获取系统性能统计"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
            "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
    
    def calculate_performance_score(self, results: dict) -> dict:
        """计算性能评分"""
        score = {"response_score": 0, "stability_score": 0, "overall_score": 0}
        
        # 响应时间评分
        if "response_times" in results and results["response_times"].get("avg_response_time"):
            avg_time = results["response_times"]["avg_response_time"]
            if avg_time < 10:
                score["response_score"] = 100
            elif avg_time < 20:
                score["response_score"] = 80
            elif avg_time < 30:
                score["response_score"] = 60
            else:
                score["response_score"] = 40
        
        # 稳定性评分
        if "sustained_load" in results and results["sustained_load"].get("success_rate"):
            success_rate = results["sustained_load"]["success_rate"]
            if success_rate >= 95:
                score["stability_score"] = 100
            elif success_rate >= 90:
                score["stability_score"] = 80
            elif success_rate >= 80:
                score["stability_score"] = 60
            else:
                score["stability_score"] = 40
        
        # 综合评分
        score["overall_score"] = int((score["response_score"] + score["stability_score"]) / 2)
        return score
    
    async def run_quick_benchmark(self) -> dict:
        """运行快速基准测试"""
        print("🚀 开始快速性能基准测试")
        print("=" * 50)
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "Quick Performance Benchmark",
            "service": "Claude Mini Wrapper"
        }
        
        # 1. 基础响应时间测试
        print("\n1️⃣ 基础响应时间测试...")
        test_results["response_times"] = await self.test_response_times(concurrent_count=3)
        if "avg_response_time" in test_results["response_times"]:
            print(f"   平均响应时间: {test_results['response_times']['avg_response_time']:.2f}秒")
            print(f"   成功率: {test_results['response_times']['success_rate']:.1f}%")
        
        # 2. 轻量级并发测试
        print("\n2️⃣ 轻量级并发测试...")
        test_results["concurrent_test"] = await self.test_response_times(concurrent_count=5)
        if "avg_response_time" in test_results["concurrent_test"]:
            print(f"   5并发平均响应时间: {test_results['concurrent_test']['avg_response_time']:.2f}秒")
            print(f"   吞吐量: {test_results['concurrent_test']['throughput']:.2f} req/s")
        
        # 3. 持续负载测试
        print("\n3️⃣ 持续负载测试...")
        test_results["sustained_load"] = await self.test_sustained_load(duration_seconds=60, request_interval=20)
        if "success_rate" in test_results["sustained_load"]:
            print(f"   持续测试成功率: {test_results['sustained_load']['success_rate']:.1f}%")
            print(f"   持续测试平均响应时间: {test_results['sustained_load']['avg_response_time']:.2f}秒")
        
        # 4. 系统资源统计
        print("\n4️⃣ 系统资源统计...")
        test_results["system_stats"] = self.get_system_stats()
        print(f"   CPU使用率: {test_results['system_stats']['cpu_percent']:.1f}%")
        print(f"   内存使用率: {test_results['system_stats']['memory_percent']:.1f}%")
        print(f"   可用内存: {test_results['system_stats']['memory_available_mb']:.0f}MB")
        
        # 5. 性能评分
        test_results["performance_score"] = self.calculate_performance_score(test_results)
        
        print("\n" + "=" * 50)
        print("📊 快速基准测试完成!")
        print(f"   响应时间评分: {test_results['performance_score']['response_score']}/100")
        print(f"   稳定性评分: {test_results['performance_score']['stability_score']}/100")
        print(f"   综合性能评分: {test_results['performance_score']['overall_score']}/100")
        
        return test_results

async def main():
    """主函数"""
    benchmark = QuickPerformanceBenchmark()
    results = await benchmark.run_quick_benchmark()
    
    # 保存测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quick_benchmark_results_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 基准测试结果已保存到: {filename}")
    return results

if __name__ == "__main__":
    asyncio.run(main())