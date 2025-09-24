#!/usr/bin/env python3
"""
批量工作流协调器 - 安全的批量处理扩展
不修改现有单文档处理逻辑，仅作为包装层
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import asyncio
import concurrent.futures

# 导入现有的单文档处理函数（不修改原函数）
import sys
sys.path.append('/root/projects/tencent-doc-manager')
from production_integrated_test_system_8093 import run_complete_workflow

logger = logging.getLogger(__name__)

class BatchWorkflowOrchestrator:
    """批量工作流协调器 - 向后兼容的扩展"""

    def __init__(self, mode: str = "sequential"):
        """
        Args:
            mode: 处理模式
                - "sequential": 串行处理（安全，默认）
                - "parallel": 并行处理（快速）
                - "single": 单文档模式（完全兼容旧版）
        """
        self.mode = mode
        self.results = []
        self.detailed_files = []

    def process_batch(self, document_pairs: List[Dict], cookie: str,
                      advanced_settings: dict = None) -> Dict:
        """
        批量处理多个文档对

        Args:
            document_pairs: 文档对列表
                [
                    {
                        "baseline_url": "https://...",
                        "target_url": "https://...",
                        "name": "出国销售计划表"
                    },
                    ...
                ]
            cookie: 腾讯文档cookie
            advanced_settings: 高级设置

        Returns:
            批量处理结果
        """

        # 如果是单文档模式，直接调用原函数
        if self.mode == "single" or len(document_pairs) == 1:
            pair = document_pairs[0]
            return run_complete_workflow(
                pair["baseline_url"],
                pair["target_url"],
                cookie,
                advanced_settings
            )

        # 批量处理模式
        start_time = datetime.now()
        batch_id = start_time.strftime("%Y%m%d_%H%M%S")

        logger.info(f"开始批量处理 {len(document_pairs)} 个文档对")

        # 串行处理（最安全）
        if self.mode == "sequential":
            for idx, pair in enumerate(document_pairs, 1):
                logger.info(f"处理第 {idx}/{len(document_pairs)} 个文档: {pair.get('name', 'unknown')}")
                try:
                    result = run_complete_workflow(
                        pair["baseline_url"],
                        pair["target_url"],
                        cookie,
                        advanced_settings
                    )
                    self.results.append({
                        "document": pair.get("name", f"文档{idx}"),
                        "status": "success",
                        "result": result
                    })

                    # 记录详细打分文件路径
                    if result and "detailed_score_file" in result:
                        self.detailed_files.append(result["detailed_score_file"])

                except Exception as e:
                    logger.error(f"处理文档 {pair.get('name', 'unknown')} 失败: {e}")
                    self.results.append({
                        "document": pair.get("name", f"文档{idx}"),
                        "status": "failed",
                        "error": str(e)
                    })

        # 并行处理（更快但需要更多资源）
        elif self.mode == "parallel":
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for idx, pair in enumerate(document_pairs, 1):
                    future = executor.submit(
                        self._process_single_document,
                        pair, cookie, advanced_settings, idx
                    )
                    futures.append((future, pair, idx))

                for future, pair, idx in futures:
                    try:
                        result = future.result(timeout=300)  # 5分钟超时
                        self.results.append(result)
                        if result["status"] == "success" and "detailed_score_file" in result.get("result", {}):
                            self.detailed_files.append(result["result"]["detailed_score_file"])
                    except Exception as e:
                        logger.error(f"并行处理失败: {e}")
                        self.results.append({
                            "document": pair.get("name", f"文档{idx}"),
                            "status": "failed",
                            "error": str(e)
                        })

        # 生成批量处理摘要
        end_time = datetime.now()
        summary = {
            "batch_id": batch_id,
            "mode": self.mode,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": (end_time - start_time).total_seconds(),
            "total_documents": len(document_pairs),
            "successful": sum(1 for r in self.results if r["status"] == "success"),
            "failed": sum(1 for r in self.results if r["status"] == "failed"),
            "results": self.results,
            "detailed_files": self.detailed_files
        }

        # 保存批量处理结果
        self._save_batch_results(summary)

        # 触发综合打分聚合
        if self.detailed_files and len(self.detailed_files) > 1:
            logger.info(f"准备聚合 {len(self.detailed_files)} 个详细打分文件")
            self._trigger_comprehensive_aggregation()

        return summary

    def _process_single_document(self, pair: Dict, cookie: str,
                                advanced_settings: dict, idx: int) -> Dict:
        """处理单个文档对（内部方法）"""
        try:
            result = run_complete_workflow(
                pair["baseline_url"],
                pair["target_url"],
                cookie,
                advanced_settings
            )
            return {
                "document": pair.get("name", f"文档{idx}"),
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "document": pair.get("name", f"文档{idx}"),
                "status": "failed",
                "error": str(e)
            }

    def _save_batch_results(self, summary: Dict):
        """保存批量处理结果"""
        batch_dir = Path("/root/projects/tencent-doc-manager/batch_results")
        batch_dir.mkdir(exist_ok=True)

        filename = f"batch_{summary['batch_id']}.json"
        filepath = batch_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"批量处理结果已保存: {filepath}")

    def _trigger_comprehensive_aggregation(self):
        """触发综合打分聚合"""
        try:
            from production.core_modules.multi_doc_aggregator import MultiDocumentAggregator
            aggregator = MultiDocumentAggregator()
            aggregator.aggregate_all_detailed_scores(self.detailed_files)
            logger.info("综合打分聚合完成")
        except ImportError:
            logger.warning("多文档聚合器尚未实现，将在下一步创建")
        except Exception as e:
            logger.error(f"综合打分聚合失败: {e}")


# 向后兼容的便捷函数
def run_batch_workflow(document_pairs: List[Dict], cookie: str,
                       advanced_settings: dict = None, mode: str = "sequential") -> Dict:
    """
    批量处理的便捷入口

    完全向后兼容：
    - 如果只传入一个文档对，行为与原函数完全相同
    - 如果传入多个文档对，自动启用批量处理
    """
    orchestrator = BatchWorkflowOrchestrator(mode=mode)
    return orchestrator.process_batch(document_pairs, cookie, advanced_settings)


# 兼容性包装器 - 确保旧代码仍然可以工作
def run_single_workflow_compat(baseline_url: str, target_url: str,
                              cookie: str, advanced_settings: dict = None) -> Dict:
    """
    单文档处理的兼容包装器
    保持与原函数完全相同的接口
    """
    return run_batch_workflow(
        [{"baseline_url": baseline_url, "target_url": target_url}],
        cookie,
        advanced_settings,
        mode="single"
    )


if __name__ == "__main__":
    # 测试代码
    print("批量工作流协调器已就绪")
    print("支持模式: sequential(串行), parallel(并行), single(单文档)")
    print("此模块完全向后兼容，不会影响现有功能")