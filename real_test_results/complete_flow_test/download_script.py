#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Flow Test - 下载腾讯文档
"""

import os
import sys
import json
from datetime import datetime

# 添加测试版本路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

from tencent_export_automation import TencentDocAutoExporter

def main():
    print("=== 腾讯文档完整流程测试 - 下载阶段 ===")
    
    # Cookie信息 (从参考文件读取的)
    cookies = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; dark_mode_setting=system; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; traceid=f37248fc8d; language=zh-CN; TOK=f37248fc8def26b7; hashkey=f37248fc; optimal_cdn_domain=docs2.gtimg.com; backup_cdn_domain=docs2.gtimg.com"
    
    # 目标文档URL
    doc_url = "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN"
    
    # 下载目录
    download_dir = "/root/projects/tencent-doc-manager/real_test_results/complete_flow_test"
    
    # 创建导出器实例
    exporter = TencentDocAutoExporter(
        download_dir=download_dir,
        enable_version_management=False  # 禁用版本管理，简化测试
    )
    
    # 执行下载
    try:
        print(f"开始下载文档: {doc_url}")
        print(f"下载目录: {download_dir}")
        
        # 使用统一接口进行下载
        result = exporter.export_document(
            url=doc_url,
            cookies=cookies,
            format='excel',  # 要求Excel格式
            download_dir=download_dir
        )
        
        # 记录结果
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "test_phase": "download",
            "document_url": doc_url,
            "target_format": "excel",
            "success": result.get('success', False),
            "downloaded_files": result.get('files', []),
            "primary_file": result.get('file_path'),
            "error": result.get('error'),
            "details": result
        }
        
        # 保存测试结果
        result_file = os.path.join(download_dir, "download_test_result.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        if result.get('success'):
            print(f"✅ 下载成功!")
            print(f"主文件: {result.get('file_path')}")
            print(f"所有文件: {result.get('files')}")
            
            # 验证文件存在且为Excel格式
            primary_file = result.get('file_path')
            if primary_file and os.path.exists(primary_file):
                if primary_file.lower().endswith('.xlsx'):
                    print(f"✅ 确认文件格式为XLSX: {os.path.basename(primary_file)}")
                    file_size = os.path.getsize(primary_file)
                    print(f"文件大小: {file_size} 字节")
                    
                    return {
                        "success": True,
                        "file_path": primary_file,
                        "file_size": file_size,
                        "format": "xlsx"
                    }
                else:
                    print(f"⚠️ 文件格式不是XLSX: {primary_file}")
                    return {
                        "success": False,
                        "error": f"文件格式不正确: {primary_file}"
                    }
            else:
                print(f"❌ 文件不存在: {primary_file}")
                return {
                    "success": False,
                    "error": f"下载的文件不存在: {primary_file}"
                }
        else:
            print(f"❌ 下载失败: {result.get('error')}")
            return {
                "success": False,
                "error": result.get('error')
            }
            
    except Exception as e:
        error_msg = f"下载过程异常: {e}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

if __name__ == "__main__":
    main()