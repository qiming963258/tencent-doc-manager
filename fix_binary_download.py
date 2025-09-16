#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复二进制Excel下载问题 - 分析和解决方案
"""

import json
import requests
import time
import os
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode
import re
from bs4 import BeautifulSoup

class BinaryDownloadFixer:
    """修复腾讯文档二进制下载问题"""
    
    def __init__(self):
        self.cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        self.download_dir = "/root/projects/tencent-doc-manager/downloads"
        self.load_cookies()
        
    def load_cookies(self):
        """加载Cookie配置"""
        with open(self.cookie_file, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
            self.cookie_str = cookie_data['current_cookies']
            
    def analyze_ejs_response(self, doc_id: str) -> Dict:
        """分析EJS响应寻找二进制下载线索"""
        print(f"\n=== 分析文档 {doc_id} 的EJS响应 ===")
        
        # 首先获取文档页面
        page_url = f"https://docs.qq.com/sheet/{doc_id}"
        headers = {
            'Cookie': self.cookie_str,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(page_url, headers=headers, timeout=30)
        print(f"页面访问状态: {response.status_code}")
        
        # 从页面中提取必要的参数
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找可能的下载链接或参数
        findings = {
            'doc_id': doc_id,
            'export_urls': [],
            'auth_params': {},
            'potential_endpoints': []
        }
        
        # 搜索script标签中的导出相关代码
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.string if script.string else ""
            
            # 查找导出相关的URL模式
            export_patterns = [
                r'exportUrl["\']?\s*[:=]\s*["\']([^"\']+)',
                r'downloadUrl["\']?\s*[:=]\s*["\']([^"\']+)',
                r'/api/.*?export[^"\']*',
                r'/dop-api/.*?export[^"\']*'
            ]
            
            for pattern in export_patterns:
                matches = re.findall(pattern, script_text, re.IGNORECASE)
                if matches:
                    findings['export_urls'].extend(matches)
            
            # 提取认证参数
            auth_patterns = [
                (r'nowUserId["\']?\s*[:=]\s*["\']?(\d+)', 'uid'),
                (r'docId["\']?\s*[:=]\s*["\']([^"\']+)', 'doc_id'),
                (r'padId["\']?\s*[:=]\s*["\']([^"\']+)', 'pad_id'),
                (r'sessionId["\']?\s*[:=]\s*["\']([^"\']+)', 'session_id'),
            ]
            
            for pattern, key in auth_patterns:
                match = re.search(pattern, script_text)
                if match:
                    findings['auth_params'][key] = match.group(1)
        
        return findings
        
    def try_binary_download_methods(self, doc_id: str) -> Optional[bytes]:
        """尝试多种方法获取二进制Excel文件"""
        print(f"\n=== 尝试下载二进制文件 ===")
        
        methods = [
            # 方法1: 使用openFile端点
            {
                'name': 'openFile API',
                'url': f'https://docs.qq.com/dop-api/openfile',
                'params': {
                    'id': doc_id,
                    'type': 'export_excel',
                    'download': '1'
                }
            },
            # 方法2: 使用get端点
            {
                'name': 'get API',
                'url': f'https://docs.qq.com/dop-api/get',
                'params': {
                    'id': doc_id,
                    'type': 'export_excel',
                    'normal': '1'
                }
            },
            # 方法3: 直接文件端点
            {
                'name': 'file endpoint',
                'url': f'https://docs.qq.com/file/{doc_id}.xlsx',
                'params': {}
            },
            # 方法4: 使用export_v2端点
            {
                'name': 'export_v2',
                'url': f'https://docs.qq.com/v2/export/sheet',
                'params': {
                    'docId': doc_id,
                    'format': 'xlsx'
                }
            }
        ]
        
        headers = {
            'Cookie': self.cookie_str,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*',
            'Referer': f'https://docs.qq.com/sheet/{doc_id}'
        }
        
        for method in methods:
            print(f"\n尝试方法: {method['name']}")
            
            # 构建完整URL
            if method['params']:
                url = f"{method['url']}?{urlencode(method['params'])}"
            else:
                url = method['url']
            
            print(f"URL: {url[:80]}...")
            
            try:
                response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
                print(f"状态码: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"Content-Length: {len(response.content)} bytes")
                
                # 检查是否是二进制Excel文件
                if response.content[:4] == b'PK\x03\x04':
                    print("✅ 成功! 这是有效的Excel二进制文件")
                    return response.content
                    
                # 检查响应类型
                if b'<html' in response.content[:1000].lower():
                    print("❌ HTML响应")
                elif b'head\njson' in response.content[:20]:
                    print("❌ EJS/JSON响应")
                elif response.status_code == 404:
                    print("❌ 端点不存在")
                else:
                    print(f"❌ 未知响应类型: {response.content[:50]}")
                    
            except Exception as e:
                print(f"❌ 请求失败: {e}")
                
        return None
        
    def parse_ejs_to_data(self, ejs_content: bytes) -> Optional[Dict]:
        """解析EJS响应提取表格数据"""
        print(f"\n=== 解析EJS内容提取数据 ===")
        
        try:
            # EJS格式: head\njson\n长度\nJSON内容
            lines = ejs_content.decode('utf-8').split('\n', 3)
            if len(lines) >= 4 and lines[0] == 'head' and lines[1] == 'json':
                json_data = json.loads(lines[3])
                
                # 检查是否包含表格数据
                if 'bodyData' in json_data:
                    body_data = json_data['bodyData']
                    
                    # 寻找表格数据的各种可能位置
                    possible_keys = ['sheetData', 'gridData', 'cells', 'data', 'content']
                    
                    for key in possible_keys:
                        if key in body_data:
                            print(f"找到数据字段: {key}")
                            return body_data[key]
                    
                    # 检查padHTML中是否有表格
                    if 'padHTML' in body_data and body_data['padHTML']:
                        print("在padHTML中查找表格数据")
                        soup = BeautifulSoup(body_data['padHTML'], 'html.parser')
                        tables = soup.find_all('table')
                        if tables:
                            print(f"找到 {len(tables)} 个表格")
                            return self._extract_table_data(tables[0])
                
                print("EJS响应中未找到表格数据")
                return None
                
        except Exception as e:
            print(f"解析EJS失败: {e}")
            return None
            
    def _extract_table_data(self, table_element):
        """从HTML表格提取数据"""
        data = []
        rows = table_element.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            data.append(row_data)
        return data

def main():
    """主函数"""
    print("腾讯文档二进制下载问题修复工具")
    print("=" * 60)
    
    fixer = BinaryDownloadFixer()
    
    # 测试文档
    test_doc_id = "DWEVjZndkR2xVSWJN"
    
    # 1. 分析EJS响应
    findings = fixer.analyze_ejs_response(test_doc_id)
    print(f"\n发现的导出URL: {findings['export_urls'][:3]}")
    print(f"发现的认证参数: {findings['auth_params']}")
    
    # 2. 尝试二进制下载
    binary_content = fixer.try_binary_download_methods(test_doc_id)
    
    if binary_content:
        # 保存二进制文件
        output_file = f"/root/projects/tencent-doc-manager/downloads/fixed_binary_{int(time.time())}.xlsx"
        with open(output_file, 'wb') as f:
            f.write(binary_content)
        print(f"\n✅ 二进制文件已保存: {output_file}")
    else:
        print("\n❌ 所有二进制下载方法都失败了")
        
        # 3. 尝试从EJS提取数据
        print("\n尝试从现有EJS文件提取数据...")
        ejs_file = "/root/projects/tencent-doc-manager/downloads/tencent_doc_DWEVjZndkR2xVSWJN_xlsx_20250827_103448.xlsx"
        if os.path.exists(ejs_file):
            with open(ejs_file, 'rb') as f:
                ejs_content = f.read()
            data = fixer.parse_ejs_to_data(ejs_content)
            if data:
                print(f"成功提取数据: {len(data)} 行" if isinstance(data, list) else "提取到数据结构")
            else:
                print("无法从EJS提取有效数据")

if __name__ == "__main__":
    main()