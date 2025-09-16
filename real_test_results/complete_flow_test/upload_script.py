#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Flow Test - 上传修改后的Excel文件到腾讯文档
"""

import os
import sys
import json
from datetime import datetime

# 添加测试版本路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

from tencent_upload_automation import TencentDocUploader

async def upload_modified_file():
    """上传修改后的Excel文件"""
    print("=== 腾讯文档完整流程测试 - 上传阶段 ===")
    
    # Cookie信息 (与下载时使用的相同)
    cookies = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; dark_mode_setting=system; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; traceid=f37248fc8d; language=zh-CN; TOK=f37248fc8def26b7; hashkey=f37248fc; optimal_cdn_domain=docs2.gtimg.com; backup_cdn_domain=docs2.gtimg.com"
    
    # 文件路径
    base_dir = "/root/projects/tencent-doc-manager/real_test_results/complete_flow_test"
    modified_file = os.path.join(base_dir, "测试版本-小红书部门_修改标记.xlsx")
    
    # 检查文件是否存在
    if not os.path.exists(modified_file):
        error_msg = f"修改后的文件不存在: {modified_file}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    
    file_size = os.path.getsize(modified_file)
    print(f"准备上传文件: {modified_file}")
    print(f"文件大小: {file_size} 字节")
    
    # 创建上传器实例
    uploader = TencentDocUploader()
    
    try:
        print("启动浏览器...")
        await uploader.start_browser(headless=True)  # 使用无头模式
        
        print("应用登录Cookie...")
        await uploader.login_with_cookies(cookies)
        
        print("开始上传文件...")
        success = await uploader.upload_file_to_main_page(
            file_path=modified_file,
            homepage_url="https://docs.qq.com/desktop"
        )
        
        if success:
            print("✅ 文件上传成功!")
            
            # 记录上传结果
            upload_result = {
                "success": True,
                "file_path": modified_file,
                "file_size": file_size,
                "upload_timestamp": datetime.now().isoformat(),
                "target_url": "https://docs.qq.com/desktop",
                "upload_method": "automated_browser_upload"
            }
        else:
            print("❌ 文件上传失败")
            upload_result = {
                "success": False,
                "file_path": modified_file,
                "error": "上传过程失败",
                "upload_timestamp": datetime.now().isoformat()
            }
        
        # 保存测试结果
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "test_phase": "upload",
            "modified_file": modified_file,
            "upload_result": upload_result
        }
        
        result_file = os.path.join(base_dir, "upload_test_result.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        return upload_result
        
    except Exception as e:
        error_msg = f"上传过程异常: {e}"
        print(f"❌ {error_msg}")
        
        upload_result = {
            "success": False,
            "file_path": modified_file,
            "error": error_msg,
            "upload_timestamp": datetime.now().isoformat()
        }
        
        # 保存错误结果
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "test_phase": "upload_error",
            "modified_file": modified_file,
            "upload_result": upload_result
        }
        
        result_file = os.path.join(base_dir, "upload_error_result.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        return upload_result
        
    finally:
        try:
            await uploader.cleanup()
        except:
            pass

def main():
    """同步入口函数"""
    import asyncio
    
    try:
        # 在同步环境中运行异步代码
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，创建新的线程执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, upload_modified_file())
                result = future.result()
        except RuntimeError:
            # 如果没有运行的事件循环，直接运行
            result = asyncio.run(upload_modified_file())
        
        return result
        
    except Exception as e:
        print(f"❌ 主函数执行失败: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = main()
    if result.get('success'):
        print("🎉 上传阶段完成!")
    else:
        print(f"❌ 上传阶段失败: {result.get('error')}")