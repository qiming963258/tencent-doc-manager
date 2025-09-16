#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XSRF增强版下载器测试脚本
用于快速验证下载器的各项功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

from xsrf_enhanced_downloader import XSRFEnhancedDownloader
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_download():
    """测试单个文档下载"""
    print("=" * 60)
    print("测试单个文档下载功能")
    print("=" * 60)
    
    downloader = XSRFEnhancedDownloader()
    
    # 使用第一个测试文档
    test_doc = {
        'name': '测试版本-小红书部门',
        'doc_id': 'DWEVjZndkR2xVSWJN'
    }
    
    print(f"正在下载: {test_doc['name']}")
    print(f"文档ID: {test_doc['doc_id']}")
    
    result = downloader.download_document(
        doc_id=test_doc['doc_id'],
        format_type='csv',
        document_name=test_doc['name']
    )
    
    print(f"\n下载结果:")
    print(f"成功: {result.success}")
    print(f"错误信息: {result.error_message}")
    print(f"文件路径: {result.file_path}")
    print(f"文件大小: {result.file_size} bytes")
    print(f"下载耗时: {result.download_time:.2f} 秒")
    print(f"认证方法: {result.auth_method}")
    
    return result

def test_batch_download():
    """测试批量下载功能"""
    print("=" * 60)
    print("测试批量下载功能")
    print("=" * 60)
    
    downloader = XSRFEnhancedDownloader()
    
    print("开始批量下载测试...")
    results = downloader.batch_download_test()
    
    print(f"\n批量下载完成，共测试 {len(results)} 个文档")
    
    # 统计结果
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/len(results)*100:.1f}%")
    
    # 显示详细结果
    print("\n详细结果:")
    for i, result in enumerate(results, 1):
        status = "✅" if result.success else "❌"
        print(f"{i:2d}. {status} {result.document_name} ({result.format_type})")
        if not result.success:
            print(f"     错误: {result.error_message}")
        else:
            print(f"     文件: {os.path.basename(result.file_path)} ({result.file_size} bytes)")
    
    return results

def test_auth_extraction():
    """测试认证信息提取功能"""
    print("=" * 60)
    print("测试认证信息提取功能")
    print("=" * 60)
    
    downloader = XSRFEnhancedDownloader()
    
    # 模拟HTML内容进行测试
    test_html = '''
    <html>
    <head>
        <meta name="csrf-token" content="test_csrf_token_12345">
        <meta name="xsrf-token" content="test_xsrf_token_67890">
    </head>
    <body>
        <script>
            window.__INITIAL_STATE__ = {
                "user": {
                    "uid": "144115414584628119",
                    "session_id": "test_session_12345"
                },
                "auth": {
                    "xsrf_token": "script_xsrf_token_abcdef",
                    "hashkey": "test_hashkey_xyz"
                }
            };
            
            var TOK = "test_tok_token_123456";
            var DOC_SID = "test_doc_sid_789012";
        </script>
    </body>
    </html>
    '''
    
    print("从模拟HTML页面提取认证信息...")
    auth_info = downloader._extract_auth_info_from_page(test_html, "DWEVjZndkR2xVSWJN")
    
    print(f"提取结果:")
    print(f"XSRF Token: {auth_info.xsrf_token}")
    print(f"Session ID: {auth_info.session_id}")
    print(f"UID: {auth_info.uid}")
    print(f"Doc SID: {auth_info.doc_sid}")
    print(f"Hashkey: {auth_info.hashkey}")
    print(f"TOK: {auth_info.tok}")
    
    return auth_info

def test_dop_api_url_building():
    """测试dop-api URL构建功能"""
    print("=" * 60)
    print("测试dop-api URL构建功能")
    print("=" * 60)
    
    from xsrf_enhanced_downloader import AuthInfo
    
    downloader = XSRFEnhancedDownloader()
    
    # 创建测试认证信息
    auth_info = AuthInfo(
        xsrf_token="test_xsrf_12345",
        session_id="test_session_67890",
        uid="144115414584628119",
        doc_sid="test_doc_sid_abc",
        hashkey="test_hashkey_xyz",
        tok="test_tok_123"
    )
    
    doc_id = "DWEVjZndkR2xVSWJN"
    format_type = "csv"
    
    print(f"构建dop-api URL:")
    print(f"文档ID: {doc_id}")
    print(f"格式: {format_type}")
    
    url = downloader._build_dop_api_url(doc_id, format_type, auth_info)
    
    print(f"\n生成的URL:")
    print(url)
    
    # 分析URL参数
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    print(f"\nURL参数分析:")
    for key, value in params.items():
        print(f"  {key}: {value[0] if value else 'None'}")
    
    return url

def save_test_report(results, filename=None):
    """保存测试报告"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'/root/projects/tencent-doc-manager/test_results/xsrf_test_report_{timestamp}.json'
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 准备报告数据
    report_data = {
        'test_timestamp': datetime.now().isoformat(),
        'test_type': 'XSRF Enhanced Downloader Test',
        'results': []
    }
    
    for result in results:
        report_data['results'].append({
            'success': result.success,
            'document_name': result.document_name,
            'doc_id': result.doc_id,
            'format_type': result.format_type,
            'file_path': result.file_path,
            'file_size': result.file_size,
            'download_time': result.download_time,
            'error_message': result.error_message,
            'auth_method': result.auth_method,
            'endpoint_used': result.endpoint_used
        })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试报告已保存到: {filename}")
    return filename

def main():
    """主测试函数"""
    print("腾讯文档XSRF增强版下载器 - 功能测试")
    print("=" * 60)
    
    try:
        # 测试1: 认证信息提取
        print("\n【测试1】认证信息提取功能")
        test_auth_extraction()
        
        # 测试2: URL构建功能
        print("\n【测试2】dop-api URL构建功能")
        test_dop_api_url_building()
        
        # 测试3: 单个文档下载
        print("\n【测试3】单个文档下载功能")
        single_result = test_single_download()
        
        # 如果单个下载成功，继续批量测试
        if single_result.success:
            print("\n【测试4】批量下载功能")
            batch_results = test_batch_download()
            
            # 保存测试报告
            save_test_report(batch_results)
        else:
            print("\n⚠️ 由于单个下载失败，跳过批量测试")
            print("请检查Cookie配置和网络连接")
    
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        print(f"测试执行异常: {e}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()