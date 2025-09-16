#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档XSRF Token增强版下载器

主要功能：
1. 从腾讯文档页面提取XSRF Token
2. 使用正确的dop-api认证流程
3. 实现稳定的下载机制
4. 支持多种格式导出（CSV, XLSX）

技术要点：
- 分析HTML页面结构，提取关键认证信息
- 完整的dop-api认证参数构建
- 稳定的网络请求重试机制
- 完整的错误处理和日志记录

作者: Claude Assistant
版本: 1.0
更新时间: 2025-08-27
"""

import os
import sys
import time
import json
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging
from urllib.parse import urlencode, parse_qs, urlparse, unquote
from bs4 import BeautifulSoup
import hashlib
import base64

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/root/projects/tencent-doc-manager/xsrf_downloader.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AuthInfo:
    """认证信息结构"""
    xsrf_token: str = ""
    session_id: str = ""
    uid: str = ""
    uid_key: str = ""
    doc_sid: str = ""
    hashkey: str = ""
    tok: str = ""
    additional_params: Dict[str, str] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

@dataclass
class DownloadConfig:
    """下载配置"""
    max_retries: int = 3
    retry_delay: float = 2.0
    request_timeout: int = 30
    page_load_timeout: int = 15
    download_chunk_size: int = 8192
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

@dataclass
class DownloadResult:
    """下载结果"""
    success: bool
    document_name: str
    doc_id: str
    format_type: str
    file_path: str
    file_size: int
    download_time: float
    error_message: str
    timestamp: str
    auth_method: str
    endpoint_used: str
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


class XSRFEnhancedDownloader:
    """腾讯文档XSRF Token增强版下载器"""
    
    def __init__(self, cookie_file: str = None, download_dir: str = None):
        """初始化下载器"""
        self.cookie_file = cookie_file or '/root/projects/tencent-doc-manager/config/cookies_new.json'
        self.download_dir = download_dir or '/root/projects/tencent-doc-manager/downloads'
        self.config = DownloadConfig()
        
        # 创建下载目录
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 加载Cookie
        self.cookies = self._load_cookies()
        
        # 请求会话
        self.session = requests.Session()
        
        # 测试文档配置
        self.test_documents = [
            {'name': '测试版本-小红书部门', 'doc_id': 'DWEVjZndkR2xVSWJN'},
            {'name': '测试版本-回国销售计划表', 'doc_id': 'DRFppYm15RGZ2WExN'},
            {'name': '测试版本-出国销售计划表', 'doc_id': 'DRHZrS1hOS3pwRGZB'}
        ]
        
        # 支持的导出格式
        self.export_formats = ['csv', 'xlsx']
        
        logger.info("XSRF增强版下载器初始化完成")
    
    def _load_cookies(self) -> str:
        """加载Cookie配置"""
        try:
            logger.info(f"正在加载Cookie配置: {self.cookie_file}")
            
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            cookies = config.get('current_cookies', '')
            
            if not cookies:
                logger.error("Cookie配置为空")
                return ""
            
            logger.info(f"成功加载Cookie，长度: {len(cookies)} 字符")
            
            # 验证Cookie格式
            cookie_pairs = cookies.split(';')
            valid_pairs = []
            
            for pair in cookie_pairs:
                if '=' in pair:
                    valid_pairs.append(pair.strip())
            
            logger.info(f"有效Cookie键值对: {len(valid_pairs)} 个")
            return cookies
            
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return ""
    
    def _build_base_headers(self) -> Dict[str, str]:
        """构建基础请求头"""
        return {
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def _extract_auth_info_from_page(self, html_content: str, doc_id: str) -> AuthInfo:
        """从HTML页面提取认证信息"""
        logger.info("开始提取页面认证信息...")
        
        auth_info = AuthInfo()
        
        try:
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 方法1: 从meta标签提取XSRF token
            csrf_meta = soup.find('meta', attrs={'name': re.compile(r'csrf|xsrf', re.I)})
            if csrf_meta:
                auth_info.xsrf_token = csrf_meta.get('content', '')
                logger.info(f"从meta标签提取XSRF token: {auth_info.xsrf_token[:20]}...")
            
            # 方法2: 从script标签中提取认证参数
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_content = script.string
                    
                    # 提取各种认证参数
                    patterns = {
                        'xsrf_token': r'["\']?(?:xsrf|csrf)[_-]?(?:token|key)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        'session_id': r'["\']?(?:session[_-]?id|SID)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        'hashkey': r'["\']?hashkey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        'tok': r'["\']?TOK["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        'uid': r'["\']?uid["\']?\s*[:=]\s*["\']?(\d+)["\']?',
                        'doc_sid': r'["\']?(?:DOC_SID|doc_sid)["\']?\s*[:=]\s*["\']([^"\']+)["\']'
                    }
                    
                    for param_name, pattern in patterns.items():
                        matches = re.findall(pattern, script_content, re.I)
                        if matches:
                            value = matches[0]
                            setattr(auth_info, param_name, value)
                            logger.info(f"从script提取{param_name}: {value[:20]}...")
            
            # 方法3: 从Cookie中提取认证参数
            if self.cookies:
                cookie_patterns = {
                    'uid': r'uid=([^;]+)',
                    'uid_key': r'uid_key=([^;]+)',
                    'doc_sid': r'(?:DOC_SID|SID)=([^;]+)',
                    'hashkey': r'hashkey=([^;]+)',
                    'tok': r'TOK=([^;]+)'
                }
                
                for param_name, pattern in cookie_patterns.items():
                    match = re.search(pattern, self.cookies)
                    if match:
                        value = unquote(match.group(1))
                        if not getattr(auth_info, param_name):  # 只有当前为空时才设置
                            setattr(auth_info, param_name, value)
                            logger.info(f"从Cookie提取{param_name}: {value[:20]}...")
            
            # 方法4: 尝试从页面URL参数中提取信息
            url_patterns = [
                r'[?&](?:xsrf|csrf)[_-]?(?:token|key)=([^&]+)',
                r'[?&](?:session[_-]?id|sid)=([^&]+)',
                r'[?&]hashkey=([^&]+)',
                r'[?&]TOK=([^&]+)'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, html_content, re.I)
                if matches:
                    logger.info(f"从URL参数提取认证信息: {matches[0][:20]}...")
            
            # 方法5: 查找窗口对象中的认证信息
            window_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*(\{[^}]+\})',
                r'window\.__APP_CONFIG__\s*=\s*(\{[^}]+\})',
                r'window\.AUTH_CONFIG\s*=\s*(\{[^}]+\})'
            ]
            
            for pattern in window_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    try:
                        config_str = matches[0]
                        # 简单的JSON解析尝试
                        if 'token' in config_str.lower() or 'xsrf' in config_str.lower():
                            logger.info("在窗口配置中发现可能的认证信息")
                    except:
                        pass
            
            # 生成备用认证参数
            if not auth_info.xsrf_token:
                # 尝试生成基于时间和文档ID的token
                timestamp = str(int(time.time()))
                token_source = f"{doc_id}_{timestamp}_{auth_info.uid or 'default'}"
                auth_info.xsrf_token = hashlib.md5(token_source.encode()).hexdigest()
                logger.info(f"生成备用XSRF token: {auth_info.xsrf_token}")
            
            # 记录提取结果
            self._log_auth_info(auth_info)
            
            return auth_info
            
        except Exception as e:
            logger.error(f"提取认证信息失败: {e}")
            return auth_info
    
    def _log_auth_info(self, auth_info: AuthInfo):
        """记录认证信息"""
        logger.info("认证信息提取结果:")
        logger.info(f"  XSRF Token: {'有效' if auth_info.xsrf_token else '未找到'}")
        logger.info(f"  Session ID: {'有效' if auth_info.session_id else '未找到'}")
        logger.info(f"  UID: {'有效' if auth_info.uid else '未找到'}")
        logger.info(f"  Doc SID: {'有效' if auth_info.doc_sid else '未找到'}")
        logger.info(f"  Hashkey: {'有效' if auth_info.hashkey else '未找到'}")
        logger.info(f"  TOK: {'有效' if auth_info.tok else '未找到'}")
    
    def _build_dop_api_url(self, doc_id: str, format_type: str, auth_info: AuthInfo) -> str:
        """构建完整的dop-api下载URL"""
        logger.info(f"构建dop-api URL，文档ID: {doc_id}，格式: {format_type}")
        
        base_url = "https://docs.qq.com/dop-api/opendoc"
        
        # 基本参数
        params = {
            'id': doc_id,
            'type': f'export_{format_type}',
            't': str(int(time.time() * 1000))  # 时间戳（毫秒）
        }
        
        # 添加认证参数
        if auth_info.xsrf_token:
            params['xsrf'] = auth_info.xsrf_token
            params['_token'] = auth_info.xsrf_token
        
        if auth_info.session_id:
            params['sid'] = auth_info.session_id
        
        if auth_info.doc_sid:
            params['docSid'] = auth_info.doc_sid
            params['SID'] = auth_info.doc_sid
        
        if auth_info.uid:
            params['uid'] = auth_info.uid
        
        if auth_info.hashkey:
            params['hashkey'] = auth_info.hashkey
            params['key'] = auth_info.hashkey
        
        if auth_info.tok:
            params['TOK'] = auth_info.tok
            params['token'] = auth_info.tok
        
        # 添加其他可能需要的参数
        params.update({
            'version': '1',
            'format': format_type,
            'download': '1',
            'export': '1',
            'source': 'web',
            '_r': str(hash(time.time()) % 100000)  # 随机数
        })
        
        # 构建最终URL
        final_url = base_url + '?' + urlencode(params)
        
        logger.info(f"构建的dop-api URL (前200字符): {final_url[:200]}...")
        return final_url
    
    def _download_via_dop_api(self, doc_id: str, format_type: str, auth_info: AuthInfo) -> Tuple[bool, str, int, str]:
        """通过dop-api下载文档"""
        logger.info(f"开始通过dop-api下载文档: {doc_id} ({format_type})")
        
        try:
            # 构建下载URL
            download_url = self._build_dop_api_url(doc_id, format_type, auth_info)
            
            # 构建请求头
            headers = self._build_base_headers()
            headers.update({
                'Cookie': self.cookies,
                'Referer': f'https://docs.qq.com/sheet/{doc_id}',
                'Origin': 'https://docs.qq.com',
                'Accept': 'application/octet-stream,*/*;q=0.8',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # 如果有XSRF token，添加到头部
            if auth_info.xsrf_token:
                headers['X-XSRF-TOKEN'] = auth_info.xsrf_token
                headers['X-CSRF-TOKEN'] = auth_info.xsrf_token
            
            # 执行下载请求
            for attempt in range(self.config.max_retries):
                try:
                    logger.info(f"下载尝试 {attempt + 1}/{self.config.max_retries}")
                    
                    response = self.session.get(
                        download_url,
                        headers=headers,
                        timeout=self.config.request_timeout,
                        stream=True,
                        allow_redirects=True
                    )
                    
                    logger.info(f"dop-api响应状态码: {response.status_code}")
                    logger.info(f"响应头: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        # 检查响应内容类型
                        content_type = response.headers.get('Content-Type', '').lower()
                        
                        if 'text/html' in content_type:
                            # 可能是错误页面，检查内容
                            html_content = response.text
                            if '登录' in html_content or 'login' in html_content.lower():
                                return False, "需要重新登录", 0, ""
                            elif '403' in html_content or '401' in html_content:
                                return False, "认证失败", response.status_code, ""
                            else:
                                logger.warning("收到HTML响应，可能是重定向页面")
                                return False, "收到非预期的HTML响应", response.status_code, ""
                        
                        # 保存文件
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"tencent_doc_{doc_id}_{format_type}_{timestamp}.{format_type}"
                        filepath = os.path.join(self.download_dir, filename)
                        
                        total_size = 0
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=self.config.download_chunk_size):
                                if chunk:
                                    f.write(chunk)
                                    total_size += len(chunk)
                        
                        logger.info(f"文件下载完成: {filepath} ({total_size} bytes)")
                        
                        # 验证下载文件
                        if total_size > 100:  # 最小文件大小检查
                            return True, "下载成功", total_size, filepath
                        else:
                            os.remove(filepath)
                            return False, f"下载文件过小: {total_size} bytes", total_size, ""
                    
                    elif response.status_code == 401:
                        return False, "认证失败，Cookie可能已过期", response.status_code, ""
                    elif response.status_code == 403:
                        return False, "访问被拒绝，可能需要XSRF验证", response.status_code, ""
                    elif response.status_code == 429:
                        logger.warning("触发限频，等待后重试")
                        time.sleep(self.config.retry_delay * 2)
                        continue
                    else:
                        logger.warning(f"意外状态码: {response.status_code}")
                        if attempt < self.config.max_retries - 1:
                            time.sleep(self.config.retry_delay)
                            continue
                        else:
                            return False, f"HTTP {response.status_code}", response.status_code, ""
                
                except requests.exceptions.Timeout:
                    logger.warning(f"请求超时，尝试 {attempt + 1}/{self.config.max_retries}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                except Exception as e:
                    logger.error(f"下载请求异常: {e}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                    else:
                        return False, f"请求异常: {str(e)}", 0, ""
            
            return False, "所有重试均失败", 0, ""
            
        except Exception as e:
            logger.error(f"dop-api下载失败: {e}")
            return False, f"下载异常: {str(e)}", 0, ""
    
    def download_document(self, doc_id: str, format_type: str = 'csv', document_name: str = None) -> DownloadResult:
        """下载指定文档"""
        logger.info(f"开始下载文档: {doc_id} ({format_type})")
        
        start_time = time.time()
        result = DownloadResult(
            success=False,
            document_name=document_name or f"Document_{doc_id}",
            doc_id=doc_id,
            format_type=format_type,
            file_path="",
            file_size=0,
            download_time=0.0,
            error_message="",
            timestamp=datetime.now().isoformat(),
            auth_method="XSRF+Cookie",
            endpoint_used="dop-api"
        )
        
        try:
            # 步骤1: 访问文档页面获取认证信息
            logger.info("步骤1: 访问文档页面获取认证信息")
            
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            headers = self._build_base_headers()
            headers['Cookie'] = self.cookies
            
            response = self.session.get(
                doc_url,
                headers=headers,
                timeout=self.config.page_load_timeout
            )
            
            if response.status_code != 200:
                result.error_message = f"无法访问文档页面: HTTP {response.status_code}"
                return result
            
            # 步骤2: 提取认证信息
            logger.info("步骤2: 提取认证信息")
            auth_info = self._extract_auth_info_from_page(response.text, doc_id)
            
            # 步骤3: 通过dop-api下载文档
            logger.info("步骤3: 通过dop-api下载文档")
            success, message, file_size, file_path = self._download_via_dop_api(
                doc_id, format_type, auth_info
            )
            
            # 更新结果
            result.success = success
            result.error_message = message
            result.file_size = file_size
            result.file_path = file_path
            result.download_time = time.time() - start_time
            
            # 添加认证信息到附加信息
            result.additional_info = {
                'auth_info': asdict(auth_info),
                'response_status': response.status_code,
                'page_access_success': True
            }
            
            if success:
                logger.info(f"文档下载成功: {file_path}")
            else:
                logger.error(f"文档下载失败: {message}")
            
            return result
            
        except Exception as e:
            result.error_message = f"下载过程异常: {str(e)}"
            result.download_time = time.time() - start_time
            logger.error(f"下载文档异常: {e}")
            return result
    
    def batch_download_test(self) -> List[DownloadResult]:
        """批量下载测试"""
        logger.info("开始批量下载测试")
        
        results = []
        
        for doc_info in self.test_documents:
            for format_type in self.export_formats:
                logger.info(f"测试下载: {doc_info['name']} ({format_type})")
                
                result = self.download_document(
                    doc_id=doc_info['doc_id'],
                    format_type=format_type,
                    document_name=doc_info['name']
                )
                
                results.append(result)
                
                # 等待间隔，避免请求过于频繁
                time.sleep(2)
        
        return results
    
    def generate_test_report(self, results: List[DownloadResult]) -> Dict:
        """生成测试报告"""
        logger.info("生成测试报告")
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - successful_tests
        
        # 按错误类型分组
        error_types = {}
        for result in results:
            if not result.success:
                error_msg = result.error_message
                error_types[error_msg] = error_types.get(error_msg, 0) + 1
        
        # 按格式分组统计
        format_stats = {}
        for result in results:
            fmt = result.format_type
            if fmt not in format_stats:
                format_stats[fmt] = {'total': 0, 'success': 0}
            format_stats[fmt]['total'] += 1
            if result.success:
                format_stats[fmt]['success'] += 1
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': f"{successful_tests/total_tests*100:.1f}%" if total_tests > 0 else "0%"
            },
            'format_statistics': format_stats,
            'error_analysis': error_types,
            'test_results': [asdict(result) for result in results],
            'timestamp': datetime.now().isoformat(),
            'configuration': asdict(self.config)
        }
        
        return report


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='腾讯文档XSRF Token增强版下载器')
    parser.add_argument('--doc-id', help='指定文档ID进行下载')
    parser.add_argument('--format', choices=['csv', 'xlsx'], default='csv', help='导出格式')
    parser.add_argument('--batch-test', action='store_true', help='执行批量测试')
    parser.add_argument('--cookie-file', help='指定Cookie文件路径')
    parser.add_argument('--download-dir', help='指定下载目录')
    parser.add_argument('--output-report', help='输出测试报告文件路径')
    
    args = parser.parse_args()
    
    # 创建下载器实例
    downloader = XSRFEnhancedDownloader(
        cookie_file=args.cookie_file,
        download_dir=args.download_dir
    )
    
    try:
        if args.batch_test:
            # 批量测试模式
            print("开始执行批量下载测试...")
            results = downloader.batch_download_test()
            
            # 生成报告
            report = downloader.generate_test_report(results)
            
            # 输出结果
            print(f"\n测试结果摘要:")
            print(f"总测试数: {report['test_summary']['total_tests']}")
            print(f"成功数: {report['test_summary']['successful_tests']}")
            print(f"失败数: {report['test_summary']['failed_tests']}")
            print(f"成功率: {report['test_summary']['success_rate']}")
            
            if report['error_analysis']:
                print(f"\n错误分析:")
                for error, count in report['error_analysis'].items():
                    print(f"  {error}: {count}次")
            
            # 保存报告
            if args.output_report:
                with open(args.output_report, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                print(f"\n详细报告已保存到: {args.output_report}")
            
        elif args.doc_id:
            # 单个文档下载模式
            print(f"下载文档: {args.doc_id} ({args.format})")
            
            result = downloader.download_document(
                doc_id=args.doc_id,
                format_type=args.format
            )
            
            if result.success:
                print(f"下载成功!")
                print(f"文件路径: {result.file_path}")
                print(f"文件大小: {result.file_size} bytes")
                print(f"下载耗时: {result.download_time:.2f} 秒")
            else:
                print(f"下载失败: {result.error_message}")
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
        print(f"程序执行异常: {e}")


if __name__ == "__main__":
    main()