#!/usr/bin/env python3
"""
增强版腾讯文档下载诊断程序
用于诊断和测试不同的下载端点，找到可用的API接口
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
import logging
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TencentDocDiagnostic:
    """腾讯文档下载诊断工具"""
    
    def __init__(self, cookie_file: str = None):
        self.cookie_file = cookie_file or '/root/projects/tencent-doc-manager/config/cookies_new.json'
        self.cookies = self._load_cookies()
        
        # 多种可能的导出端点
        self.test_endpoints = [
            # 原有端点
            {
                'name': 'v1_export_original',
                'url': 'https://docs.qq.com/v1/export/export_office',
                'method': 'GET',
                'params_template': {
                    'docid': '{doc_id}',
                    'type': '{format}',
                    'download': '1',
                    'normal': '1',
                    'preview': '0',
                    'export_source': 'client'
                }
            },
            {
                'name': 'sheet_export_original', 
                'url': 'https://docs.qq.com/sheet/export',
                'method': 'GET',
                'params_template': {
                    'id': '{doc_id}',
                    'type': '{format}',
                    'download': '1'
                }
            },
            {
                'name': 'cgi_export_original',
                'url': 'https://docs.qq.com/cgi-bin/excel/export',
                'method': 'POST',
                'params_template': {
                    'id': '{doc_id}',
                    'type': '{format}'
                }
            },
            
            # 新的可能端点
            {
                'name': 'v2_export',
                'url': 'https://docs.qq.com/v2/export',
                'method': 'GET',
                'params_template': {
                    'docid': '{doc_id}',
                    'exportType': '{format}',
                    'download': '1'
                }
            },
            {
                'name': 'api_export',
                'url': 'https://docs.qq.com/api/export',
                'method': 'GET',
                'params_template': {
                    'docId': '{doc_id}',
                    'format': '{format}',
                    'download': 'true'
                }
            },
            {
                'name': 'dop_export',
                'url': 'https://docs.qq.com/dop-api/export',
                'method': 'GET',
                'params_template': {
                    'docid': '{doc_id}',
                    'format': '{format}',
                    'download': '1'
                }
            },
            {
                'name': 'office_export',
                'url': 'https://docs.qq.com/office/export',
                'method': 'GET',
                'params_template': {
                    'id': '{doc_id}',
                    'type': '{format}',
                    'download': '1'
                }
            },
            {
                'name': 'cgi_office_export',
                'url': 'https://docs.qq.com/cgi-bin/office/export',
                'method': 'GET',
                'params_template': {
                    'docid': '{doc_id}',
                    'type': '{format}',
                    'download': '1'
                }
            },
            
            # 尝试不同的URL格式
            {
                'name': 'direct_sheet_download',
                'url': 'https://docs.qq.com/sheet/{doc_id}/export',
                'method': 'GET',
                'params_template': {
                    'format': '{format}',
                    'download': '1'
                }
            },
            {
                'name': 'sheet_download_api',
                'url': 'https://docs.qq.com/sheet/{doc_id}',
                'method': 'GET',
                'params_template': {
                    'export': '{format}',
                    'download': '1'
                }
            }
        ]
        
        # 测试文档
        self.test_docs = [
            {
                'name': '测试版本-小红书部门',
                'url': 'https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN',
                'doc_id': 'DWEVjZndkR2xVSWJN'
            }
        ]
        
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
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def test_endpoint(self, endpoint: Dict, doc_id: str, export_format: str = 'csv') -> Dict:
        """测试单个端点"""
        start_time = time.time()
        
        try:
            # 构建URL
            if '{doc_id}' in endpoint['url']:
                url = endpoint['url'].format(doc_id=doc_id)
            else:
                url = endpoint['url']
            
            # 构建参数
            params = {}
            if 'params_template' in endpoint:
                for key, value in endpoint['params_template'].items():
                    if '{doc_id}' in value:
                        params[key] = value.format(doc_id=doc_id)
                    elif '{format}' in value:
                        params[key] = value.format(format=export_format)
                    else:
                        params[key] = value
            
            headers = self._build_headers()
            
            logger.info(f"🔍 测试端点: {endpoint['name']}")
            logger.info(f"   URL: {url}")
            logger.info(f"   参数: {params}")
            
            # 发送请求
            if endpoint['method'].upper() == 'GET':
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    allow_redirects=True,
                    timeout=10,
                    stream=False  # 不流式下载，只检查响应
                )
            else:  # POST
                response = requests.post(
                    url,
                    data=params,
                    headers=headers,
                    allow_redirects=True,
                    timeout=10
                )
            
            elapsed = time.time() - start_time
            
            # 分析响应
            result = {
                'endpoint': endpoint['name'],
                'url': url,
                'params': params,
                'method': endpoint['method'],
                'status_code': response.status_code,
                'response_time': elapsed,
                'content_type': response.headers.get('Content-Type', ''),
                'content_length': response.headers.get('Content-Length', ''),
                'response_headers': dict(response.headers),
                'success': False,
                'error': None,
                'response_preview': ''
            }
            
            # 检查响应状态
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        result['response_preview'] = str(json_data)[:500]
                        
                        # 检查JSON响应是否表示成功
                        if json_data.get('ret') == 0 or json_data.get('retcode') == 0:
                            result['success'] = True
                        else:
                            result['error'] = f"API返回错误: {json_data}"
                    except:
                        result['error'] = "JSON解析失败"
                        
                elif any(ct in content_type for ct in ['text/csv', 'application/vnd.ms-excel', 
                                                      'application/vnd.openxmlformats-officedocument']):
                    # 可能是文件内容
                    result['success'] = True
                    result['response_preview'] = f"文件内容 (前100字节): {response.content[:100]}"
                    
                elif 'text/html' in content_type:
                    # HTML响应，可能是错误页面
                    html_preview = response.text[:500]
                    result['response_preview'] = html_preview
                    
                    if 'error' in html_preview.lower() or '404' in html_preview:
                        result['error'] = "HTML错误页面"
                    else:
                        # 可能是包含下载链接的页面
                        result['success'] = True
                        
                else:
                    result['response_preview'] = f"未知内容类型: {response.content[:100]}"
                    result['success'] = True  # 假设是文件内容
                    
            else:
                result['error'] = f"HTTP {response.status_code}"
                if response.text:
                    result['response_preview'] = response.text[:200]
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                'endpoint': endpoint['name'],
                'url': url if 'url' in locals() else endpoint['url'],
                'error': '请求超时',
                'success': False,
                'response_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'endpoint': endpoint['name'],
                'url': url if 'url' in locals() else endpoint['url'], 
                'error': f'请求异常: {str(e)}',
                'success': False,
                'response_time': time.time() - start_time
            }
    
    def run_comprehensive_diagnostic(self) -> Dict:
        """运行全面诊断"""
        logger.info("🔍 开始腾讯文档下载端点诊断...")
        
        if not self.cookies:
            logger.error("❌ 没有有效的Cookie，无法进行测试")
            return {}
        
        results = {
            'test_time': datetime.now().isoformat(),
            'cookie_loaded': bool(self.cookies),
            'cookie_length': len(self.cookies),
            'endpoints_tested': len(self.test_endpoints),
            'documents_tested': len(self.test_docs),
            'test_results': [],
            'successful_endpoints': [],
            'failed_endpoints': [],
            'recommendations': []
        }
        
        # 测试每个文档的每个端点
        for doc in self.test_docs:
            logger.info(f"📄 测试文档: {doc['name']}")
            
            doc_results = []
            
            for endpoint in self.test_endpoints:
                # 测试CSV格式
                csv_result = self.test_endpoint(endpoint, doc['doc_id'], 'csv')
                csv_result['document'] = doc['name']
                csv_result['format'] = 'csv'
                doc_results.append(csv_result)
                
                if csv_result['success']:
                    logger.info(f"✅ 成功: {endpoint['name']} (CSV)")
                    results['successful_endpoints'].append(csv_result)
                else:
                    logger.warning(f"❌ 失败: {endpoint['name']} (CSV) - {csv_result.get('error', 'Unknown')}")
                    results['failed_endpoints'].append(csv_result)
                
                time.sleep(2)  # 避免请求过快
                
                # 测试XLSX格式
                xlsx_result = self.test_endpoint(endpoint, doc['doc_id'], 'xlsx')
                xlsx_result['document'] = doc['name']
                xlsx_result['format'] = 'xlsx'
                doc_results.append(xlsx_result)
                
                if xlsx_result['success']:
                    logger.info(f"✅ 成功: {endpoint['name']} (XLSX)")
                    results['successful_endpoints'].append(xlsx_result)
                else:
                    logger.warning(f"❌ 失败: {endpoint['name']} (XLSX) - {xlsx_result.get('error', 'Unknown')}")
                    results['failed_endpoints'].append(xlsx_result)
                
                time.sleep(2)
            
            results['test_results'].extend(doc_results)
        
        # 生成建议
        if results['successful_endpoints']:
            results['recommendations'].append("找到可用的下载端点，建议更新下载器配置")
            
            # 按成功率排序端点
            endpoint_success = {}
            for result in results['successful_endpoints']:
                endpoint = result['endpoint']
                if endpoint not in endpoint_success:
                    endpoint_success[endpoint] = 0
                endpoint_success[endpoint] += 1
            
            best_endpoint = max(endpoint_success.items(), key=lambda x: x[1])
            results['recommendations'].append(f"推荐使用端点: {best_endpoint[0]} (成功 {best_endpoint[1]} 次)")
        else:
            results['recommendations'].append("所有端点都失败，可能是Cookie过期或API已更改")
            results['recommendations'].append("建议检查Cookie有效性或联系腾讯文档官方API文档")
        
        return results
    
    def save_diagnostic_report(self, results: Dict) -> str:
        """保存诊断报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'/root/projects/tencent-doc-manager/diagnostic_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 诊断报告已保存: {report_file}")
        return report_file
    
    def print_summary(self, results: Dict):
        """打印诊断摘要"""
        print("\n" + "="*60)
        print("🔍 腾讯文档下载端点诊断报告")
        print("="*60)
        
        print(f"📊 测试概况:")
        print(f"   测试端点数: {results['endpoints_tested']}")
        print(f"   成功端点数: {len(results['successful_endpoints'])}")
        print(f"   失败端点数: {len(results['failed_endpoints'])}")
        print(f"   Cookie状态: {'有效' if results['cookie_loaded'] else '无效'}")
        
        if results['successful_endpoints']:
            print(f"\n✅ 可用端点:")
            for endpoint in results['successful_endpoints']:
                print(f"   {endpoint['endpoint']} ({endpoint['format']}) - {endpoint['response_time']:.2f}s")
        
        if results['failed_endpoints']:
            print(f"\n❌ 失败端点 (示例):")
            for endpoint in results['failed_endpoints'][:5]:  # 只显示前5个
                print(f"   {endpoint['endpoint']} ({endpoint.get('format', 'N/A')}) - {endpoint.get('error', 'Unknown error')}")
        
        if results['recommendations']:
            print(f"\n💡 建议:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print("="*60)


def main():
    """主函数"""
    print("🚀 启动腾讯文档下载端点诊断...")
    
    try:
        diagnostic = TencentDocDiagnostic()
        results = diagnostic.run_comprehensive_diagnostic()
        
        if results:
            diagnostic.print_summary(results)
            report_file = diagnostic.save_diagnostic_report(results)
            print(f"\n📋 详细报告: {report_file}")
        else:
            print("❌ 诊断失败")
            
    except Exception as e:
        logger.error(f"诊断程序异常: {e}")
        print(f"❌ 诊断失败: {e}")


if __name__ == "__main__":
    main()