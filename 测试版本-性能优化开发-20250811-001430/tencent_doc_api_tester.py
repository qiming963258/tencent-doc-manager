#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档内部API接口可用性测试工具
用于验证 docs.qq.com/dop-api/opendoc 接口的当前状态
作者：Claude Assistant
更新日期：2025-01-20
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
import re
from urllib.parse import urlparse, parse_qs

class TencentDocAPITester:
    """腾讯文档内部API测试类"""
    
    def __init__(self):
        self.base_url = "https://docs.qq.com/dop-api/opendoc"
        self.test_results = []
        
    def extract_doc_info(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从腾讯文档URL中提取文档ID和表格ID
        
        支持的URL格式：
        - https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=BB08J2
        - https://docs.qq.com/doc/DYktXWXFmUkdEb29V
        """
        try:
            # 提取文档ID
            doc_id_match = re.search(r'/(?:sheet|doc)/([A-Za-z0-9]+)', url)
            if not doc_id_match:
                return None, None
            
            doc_id = doc_id_match.group(1)
            
            # 提取表格tab ID（如果有）
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            sheet_id = query_params.get('tab', ['BB08J2'])[0]  # 默认值
            
            return doc_id, sheet_id
        except Exception as e:
            print(f"URL解析错误: {e}")
            return None, None
    
    def test_api_endpoint(self, doc_id: str, sheet_id: str = 'BB08J2') -> Dict:
        """
        测试API接口是否可用
        
        参数:
            doc_id: 文档ID
            sheet_id: 表格标签ID（默认BB08J2）
        
        返回:
            测试结果字典
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'doc_id': doc_id,
            'sheet_id': sheet_id,
            'status': 'unknown',
            'status_code': None,
            'response_time': None,
            'error_message': None,
            'data_structure': None
        }
        
        # 构建请求参数
        params = {
            'tab': sheet_id,
            'id': doc_id,
            'outformat': 1,
            'normal': 1
        }
        
        headers = {
            'referer': f"https://docs.qq.com/sheet/{doc_id}?tab={sheet_id}",
            'authority': "docs.qq.com",
            'accept': "*/*",
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # 发送请求并计时
            start_time = time.time()
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response_time = round((time.time() - start_time) * 1000, 2)  # 毫秒
            
            result['status_code'] = response.status_code
            result['response_time'] = response_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # 检查响应数据结构
                    if 'clientVars' in data:
                        result['status'] = 'success'
                        result['data_structure'] = self._analyze_data_structure(data)
                    else:
                        result['status'] = 'invalid_structure'
                        result['error_message'] = '响应数据结构不符合预期'
                        
                except json.JSONDecodeError:
                    result['status'] = 'json_error'
                    result['error_message'] = '响应不是有效的JSON格式'
            else:
                result['status'] = 'http_error'
                result['error_message'] = f'HTTP {response.status_code}'
                
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error_message'] = '请求超时（10秒）'
        except requests.exceptions.ConnectionError:
            result['status'] = 'connection_error'
            result['error_message'] = '无法连接到服务器'
        except Exception as e:
            result['status'] = 'error'
            result['error_message'] = str(e)
            
        self.test_results.append(result)
        return result
    
    def _analyze_data_structure(self, data: Dict) -> Dict:
        """分析响应数据结构"""
        structure = {
            'has_clientVars': 'clientVars' in data,
            'has_collab_client_vars': False,
            'has_initialAttributedText': False,
            'has_text_content': False,
            'data_type': None
        }
        
        try:
            if 'clientVars' in data:
                client_vars = data['clientVars']
                
                if 'collab_client_vars' in client_vars:
                    structure['has_collab_client_vars'] = True
                    collab_vars = client_vars['collab_client_vars']
                    
                    if 'initialAttributedText' in collab_vars:
                        structure['has_initialAttributedText'] = True
                        
                        if 'text' in collab_vars['initialAttributedText']:
                            structure['has_text_content'] = True
                            
                            # 判断文档类型
                            text_data = collab_vars['initialAttributedText']['text']
                            if isinstance(text_data, list) and len(text_data) > 0:
                                if isinstance(text_data[0], list):
                                    structure['data_type'] = 'spreadsheet'  # 表格
                                else:
                                    structure['data_type'] = 'document'  # 文档
        except:
            pass
            
        return structure
    
    def test_multiple_docs(self, test_urls: list) -> None:
        """测试多个文档URL"""
        print("=" * 60)
        print("腾讯文档内部API接口批量测试")
        print("=" * 60)
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n测试 {i}/{len(test_urls)}: {url}")
            doc_id, sheet_id = self.extract_doc_info(url)
            
            if doc_id:
                result = self.test_api_endpoint(doc_id, sheet_id)
                self._print_result(result)
            else:
                print("  [ERROR] 无法从URL中提取文档ID")
    
    def _print_result(self, result: Dict) -> None:
        """打印测试结果"""
        status_emoji = {
            'success': '[OK]',
            'http_error': '[ERR]',
            'timeout': '[TIMEOUT]',
            'connection_error': '[CONN_ERR]',
            'json_error': '[JSON_ERR]',
            'invalid_structure': '[STRUCT_ERR]',
            'error': '[ERROR]',
            'unknown': '[UNKNOWN]'
        }
        
        emoji = status_emoji.get(result['status'], '[UNKNOWN]')
        print(f"  {emoji} 状态: {result['status']}")
        print(f"     HTTP状态码: {result['status_code']}")
        print(f"     响应时间: {result['response_time']}ms")
        
        if result['error_message']:
            print(f"     错误信息: {result['error_message']}")
            
        if result['data_structure']:
            struct = result['data_structure']
            print(f"     数据结构: {struct['data_type'] or '未知'}")
            print(f"     结构完整性: ", end="")
            checks = [
                struct['has_clientVars'],
                struct['has_collab_client_vars'],
                struct['has_initialAttributedText'],
                struct['has_text_content']
            ]
            print(f"{sum(checks)}/4 检查通过")
    
    def generate_report(self) -> str:
        """生成测试报告"""
        if not self.test_results:
            return "没有测试结果"
        
        report = []
        report.append("\n" + "=" * 60)
        report.append("测试报告总结")
        report.append("=" * 60)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试数量: {len(self.test_results)}")
        
        # 统计结果
        success_count = sum(1 for r in self.test_results if r['status'] == 'success')
        avg_response_time = sum(r['response_time'] or 0 for r in self.test_results 
                              if r['response_time']) / len(self.test_results)
        
        report.append(f"成功率: {success_count}/{len(self.test_results)} "
                     f"({success_count/len(self.test_results)*100:.1f}%)")
        report.append(f"平均响应时间: {avg_response_time:.2f}ms")
        
        # 状态分布
        status_counts = {}
        for result in self.test_results:
            status = result['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        report.append("\n状态分布:")
        for status, count in status_counts.items():
            report.append(f"  - {status}: {count}")
        
        # 稳定性评估
        report.append("\n稳定性评估:")
        if success_count == len(self.test_results):
            report.append("  优秀 - 所有测试都成功")
        elif success_count >= len(self.test_results) * 0.8:
            report.append("  良好 - 大部分测试成功")
        elif success_count >= len(self.test_results) * 0.5:
            report.append("  一般 - 部分测试成功")
        else:
            report.append("  差 - 大部分测试失败")
        
        return "\n".join(report)


def main():
    """主函数"""
    print("\n腾讯文档内部API接口可用性测试工具 v1.0")
    print("-" * 60)
    
    # 创建测试器实例
    tester = TencentDocAPITester()
    
    # 测试用例（使用公开的腾讯文档作为示例）
    test_urls = [
        # 可以替换为您自己的腾讯文档URL进行测试
        "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=BB08J2",  # 示例表格
        "https://docs.qq.com/doc/DYktXWXFmUkdEb29V",  # 示例文档
    ]
    
    print("\n请选择测试模式:")
    print("1. 使用默认测试URL")
    print("2. 输入自定义URL")
    print("3. 退出")
    
    choice = input("\n请输入选择 (1/2/3): ").strip()
    
    if choice == '1':
        tester.test_multiple_docs(test_urls)
    elif choice == '2':
        custom_url = input("请输入腾讯文档URL: ").strip()
        if custom_url:
            tester.test_multiple_docs([custom_url])
        else:
            print("URL不能为空")
            return
    elif choice == '3':
        print("退出程序")
        return
    else:
        print("无效选择")
        return
    
    # 生成并打印报告
    print(tester.generate_report())
    
    print("\n" + "=" * 60)
    print("测试结论:")
    
    # 基于测试结果给出建议
    if tester.test_results:
        success_rate = sum(1 for r in tester.test_results 
                          if r['status'] == 'success') / len(tester.test_results)
        
        if success_rate >= 0.8:
            print("[+] API接口当前可用，可以正常使用")
            print("    建议：定期监控接口状态，做好降级方案")
        elif success_rate >= 0.5:
            print("[!] API接口部分可用，稳定性一般")
            print("    建议：考虑备用方案，如Selenium或Playwright")
        else:
            print("[-] API接口基本不可用或已失效")
            print("    建议：改用其他技术方案（Selenium/Playwright）")
    
    print("=" * 60)


if __name__ == "__main__":
    main()