#!/usr/bin/env python3
"""
真实上传测试脚本
深度分析上传问题并尝试真实上传
"""

import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append('/root/projects/tencent-doc-manager')


async def test_upload_with_v3():
    """使用V3上传器测试上传"""

    logger.info("="*70)
    logger.info("🚀 深度分析：尝试真实上传到腾讯文档")
    logger.info("="*70)

    # 检查Cookie
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    if cookie_file.exists():
        with open(cookie_file) as f:
            cookie_data = json.load(f)

        last_update = cookie_data.get('last_update', 'Unknown')
        logger.info(f"📋 Cookie状态:")
        logger.info(f"   最后更新: {last_update}")
        logger.info(f"   是否有效: {cookie_data.get('is_valid', False)}")

        # 检查Cookie是否过期（超过7天）
        from datetime import datetime
        try:
            last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            days_old = (datetime.now() - last_update_time.replace(tzinfo=None)).days
            if days_old > 7:
                logger.warning(f"⚠️ Cookie可能已过期 ({days_old}天前更新)")
            else:
                logger.info(f"✅ Cookie相对较新 ({days_old}天前更新)")
        except:
            pass

        cookies = cookie_data.get('current_cookies', '')
    else:
        logger.error("❌ Cookie文件不存在!")
        return None

    # 导入上传模块
    try:
        from production.core_modules.tencent_doc_upload_production_v3 import TencentDocProductionUploaderV3

        logger.info("\n📦 使用V3上传器...")

        # 创建上传器实例
        uploader = TencentDocProductionUploaderV3(headless=True)

        # 要上传的文件
        test_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/colored_test_REAL_20250921_193215.xlsx'

        if not Path(test_file).exists():
            logger.error(f"❌ 测试文件不存在: {test_file}")
            return None

        logger.info(f"📄 准备上传文件: {Path(test_file).name}")
        logger.info(f"   文件大小: {Path(test_file).stat().st_size:,} bytes")

        # 异步执行上传
        async with uploader:
            # 设置Cookie
            result = await uploader.apply_cookies(cookies)
            if result:
                logger.info("✅ Cookie设置成功")
            else:
                logger.warning("⚠️ Cookie设置可能失败")

            # 导航到腾讯文档
            await uploader.navigate_to_tencent_docs()

            # 验证登录状态
            is_logged_in = await uploader.verify_login_status()
            if is_logged_in:
                logger.info("✅ 已登录腾讯文档")
            else:
                logger.error("❌ 未登录，需要更新Cookie")
                return None

            # 执行上传
            logger.info("\n🚀 开始上传...")
            upload_result = await uploader.upload_file(test_file)

            if upload_result['success']:
                logger.info(f"✅ 上传成功!")
                logger.info(f"🔗 文档URL: {upload_result['url']}")
                return upload_result['url']
            else:
                logger.error(f"❌ 上传失败: {upload_result['message']}")
                return None

    except ImportError as e:
        logger.error(f"❌ 无法导入上传模块: {e}")
        logger.info("尝试使用备用方案...")

        # 尝试其他上传方法
        return await test_alternative_upload()

    except Exception as e:
        logger.error(f"❌ 上传过程出错: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_alternative_upload():
    """使用备用上传方案"""

    logger.info("\n🔄 尝试备用上传方案...")

    # 方案1: 使用requests直接POST
    try:
        import requests

        # 读取Cookie
        cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
        with open(cookie_file) as f:
            cookie_data = json.load(f)

        cookies_str = cookie_data.get('current_cookies', '')

        # 解析Cookie为字典
        cookies = {}
        for item in cookies_str.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key] = value

        # 尝试获取上传接口
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://docs.qq.com/',
            'Origin': 'https://docs.qq.com',
        }

        # 检查登录状态
        check_url = 'https://docs.qq.com/api/user/info'
        response = requests.get(check_url, cookies=cookies, headers=headers)

        if response.status_code == 200:
            logger.info("✅ Cookie有效，已认证")

            # 这里应该实现实际的上传逻辑
            # 但腾讯文档的上传API比较复杂，需要多步骤
            logger.info("⚠️ 备用方案需要更复杂的实现")
            return None
        else:
            logger.error(f"❌ 认证失败: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"❌ 备用方案失败: {e}")
        return None


async def analyze_upload_problem():
    """深度分析上传问题"""

    logger.info("\n" + "="*70)
    logger.info("🔍 深度分析：为什么文件没有上传到腾讯文档")
    logger.info("="*70)

    problems = []

    # 1. 检查Cookie
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    if not cookie_file.exists():
        problems.append("Cookie文件不存在")
    else:
        with open(cookie_file) as f:
            cookie_data = json.load(f)

        # 检查Cookie年龄
        last_update = cookie_data.get('last_update', '')
        if last_update:
            try:
                from datetime import datetime
                last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                days_old = (datetime.now() - last_update_time.replace(tzinfo=None)).days

                if days_old > 7:
                    problems.append(f"Cookie可能已过期 ({days_old}天前更新)")
                elif days_old > 3:
                    problems.append(f"Cookie较旧 ({days_old}天前更新)，可能需要更新")
            except:
                problems.append("无法解析Cookie更新时间")

    # 2. 检查上传模块
    try:
        from production.core_modules import tencent_doc_upload_production_v3
        logger.info("✅ V3上传模块存在")
    except ImportError:
        problems.append("V3上传模块无法导入")

    # 3. 检查Playwright
    try:
        import playwright
        logger.info("✅ Playwright已安装")
    except ImportError:
        problems.append("Playwright未安装 (需要: pip install playwright)")

    # 4. 检查文件
    test_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/colored_test_REAL_20250921_193215.xlsx'
    if not Path(test_file).exists():
        problems.append(f"测试文件不存在: {test_file}")
    else:
        logger.info(f"✅ 测试文件存在 ({Path(test_file).stat().st_size:,} bytes)")

    # 5. 总结问题
    logger.info("\n📊 问题分析结果:")
    if problems:
        for i, problem in enumerate(problems, 1):
            logger.warning(f"   {i}. {problem}")
    else:
        logger.info("   ✅ 未发现明显问题")

    # 6. 根本原因
    logger.info("\n🎯 根本原因分析:")
    logger.info("   1. 之前的测试只是【模拟】了上传，没有真正执行")
    logger.info("   2. 真实上传需要有效的Cookie认证")
    logger.info("   3. Cookie可能已过期（最后更新: 09-19）")
    logger.info("   4. 上传需要浏览器自动化（Playwright）")

    # 7. 解决方案
    logger.info("\n💡 解决方案:")
    logger.info("   1. 更新Cookie (从浏览器导出新的Cookie)")
    logger.info("   2. 安装Playwright: pip install playwright")
    logger.info("   3. 安装浏览器: playwright install chromium")
    logger.info("   4. 运行真实上传脚本")

    return problems


def main():
    """主函数"""

    # 先分析问题
    asyncio.run(analyze_upload_problem())

    # 尝试上传
    logger.info("\n" + "="*70)
    logger.info("📤 尝试真实上传...")
    logger.info("="*70)

    url = asyncio.run(test_upload_with_v3())

    if url:
        logger.info("\n" + "="*70)
        logger.info("🎉 上传成功!")
        logger.info(f"🔗 访问链接: {url}")
        logger.info("="*70)
    else:
        logger.info("\n" + "="*70)
        logger.info("❌ 上传失败")
        logger.info("="*70)

        # 提供手动上传指南
        logger.info("\n📋 手动上传指南:")
        logger.info("1. 下载文件到本地:")
        logger.info("   /root/projects/tencent-doc-manager/excel_outputs/marked/colored_test_REAL_20250921_193215.xlsx")
        logger.info("")
        logger.info("2. 访问腾讯文档: https://docs.qq.com")
        logger.info("3. 登录您的账号")
        logger.info("4. 点击'新建' -> '导入' -> '本地文件'")
        logger.info("5. 选择下载的Excel文件")
        logger.info("6. 等待上传完成，获取分享链接")

    return url


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)