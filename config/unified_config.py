"""
统一配置管理模块
==============
解决系统配置混乱问题，提供单一配置源

创建日期: 2025-09-11
目的: 解决API密钥硬编码和配置分散问题
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class UnifiedConfig:
    """统一配置管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化配置"""
        # 1. 加载.env文件
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ 已加载配置文件: {env_path}")
        else:
            print(f"⚠️ 配置文件不存在: {env_path}")
        
        # 2. 加载所有配置
        self._config = {
            # API密钥配置
            'api': {
                'deepseek_api_key': os.getenv('DEEPSEEK_API_KEY'),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
                'siliconflow_api_key': os.getenv('SILICONFLOW_API_KEY'),
            },
            
            # 服务端口配置
            'ports': {
                'claude_wrapper': 8081,
                'heatmap_ui': 8089,
                'test_system_8093': 8093,
                'test_system_8094': 8094,
                'deepseek_service': 8098,
                'scoring_server': 8100,
                'excel_handler': 8101,
            },
            
            # 路径配置
            'paths': {
                'project_root': '/root/projects/tencent-doc-manager',
                'csv_versions': '/root/projects/tencent-doc-manager/csv_versions',
                'downloads': '/root/projects/tencent-doc-manager/downloads',
                'excel_uploads': '/root/projects/tencent-doc-manager/excel_uploads',
                'semantic_results': '/root/projects/tencent-doc-manager/semantic_results',
                'comparison_results': '/root/projects/tencent-doc-manager/comparison_results',
            },
            
            # 系统配置
            'system': {
                'project_name': os.getenv('PROJECT_NAME', '腾讯文档管理系统'),
                'node_env': os.getenv('NODE_ENV', 'development'),
                'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            },
            
            # Cookie配置
            'cookies': {
                'cookie_file': '/root/projects/tencent-doc-manager/config/cookies.json',
                'cookie_key_file': '/root/projects/tencent-doc-manager/config/cookie_key.key',
            }
        }
        
        # 3. 验证关键配置
        self._validate_config()
    
    def _validate_config(self):
        """验证配置完整性"""
        errors = []
        warnings = []
        
        # 检查API密钥
        if not self._config['api']['deepseek_api_key']:
            warnings.append("DEEPSEEK_API_KEY未配置")
        
        if not self._config['api']['anthropic_api_key']:
            warnings.append("ANTHROPIC_API_KEY未配置")
        
        # 检查关键路径
        for name, path in self._config['paths'].items():
            if not Path(path).exists():
                warnings.append(f"路径不存在: {name} = {path}")
        
        # 输出验证结果
        if errors:
            print("❌ 配置错误:")
            for error in errors:
                print(f"  - {error}")
            raise ValueError("配置验证失败")
        
        if warnings:
            print("⚠️ 配置警告:")
            for warning in warnings:
                print(f"  - {warning}")
    
    def get(self, key_path: str, default=None):
        """
        获取配置值
        
        Args:
            key_path: 配置路径，如 'api.deepseek_api_key'
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        获取API密钥
        
        Args:
            service: 服务名称 (deepseek/anthropic/siliconflow)
        
        Returns:
            API密钥或None
        """
        return self.get(f'api.{service}_api_key')
    
    def get_port(self, service: str) -> Optional[int]:
        """
        获取服务端口
        
        Args:
            service: 服务名称
        
        Returns:
            端口号或None
        """
        return self.get(f'ports.{service}')
    
    def get_path(self, name: str) -> Optional[str]:
        """
        获取路径配置
        
        Args:
            name: 路径名称
        
        Returns:
            路径字符串或None
        """
        return self.get(f'paths.{name}')
    
    def update(self, key_path: str, value: Any):
        """
        更新配置值（仅在内存中，不持久化）
        
        Args:
            key_path: 配置路径
            value: 新值
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        print(f"✅ 配置已更新: {key_path} = {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self._config.copy()
    
    def save_env(self):
        """保存配置到.env文件"""
        env_path = Path(__file__).parent.parent / '.env'
        lines = []
        
        # API密钥
        if self._config['api']['deepseek_api_key']:
            lines.append(f"DEEPSEEK_API_KEY={self._config['api']['deepseek_api_key']}")
        if self._config['api']['anthropic_api_key']:
            lines.append(f"ANTHROPIC_API_KEY={self._config['api']['anthropic_api_key']}")
        if self._config['api']['siliconflow_api_key']:
            lines.append(f"SILICONFLOW_API_KEY={self._config['api']['siliconflow_api_key']}")
        
        # 系统配置
        lines.append(f"PROJECT_NAME={self._config['system']['project_name']}")
        lines.append(f"NODE_ENV={self._config['system']['node_env']}")
        lines.append(f"DEBUG={'true' if self._config['system']['debug'] else 'false'}")
        
        # 写入文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        
        print(f"✅ 配置已保存到: {env_path}")


# 全局配置实例
config = UnifiedConfig()

# 便捷函数
def get_config(key_path: str, default=None):
    """获取配置值的便捷函数"""
    return config.get(key_path, default)

def get_api_key(service: str) -> Optional[str]:
    """获取API密钥的便捷函数"""
    return config.get_api_key(service)

def get_port(service: str) -> Optional[int]:
    """获取服务端口的便捷函数"""
    return config.get_port(service)

def get_path(name: str) -> Optional[str]:
    """获取路径配置的便捷函数"""
    return config.get_path(name)


if __name__ == "__main__":
    # 测试配置管理器
    print("\n=== 统一配置管理器测试 ===\n")
    
    print("API密钥配置:")
    print(f"  DeepSeek: {config.get_api_key('deepseek')[:20]}..." if config.get_api_key('deepseek') else "  DeepSeek: 未配置")
    print(f"  Anthropic: {config.get_api_key('anthropic')[:20]}..." if config.get_api_key('anthropic') else "  Anthropic: 未配置")
    
    print("\n服务端口配置:")
    for service in ['claude_wrapper', 'heatmap_ui', 'test_system_8093', 'deepseek_service']:
        print(f"  {service}: {config.get_port(service)}")
    
    print("\n路径配置:")
    print(f"  项目根目录: {config.get_path('project_root')}")
    print(f"  CSV版本目录: {config.get_path('csv_versions')}")
    
    print("\n系统配置:")
    print(f"  项目名称: {config.get('system.project_name')}")
    print(f"  环境: {config.get('system.node_env')}")
    print(f"  调试模式: {config.get('system.debug')}")