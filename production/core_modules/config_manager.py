#!/usr/bin/env python3
"""
统一配置管理器 - 管理系统所有配置文件

核心功能：
1. 自动初始化缺失的配置文件
2. 统一管理所有配置文件
3. 提供配置验证和同步机制
4. Cookie有效期自动检测
5. 配置文件备份和恢复

配置文件清单：
- config.json: Cookie主存储
- download_config.json: 文档链接配置
- monitor_config.json: 监控设置
- schedule_tasks.json: 定时任务
- real_documents.json: 真实文档配置
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import shutil
import hashlib

logger = logging.getLogger(__name__)


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, project_root: str = None):
        """
        初始化配置管理器
        
        Args:
            project_root: 项目根目录
        """
        if project_root is None:
            project_root = '/root/projects/tencent-doc-manager'
        
        self.project_root = Path(project_root)
        self.config_dir = self.project_root / 'config'
        self.production_config_dir = self.project_root / 'production' / 'config'
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.production_config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件映射
        self.config_files = {
            'cookie': self.project_root / 'config.json',
            'download': self.config_dir / 'download_config.json',
            'monitor': self.config_dir / 'monitor_config.json',
            'schedule': self.config_dir / 'schedule_tasks.json',
            'documents': self.production_config_dir / 'real_documents.json'
        }
        
        # 默认配置模板
        self.default_configs = self._get_default_configs()
        
        # 初始化所有配置文件
        self.initialize_all_configs()
        
        # 加载所有配置
        self.configs = self.load_all_configs()
    
    def _get_default_configs(self) -> Dict[str, Dict]:
        """获取默认配置模板"""
        return {
            'cookie': {
                'cookie': '',
                'last_updated': datetime.now().isoformat(),
                'cookie_id': '',
                'set_time': datetime.now().isoformat()
            },
            'download': {
                'document_links': [
                    {
                        'name': '副本-测试版本-出国销售计划表',
                        'url': 'https://docs.qq.com/sheet/DWEFNU25TemFnZXJN',
                        'doc_id': 'DWEFNU25TemFnZXJN',
                        'description': '出国销售数据监控'
                    },
                    {
                        'name': '副本-测试版本-回国销售计划表',
                        'url': 'https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr',
                        'doc_id': 'DWGZDZkxpaGVQaURr',
                        'description': '回国销售数据监控'
                    },
                    {
                        'name': '测试版本-小红书部门',
                        'url': 'https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R',
                        'doc_id': 'DWFJzdWNwd0RGbU5R',
                        'description': '小红书部门数据监控'
                    }
                ],
                'download_format': 'csv',
                'schedule': {
                    'enabled': False,
                    'interval': 'weekly',
                    'last_download': None
                },
                'download_status': '未配置',
                'last_updated': datetime.now().isoformat()
            },
            'monitor': {
                'alert_settings': {
                    'threshold': 'L1',
                    'levels': ['L1级别修改', '高风险修改', '所有修改'],
                    'current_level': 'L1级别修改'
                },
                'notification': {
                    'enabled': True,
                    'channels': ['console', 'log'],
                    'alert_frequency': 300
                },
                'display': {
                    'refresh_interval': 300,
                    'auto_refresh': False,
                    'heatmap_smoothing': True,
                    'show_tooltips': True,
                    'color_scheme': 'scientific'
                },
                'comparison': {
                    'auto_comparison': True,
                    'comparison_interval': 3600,
                    'baseline_retention_days': 30,
                    'generate_reports': True
                },
                'last_updated': datetime.now().isoformat()
            },
            'schedule': {
                'preset_tasks': [
                    {
                        'task_id': 'weekly_baseline_download',
                        'name': '周二基准下载任务',
                        'description': '每周二12:00下载基准CSV文件',
                        'schedule': {
                            'type': 'simple',
                            'expression': 'weekly:tuesday:12:00',
                            'timezone': 'Asia/Shanghai'
                        },
                        'enabled': False
                    },
                    {
                        'task_id': 'weekly_midweek_update',
                        'name': '周四中期更新任务',
                        'description': '每周四09:00下载全部表格CSV并更新系统',
                        'schedule': {
                            'type': 'simple',
                            'expression': 'weekly:thursday:09:00',
                            'timezone': 'Asia/Shanghai'
                        },
                        'enabled': False
                    },
                    {
                        'task_id': 'weekly_full_update',
                        'name': '周六完整更新任务',
                        'description': '每周六19:00完整更新系统',
                        'schedule': {
                            'type': 'simple',
                            'expression': 'weekly:saturday:19:00',
                            'timezone': 'Asia/Shanghai'
                        },
                        'enabled': False
                    }
                ],
                'global_settings': {
                    'max_concurrent_tasks': 2,
                    'retry_failed_tasks': True,
                    'retry_count': 3,
                    'log_level': 'INFO'
                }
            },
            'documents': {
                'documents': [
                    {
                        'name': '副本-测试版本-出国销售计划表',
                        'url': 'https://docs.qq.com/sheet/DWEFNU25TemFnZXJN',
                        'doc_id': 'DWEFNU25TemFnZXJN',
                        'csv_pattern': 'test',
                        'description': '出国销售数据监控'
                    },
                    {
                        'name': '副本-测试版本-回国销售计划表',
                        'url': 'https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr',
                        'doc_id': 'DWGZDZkxpaGVQaURr',
                        'csv_pattern': 'realtest',
                        'description': '回国销售数据监控'
                    },
                    {
                        'name': '测试版本-小红书部门',
                        'url': 'https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R',
                        'doc_id': 'DWFJzdWNwd0RGbU5R',
                        'csv_pattern': 'test_data',
                        'description': '小红书部门数据监控'
                    }
                ],
                'paste_format': '【腾讯文档】{name}\\n{url}',
                'max_documents': None
            }
        }
    
    def initialize_all_configs(self):
        """初始化所有配置文件（如果不存在则创建）"""
        initialized = []
        
        for config_name, config_path in self.config_files.items():
            if not config_path.exists():
                # 创建默认配置
                default_config = self.default_configs.get(config_name, {})
                
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(default_config, f, ensure_ascii=False, indent=2)
                    
                    initialized.append(config_name)
                    logger.info(f"✅ 初始化配置文件: {config_path}")
                except Exception as e:
                    logger.error(f"❌ 创建配置文件失败 {config_path}: {e}")
        
        if initialized:
            logger.info(f"📝 初始化了 {len(initialized)} 个配置文件: {', '.join(initialized)}")
        else:
            logger.info("✅ 所有配置文件已存在")
    
    def load_all_configs(self) -> Dict[str, Dict]:
        """加载所有配置文件"""
        configs = {}
        
        for config_name, config_path in self.config_files.items():
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        configs[config_name] = json.load(f)
                except Exception as e:
                    logger.error(f"加载配置失败 {config_name}: {e}")
                    configs[config_name] = self.default_configs.get(config_name, {})
            else:
                configs[config_name] = self.default_configs.get(config_name, {})
        
        return configs
    
    def save_config(self, config_name: str, data: Dict) -> bool:
        """
        保存单个配置文件
        
        Args:
            config_name: 配置名称
            data: 配置数据
        
        Returns:
            是否成功保存
        """
        if config_name not in self.config_files:
            logger.error(f"未知的配置类型: {config_name}")
            return False
        
        config_path = self.config_files[config_name]
        
        # 备份原配置
        self.backup_config(config_name)
        
        try:
            # 更新最后修改时间
            data['last_updated'] = datetime.now().isoformat()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的配置
            self.configs[config_name] = data
            
            logger.info(f"✅ 保存配置 {config_name}: {config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存配置失败 {config_name}: {e}")
            return False
    
    def backup_config(self, config_name: str):
        """备份配置文件"""
        if config_name not in self.config_files:
            return
        
        config_path = self.config_files[config_name]
        if not config_path.exists():
            return
        
        # 创建备份目录
        backup_dir = self.config_dir / 'backup'
        backup_dir.mkdir(exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"{config_name}_{timestamp}.json"
        
        try:
            shutil.copy2(config_path, backup_file)
            logger.debug(f"备份配置 {config_name} 到 {backup_file}")
            
            # 清理旧备份（保留最近10个）
            self._cleanup_old_backups(backup_dir, config_name, keep=10)
        except Exception as e:
            logger.warning(f"备份配置失败 {config_name}: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path, config_name: str, keep: int = 10):
        """清理旧备份文件"""
        pattern = f"{config_name}_*.json"
        backups = sorted(backup_dir.glob(pattern))
        
        if len(backups) > keep:
            for backup_file in backups[:-keep]:
                try:
                    backup_file.unlink()
                    logger.debug(f"删除旧备份: {backup_file}")
                except:
                    pass
    
    def get_config(self, config_name: str) -> Optional[Dict]:
        """获取配置"""
        return self.configs.get(config_name)
    
    def update_config(self, config_name: str, updates: Dict, merge: bool = True) -> bool:
        """
        更新配置
        
        Args:
            config_name: 配置名称
            updates: 更新内容
            merge: 是否合并更新（True）或完全替换（False）
        
        Returns:
            是否成功更新
        """
        current_config = self.get_config(config_name)
        if current_config is None:
            logger.error(f"配置不存在: {config_name}")
            return False
        
        if merge:
            # 深度合并配置
            new_config = self._deep_merge(current_config, updates)
        else:
            new_config = updates
        
        return self.save_config(config_name, new_config)
    
    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_cookie(self) -> Tuple[bool, str]:
        """
        验证Cookie有效性
        
        Returns:
            (是否有效, 消息)
        """
        cookie_config = self.get_config('cookie')
        if not cookie_config or not cookie_config.get('cookie'):
            return False, "Cookie未配置"
        
        # 检查Cookie年龄
        set_time_str = cookie_config.get('set_time')
        if set_time_str:
            try:
                set_time = datetime.fromisoformat(set_time_str)
                age = datetime.now() - set_time
                
                if age > timedelta(hours=48):
                    return False, f"Cookie已过期 ({age.total_seconds()/3600:.1f}小时)"
                elif age > timedelta(hours=24):
                    return True, f"Cookie即将过期 ({age.total_seconds()/3600:.1f}小时)"
                else:
                    return True, f"Cookie有效 ({age.total_seconds()/3600:.1f}小时)"
            except:
                pass
        
        return True, "Cookie状态未知"
    
    def sync_url_configs(self):
        """同步URL配置（确保download_config和real_documents一致）"""
        documents_config = self.get_config('documents')
        download_config = self.get_config('download')
        
        if documents_config and download_config:
            # 从real_documents同步到download_config
            doc_links = []
            for doc in documents_config.get('documents', []):
                doc_links.append({
                    'name': doc.get('name'),
                    'url': doc.get('url'),
                    'doc_id': doc.get('doc_id'),
                    'description': doc.get('description', '')
                })
            
            # 更新download_config
            self.update_config('download', {
                'document_links': doc_links
            })
            
            logger.info(f"✅ 同步了 {len(doc_links)} 个文档URL")
    
    def get_all_document_urls(self) -> List[Dict]:
        """获取所有文档URL（合并所有来源）"""
        urls = []
        
        # 从download_config获取
        download_config = self.get_config('download')
        if download_config:
            urls.extend(download_config.get('document_links', []))
        
        # 从real_documents获取
        documents_config = self.get_config('documents')
        if documents_config:
            for doc in documents_config.get('documents', []):
                # 检查是否已存在
                if not any(u['url'] == doc['url'] for u in urls):
                    urls.append({
                        'name': doc.get('name'),
                        'url': doc.get('url'),
                        'doc_id': doc.get('doc_id'),
                        'description': doc.get('description', '')
                    })
        
        return urls
    
    def get_schedule_status(self) -> Dict[str, bool]:
        """获取调度任务状态"""
        schedule_config = self.get_config('schedule')
        status = {
            'baseline_enabled': False,
            'midweek_enabled': False,
            'weekend_enabled': False,
            'scheduler_running': False
        }
        
        if schedule_config:
            for task in schedule_config.get('preset_tasks', []):
                task_id = task.get('task_id', '')
                enabled = task.get('enabled', False)
                
                if 'baseline' in task_id:
                    status['baseline_enabled'] = enabled
                elif 'midweek' in task_id:
                    status['midweek_enabled'] = enabled
                elif 'weekend' in task_id or 'full' in task_id:
                    status['weekend_enabled'] = enabled
            
            # 检查是否有任何任务启用
            status['scheduler_running'] = any([
                status['baseline_enabled'],
                status['midweek_enabled'],
                status['weekend_enabled']
            ])
        
        return status
    
    def get_monitor_settings(self) -> Dict:
        """获取监控设置"""
        monitor_config = self.get_config('monitor')
        if monitor_config:
            return monitor_config
        return self.default_configs['monitor']
    
    def get_statistics(self) -> Dict:
        """获取配置统计信息"""
        stats = {
            'total_configs': len(self.config_files),
            'loaded_configs': len(self.configs),
            'document_count': 0,
            'schedule_enabled': False,
            'cookie_status': 'unknown',
            'last_sync': None
        }
        
        # 文档数量
        urls = self.get_all_document_urls()
        stats['document_count'] = len(urls)
        
        # 调度状态
        schedule_status = self.get_schedule_status()
        stats['schedule_enabled'] = schedule_status['scheduler_running']
        
        # Cookie状态
        valid, msg = self.validate_cookie()
        stats['cookie_status'] = 'valid' if valid else 'invalid'
        stats['cookie_message'] = msg
        
        return stats


# 单例实例
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == "__main__":
    # 测试代码
    manager = get_config_manager()
    
    # 打印统计信息
    stats = manager.get_statistics()
    print("📊 配置统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 验证Cookie
    valid, msg = manager.validate_cookie()
    print(f"\n🔐 Cookie状态: {msg}")
    
    # 获取所有文档URL
    urls = manager.get_all_document_urls()
    print(f"\n📄 文档URL ({len(urls)}个):")
    for url_info in urls:
        print(f"  - {url_info['name']}: {url_info['url']}")
    
    # 同步URL配置
    manager.sync_url_configs()
    print("\n✅ URL配置已同步")