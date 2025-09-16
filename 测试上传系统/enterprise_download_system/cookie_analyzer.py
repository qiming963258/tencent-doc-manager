#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档Cookie分析器 - 识别长效和临时Cookie
"""

def analyze_tencent_cookies():
    current_cookie = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
    print("="*80)
    print("                腾讯文档Cookie分析报告")
    print("="*80)
    
    cookies = {}
    for pair in current_cookie.split('; '):
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookies[name.strip()] = value.strip()
    
    print(f"\n[总览] 发现 {len(cookies)} 个Cookie项")
    
    # 按类别分析Cookie
    categories = {
        '用户身份认证': ['uid', 'utype', 'DOC_QQ_APPID', 'DOC_QQ_OPENID', 'uid_key'],
        '会话管理': ['DOC_SID', 'SID', 'traceid', 'TOK', 'hashkey'],
        '登录状态': ['loginTime', 'low_login_enable'],
        '用户设置': ['language', 'dark_mode_setting', 'polish_tooltip'],
        '系统配置': ['env_id', 'gray_user', 'backup_cdn_domain', 'optimal_cdn_domain'],
        '追踪分析': ['RK', 'ptcz', 'pgv_pvid', 'adtag', 'yyb_muid'],
        '指纹识别': ['fingerprint']
    }
    
    print("\n" + "="*80)
    print("                    Cookie分类分析")
    print("="*80)
    
    critical_cookies = []
    session_cookies = []
    config_cookies = []
    
    for category, cookie_names in categories.items():
        print(f"\n[{category}]")
        for name in cookie_names:
            if name in cookies:
                value = cookies[name]
                
                # 判断Cookie类型
                if name in ['uid', 'DOC_QQ_OPENID', 'DOC_QQ_APPID']:
                    cookie_type = "🔑 长效-用户标识"
                    critical_cookies.append(name)
                elif name in ['DOC_SID', 'SID', 'TOK', 'uid_key']:
                    cookie_type = "⚡ 会话-可能过期"
                    session_cookies.append(name)
                elif name in ['traceid', 'hashkey']:
                    cookie_type = "🔄 临时-会变化"
                elif name == 'loginTime':
                    cookie_type = "📅 时间戳"
                    # 分析登录时间
                    try:
                        import time
                        login_timestamp = int(value) / 1000
                        login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(login_timestamp))
                        print(f"    登录时间: {login_time}")
                    except:
                        pass
                else:
                    cookie_type = "⚙️ 配置-相对稳定"
                    config_cookies.append(name)
                
                # 显示值（敏感信息部分隐藏）
                display_value = value
                if len(value) > 50:
                    display_value = value[:20] + "..." + value[-10:]
                
                print(f"  {name}: {display_value}")
                print(f"    类型: {cookie_type}")
        
    print("\n" + "="*80)
    print("                      关键结论")
    print("="*80)
    
    print("\n[🔑 最关键的长效Cookie] (通常不会过期):")
    for name in critical_cookies:
        if name in cookies:
            print(f"  ✅ {name} = {cookies[name]}")
    
    print("\n[⚡ 会话Cookie] (可能已过期，需要重新获取):")
    for name in session_cookies:
        if name in cookies:
            value = cookies[name][:30] + "..." if len(cookies[name]) > 30 else cookies[name]
            print(f"  ⚠️  {name} = {value}")
    
    print("\n[💡 建议操作]:")
    print("1. 首先尝试只使用关键长效Cookie")
    print("2. 如果失败，需要重新登录获取新的会话Cookie")
    print("3. 特别关注 DOC_SID, SID, uid_key 这三个可能过期")
    
    # 生成最小Cookie字符串
    essential_cookies = []
    for name in ['uid', 'utype', 'DOC_QQ_APPID', 'DOC_QQ_OPENID']:
        if name in cookies:
            essential_cookies.append(f"{name}={cookies[name]}")
    
    print(f"\n[🧪 测试用最小Cookie字符串]:")
    print("; ".join(essential_cookies))
    
    return cookies

if __name__ == "__main__":
    cookies = analyze_tencent_cookies()