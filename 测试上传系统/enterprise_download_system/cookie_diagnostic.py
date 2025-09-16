#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie有效性诊断工具 - 检测关键认证接口
"""

import asyncio
from playwright.async_api import async_playwright

class CookieDiagnostic:
    def __init__(self):
        # 你当前使用的Cookie
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
        
    def parse_cookies(self):
        cookies = []
        for cookie_pair in self.cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',
                    'path': '/'
                })
        return cookies

    async def test_key_endpoints(self):
        """测试关键的认证端点"""
        
        print("\n" + "="*50)
        print("   腾讯文档Cookie有效性诊断")
        print("="*50)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # 设置Cookie
            await context.add_cookies(self.parse_cookies())
            page = await context.new_page()
            
            # 关键测试端点列表
            test_endpoints = [
                {
                    'name': '用户信息接口(核心)',
                    'url': 'https://docs.qq.com/cgi-bin/online_docs/user_info?get_vip_info=1',
                    'critical': True
                },
                {
                    'name': '用户信息接口(备用)',
                    'url': 'https://docs.qq.com/cgi-bin/online_docs/user_info?xsrf=25ea7d9ac7e65c7d&get_vip_info=1',
                    'critical': True
                },
                {
                    'name': '账户列表',
                    'url': 'https://docs.qq.com/cgi-bin/online_docs/account_list?xsrf=25ea7d9ac7e65c7d',
                    'critical': True
                },
                {
                    'name': '桌面主页',
                    'url': 'https://docs.qq.com/desktop/',
                    'critical': False
                },
                {
                    'name': '我的文档',
                    'url': 'https://docs.qq.com/desktop/mydocs',
                    'critical': False
                }
            ]
            
            valid_endpoints = 0
            critical_failures = 0
            
            for endpoint in test_endpoints:
                try:
                    print(f"\n[TEST] {endpoint['name']}")
                    print(f"[URL]  {endpoint['url']}")
                    
                    response = await page.goto(endpoint['url'], 
                                             wait_until='domcontentloaded', 
                                             timeout=15000)
                    
                    status = response.status
                    print(f"[STATUS] {status}")
                    
                    # 获取响应内容
                    content = await page.content()
                    
                    if status == 200:
                        # 检查响应内容
                        if 'login' in content.lower() or '登录' in content:
                            print("[RESULT] 需要登录 - Cookie可能无效")
                            if endpoint['critical']:
                                critical_failures += 1
                        elif 'uid' in content and 'guest' not in content:
                            print("[RESULT] 认证成功 - 检测到用户信息")
                            valid_endpoints += 1
                        elif 'userType":"guest"' in content:
                            print("[RESULT] Guest模式 - Cookie可能过期")
                            if endpoint['critical']:
                                critical_failures += 1
                        elif len(content) > 1000:
                            print("[RESULT] 页面加载成功 - 可能有效")
                            valid_endpoints += 1
                        else:
                            print(f"[RESULT] 响应异常 - 内容长度{len(content)}")
                    
                    elif status == 302:
                        redirect_url = response.headers.get('location', 'Unknown')
                        print(f"[RESULT] 重定向 -> {redirect_url}")
                        if 'login' in redirect_url:
                            print("[ERROR] 重定向到登录页面 - Cookie无效!")
                            if endpoint['critical']:
                                critical_failures += 1
                    
                    else:
                        print(f"[RESULT] HTTP错误 {status}")
                        if endpoint['critical']:
                            critical_failures += 1
                            
                except Exception as e:
                    print(f"[ERROR] 请求失败: {str(e)}")
                    if endpoint['critical']:
                        critical_failures += 1
                
                await asyncio.sleep(2)  # 避免请求过快
            
            # 诊断结果
            print(f"\n" + "="*50)
            print("         诊断结果")
            print("="*50)
            print(f"有效端点数: {valid_endpoints}/{len(test_endpoints)}")
            print(f"关键失败数: {critical_failures}")
            
            if critical_failures == 0:
                print("[DIAGNOSIS] Cookie状态: 良好")
                print("[ADVICE] Cookie有效，问题可能在页面交互逻辑")
            elif critical_failures >= 2:
                print("[DIAGNOSIS] Cookie状态: 无效或过期")
                print("[ADVICE] 需要重新获取Cookie!")
                print("\n解决方案:")
                print("1. 手动登录 https://docs.qq.com")
                print("2. F12 -> Application -> Cookies")
                print("3. 复制所有Cookie值更新脚本")
            else:
                print("[DIAGNOSIS] Cookie状态: 部分有效")
                print("[ADVICE] 某些关键Cookie可能缺失")
            
            # 保持浏览器让用户观察
            print(f"\n[WAIT] 保持浏览器15秒供检查...")
            await asyncio.sleep(15)
            await browser.close()

async def main():
    diagnostic = CookieDiagnostic()
    await diagnostic.test_key_endpoints()

if __name__ == "__main__":
    asyncio.run(main())