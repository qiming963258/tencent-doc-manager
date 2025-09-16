#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据存储管理器 - 管理采集数据和对比结果的存储
支持高效的数据检索和历史数据管理
"""

import json
import shutil
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor


@dataclass
class CollectionRecord:
    """采集记录"""
    collection_id: str
    task_id: str
    timestamp: float
    status: str
    total_docs: int
    successful_docs: int
    data_path: str
    metadata: Dict[str, Any]


@dataclass
class ComparisonRecord:
    """对比记录"""
    comparison_id: str
    task_id: str
    previous_collection_id: str
    current_collection_id: str
    timestamp: float
    total_changes: int
    similarity_score: float
    data_path: str
    metadata: Dict[str, Any]


class CollectionStorage:
    """采集存储管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.collections_dir = self.data_dir / "collections"
        self.comparisons_dir = self.data_dir / "comparisons"
        self.db_path = self.data_dir / "storage.db"
        
        # 创建目录结构
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.collections_dir.mkdir(parents=True, exist_ok=True)
        self.comparisons_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 创建采集记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                    collection_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    status TEXT NOT NULL,
                    total_docs INTEGER NOT NULL,
                    successful_docs INTEGER NOT NULL,
                    data_path TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # 创建对比记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparisons (
                    comparison_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    previous_collection_id TEXT NOT NULL,
                    current_collection_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    total_changes INTEGER NOT NULL,
                    similarity_score REAL NOT NULL,
                    data_path TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_collections_task_id ON collections(task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_collections_timestamp ON collections(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparisons_task_id ON comparisons(task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparisons_timestamp ON comparisons(timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def save_collection(self, task_id: str, collection_data: Dict, 
                            collection_id: str = None) -> str:
        """保存采集数据"""
        if not collection_id:
            collection_id = f"{task_id}_{int(time.time())}"
        
        try:
            # 创建采集目录
            collection_dir = self.collections_dir / collection_id
            collection_dir.mkdir(exist_ok=True)
            
            # 保存原始数据
            data_file = collection_dir / "data.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(collection_data, f, indent=2, ensure_ascii=False)
            
            # 提取统计信息
            total_docs = len(collection_data) if isinstance(collection_data, dict) else 0
            successful_docs = 0
            
            if isinstance(collection_data, dict):
                successful_docs = sum(1 for result in collection_data.values() 
                                    if isinstance(result, dict) and result.get("success", False))
            
            # 创建采集记录
            record = CollectionRecord(
                collection_id=collection_id,
                task_id=task_id,
                timestamp=time.time(),
                status="completed" if successful_docs == total_docs else "partial",
                total_docs=total_docs,
                successful_docs=successful_docs,
                data_path=str(data_file),
                metadata={
                    "collection_dir": str(collection_dir),
                    "success_rate": (successful_docs / total_docs * 100) if total_docs > 0 else 0
                }
            )
            
            # 保存到数据库
            await self._save_collection_record(record)
            
            self.logger.info(f"采集数据已保存: {collection_id}")
            return collection_id
            
        except Exception as e:
            self.logger.error(f"保存采集数据失败: {e}")
            raise
    
    async def _save_collection_record(self, record: CollectionRecord):
        """保存采集记录到数据库"""
        def _save():
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO collections 
                (collection_id, task_id, timestamp, status, total_docs, successful_docs, data_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.collection_id,
                record.task_id,
                record.timestamp,
                record.status,
                record.total_docs,
                record.successful_docs,
                record.data_path,
                json.dumps(record.metadata)
            ))
            
            conn.commit()
            conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _save)
    
    async def get_collection(self, collection_id: str) -> Optional[Dict]:
        """获取采集数据"""
        try:
            # 从数据库获取记录
            record = await self._get_collection_record(collection_id)
            if not record:
                return None
            
            # 读取数据文件
            data_file = Path(record.data_path)
            if not data_file.exists():
                self.logger.warning(f"采集数据文件不存在: {data_file}")
                return None
            
            with open(data_file, 'r', encoding='utf-8') as f:
                collection_data = json.load(f)
            
            return {
                "record": asdict(record),
                "data": collection_data
            }
            
        except Exception as e:
            self.logger.error(f"获取采集数据失败: {e}")
            return None
    
    async def _get_collection_record(self, collection_id: str) -> Optional[CollectionRecord]:
        """从数据库获取采集记录"""
        def _get():
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT collection_id, task_id, timestamp, status, total_docs, 
                       successful_docs, data_path, metadata
                FROM collections 
                WHERE collection_id = ?
            ''', (collection_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return CollectionRecord(
                    collection_id=row[0],
                    task_id=row[1],
                    timestamp=row[2],
                    status=row[3],
                    total_docs=row[4],
                    successful_docs=row[5],
                    data_path=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                )
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _get)
    
    async def get_latest_collection(self, task_id: str, exclude_id: str = None) -> Optional[Dict]:
        """获取任务的最新采集数据"""
        def _get_latest():
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            query = '''
                SELECT collection_id, task_id, timestamp, status, total_docs, 
                       successful_docs, data_path, metadata
                FROM collections 
                WHERE task_id = ?
            '''
            params = [task_id]
            
            if exclude_id:
                query += ' AND collection_id != ?'
                params.append(exclude_id)
            
            query += ' ORDER BY timestamp DESC LIMIT 1'
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return CollectionRecord(
                    collection_id=row[0],
                    task_id=row[1],
                    timestamp=row[2],
                    status=row[3],
                    total_docs=row[4],
                    successful_docs=row[5],
                    data_path=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                )
            return None
        
        loop = asyncio.get_event_loop()
        record = await loop.run_in_executor(self.executor, _get_latest)
        
        if not record:
            return None
        
        # 读取数据
        collection = await self.get_collection(record.collection_id)
        return collection
    
    async def save_comparison(self, task_id: str, comparison_data: Dict, 
                            previous_collection_id: str, current_collection_id: str,
                            comparison_id: str = None) -> str:
        """保存对比数据"""
        if not comparison_id:
            comparison_id = f"{task_id}_comparison_{int(time.time())}"
        
        try:
            # 创建对比目录
            comparison_dir = self.comparisons_dir / comparison_id
            comparison_dir.mkdir(exist_ok=True)
            
            # 保存对比数据
            data_file = comparison_dir / "comparison.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_data, f, indent=2, ensure_ascii=False)
            
            # 提取统计信息
            total_changes = 0
            similarity_score = 0.0
            
            if isinstance(comparison_data, dict):
                for url_comparison in comparison_data.values():
                    if isinstance(url_comparison, dict):
                        changes = url_comparison.get("changes", {})
                        summary = changes.get("summary", {})
                        total_changes += summary.get("total_changes", 0)
                        
                        metadata = url_comparison.get("metadata", {})
                        similarity_score = max(similarity_score, metadata.get("similarity_score", 0))
            
            # 创建对比记录
            record = ComparisonRecord(
                comparison_id=comparison_id,
                task_id=task_id,
                previous_collection_id=previous_collection_id,
                current_collection_id=current_collection_id,
                timestamp=time.time(),
                total_changes=total_changes,
                similarity_score=similarity_score,
                data_path=str(data_file),
                metadata={
                    "comparison_dir": str(comparison_dir),
                    "document_count": len(comparison_data) if isinstance(comparison_data, dict) else 0
                }
            )
            
            # 保存到数据库
            await self._save_comparison_record(record)
            
            self.logger.info(f"对比数据已保存: {comparison_id}")
            return comparison_id
            
        except Exception as e:
            self.logger.error(f"保存对比数据失败: {e}")
            raise
    
    async def _save_comparison_record(self, record: ComparisonRecord):
        """保存对比记录到数据库"""
        def _save():
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO comparisons 
                (comparison_id, task_id, previous_collection_id, current_collection_id,
                 timestamp, total_changes, similarity_score, data_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.comparison_id,
                record.task_id,
                record.previous_collection_id,
                record.current_collection_id,
                record.timestamp,
                record.total_changes,
                record.similarity_score,
                record.data_path,
                json.dumps(record.metadata)
            ))
            
            conn.commit()
            conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _save)
    
    async def get_collections_by_task(self, task_id: str, limit: int = 10) -> List[CollectionRecord]:
        """获取任务的采集历史"""
        def _get_collections():
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT collection_id, task_id, timestamp, status, total_docs, 
                       successful_docs, data_path, metadata
                FROM collections 
                WHERE task_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (task_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                records.append(CollectionRecord(
                    collection_id=row[0],
                    task_id=row[1],
                    timestamp=row[2],
                    status=row[3],
                    total_docs=row[4],
                    successful_docs=row[5],
                    data_path=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                ))
            
            return records
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _get_collections)
    
    async def cleanup_old_data(self, keep_days: int = 30):
        """清理历史数据"""
        try:
            cutoff_time = time.time() - (keep_days * 24 * 3600)
            
            def _cleanup():
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                # 获取需要删除的采集记录
                cursor.execute('''
                    SELECT collection_id, data_path FROM collections
                    WHERE timestamp < ?
                ''', (cutoff_time,))
                
                old_collections = cursor.fetchall()
                
                # 获取需要删除的对比记录
                cursor.execute('''
                    SELECT comparison_id, data_path FROM comparisons
                    WHERE timestamp < ?
                ''', (cutoff_time,))
                
                old_comparisons = cursor.fetchall()
                
                # 删除数据库记录
                cursor.execute('DELETE FROM collections WHERE timestamp < ?', (cutoff_time,))
                cursor.execute('DELETE FROM comparisons WHERE timestamp < ?', (cutoff_time,))
                
                conn.commit()
                conn.close()
                
                return old_collections, old_comparisons
            
            loop = asyncio.get_event_loop()
            old_collections, old_comparisons = await loop.run_in_executor(self.executor, _cleanup)
            
            # 删除文件
            deleted_count = 0
            for collection_id, data_path in old_collections:
                try:
                    collection_dir = Path(data_path).parent
                    if collection_dir.exists():
                        shutil.rmtree(collection_dir)
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"删除采集目录失败: {collection_dir} - {e}")
            
            for comparison_id, data_path in old_comparisons:
                try:
                    comparison_dir = Path(data_path).parent
                    if comparison_dir.exists():
                        shutil.rmtree(comparison_dir)
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"删除对比目录失败: {comparison_dir} - {e}")
            
            self.logger.info(f"清理完成，删除了 {deleted_count} 个历史数据目录")
            
        except Exception as e:
            self.logger.error(f"清理历史数据失败: {e}")
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        def _get_stats():
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 采集统计
            cursor.execute('SELECT COUNT(*), SUM(total_docs), SUM(successful_docs) FROM collections')
            collections_stats = cursor.fetchone()
            
            # 对比统计
            cursor.execute('SELECT COUNT(*), SUM(total_changes), AVG(similarity_score) FROM comparisons')
            comparisons_stats = cursor.fetchone()
            
            # 任务统计
            cursor.execute('SELECT COUNT(DISTINCT task_id) FROM collections')
            unique_tasks = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "collections": {
                    "total_count": collections_stats[0] or 0,
                    "total_docs": collections_stats[1] or 0,
                    "successful_docs": collections_stats[2] or 0
                },
                "comparisons": {
                    "total_count": comparisons_stats[0] or 0,
                    "total_changes": comparisons_stats[1] or 0,
                    "avg_similarity": comparisons_stats[2] or 0
                },
                "tasks": {
                    "unique_count": unique_tasks or 0
                }
            }
        
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(self.executor, _get_stats)
        
        # 添加磁盘使用统计
        try:
            total_size = 0
            for dir_path in [self.collections_dir, self.comparisons_dir]:
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            stats["storage"] = {
                "total_size_mb": total_size / 1024 / 1024,
                "data_dir": str(self.data_dir)
            }
        except Exception as e:
            self.logger.warning(f"计算存储大小失败: {e}")
        
        return stats
    
    async def close(self):
        """关闭存储管理器"""
        self.executor.shutdown(wait=True)
        self.logger.info("存储管理器已关闭")


async def main():
    """测试存储管理器"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    storage = CollectionStorage("./test_storage")
    
    try:
        # 测试保存采集数据
        test_collection_data = {
            "url1": {"success": True, "duration": 5.2, "row_count": 100},
            "url2": {"success": True, "duration": 3.8, "row_count": 80},
            "url3": {"success": False, "error": "timeout"}
        }
        
        collection_id = await storage.save_collection("test_task", test_collection_data)
        print(f"保存采集数据: {collection_id}")
        
        # 测试获取采集数据
        collection = await storage.get_collection(collection_id)
        if collection:
            print(f"获取采集数据成功，记录数: {collection['record']['total_docs']}")
        
        # 测试保存对比数据
        test_comparison_data = {
            "url1": {
                "changes": {"summary": {"total_changes": 5}},
                "metadata": {"similarity_score": 0.95}
            }
        }
        
        comparison_id = await storage.save_comparison(
            "test_task", test_comparison_data, "prev_id", collection_id
        )
        print(f"保存对比数据: {comparison_id}")
        
        # 获取统计信息
        stats = await storage.get_storage_statistics()
        print(f"\n存储统计:")
        print(f"  采集总数: {stats['collections']['total_count']}")
        print(f"  对比总数: {stats['comparisons']['total_count']}")
        print(f"  任务总数: {stats['tasks']['unique_count']}")
        if 'storage' in stats:
            print(f"  存储大小: {stats['storage']['total_size_mb']:.2f}MB")
        
        print("\n测试完成")
        
    finally:
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())