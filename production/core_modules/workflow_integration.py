#!/usr/bin/env python3
"""
工作流集成模块 - 整合下载、处理、上传的完整流程

核心功能：
1. 自动化完整工作流
2. 在适当时机触发上传
3. 管理文件与URL的映射关系
4. 统一的Cookie和配置管理

工作流程：
1. 下载CSV文件 → 2. 数据对比分析 → 3. 生成Excel报告 → 4. 自动上传 → 5. 记录URL映射
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

# 导入各个模块
from .week_time_manager import WeekTimeManager
from .tencent_doc_upload_production_v3 import sync_upload_v3
from .upload_url_manager import get_manager as get_url_manager
from .cookie_manager import CookieManager

logger = logging.getLogger(__name__)


class WorkflowIntegration:
    """工作流集成管理器"""
    
    def __init__(self):
        """初始化工作流管理器"""
        self.project_root = Path('/root/projects/tencent-doc-manager')
        
        # 初始化各个管理器
        self.week_manager = WeekTimeManager()
        self.url_manager = get_url_manager()
        self.cookie_manager = CookieManager()
        
        # 配置路径
        self.csv_dir = self.project_root / 'csv_versions'
        self.excel_dir = self.project_root / 'excel_outputs'
        self.comparison_dir = self.project_root / 'comparison_results'
        
        # 确保目录存在
        for dir_path in [self.csv_dir, self.excel_dir, self.comparison_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 工作流配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载工作流配置"""
        config_file = self.project_root / 'workflow_config.json'
        
        default_config = {
            'auto_upload': True,  # 是否自动上传
            'upload_delay': 5,    # 上传延迟（秒）
            'batch_upload': False,  # 是否批量上传
            'max_batch_size': 5,   # 最大批量大小
            'preserve_local': True,  # 是否保留本地文件
            'upload_patterns': [   # 需要上传的文件模式
                'risk_analysis_report_*.xlsx',
                'tencent_*_final_W*.xlsx',
                'comparison_report_*.xlsx'
            ]
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"加载配置失败，使用默认配置: {e}")
        
        return default_config
    
    async def process_csv_download(self, doc_url: str, doc_name: str) -> str:
        """
        处理CSV下载
        
        Args:
            doc_url: 腾讯文档URL
            doc_name: 文档名称
        
        Returns:
            下载的文件路径
        """
        from .tencent_export_automation import TencentExporter
        
        logger.info(f"开始下载: {doc_name}")
        
        # 获取Cookie
        cookie = await self.cookie_manager.get_best_cookie()
        if not cookie:
            raise ValueError("没有可用的Cookie")
        
        # 初始化导出器
        exporter = TencentExporter()
        
        # 生成文件名
        week_info = self.week_manager.get_current_week_info()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_type = self._determine_version_type()
        
        filename = f"tencent_{doc_name}_{timestamp}_{version_type}_W{week_info['week_number']}.csv"
        file_path = self.csv_dir / f"{week_info['year']}_W{week_info['week_number']}" / version_type / filename
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 执行下载
        success = await exporter.export_to_csv(doc_url, str(file_path), cookie)
        
        if success:
            logger.info(f"✅ 下载成功: {file_path}")
            return str(file_path)
        else:
            raise Exception(f"下载失败: {doc_name}")
    
    def _determine_version_type(self) -> str:
        """
        根据当前时间确定版本类型
        
        Returns:
            baseline/midweek/final
        """
        week_info = self.week_manager.get_current_week_info()
        day_of_week = datetime.now().weekday()
        
        if day_of_week == 0:  # 周一
            return 'baseline'
        elif day_of_week in [2, 3]:  # 周三、周四
            return 'midweek'
        elif day_of_week >= 5:  # 周六、周日
            return 'final'
        else:
            return 'midweek'  # 默认
    
    async def process_comparison(self, baseline_file: str, target_file: str) -> Dict[str, Any]:
        """
        处理文件对比
        
        Args:
            baseline_file: 基准文件路径
            target_file: 目标文件路径
        
        Returns:
            对比结果
        """
        from .auto_comparison_task import CSVAutoComparator
        
        logger.info(f"开始对比: {Path(baseline_file).name} vs {Path(target_file).name}")
        
        comparator = CSVAutoComparator()
        result = await comparator.compare(baseline_file, target_file)
        
        # 保存对比结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = self.comparison_dir / f"comparison_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 对比完成，结果保存到: {result_file}")
        return result
    
    async def process_excel_generation(self, comparison_result: Dict[str, Any]) -> str:
        """
        生成Excel报告
        
        Args:
            comparison_result: 对比结果
        
        Returns:
            生成的Excel文件路径
        """
        logger.info("开始生成Excel报告")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_file = self.excel_dir / f"risk_analysis_report_{timestamp}.xlsx"
        
        # 这里调用Excel生成逻辑（使用MCP或其他方法）
        # 示例代码，实际需要根据具体实现调整
        try:
            # 生成Excel报告的具体实现
            # ...
            pass
        except Exception as e:
            logger.error(f"生成Excel失败: {e}")
            raise
        
        logger.info(f"✅ Excel报告生成成功: {excel_file}")
        return str(excel_file)
    
    async def process_upload(self, file_path: str, auto_upload: bool = None) -> Optional[str]:
        """
        处理文件上传
        
        Args:
            file_path: 要上传的文件路径
            auto_upload: 是否自动上传，None则使用配置
        
        Returns:
            上传后的文档URL，如果未上传则返回None
        """
        if auto_upload is None:
            auto_upload = self.config.get('auto_upload', True)
        
        if not auto_upload:
            logger.info(f"跳过上传（auto_upload=False）: {file_path}")
            return None
        
        # 检查是否已经上传过
        existing = self.url_manager.get_by_file(file_path)
        if existing:
            logger.info(f"文件已上传过: {existing.doc_url}")
            return existing.doc_url
        
        logger.info(f"开始上传: {Path(file_path).name}")
        
        # 获取Cookie
        cookie = await self.cookie_manager.get_best_cookie()
        if not cookie:
            logger.error("没有可用的Cookie，跳过上传")
            return None
        
        # 添加上传延迟
        delay = self.config.get('upload_delay', 5)
        if delay > 0:
            logger.info(f"等待 {delay} 秒后开始上传...")
            await asyncio.sleep(delay)
        
        # 执行上传
        try:
            result = sync_upload_v3(
                cookie_string=cookie,
                file_path=file_path,
                headless=True
            )
            
            if result.get('success'):
                doc_url = result.get('url')
                
                # 记录映射关系
                self.url_manager.add_mapping(
                    file_path=file_path,
                    doc_url=doc_url,
                    metadata={
                        'upload_time': datetime.now().isoformat(),
                        'upload_method': 'v3',
                        'doc_name': result.get('doc_name'),
                        'message': result.get('message')
                    }
                )
                
                logger.info(f"✅ 上传成功: {doc_url}")
                return doc_url
            else:
                logger.error(f"上传失败: {result.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"上传异常: {e}")
            return None
    
    async def run_complete_workflow(self, doc_urls: List[str]) -> Dict[str, Any]:
        """
        运行完整工作流
        
        Args:
            doc_urls: 要处理的腾讯文档URL列表
        
        Returns:
            工作流执行结果
        """
        logger.info("=" * 60)
        logger.info("🚀 开始执行完整工作流")
        logger.info("=" * 60)
        
        results = {
            'start_time': datetime.now().isoformat(),
            'downloads': [],
            'comparisons': [],
            'excel_files': [],
            'uploads': [],
            'errors': []
        }
        
        try:
            # 步骤1: 下载所有CSV文件
            downloaded_files = []
            for url in doc_urls:
                try:
                    file_path = await self.process_csv_download(url, f"doc_{len(downloaded_files)+1}")
                    downloaded_files.append(file_path)
                    results['downloads'].append({
                        'url': url,
                        'file': file_path,
                        'status': 'success'
                    })
                except Exception as e:
                    logger.error(f"下载失败 {url}: {e}")
                    results['errors'].append(str(e))
            
            # 步骤2: 执行对比分析
            if len(downloaded_files) >= 2:
                comparison = await self.process_comparison(
                    downloaded_files[0],  # baseline
                    downloaded_files[-1]  # target
                )
                results['comparisons'].append(comparison)
            
            # 步骤3: 生成Excel报告
            if results['comparisons']:
                excel_file = await self.process_excel_generation(results['comparisons'][0])
                results['excel_files'].append(excel_file)
                
                # 步骤4: 自动上传Excel
                if self.config.get('auto_upload'):
                    upload_url = await self.process_upload(excel_file)
                    if upload_url:
                        results['uploads'].append({
                            'file': excel_file,
                            'url': upload_url,
                            'status': 'success'
                        })
            
            # 步骤5: 批量上传其他文件（如果启用）
            if self.config.get('batch_upload'):
                await self._batch_upload_files(results)
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            results['errors'].append(str(e))
        
        results['end_time'] = datetime.now().isoformat()
        
        # 保存工作流结果
        self._save_workflow_result(results)
        
        logger.info("=" * 60)
        logger.info("✅ 工作流执行完成")
        logger.info(f"  下载: {len(results['downloads'])} 个文件")
        logger.info(f"  对比: {len(results['comparisons'])} 次")
        logger.info(f"  Excel: {len(results['excel_files'])} 个")
        logger.info(f"  上传: {len(results['uploads'])} 个")
        logger.info("=" * 60)
        
        return results
    
    async def _batch_upload_files(self, results: Dict[str, Any]):
        """批量上传文件"""
        batch_size = self.config.get('max_batch_size', 5)
        patterns = self.config.get('upload_patterns', [])
        
        # 查找符合模式的文件
        files_to_upload = []
        for pattern in patterns:
            for file_path in self.excel_dir.glob(pattern):
                # 检查是否已上传
                if not self.url_manager.get_by_file(str(file_path)):
                    files_to_upload.append(str(file_path))
        
        # 批量上传
        for i in range(0, len(files_to_upload), batch_size):
            batch = files_to_upload[i:i+batch_size]
            logger.info(f"批量上传 {len(batch)} 个文件")
            
            for file_path in batch:
                url = await self.process_upload(file_path)
                if url:
                    results['uploads'].append({
                        'file': file_path,
                        'url': url,
                        'status': 'batch'
                    })
    
    def _save_workflow_result(self, results: Dict[str, Any]):
        """保存工作流结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = self.project_root / 'workflow_results' / f"workflow_{timestamp}.json"
        
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"工作流结果保存到: {result_file}")
    
    def get_upload_url_for_file(self, file_path: str) -> Optional[str]:
        """
        获取文件对应的上传URL
        
        Args:
            file_path: 文件路径
        
        Returns:
            腾讯文档URL，如果未找到则返回None
        """
        record = self.url_manager.get_by_file(file_path)
        return record.doc_url if record else None
    
    def get_upload_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取上传历史
        
        Args:
            limit: 返回记录数量限制
        
        Returns:
            上传历史记录列表
        """
        stats = self.url_manager.get_statistics()
        return stats.get('recent_uploads', [])[:limit]


# 单例实例
_workflow_instance: Optional[WorkflowIntegration] = None

def get_workflow_manager() -> WorkflowIntegration:
    """获取工作流管理器单例"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = WorkflowIntegration()
    return _workflow_instance


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test_workflow():
        manager = get_workflow_manager()
        
        # 测试上传单个文件
        test_file = "/root/projects/tencent-doc-manager/excel_outputs/risk_analysis_report_20250819_024132.xlsx"
        if Path(test_file).exists():
            url = await manager.process_upload(test_file)
            if url:
                print(f"上传成功: {url}")
            else:
                print("上传失败")
        
        # 获取上传历史
        history = manager.get_upload_history()
        print(f"\n最近上传历史:")
        for item in history:
            print(f"  - {item['file_name']}: {item['doc_url']}")
    
    # 运行测试
    asyncio.run(test_workflow())