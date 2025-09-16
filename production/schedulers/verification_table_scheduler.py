#!/usr/bin/env python3
"""
第十一步定时任务调度器 - 周四和周六自动生成核验表

实现自动化调度机制:
- 每周四 09:00 生成核验表
- 每周六 09:00 生成核验表  
- 支持手动触发和错误重试
- 记录调度历史和执行结果
"""

import sys
import os
import datetime
import time
import json
import logging
from pathlib import Path

# 添加核心模块路径
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

# 配置日志
log_dir = Path('/root/projects/tencent-doc-manager/logs/schedulers')
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'verification_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VerificationTableScheduler:
    """核验表定时调度器"""
    
    def __init__(self):
        self.schedule_config_file = '/root/projects/tencent-doc-manager/config/scheduler_config.json'
        self.execution_history_file = '/root/projects/tencent-doc-manager/logs/schedulers/execution_history.json'
        
        # 确保配置目录存在
        os.makedirs(os.path.dirname(self.schedule_config_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.execution_history_file), exist_ok=True)
        
        # 调度配置
        self.schedule_config = {
            "enabled": True,
            "thursday_time": "09:00",  # 周四09:00
            "saturday_time": "09:00",  # 周六09:00
            "timezone": "Asia/Shanghai",
            "retry_attempts": 3,
            "retry_interval": 300  # 5分钟
        }
        
        # 加载配置
        self._load_config()
        
        # 初始化核验表生成器
        self.generator = None
        self._init_generator()
    
    def _init_generator(self):
        """初始化核验表生成器"""
        try:
            from verification_table_generator import VerificationTableGenerator
            self.generator = VerificationTableGenerator()
            logger.info("✅ 核验表生成器初始化成功")
        except ImportError as e:
            logger.error(f"❌ 核验表生成器初始化失败: {e}")
            self.generator = None
    
    def _load_config(self):
        """加载调度配置"""
        try:
            if os.path.exists(self.schedule_config_file):
                with open(self.schedule_config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                self.schedule_config.update(loaded_config)
                logger.info("📋 调度配置加载完成")
        except Exception as e:
            logger.warning(f"⚠️ 调度配置加载失败: {e}, 使用默认配置")
    
    def _save_config(self):
        """保存调度配置"""
        try:
            with open(self.schedule_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedule_config, f, ensure_ascii=False, indent=2)
            logger.info("💾 调度配置保存完成")
        except Exception as e:
            logger.error(f"❌ 调度配置保存失败: {e}")
    
    def _load_execution_history(self):
        """加载执行历史"""
        try:
            if os.path.exists(self.execution_history_file):
                with open(self.execution_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"executions": []}
        except Exception as e:
            logger.error(f"❌ 执行历史加载失败: {e}")
            return {"executions": []}
    
    def _save_execution_record(self, execution_record):
        """保存执行记录"""
        try:
            history = self._load_execution_history()
            history["executions"].append(execution_record)
            
            # 只保留最近100次记录
            if len(history["executions"]) > 100:
                history["executions"] = history["executions"][-100:]
            
            with open(self.execution_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            logger.info("📝 执行记录保存完成")
        except Exception as e:
            logger.error(f"❌ 执行记录保存失败: {e}")
    
    def is_scheduled_time(self):
        """检查是否到了预定的执行时间"""
        if not self.schedule_config["enabled"]:
            return False
        
        now = datetime.datetime.now()
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.strftime("%H:%M")
        
        # 周四 (weekday=3) 和周六 (weekday=5)
        if current_weekday == 3:  # Thursday
            return current_time == self.schedule_config["thursday_time"]
        elif current_weekday == 5:  # Saturday
            return current_time == self.schedule_config["saturday_time"]
        
        return False
    
    def execute_generation(self, trigger_type="scheduled"):
        """执行核验表生成"""
        execution_record = {
            "trigger_type": trigger_type,
            "start_time": datetime.datetime.now().isoformat(),
            "success": False,
            "error_message": None,
            "file_path": None,
            "attempts": 0
        }
        
        if not self.generator:
            execution_record["error_message"] = "核验表生成器未初始化"
            self._save_execution_record(execution_record)
            return False
        
        retry_attempts = self.schedule_config.get("retry_attempts", 3)
        retry_interval = self.schedule_config.get("retry_interval", 300)
        
        for attempt in range(1, retry_attempts + 1):
            execution_record["attempts"] = attempt
            
            try:
                logger.info(f"🚀 开始第{attempt}次尝试生成核验表...")
                
                # 执行生成
                success, file_path, generation_info = self.generator.generate_verification_table()
                
                if success:
                    execution_record["success"] = True
                    execution_record["file_path"] = file_path
                    execution_record["generation_info"] = generation_info
                    execution_record["end_time"] = datetime.datetime.now().isoformat()
                    
                    logger.info(f"✅ 核验表生成成功: {file_path}")
                    logger.info(f"📊 矩阵大小: {generation_info.get('matrix_size', '未知')}")
                    
                    self._save_execution_record(execution_record)
                    return True
                else:
                    execution_record["error_message"] = "生成器返回失败"
                    
            except Exception as e:
                execution_record["error_message"] = str(e)
                logger.error(f"❌ 第{attempt}次尝试失败: {e}")
            
            # 如果不是最后一次尝试，等待重试
            if attempt < retry_attempts:
                logger.info(f"⏰ {retry_interval}秒后进行第{attempt+1}次尝试...")
                time.sleep(retry_interval)
        
        # 所有尝试都失败
        execution_record["end_time"] = datetime.datetime.now().isoformat()
        logger.error(f"❌ 所有{retry_attempts}次尝试都失败")
        self._save_execution_record(execution_record)
        return False
    
    def run_daemon(self):
        """运行守护进程模式"""
        logger.info("🎯 启动核验表定时调度守护进程")
        logger.info(f"📅 调度时间: 周四 {self.schedule_config['thursday_time']}, 周六 {self.schedule_config['saturday_time']}")
        
        while True:
            try:
                if self.is_scheduled_time():
                    logger.info("⏰ 到达预定执行时间，开始生成核验表")
                    self.execute_generation(trigger_type="scheduled")
                    
                    # 执行后等待60秒，避免同一分钟内重复执行
                    time.sleep(60)
                else:
                    # 每30秒检查一次
                    time.sleep(30)
                    
            except KeyboardInterrupt:
                logger.info("👋 接收到中断信号，停止调度器")
                break
            except Exception as e:
                logger.error(f"❌ 调度器异常: {e}")
                time.sleep(60)
    
    def manual_trigger(self):
        """手动触发生成"""
        logger.info("🔧 手动触发核验表生成")
        return self.execute_generation(trigger_type="manual")
    
    def get_status(self):
        """获取调度器状态"""
        history = self._load_execution_history()
        recent_executions = history["executions"][-5:] if history["executions"] else []
        
        return {
            "scheduler_enabled": self.schedule_config["enabled"],
            "schedule_times": {
                "thursday": self.schedule_config["thursday_time"],
                "saturday": self.schedule_config["saturday_time"]
            },
            "generator_available": self.generator is not None,
            "recent_executions": recent_executions,
            "total_executions": len(history["executions"])
        }


def main():
    """主函数"""
    scheduler = VerificationTableScheduler()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "manual":
            # 手动触发
            success = scheduler.manual_trigger()
            sys.exit(0 if success else 1)
            
        elif command == "status":
            # 显示状态
            status = scheduler.get_status()
            print(json.dumps(status, ensure_ascii=False, indent=2))
            sys.exit(0)
            
        elif command == "daemon":
            # 守护进程模式
            scheduler.run_daemon()
            sys.exit(0)
        else:
            print("用法: python3 verification_table_scheduler.py [manual|status|daemon]")
            sys.exit(1)
    else:
        # 默认显示状态
        status = scheduler.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()