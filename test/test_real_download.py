#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档下载真实测试脚本
测试环境: Linux服务器
目标: 验证三种下载方案的实际可行性
"""

import json
import requests
import time
import os
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import traceback
from datetime import datetime

# 配置信息
COOKIE_FILE = "/root/projects/tencent-doc-manager/config/cookies_new.json"
TEST_DOC_ID = "DWEVjZndkR2xVSWJN"
DOWNLOAD_DIR = "/root/projects/tencent-doc-manager/downloads"

class TencentDocRealTester:
    """腾讯文档真实下载测试器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.cookie_str = ""
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_doc_id": TEST_DOC_ID,
            "tests": {}
        }
        self.setup_session()
    
    def setup_session(self):
        """设置会话和cookie"""
        try:
            with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
                self.cookie_str = cookie_data.get("current_cookies", "")
            
            # 解析cookie字符串为字典
            cookies_dict = {}
            for cookie in self.cookie_str.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies_dict[key] = value
            
            self.session.cookies.update(cookies_dict)
            
            # 设置常用请求头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': 'https://docs.qq.com/',
                'Origin': 'https://docs.qq.com'
            })
            
            print(f"✅ Session setup complete with {len(cookies_dict)} cookies")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup session: {e}")
            return False
    
    def test_method_1_direct_download(self):
        """方案1: 简单直接下载测试"""
        print("\n🔬 测试方案1: 简单直接下载")
        test_name = "direct_download"
        
        # 测试多个可能的下载URL
        test_urls = [
            f"https://docs.qq.com/dop-api/opendoc?id={TEST_DOC_ID}&type=export_xlsx",
            f"https://docs.qq.com/api/doc/export?docId={TEST_DOC_ID}&format=xlsx",
            f"https://docs.qq.com/dop-api/opendoc?id={TEST_DOC_ID}&type=export_csv",
            f"https://docs.qq.com/api/doc/export?docId={TEST_DOC_ID}&format=csv",
            f"https://docs.qq.com/sheet/export?id={TEST_DOC_ID}&exportType=xlsx",
            f"https://docs.qq.com/sheet/export?id={TEST_DOC_ID}&exportType=csv"
        ]
        
        results = []
        
        for i, url in enumerate(test_urls, 1):
            print(f"  📡 测试URL {i}: {url}")
            try:
                response = self.session.get(url, timeout=30)
                
                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": response.headers.get('Content-Type', ''),
                    "content_length": len(response.content),
                    "content_preview": response.text[:200] if response.text else "No text content",
                    "headers": dict(response.headers),
                    "success": False
                }
                
                # 判断是否成功获取文件
                if response.status_code == 200:
                    if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers.get('Content-Type', ''):
                        # Excel文件
                        filename = f"test_direct_{i}_excel.xlsx"
                        filepath = os.path.join(DOWNLOAD_DIR, filename)
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        result["success"] = True
                        result["file_type"] = "Excel"
                        result["saved_as"] = filepath
                        print(f"    ✅ 成功下载Excel文件: {filename}")
                        
                    elif 'text/csv' in response.headers.get('Content-Type', '') or response.text.count(',') > 10:
                        # CSV文件
                        filename = f"test_direct_{i}_csv.csv"
                        filepath = os.path.join(DOWNLOAD_DIR, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        result["success"] = True
                        result["file_type"] = "CSV"
                        result["saved_as"] = filepath
                        print(f"    ✅ 成功下载CSV文件: {filename}")
                        
                    else:
                        print(f"    ⚠️ 状态码200但内容类型不匹配: {response.headers.get('Content-Type', '')}")
                else:
                    print(f"    ❌ 状态码: {response.status_code}")
                
                results.append(result)
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                error_result = {
                    "url": url,
                    "error": str(e),
                    "success": False
                }
                results.append(error_result)
                print(f"    ❌ 请求异常: {e}")
        
        self.test_results["tests"][test_name] = {
            "description": "直接使用不同URL尝试下载",
            "results": results,
            "success_count": sum(1 for r in results if r.get("success", False))
        }
        
        print(f"📊 方案1结果: {self.test_results['tests'][test_name]['success_count']}/{len(results)} 成功")
    
    def test_method_2_page_analysis(self):
        """方案2: 页面分析获取下载链接"""
        print("\n🔬 测试方案2: 页面分析获取下载链接")
        test_name = "page_analysis"
        
        try:
            # 首先访问文档页面
            doc_url = f"https://docs.qq.com/sheet/{TEST_DOC_ID}"
            print(f"  📄 访问文档页面: {doc_url}")
            
            response = self.session.get(doc_url, timeout=30)
            
            result = {
                "doc_url": doc_url,
                "status_code": response.status_code,
                "content_length": len(response.content),
                "page_title": "",
                "export_urls_found": [],
                "success": False
            }
            
            if response.status_code == 200:
                html_content = response.text
                
                # 提取页面标题
                import re
                title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                if title_match:
                    result["page_title"] = title_match.group(1)
                
                # 寻找可能的导出链接
                export_patterns = [
                    r'export[^"]*\.xlsx',
                    r'export[^"]*\.csv',
                    r'dop-api/opendoc[^"]*',
                    r'/api/doc/export[^"]*',
                    r'/sheet/export[^"]*'
                ]
                
                for pattern in export_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    result["export_urls_found"].extend(matches)
                
                # 去重
                result["export_urls_found"] = list(set(result["export_urls_found"]))
                
                if result["export_urls_found"]:
                    result["success"] = True
                    print(f"    ✅ 找到 {len(result['export_urls_found'])} 个潜在导出链接")
                    for url in result["export_urls_found"]:
                        print(f"      - {url}")
                else:
                    print("    ⚠️ 未在页面中找到导出链接")
                
                # 保存页面内容用于分析
                page_file = os.path.join(DOWNLOAD_DIR, f"page_analysis_{TEST_DOC_ID}.html")
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                result["page_saved_as"] = page_file
                
            else:
                print(f"    ❌ 无法访问文档页面，状态码: {response.status_code}")
            
            self.test_results["tests"][test_name] = {
                "description": "访问文档页面分析导出链接",
                "result": result
            }
            
        except Exception as e:
            self.test_results["tests"][test_name] = {
                "description": "访问文档页面分析导出链接",
                "error": str(e),
                "success": False
            }
            print(f"    ❌ 页面分析异常: {e}")
    
    def test_method_3_api_exploration(self):
        """方案3: API探索测试"""
        print("\n🔬 测试方案3: API探索测试")
        test_name = "api_exploration"
        
        # 测试各种API端点
        api_endpoints = [
            f"https://docs.qq.com/v1/export/office/{TEST_DOC_ID}",
            f"https://docs.qq.com/cgi-bin/office_excel_export?id={TEST_DOC_ID}",
            f"https://docs.qq.com/office/api/export?docid={TEST_DOC_ID}",
            f"https://docs.qq.com/api/v1/export?doc_id={TEST_DOC_ID}&type=xlsx",
            f"https://docs.qq.com/desktop/api/getdoc?id={TEST_DOC_ID}",
            f"https://docs.qq.com/desktop/getdoc?docId={TEST_DOC_ID}"
        ]
        
        results = []
        
        for i, endpoint in enumerate(api_endpoints, 1):
            print(f"  🔍 测试API {i}: {endpoint}")
            try:
                response = self.session.get(endpoint, timeout=15)
                
                result = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "content_type": response.headers.get('Content-Type', ''),
                    "content_length": len(response.content),
                    "response_preview": response.text[:300] if response.text else "No text content",
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    print(f"    ✅ 响应成功，内容类型: {result['content_type']}")
                else:
                    print(f"    ❌ 状态码: {response.status_code}")
                
                results.append(result)
                time.sleep(0.5)
                
            except Exception as e:
                error_result = {
                    "endpoint": endpoint,
                    "error": str(e),
                    "success": False
                }
                results.append(error_result)
                print(f"    ❌ API请求异常: {e}")
        
        self.test_results["tests"][test_name] = {
            "description": "探索各种可能的API端点",
            "results": results,
            "success_count": sum(1 for r in results if r.get("success", False))
        }
        
        print(f"📊 方案3结果: {self.test_results['tests'][test_name]['success_count']}/{len(results)} 成功")
    
    def test_desktop_api(self):
        """测试桌面版API"""
        print("\n🔬 测试方案4: 桌面版API")
        test_name = "desktop_api"
        
        try:
            # 测试桌面版获取文档信息的API
            desktop_url = "https://docs.qq.com/desktop"
            print(f"  🖥️ 访问桌面版: {desktop_url}")
            
            response = self.session.get(desktop_url, timeout=30)
            
            result = {
                "desktop_url": desktop_url,
                "status_code": response.status_code,
                "content_length": len(response.content),
                "can_access_desktop": response.status_code == 200,
                "success": False
            }
            
            if response.status_code == 200:
                print("    ✅ 可以访问桌面版")
                
                # 尝试获取文档列表API
                list_api_url = "https://docs.qq.com/desktop/api/list"
                try:
                    list_response = self.session.post(list_api_url, 
                        json={"limit": 10, "offset": 0},
                        timeout=15
                    )
                    
                    result["list_api"] = {
                        "url": list_api_url,
                        "status_code": list_response.status_code,
                        "response": list_response.text[:500] if list_response.text else "No response"
                    }
                    
                    if list_response.status_code == 200:
                        print("    ✅ 文档列表API响应成功")
                        result["success"] = True
                    else:
                        print(f"    ⚠️ 文档列表API状态码: {list_response.status_code}")
                        
                except Exception as e:
                    result["list_api_error"] = str(e)
                    print(f"    ❌ 文档列表API异常: {e}")
            else:
                print(f"    ❌ 无法访问桌面版，状态码: {response.status_code}")
            
            self.test_results["tests"][test_name] = {
                "description": "测试桌面版API访问",
                "result": result
            }
            
        except Exception as e:
            self.test_results["tests"][test_name] = {
                "description": "测试桌面版API访问",
                "error": str(e),
                "success": False
            }
            print(f"    ❌ 桌面API测试异常: {e}")
    
    def save_test_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(DOWNLOAD_DIR, f"real_download_test_results_{timestamp}.json")
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存: {results_file}")
        return results_file
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("🎯 腾讯文档下载真实测试结果摘要")
        print("="*60)
        
        total_tests = len(self.test_results["tests"])
        successful_tests = 0
        
        for test_name, test_data in self.test_results["tests"].items():
            if test_data.get("success_count", 0) > 0 or test_data.get("result", {}).get("success", False):
                successful_tests += 1
                status = "✅ 成功"
            else:
                status = "❌ 失败"
            
            print(f"{status} {test_name}: {test_data.get('description', '')}")
            
            # 详细结果
            if "results" in test_data:
                success_count = test_data.get("success_count", 0)
                total_count = len(test_data["results"])
                print(f"    📊 成功率: {success_count}/{total_count}")
            elif "result" in test_data:
                if test_data["result"].get("success", False):
                    print("    📊 测试通过")
                else:
                    print("    📊 测试失败")
        
        print(f"\n总体结果: {successful_tests}/{total_tests} 个测试方案有效")
        print("="*60)

def main():
    """主函数"""
    print("🚀 开始腾讯文档下载真实测试")
    print(f"📝 测试文档ID: {TEST_DOC_ID}")
    print(f"💾 下载目录: {DOWNLOAD_DIR}")
    
    # 确保下载目录存在
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # 创建测试器
    tester = TencentDocRealTester()
    
    if not tester.cookie_str:
        print("❌ 无法获取Cookie，测试中止")
        sys.exit(1)
    
    try:
        # 执行各种测试方案
        tester.test_method_1_direct_download()
        tester.test_method_2_page_analysis()
        tester.test_method_3_api_exploration()
        tester.test_desktop_api()
        
        # 保存结果和打印摘要
        tester.save_test_results()
        tester.print_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()