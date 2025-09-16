#!/usr/bin/env python3
"""
URL同步服务 - 确保系统中所有URL配置保持一致

核心功能：
1. 同步real_documents.json与download_config.json
2. 更新综合打分JSON中的table_url
3. 维护upload_mappings.json的一致性
4. 提供URL查询和验证服务

同步策略：
- real_documents.json作为主数据源
- 其他配置文件自动同步
- 变更检测和通知机制
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import logging
import re
from difflib import SequenceMatcher

try:
    from .config_manager import get_config_manager
    from .upload_url_manager import get_manager as get_url_manager
except ImportError:
    # 直接运行时使用
    import sys
    sys.path.insert(0, '/root/projects/tencent-doc-manager')
    from production.core_modules.config_manager import get_config_manager
    from production.core_modules.upload_url_manager import get_manager as get_url_manager

logger = logging.getLogger(__name__)


class URLSyncService:
    """URL同步服务"""
    
    def __init__(self, project_root: str = None):
        """
        初始化URL同步服务
        
        Args:
            project_root: 项目根目录
        """
        if project_root is None:
            project_root = '/root/projects/tencent-doc-manager'
        
        self.project_root = Path(project_root)
        
        # 获取管理器实例
        self.config_manager = get_config_manager()
        self.url_manager = get_url_manager()
        
        # 路径配置
        self.scoring_dir = self.project_root / 'scoring_results'
        self.comprehensive_dir = self.scoring_dir / 'comprehensive'
        
        # URL映射缓存
        self.url_cache = {}
        self._build_url_cache()
    
    def _build_url_cache(self):
        """构建URL缓存"""
        # 从real_documents.json获取主数据
        documents_config = self.config_manager.get_config('documents')
        if documents_config:
            for doc in documents_config.get('documents', []):
                self.url_cache[doc['name']] = {
                    'url': doc['url'],
                    'doc_id': doc['doc_id'],
                    'description': doc.get('description', ''),
                    'csv_pattern': doc.get('csv_pattern', '')
                }
    
    def sync_all_configs(self) -> Dict[str, Any]:
        """
        同步所有配置文件中的URL
        
        Returns:
            同步结果报告
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'synced': [],
            'errors': [],
            'changes': 0
        }
        
        # 1. 同步download_config.json
        try:
            self._sync_download_config()
            report['synced'].append('download_config')
        except Exception as e:
            report['errors'].append(f"download_config: {e}")
        
        # 2. 同步综合打分JSON文件
        try:
            changes = self._sync_comprehensive_scores()
            report['changes'] += changes
            report['synced'].append(f'comprehensive_scores ({changes} changes)')
        except Exception as e:
            report['errors'].append(f"comprehensive_scores: {e}")
        
        # 3. 验证upload_mappings一致性
        try:
            self._validate_upload_mappings()
            report['synced'].append('upload_mappings')
        except Exception as e:
            report['errors'].append(f"upload_mappings: {e}")
        
        logger.info(f"✅ URL同步完成: {len(report['synced'])}个成功, {len(report['errors'])}个错误")
        return report
    
    def _sync_download_config(self):
        """同步download_config.json"""
        documents_config = self.config_manager.get_config('documents')
        download_config = self.config_manager.get_config('download')
        
        if not documents_config or not download_config:
            return
        
        # 构建新的document_links
        new_links = []
        for doc in documents_config.get('documents', []):
            new_links.append({
                'name': doc['name'],
                'url': doc['url'],
                'doc_id': doc['doc_id'],
                'description': doc.get('description', ''),
                'enabled': True
            })
        
        # 检查是否有变化
        old_links = download_config.get('document_links', [])
        if self._compare_links(old_links, new_links):
            # 有变化，更新配置
            self.config_manager.update_config('download', {
                'document_links': new_links
            })
            logger.info(f"✅ 同步download_config: {len(new_links)}个链接")
    
    def _compare_links(self, old_links: List[Dict], new_links: List[Dict]) -> bool:
        """比较链接列表是否有变化"""
        if len(old_links) != len(new_links):
            return True
        
        old_urls = {link.get('url') for link in old_links}
        new_urls = {link.get('url') for link in new_links}
        
        return old_urls != new_urls
    
    def _sync_comprehensive_scores(self) -> int:
        """
        同步综合打分JSON文件中的table_url
        
        Returns:
            修改的文件数量
        """
        if not self.comprehensive_dir.exists():
            return 0
        
        changes = 0
        
        # 遍历所有综合打分文件
        for json_file in self.comprehensive_dir.glob('comprehensive_score_*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                modified = False
                
                # 更新table_scores中的table_url
                for table_score in data.get('table_scores', []):
                    table_name = table_score.get('table_name', '')
                    
                    # 尝试匹配表名获取URL
                    matched_url = self._match_table_url(table_name)
                    if matched_url and table_score.get('table_url') != matched_url:
                        table_score['table_url'] = matched_url
                        modified = True
                
                # 如果有修改，保存文件
                if modified:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    changes += 1
                    logger.debug(f"更新文件: {json_file.name}")
            
            except Exception as e:
                logger.warning(f"处理文件失败 {json_file.name}: {e}")
        
        if changes > 0:
            logger.info(f"✅ 更新了 {changes} 个综合打分文件的URL")
        
        return changes
    
    def _match_table_url(self, table_name: str) -> Optional[str]:
        """
        根据表名匹配URL
        
        Args:
            table_name: 表格名称
        
        Returns:
            匹配的URL，如果没有找到返回None
        """
        # 清理表名
        clean_name = self._clean_table_name(table_name)
        
        # 精确匹配
        if clean_name in self.url_cache:
            return self.url_cache[clean_name]['url']
        
        # 模糊匹配
        for doc_name, doc_info in self.url_cache.items():
            # 部分匹配
            if doc_name in clean_name or clean_name in doc_name:
                return doc_info['url']
            
            # 使用相似度匹配
            similarity = SequenceMatcher(None, doc_name, clean_name).ratio()
            if similarity > 0.7:  # 70%相似度
                return doc_info['url']
        
        return None
    
    def _clean_table_name(self, table_name: str) -> str:
        """清理表名，提取核心部分"""
        # 移除文件路径信息
        if '/' in table_name:
            table_name = table_name.split('/')[-1]
        
        # 移除文件扩展名
        table_name = re.sub(r'\.(csv|xlsx|xls)$', '', table_name)
        
        # 移除时间戳
        table_name = re.sub(r'_\d{8}_\d{6}', '', table_name)
        table_name = re.sub(r'_\d{14}', '', table_name)
        
        # 移除版本标记
        table_name = re.sub(r'_(baseline|midweek|final|current|previous)', '', table_name)
        
        # 移除周数标记
        table_name = re.sub(r'_W\d+', '', table_name)
        
        # 移除对比标记
        table_name = re.sub(r'_vs_.*', '', table_name)
        
        # 移除simplified前缀
        if table_name.startswith('simplified_'):
            table_name = table_name[11:]
        
        # 移除tencent前缀
        if table_name.startswith('tencent_'):
            table_name = table_name[8:]
        
        return table_name.strip()
    
    def _validate_upload_mappings(self):
        """验证upload_mappings的一致性"""
        # 获取所有上传记录
        stats = self.url_manager.get_statistics()
        
        # 验证每个记录的URL是否仍然有效
        invalid_count = 0
        for record in self.url_manager.mappings:
            doc_url = record.doc_url
            
            # 检查URL格式
            if not doc_url.startswith('https://docs.qq.com/'):
                invalid_count += 1
                logger.warning(f"无效URL格式: {doc_url}")
        
        if invalid_count > 0:
            logger.warning(f"⚠️ 发现 {invalid_count} 个无效的上传URL")
    
    def get_url_for_document(self, doc_name: str) -> Optional[str]:
        """
        获取文档的URL
        
        Args:
            doc_name: 文档名称
        
        Returns:
            文档URL，如果没有找到返回None
        """
        # 先尝试缓存
        if doc_name in self.url_cache:
            return self.url_cache[doc_name]['url']
        
        # 尝试匹配
        return self._match_table_url(doc_name)
    
    def get_all_urls(self) -> List[Dict[str, str]]:
        """
        获取所有文档URL
        
        Returns:
            文档URL列表
        """
        urls = []
        for doc_name, doc_info in self.url_cache.items():
            urls.append({
                'name': doc_name,
                'url': doc_info['url'],
                'doc_id': doc_info['doc_id'],
                'description': doc_info.get('description', '')
            })
        return urls
    
    def add_url_mapping(self, doc_name: str, url: str, doc_id: str = None) -> bool:
        """
        添加新的URL映射
        
        Args:
            doc_name: 文档名称
            url: 文档URL
            doc_id: 文档ID（可选）
        
        Returns:
            是否成功添加
        """
        if not doc_id:
            # 从URL提取doc_id
            match = re.search(r'/sheet/([A-Za-z0-9]+)', url)
            if match:
                doc_id = match.group(1)
        
        # 更新缓存
        self.url_cache[doc_name] = {
            'url': url,
            'doc_id': doc_id or '',
            'description': '',
            'csv_pattern': ''
        }
        
        # 更新real_documents.json
        documents_config = self.config_manager.get_config('documents')
        if documents_config:
            documents = documents_config.get('documents', [])
            
            # 检查是否已存在
            exists = False
            for doc in documents:
                if doc['name'] == doc_name:
                    doc['url'] = url
                    doc['doc_id'] = doc_id or doc.get('doc_id', '')
                    exists = True
                    break
            
            # 添加新文档
            if not exists:
                documents.append({
                    'name': doc_name,
                    'url': url,
                    'doc_id': doc_id or '',
                    'csv_pattern': '',
                    'description': ''
                })
            
            # 保存配置
            self.config_manager.update_config('documents', {
                'documents': documents
            })
            
            # 触发同步
            self.sync_all_configs()
            
            logger.info(f"✅ 添加URL映射: {doc_name} -> {url}")
            return True
        
        return False
    
    def check_url_consistency(self) -> Dict[str, List[str]]:
        """
        检查系统中URL的一致性
        
        Returns:
            不一致的URL报告
        """
        inconsistencies = {}
        
        # 获取各个来源的URL
        real_docs_urls = self._get_real_documents_urls()
        download_config_urls = self._get_download_config_urls()
        comprehensive_urls = self._get_comprehensive_urls()
        
        # 检查不一致
        all_doc_names = set()
        all_doc_names.update(real_docs_urls.keys())
        all_doc_names.update(download_config_urls.keys())
        all_doc_names.update(comprehensive_urls.keys())
        
        for doc_name in all_doc_names:
            urls = set()
            
            if doc_name in real_docs_urls:
                urls.add(real_docs_urls[doc_name])
            if doc_name in download_config_urls:
                urls.add(download_config_urls[doc_name])
            if doc_name in comprehensive_urls:
                urls.add(comprehensive_urls[doc_name])
            
            if len(urls) > 1:
                inconsistencies[doc_name] = list(urls)
        
        if inconsistencies:
            logger.warning(f"⚠️ 发现 {len(inconsistencies)} 个URL不一致")
        
        return inconsistencies
    
    def _get_real_documents_urls(self) -> Dict[str, str]:
        """获取real_documents.json中的URL"""
        urls = {}
        documents_config = self.config_manager.get_config('documents')
        if documents_config:
            for doc in documents_config.get('documents', []):
                urls[doc['name']] = doc['url']
        return urls
    
    def _get_download_config_urls(self) -> Dict[str, str]:
        """获取download_config.json中的URL"""
        urls = {}
        download_config = self.config_manager.get_config('download')
        if download_config:
            for link in download_config.get('document_links', []):
                urls[link['name']] = link['url']
        return urls
    
    def _get_comprehensive_urls(self) -> Dict[str, str]:
        """获取综合打分文件中的URL"""
        urls = {}
        
        if self.comprehensive_dir.exists():
            # 只获取最新的文件
            files = sorted(self.comprehensive_dir.glob('comprehensive_score_*.json'))
            if files:
                latest_file = files[-1]
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    for table_score in data.get('table_scores', []):
                        table_name = self._clean_table_name(table_score.get('table_name', ''))
                        table_url = table_score.get('table_url', '')
                        if table_name and table_url:
                            urls[table_name] = table_url
                except:
                    pass
        
        return urls


# 单例实例
_sync_service: Optional[URLSyncService] = None

def get_sync_service() -> URLSyncService:
    """获取URL同步服务单例"""
    global _sync_service
    if _sync_service is None:
        _sync_service = URLSyncService()
    return _sync_service


if __name__ == "__main__":
    # 测试代码
    service = get_sync_service()
    
    # 执行同步
    print("🔄 开始URL同步...")
    report = service.sync_all_configs()
    
    print(f"\n📊 同步报告:")
    print(f"  成功: {report['synced']}")
    print(f"  错误: {report['errors']}")
    print(f"  变更: {report['changes']}个文件")
    
    # 检查一致性
    inconsistencies = service.check_url_consistency()
    if inconsistencies:
        print(f"\n⚠️ URL不一致:")
        for doc_name, urls in inconsistencies.items():
            print(f"  {doc_name}: {urls}")
    else:
        print("\n✅ 所有URL一致")
    
    # 显示所有URL
    all_urls = service.get_all_urls()
    print(f"\n📄 系统中的文档URL ({len(all_urls)}个):")
    for url_info in all_urls:
        print(f"  - {url_info['name']}: {url_info['url']}")