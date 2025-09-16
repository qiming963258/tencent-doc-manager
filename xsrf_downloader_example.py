#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档XSRF Token增强版下载器 - 使用示例

本示例演示如何使用增强版下载器进行各种下载操作
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

from xsrf_enhanced_downloader import XSRFEnhancedDownloader

def example_single_download():
    """示例1: 单个文档下载"""
    print("=" * 50)
    print("示例1: 单个文档下载")
    print("=" * 50)
    
    # 创建下载器实例
    downloader = XSRFEnhancedDownloader()
    
    # 下载单个文档
    result = downloader.download_document(
        doc_id="DWEVjZndkR2xVSWJN",  # 文档ID
        format_type="csv",           # 导出格式
        document_name="测试文档"      # 文档名称
    )
    
    # 检查结果
    if result.success:
        print(f"✅ 下载成功!")
        print(f"   文件路径: {result.file_path}")
        print(f"   文件大小: {result.file_size} bytes")
        print(f"   下载耗时: {result.download_time:.2f} 秒")
    else:
        print(f"❌ 下载失败: {result.error_message}")
    
    return result

def example_batch_download():
    """示例2: 批量下载"""
    print("=" * 50)
    print("示例2: 批量下载多个文档")
    print("=" * 50)
    
    # 创建下载器实例
    downloader = XSRFEnhancedDownloader()
    
    # 批量下载所有测试文档
    results = downloader.batch_download_test()
    
    # 统计结果
    successful = sum(1 for r in results if r.success)
    total = len(results)
    
    print(f"批量下载完成:")
    print(f"  成功: {successful}/{total}")
    print(f"  成功率: {successful/total*100:.1f}%")
    
    # 显示详细结果
    for i, result in enumerate(results, 1):
        status = "✅" if result.success else "❌"
        print(f"  {i}. {status} {result.document_name} ({result.format_type})")
    
    return results

def example_custom_download():
    """示例3: 自定义配置下载"""
    print("=" * 50)
    print("示例3: 自定义配置下载")
    print("=" * 50)
    
    # 使用自定义配置创建下载器
    custom_download_dir = "/root/projects/tencent-doc-manager/custom_downloads"
    downloader = XSRFEnhancedDownloader(download_dir=custom_download_dir)
    
    # 下载为Excel格式
    result = downloader.download_document(
        doc_id="DRFppYm15RGZ2WExN",
        format_type="xlsx",
        document_name="自定义下载测试"
    )
    
    if result.success:
        print(f"✅ 自定义下载成功!")
        print(f"   文件路径: {result.file_path}")
        print(f"   下载目录: {custom_download_dir}")
    else:
        print(f"❌ 自定义下载失败: {result.error_message}")
    
    return result

def example_command_line_usage():
    """示例4: 命令行用法演示"""
    print("=" * 50)
    print("示例4: 命令行用法")
    print("=" * 50)
    
    print("命令行用法示例:")
    print()
    print("1. 单个文档下载:")
    print("   python3 xsrf_enhanced_downloader.py --doc-id DWEVjZndkR2xVSWJN --format csv")
    print()
    print("2. 批量测试:")
    print("   python3 xsrf_enhanced_downloader.py --batch-test")
    print()
    print("3. 输出测试报告:")
    print("   python3 xsrf_enhanced_downloader.py --batch-test --output-report report.json")
    print()
    print("4. 自定义下载目录:")
    print("   python3 xsrf_enhanced_downloader.py --doc-id DWEVjZndkR2xVSWJN --download-dir ./my_downloads")

def example_generate_report(results):
    """示例5: 生成测试报告"""
    print("=" * 50)
    print("示例5: 生成测试报告")
    print("=" * 50)
    
    if not results:
        print("没有可用的测试结果")
        return
    
    # 创建下载器实例
    downloader = XSRFEnhancedDownloader()
    
    # 生成报告
    report = downloader.generate_test_report(results)
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"/root/projects/tencent-doc-manager/example_report_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"测试报告已生成:")
    print(f"  文件路径: {report_file}")
    print(f"  总测试数: {report['test_summary']['total_tests']}")
    print(f"  成功率: {report['test_summary']['success_rate']}")

def main():
    """主函数 - 运行所有示例"""
    print("腾讯文档XSRF Token增强版下载器 - 使用示例")
    print("=" * 60)
    
    try:
        # 示例1: 单个文档下载
        single_result = example_single_download()
        
        # 示例2: 批量下载
        batch_results = example_batch_download()
        
        # 示例3: 自定义配置下载
        custom_result = example_custom_download()
        
        # 示例4: 命令行用法说明
        example_command_line_usage()
        
        # 示例5: 生成测试报告
        example_generate_report(batch_results)
        
        print("\n" + "=" * 60)
        print("所有示例运行完成!")
        
    except Exception as e:
        print(f"示例运行异常: {e}")

if __name__ == "__main__":
    main()