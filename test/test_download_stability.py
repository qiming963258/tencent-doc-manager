#!/usr/bin/env python3
"""
腾讯文档下载功能稳定性测试程序
测试多个文档的CSV和XLSX格式下载，记录详细性能数据和失败原因分析
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import traceback
from pathlib import Path
import statistics

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

try:
    from stable_cookie_downloader import StableCookieDownloader
except ImportError as e:
    print(f"导入下载器失败: {e}")
    print("请确保 stable_cookie_downloader.py 存在且可访问")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/root/projects/tencent-doc-manager/download_test.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """单次下载测试结果"""
    document_name: str
    url: str
    export_format: str
    success: bool
    download_time: float
    file_size: int
    endpoint_used: str
    error_message: str
    timestamp: str
    doc_id: str
    retry_count: int = 0


@dataclass
class TestSummary:
    """测试总结报告"""
    total_tests: int
    successful_downloads: int
    failed_downloads: int
    success_rate: float
    average_download_time: float
    total_download_time: float
    total_file_size: int
    test_duration: float
    csv_success_rate: float
    xlsx_success_rate: float
    endpoint_performance: Dict
    failure_reasons: Dict
    recommendations: List[str]


class TencentDocDownloadTester:
    """腾讯文档下载稳定性测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.test_documents = [
            {
                'name': '测试版本-小红书部门',
                'url': 'https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN',
                'description': '小红书部门工作表'
            },
            {
                'name': '测试版本-回国销售计划表',
                'url': 'https://docs.qq.com/sheet/DRFppYm15RGZ2WExN',
                'description': '回国销售业务计划表'
            },
            {
                'name': '测试版本-出国销售计划表',
                'url': 'https://docs.qq.com/sheet/DRHZrS1hOS3pwRGZB',
                'description': '出国销售业务计划表'
            }
        ]
        
        self.export_formats = ['csv', 'xlsx']
        self.test_results: List[TestResult] = []
        self.cookie_file = '/root/projects/tencent-doc-manager/config/cookies_new.json'
        self.output_dir = '/root/projects/tencent-doc-manager/test_results'
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs('/root/projects/tencent-doc-manager/downloads', exist_ok=True)
        
        logger.info("🚀 腾讯文档下载稳定性测试器已初始化")
        logger.info(f"测试文档数量: {len(self.test_documents)}")
        logger.info(f"测试格式: {', '.join(self.export_formats)}")
        logger.info(f"总测试数: {len(self.test_documents) * len(self.export_formats)}")
    
    def validate_cookie_config(self) -> bool:
        """验证Cookie配置"""
        try:
            if not os.path.exists(self.cookie_file):
                logger.error(f"❌ Cookie配置文件不存在: {self.cookie_file}")
                return False
            
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not config.get('current_cookies'):
                logger.error("❌ Cookie配置中没有current_cookies")
                return False
            
            if not config.get('is_valid', False):
                logger.warning("⚠️  Cookie配置标记为无效，但继续测试")
            
            logger.info("✅ Cookie配置验证通过")
            logger.info(f"Cookie更新时间: {config.get('last_update', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cookie配置验证失败: {e}")
            return False
    
    def run_single_test(self, document: Dict, export_format: str, 
                       downloader: StableCookieDownloader, retry_count: int = 0) -> TestResult:
        """执行单个下载测试"""
        start_time = time.time()
        
        logger.info(f"📥 测试下载: {document['name']} (格式: {export_format})")
        
        try:
            # 执行下载
            result = downloader.download_document(
                url=document['url'],
                export_type=export_format,
                save_dir='/root/projects/tencent-doc-manager/downloads'
            )
            
            download_time = time.time() - start_time
            
            if result.get('success', False):
                # 成功下载
                file_size = result.get('file_size', 0)
                logger.info(f"✅ 下载成功: {file_size/1024:.1f} KB, {download_time:.2f}秒")
                
                return TestResult(
                    document_name=document['name'],
                    url=document['url'],
                    export_format=export_format,
                    success=True,
                    download_time=download_time,
                    file_size=file_size,
                    endpoint_used=result.get('endpoint_used', 'unknown'),
                    error_message='',
                    timestamp=datetime.now().isoformat(),
                    doc_id=result.get('doc_id', ''),
                    retry_count=retry_count
                )
            else:
                # 下载失败
                error_msg = result.get('error', '未知错误')
                logger.error(f"❌ 下载失败: {error_msg}")
                
                return TestResult(
                    document_name=document['name'],
                    url=document['url'],
                    export_format=export_format,
                    success=False,
                    download_time=download_time,
                    file_size=0,
                    endpoint_used=result.get('endpoint_used', 'none'),
                    error_message=error_msg,
                    timestamp=datetime.now().isoformat(),
                    doc_id=result.get('doc_id', ''),
                    retry_count=retry_count
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            error_msg = f"测试异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.debug(traceback.format_exc())
            
            return TestResult(
                document_name=document['name'],
                url=document['url'],
                export_format=export_format,
                success=False,
                download_time=download_time,
                file_size=0,
                endpoint_used='error',
                error_message=error_msg,
                timestamp=datetime.now().isoformat(),
                doc_id='',
                retry_count=retry_count
            )
    
    def run_comprehensive_test(self, retry_failed: bool = True, max_retries: int = 2) -> List[TestResult]:
        """执行全面下载测试"""
        logger.info("🔍 开始全面下载测试...")
        test_start_time = time.time()
        
        # 验证Cookie
        if not self.validate_cookie_config():
            logger.error("Cookie配置无效，测试中止")
            return []
        
        # 初始化下载器
        downloader = StableCookieDownloader(cookie_file=self.cookie_file)
        results = []
        
        # 执行主要测试
        total_tests = len(self.test_documents) * len(self.export_formats)
        current_test = 0
        
        for document in self.test_documents:
            for export_format in self.export_formats:
                current_test += 1
                logger.info(f"[{current_test}/{total_tests}] 测试进行中...")
                
                # 执行测试
                result = self.run_single_test(document, export_format, downloader)
                results.append(result)
                
                # 测试间隔
                time.sleep(3)
        
        # 重试失败的测试
        if retry_failed and max_retries > 0:
            failed_results = [r for r in results if not r.success]
            if failed_results:
                logger.info(f"🔄 重试 {len(failed_results)} 个失败的测试...")
                
                for failed_result in failed_results:
                    for retry in range(max_retries):
                        logger.info(f"重试 {retry + 1}/{max_retries}: {failed_result.document_name}")
                        
                        # 找到对应的文档
                        doc = next(d for d in self.test_documents 
                                 if d['name'] == failed_result.document_name)
                        
                        retry_result = self.run_single_test(
                            doc, failed_result.export_format, downloader, retry + 1
                        )
                        results.append(retry_result)
                        
                        if retry_result.success:
                            logger.info("✅ 重试成功")
                            break
                        
                        time.sleep(5)  # 重试间隔更长
        
        test_duration = time.time() - test_start_time
        logger.info(f"🏁 测试完成，总耗时: {test_duration:.1f}秒")
        
        self.test_results = results
        return results
    
    def analyze_results(self, results: List[TestResult]) -> TestSummary:
        """分析测试结果"""
        logger.info("📊 分析测试结果...")
        
        if not results:
            logger.warning("没有测试结果可分析")
            return TestSummary(
                total_tests=0, successful_downloads=0, failed_downloads=0,
                success_rate=0.0, average_download_time=0.0, total_download_time=0.0,
                total_file_size=0, test_duration=0.0, csv_success_rate=0.0,
                xlsx_success_rate=0.0, endpoint_performance={},
                failure_reasons={}, recommendations=[]
            )
        
        # 基础统计
        total_tests = len(results)
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        successful_count = len(successful)
        failed_count = len(failed)
        success_rate = successful_count / total_tests * 100
        
        # 时间统计
        total_download_time = sum(r.download_time for r in results)
        avg_download_time = statistics.mean([r.download_time for r in results]) if results else 0
        
        # 文件大小统计
        total_file_size = sum(r.file_size for r in successful)
        
        # 按格式统计
        csv_results = [r for r in results if r.export_format == 'csv']
        xlsx_results = [r for r in results if r.export_format == 'xlsx']
        
        csv_success_rate = len([r for r in csv_results if r.success]) / len(csv_results) * 100 if csv_results else 0
        xlsx_success_rate = len([r for r in xlsx_results if r.success]) / len(xlsx_results) * 100 if xlsx_results else 0
        
        # 端点性能统计
        endpoint_stats = {}
        for result in successful:
            endpoint = result.endpoint_used
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {'count': 0, 'total_time': 0, 'avg_time': 0}
            endpoint_stats[endpoint]['count'] += 1
            endpoint_stats[endpoint]['total_time'] += result.download_time
        
        for endpoint in endpoint_stats:
            stats = endpoint_stats[endpoint]
            stats['avg_time'] = stats['total_time'] / stats['count']
        
        # 失败原因统计
        failure_reasons = {}
        for result in failed:
            reason = result.error_message
            if reason not in failure_reasons:
                failure_reasons[reason] = 0
            failure_reasons[reason] += 1
        
        # 生成建议
        recommendations = []
        
        if success_rate < 80:
            recommendations.append("成功率较低，建议检查Cookie有效性和网络连接")
        
        if csv_success_rate > xlsx_success_rate + 20:
            recommendations.append("XLSX下载失败率较高，建议优先使用CSV格式")
        
        if avg_download_time > 10:
            recommendations.append("平均下载时间较长，建议优化网络环境或使用CDN")
        
        if len(failure_reasons) > 0:
            recommendations.append("存在下载失败，建议分析失败原因并优化重试机制")
        
        if not endpoint_stats:
            recommendations.append("没有端点使用统计，可能所有请求都失败了")
        
        return TestSummary(
            total_tests=total_tests,
            successful_downloads=successful_count,
            failed_downloads=failed_count,
            success_rate=success_rate,
            average_download_time=avg_download_time,
            total_download_time=total_download_time,
            total_file_size=total_file_size,
            test_duration=total_download_time,
            csv_success_rate=csv_success_rate,
            xlsx_success_rate=xlsx_success_rate,
            endpoint_performance=endpoint_stats,
            failure_reasons=failure_reasons,
            recommendations=recommendations
        )
    
    def generate_report(self, results: List[TestResult], summary: TestSummary) -> str:
        """生成详细测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.output_dir, f'download_stability_report_{timestamp}.json')
        
        # 构建报告数据
        report_data = {
            'test_metadata': {
                'test_time': datetime.now().isoformat(),
                'test_type': 'Download Stability Test',
                'tester_version': '1.0.0',
                'cookie_file': self.cookie_file,
                'documents_tested': len(self.test_documents),
                'formats_tested': self.export_formats
            },
            'summary': asdict(summary),
            'detailed_results': [asdict(r) for r in results],
            'document_performance': self._analyze_document_performance(results),
            'format_performance': self._analyze_format_performance(results),
            'time_series_analysis': self._analyze_time_series(results)
        }
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 详细报告已保存: {report_file}")
        
        return report_file
    
    def _analyze_document_performance(self, results: List[TestResult]) -> Dict:
        """分析各文档的下载性能"""
        doc_stats = {}
        
        for doc in self.test_documents:
            doc_results = [r for r in results if r.document_name == doc['name']]
            successful = [r for r in doc_results if r.success]
            
            doc_stats[doc['name']] = {
                'total_attempts': len(doc_results),
                'successful_downloads': len(successful),
                'success_rate': len(successful) / len(doc_results) * 100 if doc_results else 0,
                'avg_download_time': statistics.mean([r.download_time for r in successful]) if successful else 0,
                'total_file_size': sum(r.file_size for r in successful),
                'formats_tested': list(set(r.export_format for r in doc_results))
            }
        
        return doc_stats
    
    def _analyze_format_performance(self, results: List[TestResult]) -> Dict:
        """分析各格式的下载性能"""
        format_stats = {}
        
        for fmt in self.export_formats:
            fmt_results = [r for r in results if r.export_format == fmt]
            successful = [r for r in fmt_results if r.success]
            
            format_stats[fmt] = {
                'total_attempts': len(fmt_results),
                'successful_downloads': len(successful),
                'success_rate': len(successful) / len(fmt_results) * 100 if fmt_results else 0,
                'avg_download_time': statistics.mean([r.download_time for r in successful]) if successful else 0,
                'avg_file_size': statistics.mean([r.file_size for r in successful]) if successful else 0,
                'total_file_size': sum(r.file_size for r in successful)
            }
        
        return format_stats
    
    def _analyze_time_series(self, results: List[TestResult]) -> Dict:
        """分析时间序列性能"""
        if not results:
            return {}
        
        # 按时间排序
        sorted_results = sorted(results, key=lambda r: r.timestamp)
        
        # 计算性能趋势
        download_times = [r.download_time for r in sorted_results if r.success]
        
        return {
            'test_start_time': sorted_results[0].timestamp,
            'test_end_time': sorted_results[-1].timestamp,
            'performance_trend': {
                'min_download_time': min(download_times) if download_times else 0,
                'max_download_time': max(download_times) if download_times else 0,
                'median_download_time': statistics.median(download_times) if download_times else 0
            }
        }
    
    def print_console_summary(self, summary: TestSummary):
        """在控制台打印测试摘要"""
        print("\n" + "="*60)
        print("🏁 腾讯文档下载稳定性测试报告")
        print("="*60)
        
        print(f"📊 总体统计:")
        print(f"   总测试数: {summary.total_tests}")
        print(f"   成功下载: {summary.successful_downloads}")
        print(f"   失败下载: {summary.failed_downloads}")
        print(f"   成功率: {summary.success_rate:.1f}%")
        
        print(f"\n⏱️  性能指标:")
        print(f"   平均下载时间: {summary.average_download_time:.2f}秒")
        print(f"   总下载时间: {summary.total_download_time:.1f}秒")
        print(f"   总文件大小: {summary.total_file_size/1024:.1f} KB")
        
        print(f"\n📁 格式性能:")
        print(f"   CSV成功率: {summary.csv_success_rate:.1f}%")
        print(f"   XLSX成功率: {summary.xlsx_success_rate:.1f}%")
        
        if summary.endpoint_performance:
            print(f"\n🌐 端点性能:")
            for endpoint, stats in summary.endpoint_performance.items():
                print(f"   {endpoint}: {stats['count']}次 (平均{stats['avg_time']:.2f}秒)")
        
        if summary.failure_reasons:
            print(f"\n❌ 失败原因:")
            for reason, count in summary.failure_reasons.items():
                print(f"   {reason}: {count}次")
        
        if summary.recommendations:
            print(f"\n💡 优化建议:")
            for i, rec in enumerate(summary.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("="*60)


def main():
    """主函数"""
    print("🚀 启动腾讯文档下载稳定性测试...")
    
    try:
        # 创建测试器
        tester = TencentDocDownloadTester()
        
        # 执行测试
        results = tester.run_comprehensive_test(retry_failed=True, max_retries=2)
        
        if not results:
            print("❌ 没有测试结果")
            return
        
        # 分析结果
        summary = tester.analyze_results(results)
        
        # 生成报告
        report_file = tester.generate_report(results, summary)
        
        # 打印控制台摘要
        tester.print_console_summary(summary)
        
        # 保存简化摘要
        summary_file = os.path.join(tester.output_dir, f'test_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(summary), f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 详细报告: {report_file}")
        print(f"📋 摘要报告: {summary_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        logger.error(f"测试执行错误: {e}")
        logger.debug(traceback.format_exc())
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()