#!/usr/bin/env python3
"""
浏览器进程管理器 - 确保所有浏览器进程被正确清理
"""

import os
import psutil
import signal
import time
import subprocess
from pathlib import Path

class BrowserProcessManager:
    """浏览器进程管理器"""
    
    @staticmethod
    def kill_all_browser_processes():
        """强制终止所有浏览器相关进程"""
        killed_count = 0
        
        # 目标进程名称列表
        browser_names = [
            'chrome', 'chromium', 'chrome-linux',
            'chromium-browser', 'Google Chrome',
            'playwright', 'node'
        ]
        
        try:
            # 使用psutil遍历所有进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # 检查进程名
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                    proc_cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    
                    # 判断是否是浏览器进程
                    is_browser = False
                    for browser in browser_names:
                        if browser.lower() in proc_name or browser.lower() in proc_cmdline.lower():
                            is_browser = True
                            break
                    
                    # 特别检查playwright和ms-playwright路径
                    if 'ms-playwright' in proc_cmdline or '.cache/ms-playwright' in proc_cmdline:
                        is_browser = True
                    
                    if is_browser:
                        print(f"🔫 终止进程: PID={proc.info['pid']}, NAME={proc.info['name']}")
                        try:
                            # 先尝试优雅终止
                            proc.terminate()
                            proc.wait(timeout=3)
                        except:
                            # 如果失败，强制终止
                            proc.kill()
                        killed_count += 1
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            print(f"⚠️ psutil清理失败: {e}")
            
        # 备用方案：使用系统命令
        try:
            # 使用pkill命令
            for browser in ['chrome', 'chromium', 'playwright']:
                subprocess.run(['pkill', '-f', browser], capture_output=True)
                
            # 使用killall命令作为最后手段
            subprocess.run(['killall', '-9', 'chrome'], capture_output=True, stderr=subprocess.DEVNULL)
            subprocess.run(['killall', '-9', 'chromium'], capture_output=True, stderr=subprocess.DEVNULL)
            
        except:
            pass
            
        if killed_count > 0:
            print(f"✅ 共终止 {killed_count} 个浏览器进程")
            time.sleep(1)  # 等待进程完全退出
        else:
            print("✅ 没有发现运行中的浏览器进程")
            
        return killed_count
    
    @staticmethod
    def clean_temp_profiles():
        """清理临时浏览器配置文件"""
        temp_dirs = [
            '/tmp/playwright*',
            '/tmp/puppeteer*',
            '/tmp/.com.google.Chrome*',
            '/tmp/chrome*',
            '/tmp/chromium*'
        ]
        
        cleaned = 0
        for pattern in temp_dirs:
            try:
                import glob
                for path in glob.glob(pattern):
                    try:
                        import shutil
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                        cleaned += 1
                    except:
                        pass
            except:
                pass
                
        if cleaned > 0:
            print(f"🧹 清理了 {cleaned} 个临时文件/目录")
            
    @staticmethod
    def get_browser_memory_usage():
        """获取所有浏览器进程的内存使用情况"""
        total_memory = 0
        process_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                if any(browser in proc_name for browser in ['chrome', 'chromium', 'playwright']):
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    total_memory += memory_mb
                    process_count += 1
                    print(f"  📊 PID {proc.info['pid']}: {memory_mb:.2f}MB")
            except:
                continue
                
        if process_count > 0:
            print(f"📊 浏览器进程总内存: {total_memory:.2f}MB ({process_count}个进程)")
        return total_memory
    
    @staticmethod
    def ensure_clean_state():
        """确保系统处于干净状态"""
        print("🔧 执行完整的浏览器清理...")
        
        # 1. 终止所有浏览器进程
        BrowserProcessManager.kill_all_browser_processes()
        
        # 2. 清理临时文件
        BrowserProcessManager.clean_temp_profiles()
        
        # 3. 显示内存状态
        import psutil
        mem = psutil.virtual_memory()
        print(f"💾 系统内存状态: 可用 {mem.available/1024/1024:.0f}MB / 总计 {mem.total/1024/1024:.0f}MB")
        
        print("✅ 浏览器清理完成！")


def test_cleanup():
    """测试清理功能"""
    print("="*60)
    print("浏览器进程清理测试")
    print("="*60)
    
    manager = BrowserProcessManager()
    
    # 检查当前状态
    print("\n📋 清理前状态:")
    manager.get_browser_memory_usage()
    
    # 执行清理
    print("\n🚀 开始清理:")
    manager.ensure_clean_state()
    
    # 检查清理后状态
    print("\n📋 清理后状态:")
    manager.get_browser_memory_usage()
    
    print("="*60)


if __name__ == "__main__":
    test_cleanup()