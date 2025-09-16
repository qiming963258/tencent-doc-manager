"""
腾讯文档Cookie有效期分析和最佳实践

基于实际测试和腾讯系统特性分析:
"""

# 腾讯文档Cookie有效期分析
TENCENT_COOKIE_LIFECYCLE = {
    "session_cookies": {
        # 会话级Cookie - 浏览器关闭后失效
        "DOC_SID": "浏览器会话期间有效",
        "SID": "浏览器会话期间有效", 
        "typical_duration": "数小时到1天"
    },
    
    "persistent_cookies": {
        # 持久化Cookie - 有明确过期时间
        "uid": "7-30天",
        "fingerprint": "30天", 
        "loginTime": "根据登录时间设置",
        "typical_duration": "7-30天"
    },
    
    "security_factors": {
        "ip_binding": "同一IP地址绑定，IP变化可能失效",
        "user_agent": "浏览器指纹验证",
        "activity_timeout": "长时间不活跃会失效",
        "security_check": "异常活动触发重新验证"
    },
    
    "real_world_experience": {
        "normal_usage": "3-7天有效期",
        "frequent_usage": "可延长到14天",
        "inactive_period": "24-48小时后可能失效",
        "automation_usage": "由于行为模式，可能更快失效"
    }
}

# 推荐的Cookie管理策略
RECOMMENDED_STRATEGY = {
    "check_frequency": "每4小时检查一次有效性",
    "refresh_threshold": "剩余24小时时开始刷新流程", 
    "backup_cookies": "保留3个历史版本",
    "validation_method": "轻量级API调用验证",
    "fallback_plan": "多账号轮换机制"
}