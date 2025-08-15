import os
from typing import List, Optional

class ClaudeConfig:
    """Claude封装程序配置管理"""
    
    # Claude API配置（从现有环境变量读取）
    API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    BASE_URL: str = os.getenv("ANTHROPIC_BASE_URL", "https://code2.ppchat.vip")
    
    # 模型配置
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
    BACKUP_MODELS: List[str] = [
        "claude-3-5-haiku-20241022",
        "claude-3-7-sonnet-20250219",
        "claude-sonnet-4-20250514-thinking"
    ]
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8081
    MAX_TOKENS: int = 4000
    DEFAULT_TIMEOUT: int = 60
    
    # 性能配置
    MAX_CONCURRENT_REQUESTS: int = 10
    CONNECTION_POOL_SIZE: int = 50
    KEEPALIVE_TIMEOUT: int = 30
    
    # 缓存配置
    CACHE_SIZE: int = 1000
    CACHE_TTL: int = 3600  # 1小时
    
    # 重试配置
    MAX_RETRIES: int = 3
    BASE_DELAY: float = 1.0
    MAX_DELAY: float = 60.0
    
    # 安全配置
    ALLOWED_IPS: List[str] = ["*"]  # 允许所有IP
    API_RATE_LIMIT: int = 100  # 每分钟请求限制
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置有效性"""
        if not cls.API_KEY:
            print("⚠️ ANTHROPIC_API_KEY 环境变量未设置")
            return False
        if not cls.BASE_URL:
            print("⚠️ ANTHROPIC_BASE_URL 环境变量未设置")
            return False
        print(f"✅ Claude API配置有效")
        print(f"   API Key: {cls.API_KEY[:20]}...")
        print(f"   Base URL: {cls.BASE_URL}")
        print(f"   Default Model: {cls.DEFAULT_MODEL}")
        return True
    
    @classmethod
    def get_available_models(cls) -> List[dict]:
        """获取可用模型列表"""
        models = [{"id": cls.DEFAULT_MODEL, "type": "primary", "description": "默认主模型"}]
        for model in cls.BACKUP_MODELS:
            models.append({"id": model, "type": "backup", "description": "备用模型"})
        return models