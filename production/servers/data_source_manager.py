#!/usr/bin/env python3
"""
数据源状态管理器
自动加载最新的综合打分文件，并持久化数据源选择
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path


class DataSourceManager:
    """数据源管理器 - 持久化和自动加载"""

    def __init__(self):
        self.config_file = '/root/projects/tencent-doc-manager/config/data_source_state.json'
        self.scoring_dir = '/root/projects/tencent-doc-manager/scoring_results'
        self.state = self.load_state()

    def load_state(self):
        """加载持久化的数据源状态"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    print(f"✅ 加载数据源状态: {state.get('source', 'unknown')}")
                    return state
            except Exception as e:
                print(f"⚠️ 加载数据源状态失败: {e}")

        # 默认状态
        return {
            'source': 'comprehensive',  # 默认使用综合打分
            'file_path': None,
            'last_updated': None,
            'auto_load': True  # 是否自动加载最新文件
        }

    def save_state(self):
        """保存数据源状态"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            print(f"💾 保存数据源状态: {self.state['source']}")
        except Exception as e:
            print(f"❌ 保存数据源状态失败: {e}")

    def find_latest_comprehensive_file(self):
        """查找最新的综合打分文件 - 标准规范：只从按周组织的目录查找"""
        try:
            # 🎯 标准规范：只从按周组织的目录（2025_W*）查找
            # 获取当前周数
            from production.core_modules.week_time_manager import WeekTimeManager
            week_manager = WeekTimeManager()
            week_info = week_manager.get_current_week_info()
            current_week = week_info['week_number']

            # 从当前周开始往前查找，最多查找4周
            for week_offset in range(0, 4):
                week_num = current_week - week_offset
                week_dir = f'2025_W{week_num}'
                week_path = os.path.join(self.scoring_dir, week_dir)

                if not os.path.exists(week_path):
                    continue

                # 在当前周目录查找综合打分文件
                pattern = os.path.join(week_path, 'comprehensive_score_*.json')
                files = glob.glob(pattern)

                if files:
                    # 按修改时间排序，获取最新的
                    latest_file = max(files, key=os.path.getmtime)
                    print(f"🔍 找到最新综合打分文件: {os.path.basename(latest_file)} (W{week_num})")
                    return latest_file

            print("⚠️ 最近4周未找到任何综合打分文件")
            return None

        except Exception as e:
            print(f"❌ 查找综合打分文件失败: {e}")
            return None

    def get_initial_data_source(self):
        """获取初始数据源配置"""
        # 如果配置为自动加载且数据源是综合打分
        if self.state.get('auto_load', True) and self.state.get('source') == 'comprehensive':
            # 查找最新的综合打分文件
            latest_file = self.find_latest_comprehensive_file()

            if latest_file:
                self.state['file_path'] = latest_file
                self.state['last_updated'] = datetime.now().isoformat()
                self.save_state()

                return {
                    'source': 'comprehensive',
                    'file_path': latest_file,
                    'auto_loaded': True
                }

        # 返回保存的状态
        return {
            'source': self.state.get('source', 'csv'),
            'file_path': self.state.get('file_path'),
            'auto_loaded': False
        }

    def update_source(self, source, file_path=None):
        """更新数据源"""
        self.state['source'] = source
        if file_path:
            self.state['file_path'] = file_path
        self.state['last_updated'] = datetime.now().isoformat()
        self.save_state()

        return {
            'success': True,
            'source': source,
            'file_path': file_path
        }

    def get_current_state(self):
        """获取当前状态"""
        return {
            'source': self.state.get('source', 'csv'),
            'file_path': self.state.get('file_path'),
            'last_updated': self.state.get('last_updated'),
            'auto_load': self.state.get('auto_load', True)
        }

    def set_auto_load(self, enabled):
        """设置是否自动加载最新文件"""
        self.state['auto_load'] = enabled
        self.save_state()
        return {'success': True, 'auto_load': enabled}


# 单例实例
data_source_manager = DataSourceManager()