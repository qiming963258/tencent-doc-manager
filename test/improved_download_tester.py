#!/usr/bin/env python3
"""
基于诊断结果改进的腾讯文档下载测试程序
使用发现的有效端点进行实际下载测试
"""

import os
import sys
import time
import json
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging
from urllib.parse import urlencode, parse_qs, urlparse
from bs4 import BeautifulSoup
import statistics

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    """下载结果"""
    document_name: str
    doc_id: str
    export_format: str
    success: bool
    download_time: float
    file_size: int
    file_path: str
    endpoint_used: str
    error_message: str
    timestamp: str
    actual_download_url: str = ""
    response_status: int = 0


class ImprovedTencentDownloader:
    """改进版腾讯文档下载器"""
    
    def __init__(self, cookie_file: str = None):
        self.cookie_file = cookie_file or '/root/projects/tencent-doc-manager/config/cookies_new.json'
        self.cookies = self._load_cookies()
        self.output_dir = '/root/projects/tencent-doc-manager/downloads'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 基于诊断结果的有效端点
        self.working_endpoints = [
            {
                'name': 'direct_sheet_export',
                'url_template': 'https://docs.qq.com/sheet/{doc_id}/export',
                'params': {
                    'format': '{format}',
                    'download': '1'
                },
                'method': 'GET',
                'needs_parsing': True  # 需要解析HTML页面获取真实下载链接
            },
            {
                'name': 'sheet_with_export_param',
                'url_template': 'https://docs.qq.com/sheet/{doc_id}',
                'params': {
                    'export': '{format}',
                    'download': '1'
                },
                'method': 'GET',
                'needs_parsing': True
            }
        ]
        
        # 测试文档
        self.test_documents = [
            {
                'name': '测试版本-小红书部门',
                'url': 'https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN',
                'doc_id': 'DWEVjZndkR2xVSWJN'
            },
            {
                'name': '测试版本-回国销售计划表',
                'url': 'https://docs.qq.com/sheet/DRFppYm15RGZ2WExN',
                'doc_id': 'DRFppYm15RGZ2WExN'
            },
            {
                'name': '测试版本-出国销售计划表',
                'url': 'https://docs.qq.com/sheet/DRHZrS1hOS3pwRGZB',
                'doc_id': 'DRHZrS1hOS3pwRGZB'
            }
        ]
        
        self.export_formats = ['csv', 'xlsx']
        self.results: List[DownloadResult] = []
        
    def _load_cookies(self) -> str:
        """加载Cookie"""
        try:
            with open(self.cookie_file, 'r') as f:
                config = json.load(f)
            return config.get('current_cookies', '')
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return ""
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            'Cookie': self.cookies,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0'
        }
    
    def _extract_download_url(self, html_content: str) -> Optional[str]:
        """从HTML页面中提取真实下载URL"""
        try:
            # 方法1: 查找dop-api链接
            dop_api_pattern = r'//docs\.qq\.com/dop-api/opendoc\?[^"]*'
            match = re.search(dop_api_pattern, html_content)
            if match:
                url = 'https:' + match.group(0).replace('&amp;', '&')
                logger.info(f"找到dop-api下载链接: {url}")
                return url
                
            # 方法2: 查找preload链接
            preload_pattern = r'rel="preload"[^>]*href="([^"]*dop-api[^"]*)"'
            match = re.search(preload_pattern, html_content)
            if match:
                url = match.group(1).replace('&amp;', '&')
                if not url.startswith('http'):
                    url = 'https:' + url
                logger.info(f"找到preload下载链接: {url}")
                return url
                
            # 方法3: 使用BeautifulSoup解析
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找包含dop-api的link标签
            link_tags = soup.find_all('link', href=True)
            for link in link_tags:
                href = link.get('href', '')
                if 'dop-api/opendoc' in href:
                    url = href.replace('&amp;', '&')
                    if not url.startswith('http'):
                        url = 'https:' + url
                    logger.info(f"通过BeautifulSoup找到下载链接: {url}")
                    return url
                    
            # 查找script中的下载链接
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    dop_match = re.search(r'dop-api/opendoc\?[^"\']*', script.string)
                    if dop_match:
                        url = 'https://docs.qq.com/' + dop_match.group(0)
                        logger.info(f"在script中找到下载链接: {url}")
                        return url
                        
        except Exception as e:
            logger.error(f"解析下载URL失败: {e}")
            
        return None
    
    def _download_file(self, download_url: str, filename: str) -> Tuple[bool, int, str]:
        """下载文件"""
        try:
            headers = self._build_headers()
            # 修改Accept头以期望文件下载
            headers['Accept'] = 'application/octet-stream,*/*;q=0.8'
            
            logger.info(f"开始下载文件: {download_url}")
            
            response = requests.get(
                download_url,
                headers=headers,
                stream=True,
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                return False, 0, f"HTTP {response.status_code}"
            
            # 检查内容类型
            content_type = response.headers.get('Content-Type', '').lower()
            logger.info(f"响应内容类型: {content_type}")
            
            # 保存文件
            filepath = os.path.join(self.output_dir, filename)
            file_size = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        file_size += len(chunk)
            
            # 检查文件大小
            actual_size = os.path.getsize(filepath)
            if actual_size < 100:
                # 文件太小，可能是错误页面，检查内容
                with open(filepath, 'rb') as f:
                    content = f.read(500)
                    if b'<html' in content.lower() or b'error' in content.lower():
                        logger.warning(f"下载的文件似乎是HTML错误页面")
                        os.remove(filepath)
                        return False, 0, "下载的文件是HTML错误页面"
            
            logger.info(f"文件下载成功: {filepath} ({actual_size} bytes)")
            return True, actual_size, filepath
            
        except Exception as e:
            logger.error(f"下载文件时出错: {e}")
            return False, 0, str(e)
    
    def _attempt_download(self, document: Dict, export_format: str, endpoint: Dict) -> DownloadResult:
        """尝试使用指定端点下载文档"""
        start_time = time.time()
        doc_id = document['doc_id']
        
        try:
            # 构建URL和参数
            url = endpoint['url_template'].format(doc_id=doc_id)
            params = {}
            for key, value in endpoint['params'].items():
                params[key] = value.format(format=export_format, doc_id=doc_id)
            
            logger.info(f"🔄 尝试端点: {endpoint['name']}")
            logger.info(f"   URL: {url}")
            logger.info(f"   参数: {params}")
            
            # 第一步: 获取包含下载链接的页面
            headers = self._build_headers()
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                error_msg = f"获取下载页面失败: HTTP {response.status_code}"
                logger.error(error_msg)
                return self._create_failed_result(document, export_format, endpoint, error_msg, start_time)
            
            # 第二步: 从HTML中提取真实下载URL
            if endpoint['needs_parsing']:
                download_url = self._extract_download_url(response.text)
                if not download_url:
                    error_msg = "无法从页面中提取下载链接"
                    logger.error(error_msg)
                    return self._create_failed_result(document, export_format, endpoint, error_msg, start_time)
            else:
                download_url = url + '?' + urlencode(params)
            
            # 第三步: 实际下载文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{document['name']}_{export_format}_{timestamp}.{export_format}"
            
            success, file_size, result_info = self._download_file(download_url, filename)
            
            download_time = time.time() - start_time
            
            if success:
                logger.info(f"✅ 下载成功: {filename} ({file_size/1024:.1f} KB, {download_time:.2f}s)")
                return DownloadResult(
                    document_name=document['name'],
                    doc_id=doc_id,
                    export_format=export_format,
                    success=True,
                    download_time=download_time,
                    file_size=file_size,
                    file_path=result_info,
                    endpoint_used=endpoint['name'],
                    error_message="",
                    timestamp=datetime.now().isoformat(),
                    actual_download_url=download_url,
                    response_status=200
                )
            else:
                logger.error(f"❌ 下载失败: {result_info}")
                return self._create_failed_result(document, export_format, endpoint, result_info, start_time, download_url)
                
        except Exception as e:
            error_msg = f"下载异常: {str(e)}"
            logger.error(error_msg)
            return self._create_failed_result(document, export_format, endpoint, error_msg, start_time)
    
    def _create_failed_result(self, document: Dict, export_format: str, endpoint: Dict, 
                             error_msg: str, start_time: float, download_url: str = "") -> DownloadResult:
        """创建失败结果"""
        return DownloadResult(
            document_name=document['name'],
            doc_id=document['doc_id'],
            export_format=export_format,
            success=False,
            download_time=time.time() - start_time,
            file_size=0,
            file_path="",
            endpoint_used=endpoint['name'],
            error_message=error_msg,
            timestamp=datetime.now().isoformat(),
            actual_download_url=download_url,
            response_status=0
        )
    
    def run_comprehensive_test(self) -> List[DownloadResult]:
        """运行全面下载测试"""
        logger.info("🚀 开始改进版腾讯文档下载测试...")
        
        if not self.cookies:
            logger.error("❌ Cookie无效，无法进行测试")
            return []
        
        results = []
        total_tests = len(self.test_documents) * len(self.export_formats)
        current_test = 0
        
        for document in self.test_documents:
            for export_format in self.export_formats:
                current_test += 1
                logger.info(f"\n[{current_test}/{total_tests}] 测试: {document['name']} ({export_format})")
                
                # 尝试所有可用端点直到成功
                success = False
                for endpoint in self.working_endpoints:
                    if success:
                        break
                        
                    result = self._attempt_download(document, export_format, endpoint)
                    results.append(result)
                    
                    if result.success:
                        success = True
                        logger.info(f"✅ 使用端点 {endpoint['name']} 下载成功")
                    else:
                        logger.warning(f"❌ 端点 {endpoint['name']} 失败: {result.error_message}")
                        time.sleep(2)  # 失败后等待
                
                if not success:
                    logger.error(f"❌ 所有端点都失败: {document['name']} ({export_format})")
                
                time.sleep(3)  # 测试间隔
        
        self.results = results
        logger.info(f"\n🏁 测试完成，共 {len(results)} 个结果")
        return results
    
    def analyze_results(self, results: List[DownloadResult]) -> Dict:
        """分析测试结果"""
        if not results:
            return {}
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # 基础统计
        analysis = {
            'test_summary': {
                'total_tests': len(results),
                'successful_downloads': len(successful),
                'failed_downloads': len(failed),
                'success_rate': len(successful) / len(results) * 100 if results else 0
            },
            'performance_metrics': {
                'average_download_time': statistics.mean([r.download_time for r in successful]) if successful else 0,
                'total_download_time': sum(r.download_time for r in results),
                'total_file_size': sum(r.file_size for r in successful),
                'average_file_size': statistics.mean([r.file_size for r in successful]) if successful else 0
            },
            'format_performance': {},
            'endpoint_performance': {},
            'document_performance': {},
            'failure_analysis': {},
            'recommendations': []
        }
        
        # 按格式分析
        for fmt in self.export_formats:
            fmt_results = [r for r in results if r.export_format == fmt]
            fmt_success = [r for r in fmt_results if r.success]
            analysis['format_performance'][fmt] = {
                'total_attempts': len(fmt_results),
                'successful': len(fmt_success),
                'success_rate': len(fmt_success) / len(fmt_results) * 100 if fmt_results else 0,
                'avg_download_time': statistics.mean([r.download_time for r in fmt_success]) if fmt_success else 0,
                'avg_file_size': statistics.mean([r.file_size for r in fmt_success]) if fmt_success else 0
            }
        
        # 按端点分析
        endpoint_stats = {}
        for result in successful:
            endpoint = result.endpoint_used
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {'successes': 0, 'total_time': 0, 'total_size': 0}
            endpoint_stats[endpoint]['successes'] += 1
            endpoint_stats[endpoint]['total_time'] += result.download_time
            endpoint_stats[endpoint]['total_size'] += result.file_size
        
        for endpoint, stats in endpoint_stats.items():
            analysis['endpoint_performance'][endpoint] = {
                'success_count': stats['successes'],
                'avg_download_time': stats['total_time'] / stats['successes'],
                'avg_file_size': stats['total_size'] / stats['successes']
            }
        
        # 按文档分析
        for doc in self.test_documents:
            doc_results = [r for r in results if r.document_name == doc['name']]
            doc_success = [r for r in doc_results if r.success]
            analysis['document_performance'][doc['name']] = {
                'total_attempts': len(doc_results),
                'successful': len(doc_success),
                'success_rate': len(doc_success) / len(doc_results) * 100 if doc_results else 0,
                'formats_tested': len(set(r.export_format for r in doc_results))
            }
        
        # 失败原因分析
        for result in failed:
            reason = result.error_message
            if reason not in analysis['failure_analysis']:
                analysis['failure_analysis'][reason] = 0
            analysis['failure_analysis'][reason] += 1
        
        # 生成建议
        success_rate = analysis['test_summary']['success_rate']
        if success_rate >= 80:
            analysis['recommendations'].append("下载成功率良好，系统运行正常")
        elif success_rate >= 50:
            analysis['recommendations'].append("下载成功率中等，建议优化网络连接或Cookie管理")
        else:
            analysis['recommendations'].append("下载成功率较低，需要检查Cookie有效性和API端点")
        
        if endpoint_stats:
            best_endpoint = max(endpoint_stats.items(), key=lambda x: x[1]['successes'])
            analysis['recommendations'].append(f"推荐使用端点: {best_endpoint[0]} (成功 {best_endpoint[1]['successes']} 次)")
        
        return analysis
    
    def save_report(self, results: List[DownloadResult], analysis: Dict) -> str:
        """保存测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'/root/projects/tencent-doc-manager/test_results/improved_download_report_{timestamp}.json'
        
        os.makedirs('/root/projects/tencent-doc-manager/test_results', exist_ok=True)
        
        report_data = {
            'test_metadata': {
                'test_time': datetime.now().isoformat(),
                'test_type': 'Improved Download Test',
                'tester_version': '2.0.0',
                'documents_tested': len(self.test_documents),
                'formats_tested': self.export_formats,
                'endpoints_tested': len(self.working_endpoints)
            },
            'results': [asdict(r) for r in results],
            'analysis': analysis
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 测试报告已保存: {report_file}")
        return report_file
    
    def print_summary(self, analysis: Dict):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("🏁 改进版腾讯文档下载测试报告")
        print("="*60)
        
        summary = analysis.get('test_summary', {})
        performance = analysis.get('performance_metrics', {})
        
        print(f"📊 总体统计:")
        print(f"   总测试数: {summary.get('total_tests', 0)}")
        print(f"   成功下载: {summary.get('successful_downloads', 0)}")
        print(f"   失败下载: {summary.get('failed_downloads', 0)}")
        print(f"   成功率: {summary.get('success_rate', 0):.1f}%")
        
        print(f"\n⏱️  性能指标:")
        print(f"   平均下载时间: {performance.get('average_download_time', 0):.2f}秒")
        print(f"   总下载时间: {performance.get('total_download_time', 0):.1f}秒")
        print(f"   总文件大小: {performance.get('total_file_size', 0)/1024:.1f} KB")
        print(f"   平均文件大小: {performance.get('average_file_size', 0)/1024:.1f} KB")
        
        format_perf = analysis.get('format_performance', {})
        if format_perf:
            print(f"\n📁 格式性能:")
            for fmt, stats in format_perf.items():
                print(f"   {fmt.upper()}: 成功率 {stats['success_rate']:.1f}% "
                      f"({stats['successful']}/{stats['total_attempts']})")
        
        endpoint_perf = analysis.get('endpoint_performance', {})
        if endpoint_perf:
            print(f"\n🌐 端点性能:")
            for endpoint, stats in endpoint_perf.items():
                print(f"   {endpoint}: {stats['success_count']}次成功 "
                      f"(平均{stats['avg_download_time']:.2f}秒)")
        
        failure_analysis = analysis.get('failure_analysis', {})
        if failure_analysis:
            print(f"\n❌ 失败原因:")
            for reason, count in failure_analysis.items():
                print(f"   {reason}: {count}次")
        
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print(f"\n💡 优化建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("="*60)


def main():
    """主函数"""
    print("🚀 启动改进版腾讯文档下载测试...")
    
    try:
        downloader = ImprovedTencentDownloader()
        results = downloader.run_comprehensive_test()
        
        if results:
            analysis = downloader.analyze_results(results)
            downloader.print_summary(analysis)
            report_file = downloader.save_report(results, analysis)
            print(f"\n📋 详细报告: {report_file}")
        else:
            print("❌ 没有测试结果")
            
    except Exception as e:
        logger.error(f"测试程序异常: {e}")
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()