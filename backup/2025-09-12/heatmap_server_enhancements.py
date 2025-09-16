#!/usr/bin/env python3
"""
8089热力图服务器增强功能
包含URL软删除管理和基线文件管理
"""

import os
import json
import datetime
import shutil
from typing import Dict, List, Any, Optional

class URLManager:
    """URL软删除管理器"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file)
        
    def save_links_with_soft_delete(self, links: List[Dict]) -> bool:
        """保存链接配置（支持软删除）"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            
            # 读取现有配置以保留软删除的链接
            existing_config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        existing_config = json.load(f)
                except:
                    existing_config = {}
            
            # 获取已软删除的链接
            deleted_links = existing_config.get('deleted_links', [])
            
            # 检查哪些链接被删除了
            current_urls = [link.get('url') for link in links]
            if 'document_links' in existing_config:
                for old_link in existing_config['document_links']:
                    if old_link.get('url') not in current_urls:
                        # 添加到软删除列表
                        old_link['deleted_at'] = datetime.datetime.now().isoformat()
                        old_link['active'] = False
                        deleted_links.append(old_link)
            
            # 保存配置
            config = {
                'document_links': links,  # 当前活跃的链接
                'deleted_links': deleted_links,  # 软删除的链接
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 保存了 {len(links)} 个活跃文档链接")
            if deleted_links:
                print(f"📋 软删除链接数: {len(deleted_links)}")
            return True
            
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_active_links(self) -> List[Dict]:
        """获取活跃的链接（不包含软删除的）"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('document_links', [])
            return []
        except:
            return []


class BaselineFileManager:
    """基线文件管理器"""
    
    def __init__(self):
        self.base_dir = '/root/projects/tencent-doc-manager/csv_versions'
        
    def get_current_week(self) -> int:
        """获取当前周数"""
        from production.core_modules.week_time_manager import WeekTimeManager
        week_manager = WeekTimeManager()
        return week_manager.get_current_week()
    
    def get_baseline_dir(self) -> str:
        """获取当前周的基线文件夹路径"""
        current_week = self.get_current_week()
        return os.path.join(
            self.base_dir,
            f'2025_W{current_week:02d}',
            'baseline'
        )
    
    def list_baseline_files(self) -> Dict[str, Any]:
        """列出基线文件"""
        baseline_dir = self.get_baseline_dir()
        files = []
        
        if os.path.exists(baseline_dir):
            for filename in os.listdir(baseline_dir):
                if filename.endswith('.csv') or filename.endswith('.xlsx'):
                    file_path = os.path.join(baseline_dir, filename)
                    files.append({
                        'name': filename,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'modified': datetime.datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat()
                    })
        
        return {
            'success': True,
            'files': files,
            'week': self.get_current_week(),
            'path': baseline_dir
        }
    
    def download_baseline_file(self, url: str, cookie_string: str) -> Dict[str, Any]:
        """下载基线文件"""
        try:
            baseline_dir = self.get_baseline_dir()
            os.makedirs(baseline_dir, exist_ok=True)
            
            # 导入下载模块
            import sys
            sys.path.append('/root/projects/tencent-doc-manager')
            from production.core_modules.tencent_export_automation import TencentExporter
            
            exporter = TencentExporter(cookie_string=cookie_string)
            
            # 下载文件
            success, result = exporter.download_single_document(url)
            
            if success:
                # 移动文件到基线文件夹
                source_path = result.get('file_path')
                if source_path and os.path.exists(source_path):
                    filename = os.path.basename(source_path)
                    target_path = os.path.join(baseline_dir, filename)
                    
                    shutil.move(source_path, target_path)
                    
                    return {
                        'success': True,
                        'file': {
                            'name': filename,
                            'path': target_path
                        }
                    }
            
            return {
                'success': False,
                'error': result.get('error', '下载失败') if result else '下载失败'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_baseline_file(self, filename: str) -> Dict[str, Any]:
        """软删除基线文件"""
        try:
            baseline_dir = self.get_baseline_dir()
            file_path = os.path.join(baseline_dir, filename)
            
            if os.path.exists(file_path):
                # 软删除：移动到已删除文件夹
                deleted_dir = os.path.join(baseline_dir, '.deleted')
                os.makedirs(deleted_dir, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                deleted_filename = f"{timestamp}_{filename}"
                deleted_path = os.path.join(deleted_dir, deleted_filename)
                
                shutil.move(file_path, deleted_path)
                
                return {
                    'success': True,
                    'message': f'文件已软删除: {filename}'
                }
            else:
                return {
                    'success': False,
                    'error': '文件不存在'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 增强的日志格式化函数
def format_log_with_icons(message: str, level: str = 'info') -> Dict[str, Any]:
    """格式化日志消息，添加图标和样式"""
    icons = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'processing': '⏳',
        'download': '📥',
        'upload': '📤',
        'analysis': '🔍',
        'complete': '🎉'
    }
    
    # 根据消息内容自动选择图标
    if '成功' in message or '完成' in message:
        icon = icons['success']
        level = 'success'
    elif '错误' in message or '失败' in message:
        icon = icons['error']
        level = 'error'
    elif '下载' in message:
        icon = icons['download']
    elif '上传' in message:
        icon = icons['upload']
    elif '分析' in message or '处理' in message:
        icon = icons['analysis']
    elif '开始' in message or '准备' in message:
        icon = icons['processing']
    else:
        icon = icons.get(level, '')
    
    return {
        'time': datetime.datetime.now().isoformat(),
        'level': level,
        'message': f"{icon} {message}" if icon else message,
        'icon': icon
    }


# React组件增强代码片段
REACT_ENHANCEMENTS = """
// 基线文件管理状态
const [baselineExpanded, setBaselineExpanded] = React.useState(false);
const [baselineUrl, setBaselineUrl] = React.useState('');
const [baselineFiles, setBaselineFiles] = React.useState([]);
const [currentWeek, setCurrentWeek] = React.useState(0);
const [baselinePath, setBaselinePath] = React.useState('');
const [downloadingBaseline, setDownloadingBaseline] = React.useState(false);
const [storedUrls, setStoredUrls] = React.useState([]);

// 加载基线文件列表
const loadBaselineFiles = async () => {
    try {
        const response = await fetch('/api/baseline-files');
        const data = await response.json();
        if (data.success) {
            setBaselineFiles(data.files || []);
            setCurrentWeek(data.week || 0);
            setBaselinePath(data.path || '');
        }
    } catch (error) {
        console.error('加载基线文件失败:', error);
    }
};

// 下载基线文件
const handleDownloadBaseline = async () => {
    if (!baselineUrl) {
        alert('请输入基线文件URL');
        return;
    }
    
    setDownloadingBaseline(true);
    try {
        const response = await fetch('/api/baseline-files', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                url: baselineUrl,
                cookie: cookieInput
            })
        });
        
        const data = await response.json();
        if (data.success) {
            alert(`基线文件下载成功: ${data.file.name}`);
            setBaselineUrl('');
            await loadBaselineFiles();  // 刷新文件列表
        } else {
            alert(`下载失败: ${data.error}`);
        }
    } catch (error) {
        alert(`下载出错: ${error.message}`);
    } finally {
        setDownloadingBaseline(false);
    }
};

// 删除基线文件
const handleDeleteBaseline = async (filename) => {
    if (!confirm(`确定要删除文件: ${filename}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/baseline-files', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filename})
        });
        
        const data = await response.json();
        if (data.success) {
            alert(data.message);
            await loadBaselineFiles();  // 刷新文件列表
        } else {
            alert(`删除失败: ${data.error}`);
        }
    } catch (error) {
        alert(`删除出错: ${error.message}`);
    }
};
"""


if __name__ == "__main__":
    # 测试代码
    config_file = '/root/projects/tencent-doc-manager/config/download_config.json'
    
    # 测试URL管理器
    url_manager = URLManager(config_file)
    test_links = [
        {"url": "https://docs.qq.com/sheet/test1", "name": "测试文档1", "enabled": True},
        {"url": "https://docs.qq.com/sheet/test2", "name": "测试文档2", "enabled": True}
    ]
    url_manager.save_links_with_soft_delete(test_links)
    
    # 测试基线文件管理器
    baseline_manager = BaselineFileManager()
    files_info = baseline_manager.list_baseline_files()
    print(f"基线文件信息: {json.dumps(files_info, ensure_ascii=False, indent=2)}")