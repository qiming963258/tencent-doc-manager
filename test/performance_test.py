#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试工具 - 测试优化后的上传下载性能
对比原版本与优化版本的性能差异
"""

import asyncio
import time
import argparse
import logging
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from optimized_download import OptimizedTencentDownloader
from optimized_upload import OptimizedTencentUploader
from performance_monitor import get_performance_monitor, cleanup_performance_monitor


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    total_time: float
    success_count: int
    failed_count: int
    success_rate: float
    avg_duration_per_task: float
    throughput: float  # 任务/秒
    peak_memory_mb: float
    peak_cpu_percent: float


class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results: List[TestResult] = []
        
    async def test_download_performance(self, urls: List[str], cookies: str, 
                                      concurrent_levels: List[int] = [1, 2, 3]) -> List[TestResult]:
        """测试下载性能"""
        results = []
        
        for concurrent in concurrent_levels:
            print(f"\n=== 测试下载性能 (并发数: {concurrent}) ===")
            
            # 启动性能监控
            monitor = await get_performance_monitor()
            
            start_time = time.time()
            
            # 创建下载器
            downloader = OptimizedTencentDownloader(max_concurrent=concurrent)
            
            # 添加任务
            task_ids = []
            for i, url in enumerate(urls):
                task_id = await downloader.add_download_task(url, cookies, priority=i)
                task_ids.append(task_id)
            
            # 启动处理
            workers = await downloader.start_processing()
            
            try:
                # 等待完成
                await downloader.wait_for_completion(timeout=300)
                
                # 获取结果
                all_results = await downloader.get_all_results()
                stats = await downloader.get_stats()
                
                total_time = time.time() - start_time
                success_count = sum(1 for r in all_results.values() if r.success)
                failed_count = len(all_results) - success_count
                
                # 获取性能指标
                perf_summary = monitor.get_metrics_summary(int(total_time/60) + 1)
                
                result = TestResult(
                    test_name=f"Download_Concurrent_{concurrent}",
                    total_time=total_time,
                    success_count=success_count,
                    failed_count=failed_count,
                    success_rate=success_count / len(urls) * 100,
                    avg_duration_per_task=total_time / len(urls),
                    throughput=len(urls) / total_time,
                    peak_memory_mb=perf_summary.get('memory', {}).get('max_mb', 0),
                    peak_cpu_percent=perf_summary.get('cpu', {}).get('max', 0)
                )
                
                results.append(result)
                self.results.append(result)
                
                print(f"总时间: {total_time:.2f}s")
                print(f"成功率: {result.success_rate:.1f}%")
                print(f"吞吐量: {result.throughput:.2f} 文档/秒")
                print(f"峰值内存: {result.peak_memory_mb:.0f}MB")
                print(f"峰值CPU: {result.peak_cpu_percent:.1f}%")
                
            finally:
                # 清理工作进程
                for worker in workers:
                    worker.cancel()
                
                await asyncio.sleep(2)  # 等待清理完成
        
        return results
    
    async def test_upload_performance(self, files: List[str], cookies: str,
                                    concurrent_levels: List[int] = [1, 2]) -> List[TestResult]:
        """测试上传性能"""
        results = []
        
        for concurrent in concurrent_levels:
            print(f"\n=== 测试上传性能 (并发数: {concurrent}) ===")
            
            # 启动性能监控
            monitor = await get_performance_monitor()
            
            start_time = time.time()
            
            # 创建上传器
            uploader = OptimizedTencentUploader(max_concurrent=concurrent)
            
            # 添加任务
            task_ids = []
            for i, file_path in enumerate(files):
                if Path(file_path).exists():
                    task_id = await uploader.add_upload_task(file_path, cookies, priority=i)
                    task_ids.append(task_id)
                else:
                    print(f"警告: 文件不存在 {file_path}")
            
            if not task_ids:
                print("没有有效的上传文件")
                continue
            
            # 启动处理
            workers = await uploader.start_processing()
            
            try:
                # 等待完成
                await uploader.wait_for_completion(timeout=600)
                
                # 获取结果
                all_results = await uploader.get_all_results()
                stats = await uploader.get_stats()
                
                total_time = time.time() - start_time
                success_count = sum(1 for r in all_results.values() if r.success)
                failed_count = len(all_results) - success_count
                
                # 获取性能指标
                perf_summary = monitor.get_metrics_summary(int(total_time/60) + 1)
                
                result = TestResult(
                    test_name=f"Upload_Concurrent_{concurrent}",
                    total_time=total_time,
                    success_count=success_count,
                    failed_count=failed_count,
                    success_rate=success_count / len(task_ids) * 100,
                    avg_duration_per_task=total_time / len(task_ids),
                    throughput=len(task_ids) / total_time,
                    peak_memory_mb=perf_summary.get('memory', {}).get('max_mb', 0),
                    peak_cpu_percent=perf_summary.get('cpu', {}).get('max', 0)
                )
                
                results.append(result)
                self.results.append(result)
                
                print(f"总时间: {total_time:.2f}s")
                print(f"成功率: {result.success_rate:.1f}%")
                print(f"吞吐量: {result.throughput:.2f} 文件/秒")
                print(f"峰值内存: {result.peak_memory_mb:.0f}MB")
                print(f"峰值CPU: {result.peak_cpu_percent:.1f}%")
                
            finally:
                # 清理工作进程
                for worker in workers:
                    worker.cancel()
                
                await asyncio.sleep(2)  # 等待清理完成
        
        return results
    
    async def test_mixed_workload(self, urls: List[str], files: List[str], cookies: str) -> TestResult:
        """测试混合负载性能"""
        print(f"\n=== 测试混合负载性能 ===")
        
        monitor = await get_performance_monitor()
        start_time = time.time()
        
        # 同时启动下载和上传任务
        download_task = asyncio.create_task(
            self._run_download_batch(urls[:3], cookies, 2)
        )
        
        valid_files = [f for f in files if Path(f).exists()]
        upload_task = asyncio.create_task(
            self._run_upload_batch(valid_files[:2], cookies, 1)
        )
        
        try:
            download_results, upload_results = await asyncio.gather(
                download_task, upload_task, return_exceptions=True
            )
            
            total_time = time.time() - start_time
            
            # 计算综合结果
            total_tasks = len(urls[:3]) + len(valid_files[:2])
            download_success = len([r for r in download_results.values() if r.success]) if isinstance(download_results, dict) else 0
            upload_success = len([r for r in upload_results.values() if r.success]) if isinstance(upload_results, dict) else 0
            
            total_success = download_success + upload_success
            
            # 获取性能指标
            perf_summary = monitor.get_metrics_summary(int(total_time/60) + 1)
            
            result = TestResult(
                test_name="Mixed_Workload",
                total_time=total_time,
                success_count=total_success,
                failed_count=total_tasks - total_success,
                success_rate=total_success / total_tasks * 100 if total_tasks > 0 else 0,
                avg_duration_per_task=total_time / total_tasks if total_tasks > 0 else 0,
                throughput=total_tasks / total_time if total_time > 0 else 0,
                peak_memory_mb=perf_summary.get('memory', {}).get('max_mb', 0),
                peak_cpu_percent=perf_summary.get('cpu', {}).get('max', 0)
            )
            
            self.results.append(result)
            
            print(f"总时间: {total_time:.2f}s")
            print(f"成功率: {result.success_rate:.1f}%")
            print(f"吞吐量: {result.throughput:.2f} 任务/秒")
            print(f"峰值内存: {result.peak_memory_mb:.0f}MB")
            print(f"峰值CPU: {result.peak_cpu_percent:.1f}%")
            
            return result
            
        except Exception as e:
            print(f"混合负载测试异常: {e}")
            return None
    
    async def _run_download_batch(self, urls: List[str], cookies: str, concurrent: int):
        """运行下载批次"""
        downloader = OptimizedTencentDownloader(max_concurrent=concurrent)
        
        task_ids = []
        for url in urls:
            task_id = await downloader.add_download_task(url, cookies)
            task_ids.append(task_id)
        
        workers = await downloader.start_processing()
        
        try:
            await downloader.wait_for_completion()
            return await downloader.get_all_results()
        finally:
            for worker in workers:
                worker.cancel()
    
    async def _run_upload_batch(self, files: List[str], cookies: str, concurrent: int):
        """运行上传批次"""
        uploader = OptimizedTencentUploader(max_concurrent=concurrent)
        
        task_ids = []
        for file_path in files:
            task_id = await uploader.add_upload_task(file_path, cookies)
            task_ids.append(task_id)
        
        workers = await uploader.start_processing()
        
        try:
            await uploader.wait_for_completion()
            return await uploader.get_all_results()
        finally:
            for worker in workers:
                worker.cancel()
    
    def generate_report(self, output_file: str = None):
        """生成性能测试报告"""
        if not self.results:
            print("没有测试结果")
            return
        
        report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(self.results),
            "summary": self._generate_summary(),
            "detailed_results": [asdict(result) for result in self.results],
            "recommendations": self._generate_recommendations()
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n性能测试报告已保存到: {output_file}")
        
        # 打印摘要
        print("\n" + "="*60)
        print("性能测试报告摘要")
        print("="*60)
        
        for category, data in report["summary"].items():
            print(f"\n{category}:")
            for key, value in data.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        
        print("\n推荐优化措施:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")
        
        return report
    
    def _generate_summary(self) -> Dict:
        """生成测试摘要"""
        if not self.results:
            return {}
        
        download_results = [r for r in self.results if "Download" in r.test_name]
        upload_results = [r for r in self.results if "Upload" in r.test_name]
        mixed_results = [r for r in self.results if "Mixed" in r.test_name]
        
        summary = {}
        
        if download_results:
            summary["下载性能"] = {
                "最高吞吐量": max(r.throughput for r in download_results),
                "平均成功率": sum(r.success_rate for r in download_results) / len(download_results),
                "最低内存峰值": min(r.peak_memory_mb for r in download_results),
                "最高内存峰值": max(r.peak_memory_mb for r in download_results)
            }
        
        if upload_results:
            summary["上传性能"] = {
                "最高吞吐量": max(r.throughput for r in upload_results),
                "平均成功率": sum(r.success_rate for r in upload_results) / len(upload_results),
                "最低内存峰值": min(r.peak_memory_mb for r in upload_results),
                "最高内存峰值": max(r.peak_memory_mb for r in upload_results)
            }
        
        if mixed_results:
            summary["混合负载"] = {
                "吞吐量": mixed_results[0].throughput,
                "成功率": mixed_results[0].success_rate,
                "内存峰值": mixed_results[0].peak_memory_mb
            }
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if not self.results:
            return recommendations
        
        # 分析内存使用
        max_memory = max(r.peak_memory_mb for r in self.results)
        if max_memory > 1600:  # 超过1.6GB
            recommendations.append(f"内存峰值达到{max_memory:.0f}MB，建议优化内存使用或增加服务器内存")
        elif max_memory < 800:  # 小于800MB
            recommendations.append("内存使用效率良好，可以考虑增加并发数以提高吞吐量")
        
        # 分析CPU使用
        max_cpu = max(r.peak_cpu_percent for r in self.results)
        if max_cpu > 90:
            recommendations.append(f"CPU峰值达到{max_cpu:.1f}%，建议减少并发数或优化CPU使用")
        elif max_cpu < 60:
            recommendations.append("CPU使用率较低，可以考虑增加并发数")
        
        # 分析成功率
        avg_success_rate = sum(r.success_rate for r in self.results) / len(self.results)
        if avg_success_rate < 95:
            recommendations.append(f"平均成功率{avg_success_rate:.1f}%，建议检查网络连接和错误处理")
        
        # 分析吞吐量
        download_results = [r for r in self.results if "Download" in r.test_name]
        if download_results:
            best_concurrent = max(download_results, key=lambda x: x.throughput)
            recommendations.append(f"下载最优并发数为{best_concurrent.test_name.split('_')[-1]}，吞吐量{best_concurrent.throughput:.2f}文档/秒")
        
        return recommendations


async def main():
    """主测试函数"""
    parser = argparse.ArgumentParser(description='腾讯文档性能测试工具')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie')
    parser.add_argument('--urls', nargs='+', help='测试下载的URL列表')
    parser.add_argument('--files', nargs='+', help='测试上传的文件列表')
    parser.add_argument('--download-only', action='store_true', help='仅测试下载')
    parser.add_argument('--upload-only', action='store_true', help='仅测试上传')
    parser.add_argument('--mixed', action='store_true', help='测试混合负载')
    parser.add_argument('--output', default='performance_test_report.json', help='报告输出文件')
    parser.add_argument('--verbose', action='store_true', help='详细日志')
    
    args = parser.parse_args()
    
    # 配置日志
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 默认测试数据
    test_urls = args.urls or [
        "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=BB08J2",
        "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=g2hi7f",
        "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=kgc5ou"
    ]
    
    test_files = args.files or [
        "副本-出国销售知识技能.xlsx",
        "测试版本-小红书部门.xlsx"
    ]
    
    test_suite = PerformanceTestSuite()
    
    try:
        print("🚀 开始性能测试...")
        print(f"测试配置: 4H2G服务器环境模拟")
        print(f"Cookie: {'已设置' if args.cookies else '未设置'}")
        
        # 执行测试
        if not args.upload_only and not args.mixed:
            await test_suite.test_download_performance(test_urls, args.cookies)
        
        if not args.download_only and not args.mixed:
            await test_suite.test_upload_performance(test_files, args.cookies)
        
        if args.mixed or (not args.download_only and not args.upload_only):
            await test_suite.test_mixed_workload(test_urls, test_files, args.cookies)
        
        # 生成报告
        test_suite.generate_report(args.output)
        
    finally:
        # 清理监控器
        await cleanup_performance_monitor()


if __name__ == "__main__":
    asyncio.run(main())