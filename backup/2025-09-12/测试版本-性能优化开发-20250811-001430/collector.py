#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档数据采集器 - 基于优化版本的腾讯文档批量采集组件
支持高并发采集和错误重试机制
"""

import asyncio
import hashlib
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from browser_pool import get_browser_pool, BrowserInstance
from optimized_download import OptimizedTencentDownloader


@dataclass
class CollectionResult:
    """单个文档采集结果"""
    url: str
    doc_id: str
    tab_id: str
    success: bool
    duration: float
    data_hash: Optional[str] = None
    row_count: Optional[int] = None  
    col_count: Optional[int] = None
    data_path: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class CollectionSummary:
    """采集汇总结果"""
    collection_id: str
    task_id: str
    timestamp: float
    status: str  # "completed" | "partial" | "failed"
    results: Dict[str, CollectionResult]
    summary: Dict[str, any]


class TencentDocumentCollector:
    """腾讯文档采集器"""
    
    def __init__(self, max_concurrent: int = 3, data_dir: str = "./data/collections"):
        self.max_concurrent = max_concurrent
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # 创建优化下载器
        self.downloader = OptimizedTencentDownloader(max_concurrent=max_concurrent)
    
    async def collect_documents(self, urls: List[str], cookies: str, 
                              concurrent_limit: int = None, timeout: int = 60,
                              retry_times: int = 2) -> Dict[str, CollectionResult]:
        """批量采集文档数据"""
        if concurrent_limit:
            self.max_concurrent = min(concurrent_limit, self.max_concurrent)
        
        self.logger.info(f"开始采集 {len(urls)} 个文档，并发数: {self.max_concurrent}")
        
        results = {}
        
        # 添加下载任务
        task_ids = {}
        for url in urls:
            try:
                task_id = await self.downloader.add_download_task(url, cookies, timeout=timeout)
                task_ids[task_id] = url
            except Exception as e:
                self.logger.error(f"添加下载任务失败: {url} - {e}")
                results[url] = CollectionResult(
                    url=url,
                    doc_id=self._extract_doc_id(url),
                    tab_id=self._extract_tab_id(url),
                    success=False,
                    duration=0.0,
                    error=str(e)
                )
        
        if not task_ids:
            self.logger.error("没有有效的下载任务")
            return results
        
        # 启动下载处理
        workers = await self.downloader.start_processing()
        
        try:
            # 等待完成
            await self.downloader.wait_for_completion(timeout=timeout * len(urls))
            
            # 收集结果
            download_results = await self.downloader.get_all_results()
            
            for task_id, url in task_ids.items():
                if task_id in download_results:
                    download_result = download_results[task_id]
                    
                    # 转换为采集结果
                    collection_result = await self._convert_download_result(url, download_result)
                    results[url] = collection_result
                    
                    # 处理数据文件
                    if collection_result.success and download_result.csv_file_path:
                        await self._process_data_file(collection_result, download_result.csv_file_path)
                else:
                    # 任务未找到结果
                    results[url] = CollectionResult(
                        url=url,
                        doc_id=self._extract_doc_id(url),
                        tab_id=self._extract_tab_id(url),
                        success=False,
                        duration=0.0,
                        error="下载任务未完成"
                    )
            
            self.logger.info(f"采集完成，成功: {sum(1 for r in results.values() if r.success)}, 失败: {sum(1 for r in results.values() if not r.success)}")
            
        finally:
            # 清理工作进程
            for worker in workers:
                worker.cancel()
        
        return results
    
    async def _convert_download_result(self, url: str, download_result) -> CollectionResult:
        """转换下载结果为采集结果"""
        return CollectionResult(
            url=url,
            doc_id=self._extract_doc_id(url),
            tab_id=self._extract_tab_id(url),
            success=download_result.success,
            duration=download_result.duration,
            error=download_result.error if not download_result.success else None
        )
    
    async def _process_data_file(self, result: CollectionResult, csv_file_path: str):
        """处理数据文件，计算哈希值和统计信息"""
        try:
            csv_path = Path(csv_file_path)
            if not csv_path.exists():
                self.logger.warning(f"CSV文件不存在: {csv_file_path}")
                return
            
            # 读取文件内容
            with open(csv_path, 'rb') as f:
                file_content = f.read()
                
            # 计算文件哈希
            result.data_hash = f"sha256:{hashlib.sha256(file_content).hexdigest()}"
            
            # 统计行列数
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    result.row_count = len(lines) - 1  # 减去标题行
                    if lines:
                        result.col_count = len(lines[0].split(','))
            except:
                pass
            
            # 移动文件到数据目录
            collection_dir = self.data_dir / f"collection_{int(time.time())}"
            collection_dir.mkdir(exist_ok=True)
            
            target_path = collection_dir / f"{result.doc_id}_{result.tab_id}.csv"
            csv_path.rename(target_path)
            result.data_path = str(target_path)
            
            self.logger.debug(f"已处理数据文件: {result.url} -> {target_path}")
            
        except Exception as e:
            self.logger.error(f"处理数据文件失败: {csv_file_path} - {e}")
    
    def _extract_doc_id(self, url: str) -> str:
        """从URL提取文档ID"""
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            # 腾讯文档URL格式: /sheet/DOC_ID
            if len(path_parts) >= 2 and path_parts[0] == 'sheet':
                return path_parts[1]
            
            return "unknown"
        except:
            return "unknown"
    
    def _extract_tab_id(self, url: str) -> str:
        """从URL提取标签页ID"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'tab' in query_params:
                return query_params['tab'][0]
            
            return "default"
        except:
            return "default"
    
    async def collect_single_document(self, url: str, cookies: str, 
                                    timeout: int = 60) -> CollectionResult:
        """采集单个文档"""
        results = await self.collect_documents([url], cookies, concurrent_limit=1, timeout=timeout)
        return results.get(url)
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.downloader.cleanup()
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")


class CollectionManager:
    """采集任务管理器"""
    
    def __init__(self, data_dir: str = "./data/collections"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.collector = TencentDocumentCollector(data_dir=str(self.data_dir))
    
    async def create_collection_task(self, task_id: str, urls: List[str], 
                                   cookies: str, options: Dict = None) -> str:
        """创建采集任务"""
        options = options or {}
        
        collection_id = f"{task_id}_{int(time.time())}"
        
        self.logger.info(f"创建采集任务: {collection_id}")
        
        # 执行采集
        results = await self.collector.collect_documents(
            urls=urls,
            cookies=cookies,
            concurrent_limit=options.get("concurrent_limit", 3),
            timeout=options.get("timeout", 60),
            retry_times=options.get("retry_times", 2)
        )
        
        # 创建汇总结果
        summary = self._create_summary(results)
        collection_summary = CollectionSummary(
            collection_id=collection_id,
            task_id=task_id,
            timestamp=time.time(),
            status=self._determine_status(results),
            results=results,
            summary=summary
        )
        
        # 保存结果
        await self._save_collection_summary(collection_summary)
        
        return collection_id
    
    def _create_summary(self, results: Dict[str, CollectionResult]) -> Dict:
        """创建采集汇总"""
        total_docs = len(results)
        successful = sum(1 for r in results.values() if r.success)
        failed = total_docs - successful
        total_duration = sum(r.duration for r in results.values())
        
        return {
            "total_docs": total_docs,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_docs * 100) if total_docs > 0 else 0,
            "total_duration": total_duration,
            "avg_duration": (total_duration / successful) if successful > 0 else 0
        }
    
    def _determine_status(self, results: Dict[str, CollectionResult]) -> str:
        """确定采集状态"""
        if not results:
            return "failed"
        
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        
        if successful == 0:
            return "failed"
        elif successful == total:
            return "completed"
        else:
            return "partial"
    
    async def _save_collection_summary(self, summary: CollectionSummary):
        """保存采集汇总"""
        try:
            summary_file = self.data_dir / f"{summary.collection_id}_summary.json"
            
            # 转换结果为可序列化格式
            serializable_summary = asdict(summary)
            serializable_summary["results"] = {
                url: asdict(result) for url, result in summary.results.items()
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"已保存采集汇总: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"保存采集汇总失败: {e}")
    
    async def get_collection_summary(self, collection_id: str) -> Optional[CollectionSummary]:
        """获取采集汇总"""
        try:
            summary_file = self.data_dir / f"{collection_id}_summary.json"
            
            if not summary_file.exists():
                return None
            
            with open(summary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换回对象
            results = {}
            for url, result_data in data["results"].items():
                results[url] = CollectionResult(**result_data)
            
            return CollectionSummary(
                collection_id=data["collection_id"],
                task_id=data["task_id"],
                timestamp=data["timestamp"],
                status=data["status"],
                results=results,
                summary=data["summary"]
            )
            
        except Exception as e:
            self.logger.error(f"获取采集汇总失败: {e}")
            return None
    
    async def cleanup(self):
        """清理资源"""
        await self.collector.cleanup()


async def main():
    """测试采集器"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 测试URL
    test_urls = [
        "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=BB08J2",
        "https://docs.qq.com/sheet/DYkNJRlp0cWRWZUlH?tab=g2hi7f"
    ]
    
    # 测试cookies（需要替换为实际的）
    test_cookies = "your_cookies_here"
    
    try:
        manager = CollectionManager("./test_collections")
        
        print("开始测试采集...")
        collection_id = await manager.create_collection_task(
            task_id="test_task",
            urls=test_urls,
            cookies=test_cookies,
            options={
                "concurrent_limit": 2,
                "timeout": 60
            }
        )
        
        print(f"采集完成: {collection_id}")
        
        # 获取结果
        summary = await manager.get_collection_summary(collection_id)
        if summary:
            print(f"采集状态: {summary.status}")
            print(f"成功率: {summary.summary['success_rate']:.1f}%")
            print(f"总耗时: {summary.summary['total_duration']:.2f}s")
        
    except Exception as e:
        print(f"测试失败: {e}")
    
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())