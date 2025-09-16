#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档Cookie简化分析器
"""

def simple_cookie_analysis():
    current_cookie = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
    cookies = {}
    for pair in current_cookie.split('; '):
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookies[name.strip()] = value.strip()
    
    print("腾讯文档Cookie分析报告")
    print("=" * 50)
    print(f"总计: {len(cookies)} 个Cookie")
    
    # 长效Cookie (用户身份，通常不过期)
    long_term = {
        'uid': '用户ID',
        'utype': '用户类型', 
        'DOC_QQ_APPID': 'QQ应用ID',
        'DOC_QQ_OPENID': 'QQ开放ID',
        'language': '语言设置'
    }
    
    # 会话Cookie (可能过期)
    session = {
        'DOC_SID': '文档会话ID',
        'SID': '会话ID',
        'uid_key': '用户密钥',
        'TOK': '令牌',
        'hashkey': '哈希密钥',
        'traceid': '追踪ID'
    }
    
    # 配置Cookie (相对稳定)
    config = {
        'fingerprint': '浏览器指纹',
        'loginTime': '登录时间',
        'env_id': '环境ID'
    }
    
    print("\n[长效Cookie - 通常不过期]")
    for name, desc in long_term.items():
        if name in cookies:
            value = cookies[name]
            if len(value) > 30:
                value = value[:15] + "..." + value[-10:]
            print(f"  {name}: {value} ({desc})")
    
    print("\n[会话Cookie - 可能已过期]")
    for name, desc in session.items():
        if name in cookies:
            value = cookies[name]
            if len(value) > 30:
                value = value[:15] + "..." + value[-10:]
            print(f"  {name}: {value} ({desc})")
    
    print("\n[配置Cookie - 相对稳定]") 
    for name, desc in config.items():
        if name in cookies:
            value = cookies[name]
            if name == 'loginTime':
                try:
                    import time
                    timestamp = int(value) / 1000
                    readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                    print(f"  {name}: {readable_time} ({desc})")
                except:
                    print(f"  {name}: {value} ({desc})")
            else:
                if len(value) > 30:
                    value = value[:15] + "..." + value[-10:]
                print(f"  {name}: {value} ({desc})")
    
    print("\n" + "=" * 50)
    print("关键结论:")
    print("1. 最可能过期的: DOC_SID, SID, uid_key")
    print("2. 长期有效的: uid, DOC_QQ_OPENID, DOC_QQ_APPID")
    print("3. 登录时间显示: 可能已经过期")
    
    # 检查登录时间
    if 'loginTime' in cookies:
        try:
            import time
            login_timestamp = int(cookies['loginTime']) / 1000
            current_timestamp = time.time()
            hours_passed = (current_timestamp - login_timestamp) / 3600
            print(f"4. 距离登录已过去: {hours_passed:.1f} 小时")
            if hours_passed > 24:
                print("   建议: Cookie可能已过期，需要重新登录")
            else:
                print("   状态: Cookie应该还有效")
        except:
            pass
    
    # 生成最小测试Cookie
    essential = []
    for name in ['uid', 'utype', 'DOC_QQ_APPID', 'DOC_QQ_OPENID', 'DOC_SID', 'SID']:
        if name in cookies:
            essential.append(f"{name}={cookies[name]}")
    
    print(f"\n最小测试Cookie组合:")
    print("; ".join(essential))

if __name__ == "__main__":
    simple_cookie_analysis()