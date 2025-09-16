#!/usr/bin/env python3
"""
上传URL管理器 - 统一管理文件与腾讯文档URL的映射关系

核心功能：
1. 存储文件路径与腾讯文档URL的映射
2. 支持通过文件名、时间戳、周数等多维度查询
3. 持久化存储，防止数据丢失
4. 与主流程无缝集成

存储格式：
{
    "mappings": [
        {
            "file_path": "/path/to/file.xlsx",
            "file_name": "risk_analysis_report_20250819_024132.xlsx",
            "doc_url": "https://docs.qq.com/sheet/DWHJjWmZkTUZkcWpB",
            "upload_time": "2025-09-10 11:53:48",
            "doc_name": "risk_analysis_report",
            "week_number": "W36",
            "version_type": "midweek",
            "metadata": {
                "original_doc": "副本-测试版本-出国销售计划表",
                "file_size": 12345,
                "upload_method": "v3",
                "cookie_id": "ec95c29d7ca948298ae4869ccdf3d6ac"
            }
        }
    ],
    "last_updated": "2025-09-10 11:53:48"
}
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class UploadRecord:
    """上传记录数据类"""
    file_path: str
    file_name: str
    doc_url: str
    upload_time: str
    doc_name: str
    week_number: Optional[str] = None
    version_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadRecord':
        """从字典创建实例"""
        return cls(**data)


class UploadURLManager:
    """上传URL管理器"""
    
    def __init__(self, storage_path: str = None):
        """
        初始化管理器
        
        Args:
            storage_path: 存储文件路径，默认为项目根目录下的upload_mappings.json
        """
        if storage_path is None:
            project_root = Path('/root/projects/tencent-doc-manager')
            storage_path = project_root / 'data' / 'upload_mappings.json'
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.mappings: List[UploadRecord] = []
        self.load_mappings()
        
        # 创建各种索引以加速查询
        self._rebuild_indexes()
    
    def _rebuild_indexes(self):
        """重建索引"""
        self.url_index = {}  # URL -> Record
        self.file_index = {}  # file_path -> Record
        self.name_index = {}  # file_name -> Record
        self.week_index = {}  # week_number -> [Records]
        
        for record in self.mappings:
            self.url_index[record.doc_url] = record
            self.file_index[record.file_path] = record
            self.name_index[record.file_name] = record
            
            if record.week_number:
                if record.week_number not in self.week_index:
                    self.week_index[record.week_number] = []
                self.week_index[record.week_number].append(record)
    
    def load_mappings(self):
        """加载映射数据"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.mappings = [
                        UploadRecord.from_dict(record) 
                        for record in data.get('mappings', [])
                    ]
                    logger.info(f"加载了 {len(self.mappings)} 条映射记录")
            except Exception as e:
                logger.error(f"加载映射文件失败: {e}")
                self.mappings = []
        else:
            logger.info("映射文件不存在，创建新的映射存储")
            self.mappings = []
    
    def save_mappings(self):
        """保存映射数据"""
        try:
            data = {
                'mappings': [record.to_dict() for record in self.mappings],
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存了 {len(self.mappings)} 条映射记录")
        except Exception as e:
            logger.error(f"保存映射文件失败: {e}")
    
    def add_mapping(self, 
                   file_path: str, 
                   doc_url: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> UploadRecord:
        """
        添加文件-URL映射
        
        Args:
            file_path: 文件路径
            doc_url: 腾讯文档URL
            metadata: 额外的元数据
        
        Returns:
            UploadRecord: 创建的记录
        """
        file_path = str(Path(file_path).resolve())
        file_name = Path(file_path).name
        
        # 解析文件名中的信息
        doc_name, week_number, version_type = self._parse_filename(file_name)
        
        # 检查是否已存在
        if file_path in self.file_index:
            logger.warning(f"文件 {file_path} 的映射已存在，更新URL")
            record = self.file_index[file_path]
            record.doc_url = doc_url
            record.upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if metadata:
                record.metadata = metadata
        else:
            # 创建新记录
            record = UploadRecord(
                file_path=file_path,
                file_name=file_name,
                doc_url=doc_url,
                upload_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                doc_name=doc_name,
                week_number=week_number,
                version_type=version_type,
                metadata=metadata or {}
            )
            self.mappings.append(record)
        
        # 重建索引并保存
        self._rebuild_indexes()
        self.save_mappings()
        
        logger.info(f"添加映射: {file_name} -> {doc_url}")
        return record
    
    def _parse_filename(self, filename: str) -> tuple:
        """
        解析文件名，提取文档名、周数、版本类型
        
        文件名格式：
        - tencent_{文档名}_{时间戳}_{版本类型}_W{周数}.{扩展名}
        - risk_analysis_report_{时间戳}.xlsx
        
        Returns:
            (doc_name, week_number, version_type)
        """
        # 尝试匹配标准格式
        pattern = r'tencent_(.+?)_(\d{8}_\d{6})_(baseline|midweek|final)_W(\d+)\.(csv|xlsx)'
        match = re.match(pattern, filename)
        
        if match:
            doc_name = match.group(1)
            version_type = match.group(3)
            week_number = f"W{match.group(4)}"
            return doc_name, week_number, version_type
        
        # 尝试匹配risk_analysis格式
        if filename.startswith('risk_analysis_report'):
            return 'risk_analysis_report', None, None
        
        # 默认提取基本名称
        base_name = Path(filename).stem
        return base_name, None, None
    
    def get_by_file(self, file_path: str) -> Optional[UploadRecord]:
        """通过文件路径获取映射"""
        file_path = str(Path(file_path).resolve())
        return self.file_index.get(file_path)
    
    def get_by_name(self, file_name: str) -> Optional[UploadRecord]:
        """通过文件名获取映射"""
        return self.name_index.get(file_name)
    
    def get_by_url(self, doc_url: str) -> Optional[UploadRecord]:
        """通过URL获取映射"""
        return self.url_index.get(doc_url)
    
    def get_by_week(self, week_number: str) -> List[UploadRecord]:
        """获取某周的所有上传记录"""
        return self.week_index.get(week_number, [])
    
    def search(self, 
              doc_name: Optional[str] = None,
              week_number: Optional[str] = None,
              version_type: Optional[str] = None) -> List[UploadRecord]:
        """
        多条件搜索
        
        Args:
            doc_name: 文档名称（支持部分匹配）
            week_number: 周数
            version_type: 版本类型
        
        Returns:
            符合条件的记录列表
        """
        results = []
        
        for record in self.mappings:
            # 检查文档名
            if doc_name and doc_name.lower() not in record.doc_name.lower():
                continue
            
            # 检查周数
            if week_number and record.week_number != week_number:
                continue
            
            # 检查版本类型
            if version_type and record.version_type != version_type:
                continue
            
            results.append(record)
        
        return results
    
    def get_latest_for_doc(self, doc_name: str) -> Optional[UploadRecord]:
        """获取某个文档的最新上传记录"""
        records = self.search(doc_name=doc_name)
        if not records:
            return None
        
        # 按上传时间排序，返回最新的
        return sorted(records, key=lambda r: r.upload_time, reverse=True)[0]
    
    def cleanup_old_records(self, days: int = 30):
        """清理过期记录"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # 过滤出未过期的记录
        self.mappings = [
            record for record in self.mappings
            if record.upload_time > cutoff_str
        ]
        
        self._rebuild_indexes()
        self.save_mappings()
        
        logger.info(f"清理了 {days} 天前的记录")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total_records': len(self.mappings),
            'unique_docs': len(set(r.doc_name for r in self.mappings)),
            'weeks_covered': sorted(self.week_index.keys()) if self.week_index else [],
            'version_types': {},
            'recent_uploads': []
        }
        
        # 统计版本类型
        for record in self.mappings:
            if record.version_type:
                stats['version_types'][record.version_type] = \
                    stats['version_types'].get(record.version_type, 0) + 1
        
        # 获取最近5条上传
        sorted_records = sorted(self.mappings, key=lambda r: r.upload_time, reverse=True)
        stats['recent_uploads'] = [
            {
                'file_name': r.file_name,
                'doc_url': r.doc_url,
                'upload_time': r.upload_time
            }
            for r in sorted_records[:5]
        ]
        
        return stats


# 单例实例
_manager_instance: Optional[UploadURLManager] = None

def get_manager() -> UploadURLManager:
    """获取管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = UploadURLManager()
    return _manager_instance


if __name__ == "__main__":
    # 测试代码
    manager = get_manager()
    
    # 添加测试映射
    record = manager.add_mapping(
        file_path="/root/projects/tencent-doc-manager/excel_outputs/risk_analysis_report_20250819_024132.xlsx",
        doc_url="https://docs.qq.com/sheet/DWHJjWmZkTUZkcWpB",
        metadata={
            "original_doc": "副本-测试版本-出国销售计划表",
            "file_size": 12345
        }
    )
    
    print(f"添加记录: {record.file_name} -> {record.doc_url}")
    
    # 查询测试
    found = manager.get_by_name("risk_analysis_report_20250819_024132.xlsx")
    if found:
        print(f"找到记录: {found.doc_url}")
    
    # 统计信息
    stats = manager.get_statistics()
    print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")