#!/usr/bin/env python3
"""
通过8089 API触发真实工作流测试
监控完整的下载-对比-打分-上传链路
"""

import asyncio
import aiohttp
import json
import logging
import time
from pathlib import Path
from datetime import datetime
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Real8089WorkflowTest:
    """真实的8089工作流测试"""

    def __init__(self):
        self.base_dir = Path('/root/projects/tencent-doc-manager')
        self.api_base = 'http://localhost:8089'
        self.test_url = 'https://docs.qq.com/sheet/DWEFNU25TemFnZXJN'

    async def prepare_config(self):
        """准备配置：确保有URL和Cookie"""
        logger.info("📋 Step 1: 准备配置")

        # 确保Cookie存在
        cookie_file = self.base_dir / 'config/cookies.json'
        if not cookie_file.exists():
            logger.error("❌ Cookie文件不存在")
            return False

        with open(cookie_file) as f:
            cookie_data = json.load(f)
            if not cookie_data.get('current_cookies'):
                logger.error("❌ Cookie为空")
                return False
            logger.info("✅ Cookie配置有效")

        # 配置下载链接
        async with aiohttp.ClientSession() as session:
            config_data = {
                "links": [
                    {
                        "name": "测试文档-出国销售计划表",
                        "url": self.test_url,
                        "category": "测试",
                        "description": "8089工作流测试文档"
                    }
                ]
            }

            # 保存下载链接配置
            async with session.post(
                f'{self.api_base}/api/save-download-links',
                json=config_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ 配置保存成功: {result}")
                    return True
                else:
                    logger.error(f"❌ 配置保存失败: {response.status}")
                    return False

    async def prepare_baseline(self):
        """准备基线文件（如果需要）"""
        logger.info("📋 Step 2: 准备基线文件")

        # 检查是否已有基线
        from production.core_modules.week_time_manager import WeekTimeManager
        week_mgr = WeekTimeManager()
        week_info = week_mgr.get_current_week_info()

        baseline_dir = self.base_dir / f"csv_versions/2025_W{week_info['week_number']}/baseline"
        baseline_files = list(baseline_dir.glob("*出国销售*.csv"))

        if baseline_files:
            logger.info(f"✅ 发现基线文件: {baseline_files[0].name}")
            return str(baseline_files[0])
        else:
            logger.info("⚠️ 未发现基线文件，将下载作为基线")
            # 先下载一个作为基线
            baseline_dir.mkdir(parents=True, exist_ok=True)

            # 使用PlaywrightDownloader下载基线
            from production.core_modules.playwright_downloader import PlaywrightDownloader

            cookie_file = self.base_dir / 'config/cookies.json'
            with open(cookie_file) as f:
                cookie_data = json.load(f)
            cookie_string = cookie_data.get('current_cookies', '')

            downloader = PlaywrightDownloader()
            result = await downloader.download(
                url=self.test_url,
                cookies=cookie_string,
                format='csv',
                download_dir=str(baseline_dir)
            )

            if result and result.get('success'):
                baseline_file = result.get('file_path')
                # 重命名为baseline
                new_name = baseline_file.replace('midweek', 'baseline')
                Path(baseline_file).rename(new_name)
                logger.info(f"✅ 创建基线文件: {Path(new_name).name}")
                return new_name
            else:
                logger.error("❌ 无法创建基线文件")
                return None

    async def trigger_workflow(self):
        """触发8089工作流"""
        logger.info("🚀 Step 3: 触发8089工作流")

        async with aiohttp.ClientSession() as session:
            # 调用start-download API
            logger.info("📡 调用 /api/start-download")

            async with session.post(
                f'{self.api_base}/api/start-download',
                json={},
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        logger.info(f"✅ 工作流启动成功: {result}")
                        return True
                    else:
                        logger.error(f"❌ 工作流启动失败: {result.get('error')}")
                        return False
                else:
                    logger.error(f"❌ API调用失败: {response.status}")
                    text = await response.text()
                    logger.error(f"响应内容: {text[:500]}")
                    return False

    async def monitor_progress(self, timeout=120):
        """监控工作流进度"""
        logger.info("📊 Step 4: 监控工作流进度")

        start_time = time.time()
        last_log_count = 0

        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < timeout:
                # 获取工作流状态
                try:
                    async with session.get(
                        f'{self.api_base}/api/workflow-status'
                    ) as response:
                        if response.status == 200:
                            status = await response.json()
                            if status.get('running'):
                                logger.info(f"🔄 工作流运行中: {status.get('current_step', '未知步骤')}")

                                # 获取日志
                                logs = status.get('logs', [])
                                if len(logs) > last_log_count:
                                    for log in logs[last_log_count:]:
                                        logger.info(f"  📝 {log}")
                                    last_log_count = len(logs)
                            else:
                                logger.info("✅ 工作流完成")
                                return status
                except:
                    pass

                await asyncio.sleep(2)

        logger.warning("⏱️ 监控超时")
        return None

    async def check_results(self):
        """检查工作流结果"""
        logger.info("🔍 Step 5: 检查工作流结果")

        results = {}

        # 1. 检查是否有新的CSV文件
        from production.core_modules.week_time_manager import WeekTimeManager
        week_mgr = WeekTimeManager()
        week_info = week_mgr.get_current_week_info()

        midweek_dir = self.base_dir / f"csv_versions/2025_W{week_info['week_number']}/midweek"
        recent_files = sorted(
            midweek_dir.glob("*.csv"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if recent_files:
            latest_csv = recent_files[0]
            # 检查是否是最近5分钟内的
            if time.time() - latest_csv.stat().st_mtime < 300:
                logger.info(f"✅ 发现新下载的CSV: {latest_csv.name}")
                results['csv_file'] = str(latest_csv)

        # 2. 检查是否有新的综合打分文件
        scoring_dir = self.base_dir / 'scoring_results/comprehensive'
        scoring_files = sorted(
            scoring_dir.glob('comprehensive_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if scoring_files:
            latest_scoring = scoring_files[0]
            if time.time() - latest_scoring.stat().st_mtime < 300:
                logger.info(f"✅ 发现新的综合打分: {latest_scoring.name}")

                with open(latest_scoring) as f:
                    scoring_data = json.load(f)
                    logger.info(f"   - 参数总数: {scoring_data.get('metadata', {}).get('total_params', 0)}")
                    logger.info(f"   - 表格数: {len(scoring_data.get('table_details', []))}")

                    # 检查是否包含9类必需参数
                    required_keys = [
                        'table_names', 'column_names', 'heatmap_data',
                        'table_details', 'hover_data', 'statistics'
                    ]
                    missing_keys = [k for k in required_keys if k not in scoring_data]
                    if missing_keys:
                        logger.warning(f"   ⚠️ 缺少参数: {missing_keys}")
                    else:
                        logger.info("   ✅ 包含所有9类必需参数")

                results['scoring_file'] = str(latest_scoring)

        # 3. 检查是否有新的Excel文件
        excel_dirs = [
            self.base_dir / "excel_outputs/marked",
            self.base_dir / "excel_outputs/complete_with_upload",
            self.base_dir / "excel_outputs"
        ]

        for excel_dir in excel_dirs:
            if excel_dir.exists():
                excel_files = sorted(
                    excel_dir.glob("*.xlsx"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )

                if excel_files:
                    latest_excel = excel_files[0]
                    if time.time() - latest_excel.stat().st_mtime < 300:
                        logger.info(f"✅ 发现新的Excel: {latest_excel.name}")
                        results['excel_file'] = str(latest_excel)
                        break

        # 4. 检查是否有URL返回
        url_file = self.base_dir / 'scoring_results/comprehensive/table_urls.json'
        if url_file.exists():
            with open(url_file) as f:
                url_data = json.load(f)
                if url_data.get('table_urls'):
                    for name, url in url_data['table_urls'].items():
                        logger.info(f"✅ 发现上传URL: {url}")
                        results['upload_url'] = url
                        break

        return results

    async def run_test(self):
        """运行完整测试"""
        logger.info("=" * 70)
        logger.info("🚀 开始8089真实工作流测试")
        logger.info("=" * 70)

        # 准备配置
        if not await self.prepare_config():
            logger.error("❌ 配置准备失败")
            return None

        # 准备基线
        baseline = await self.prepare_baseline()
        if baseline:
            logger.info(f"📊 基线文件: {Path(baseline).name}")

        # 触发工作流
        if not await self.trigger_workflow():
            logger.error("❌ 工作流触发失败")
            return None

        # 监控进度
        await self.monitor_progress()

        # 等待处理完成
        logger.info("⏳ 等待处理完成...")
        await asyncio.sleep(10)

        # 检查结果
        results = await self.check_results()

        logger.info("=" * 70)
        if results.get('upload_url'):
            logger.info("✅ 测试成功！")
            logger.info(f"🔗 最终URL: {results['upload_url']}")
        else:
            logger.warning("⚠️ 未获取到最终URL")
            logger.info("生成的文件:")
            for key, value in results.items():
                logger.info(f"  - {key}: {Path(value).name if value else '无'}")

        logger.info("=" * 70)

        return results.get('upload_url')

async def main():
    """主函数"""
    tester = Real8089WorkflowTest()
    final_url = await tester.run_test()

    if final_url:
        print(f"\n" + "=" * 70)
        print(f"🎯 最终返回的URL: {final_url}")
        print(f"=" * 70)
        print(f"\n请验证以下内容:")
        print(f"1. 访问URL查看是否有涂色: {final_url}")
        print(f"2. 检查8089 UI是否更新: http://202.140.143.88:8089/")
        print(f"3. 点击表格名称是否跳转到正确URL")
    else:
        print(f"\n❌ 未获取到最终URL")

    return final_url

if __name__ == "__main__":
    result = asyncio.run(main())