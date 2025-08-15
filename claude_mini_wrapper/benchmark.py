import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json
from datetime import datetime
import psutil
import threading

class PerformanceBenchmark:
    """Claude封装服务性能基准测试"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.results = {}
        
    async def benchmark_response_time(self, concurrent_levels: List[int] = [1, 5, 10]) -> Dict[str, Any]:
        """响应时间基准测试"""
        print("📊 运行响应时间基准测试...")
        
        results = {}
        
        for concurrency in concurrent_levels:
            print(f"   测试并发级别: {concurrency}")
            
            async with aiohttp.ClientSession() as session:
                # 创建测试任务
                tasks = []
                for i in range(concurrency):
                    task = self._single_analyze_request(session, i)
                    tasks.append(task)
                
                # 执行并发请求
                start_time = time.time()
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # 分析结果
                successful_responses = [r for r in responses if not isinstance(r, Exception)]
                failed_responses = [r for r in responses if isinstance(r, Exception)]
                
                if successful_responses:
                    response_times = [r["response_time"] for r in successful_responses]
                    
                    results[f"concurrent_{concurrency}"] = {
                        "total_requests": concurrency,
                        "successful_requests": len(successful_responses),
                        "failed_requests": len(failed_responses),
                        "total_time": total_time,
                        "avg_response_time": statistics.mean(response_times),
                        "median_response_time": statistics.median(response_times),
                        "min_response_time": min(response_times),
                        "max_response_time": max(response_times),
                        "p95_response_time": self._percentile(response_times, 95),
                        "p99_response_time": self._percentile(response_times, 99),
                        "throughput": len(successful_responses) / total_time,
                        "success_rate": len(successful_responses) / concurrency * 100
                    }
                    
                    print(f"     成功: {len(successful_responses)}/{concurrency}")
                    print(f"     平均响应时间: {results[f'concurrent_{concurrency}']['avg_response_time']:.2f}s")
                    print(f"     吞吐量: {results[f'concurrent_{concurrency}']['throughput']:.2f} req/s")
                else:
                    print(f"     ❌ 所有请求失败")
        
        return results
    
    async def _single_analyze_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """单个分析请求"""
        try:
            start_time = time.time()
            async with session.post(f"{self.base_url}/analyze", json={
                "content": f"测试分析请求 #{request_id}: 负责人从张三改为李四",
                "analysis_type": "risk_assessment",
                "context": {"request_id": request_id}
            }) as response:
                result = await response.json()
                response_time = time.time() - start_time
                
                return {
                    "request_id": request_id,
                    "success": response.status == 200,
                    "response_time": response_time,
                    "status_code": response.status,
                    "result": result
                }
        except Exception as e:
            return {
                "request_id": request_id,
                "success": False,
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def benchmark_sustained_load(self, duration_minutes: int = 5, requests_per_second: int = 2) -> Dict[str, Any]:
        """持续负载测试"""
        print(f"⏱️ 运行持续负载测试 ({duration_minutes}分钟, {requests_per_second} req/s)...")
        
        duration_seconds = duration_minutes * 60
        interval = 1.0 / requests_per_second
        
        results = {
            "duration_seconds": duration_seconds,
            "target_rps": requests_per_second,
            "requests": [],
            "system_metrics": []
        }
        
        # 启动系统监控
        system_monitor = SystemMonitor()
        monitor_thread = threading.Thread(target=system_monitor.start_monitoring, args=(duration_seconds,))
        monitor_thread.start()
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            request_id = 0
            
            while time.time() - start_time < duration_seconds:
                # 发送请求
                task_start = time.time()
                result = await self._single_analyze_request(session, request_id)
                results["requests"].append({
                    "timestamp": time.time(),
                    "request_id": request_id,
                    "success": result["success"],
                    "response_time": result["response_time"]
                })
                
                request_id += 1
                
                # 控制请求频率
                elapsed = time.time() - task_start
                if elapsed < interval:
                    await asyncio.sleep(interval - elapsed)
        
        # 等待系统监控结束
        monitor_thread.join()
        results["system_metrics"] = system_monitor.get_metrics()
        
        # 分析结果
        successful_requests = [r for r in results["requests"] if r["success"]]
        failed_requests = [r for r in results["requests"] if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            
            results["summary"] = {
                "total_requests": len(results["requests"]),
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": len(successful_requests) / len(results["requests"]) * 100,
                "actual_rps": len(results["requests"]) / duration_seconds,
                "avg_response_time": statistics.mean(response_times),
                "max_response_time": max(response_times),
                "min_response_time": min(response_times),
                "p95_response_time": self._percentile(response_times, 95)
            }
            
            print(f"   总请求数: {results['summary']['total_requests']}")
            print(f"   成功率: {results['summary']['success_rate']:.1f}%")
            print(f"   实际RPS: {results['summary']['actual_rps']:.2f}")
            print(f"   平均响应时间: {results['summary']['avg_response_time']:.2f}s")
        
        return results
    
    async def benchmark_memory_usage(self, request_count: int = 100) -> Dict[str, Any]:
        """内存使用基准测试"""
        print(f"💾 运行内存使用测试 ({request_count}个请求)...")
        
        # 获取初始内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_snapshots = [initial_memory]
        
        async with aiohttp.ClientSession() as session:
            for i in range(request_count):
                await self._single_analyze_request(session, i)
                
                # 每10个请求记录一次内存使用
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_snapshots.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        results = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": final_memory - initial_memory,
            "max_memory_mb": max(memory_snapshots),
            "avg_memory_mb": statistics.mean(memory_snapshots),
            "memory_snapshots": memory_snapshots
        }
        
        print(f"   初始内存: {initial_memory:.2f} MB")
        print(f"   最终内存: {final_memory:.2f} MB")
        print(f"   内存增长: {results['memory_increase_mb']:.2f} MB")
        print(f"   峰值内存: {results['max_memory_mb']:.2f} MB")
        
        return results
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整的性能基准测试"""
        print("🚀 开始运行Claude封装服务完整性能基准测试")
        print("=" * 70)
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "Claude Mini Wrapper Performance Benchmark",
            "version": "1.0.0"
        }
        
        # 响应时间测试
        benchmark_results["response_time"] = await self.benchmark_response_time()
        
        # 持续负载测试
        benchmark_results["sustained_load"] = await self.benchmark_sustained_load(duration_minutes=1, requests_per_second=2)
        
        # 内存使用测试
        benchmark_results["memory_usage"] = await self.benchmark_memory_usage(request_count=20)
        
        # 生成综合评分
        benchmark_results["performance_score"] = self._calculate_performance_score(benchmark_results)
        
        print("\n" + "=" * 70)
        print("📊 性能基准测试完成!")
        print(f"   综合性能评分: {benchmark_results['performance_score']['overall_score']}/100")
        print(f"   响应时间评分: {benchmark_results['performance_score']['response_time_score']}/100")
        print(f"   稳定性评分: {benchmark_results['performance_score']['stability_score']}/100")
        print(f"   资源使用评分: {benchmark_results['performance_score']['resource_score']}/100")
        
        return benchmark_results
    
    def _calculate_performance_score(self, results: Dict[str, Any]) -> Dict[str, int]:
        """计算性能评分"""
        scores = {}
        
        # 响应时间评分 (越低越好)
        if "concurrent_10" in results["response_time"]:
            avg_response = results["response_time"]["concurrent_10"]["avg_response_time"]
            if avg_response < 1.0:
                scores["response_time_score"] = 100
            elif avg_response < 2.0:
                scores["response_time_score"] = 80
            elif avg_response < 3.0:
                scores["response_time_score"] = 60
            else:
                scores["response_time_score"] = 40
        else:
            scores["response_time_score"] = 0
        
        # 稳定性评分 (成功率)
        if "summary" in results["sustained_load"]:
            success_rate = results["sustained_load"]["summary"]["success_rate"]
            if success_rate >= 99:
                scores["stability_score"] = 100
            elif success_rate >= 95:
                scores["stability_score"] = 80
            elif success_rate >= 90:
                scores["stability_score"] = 60
            else:
                scores["stability_score"] = 40
        else:
            scores["stability_score"] = 0
        
        # 资源使用评分 (内存增长越少越好)
        memory_increase = results["memory_usage"]["memory_increase_mb"]
        if memory_increase < 10:
            scores["resource_score"] = 100
        elif memory_increase < 50:
            scores["resource_score"] = 80
        elif memory_increase < 100:
            scores["resource_score"] = 60
        else:
            scores["resource_score"] = 40
        
        # 综合评分
        scores["overall_score"] = int(
            (scores["response_time_score"] + scores["stability_score"] + scores["resource_score"]) / 3
        )
        
        return scores

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.metrics = []
        self.monitoring = False
    
    def start_monitoring(self, duration_seconds: int):
        """开始系统监控"""
        self.monitoring = True
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < duration_seconds:
            self.metrics.append({
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024
            })
            time.sleep(1)
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """获取监控指标"""
        self.monitoring = False
        return self.metrics

async def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_full_benchmark()
    
    # 保存基准测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"📄 基准测试结果已保存到: {filename}")

if __name__ == "__main__":
    asyncio.run(main())