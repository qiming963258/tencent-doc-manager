#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟真实浏览器的FormData请求
"""

import requests
import time

# 真实的Cookie（您提供的）
real_cookie = """fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; dark_mode_setting=system; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1lpSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; backup_cdn_domain=docs.gtimg.com; traceid=e6181a4de6; TOK=e6181a4de6f675a1; hashkey=e6181a4d; language=zh-CN"""

print(f"Cookie长度: {len(real_cookie)} 字符")

# 测试两个不同的URL
url1 = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"  # 副本-测试版本-出国销售计划表
url2 = "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr"  # 副本-测试版本-回国销售计划表

# 使用FormData格式（模拟前端）
form_data = {
    'baseline_type': 'url',
    'baseline_url': url1,
    'baseline_cookie': real_cookie,
    'target_url': url2,
    'target_cookie': real_cookie
}

# 测试不同的端点
endpoints = [
    "http://localhost:8094/api/compare",
    "http://127.0.0.1:8094/api/compare",
    "http://202.140.143.88:8094/api/compare"
]

for endpoint in endpoints:
    print(f"\n测试端点: {endpoint}")
    print("-" * 50)
    
    try:
        start_time = time.time()
        
        # 发送请求（使用FormData）
        response = requests.post(
            endpoint,
            data=form_data,  # 使用data而不是json
            timeout=180  # 3分钟超时
        )
        
        elapsed = time.time() - start_time
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应时间: {elapsed:.2f} 秒")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success'):
                    print("✅ 对比成功!")
                    if result.get('comparison_stats'):
                        stats = result['comparison_stats']
                        print(f"  总变更: {stats.get('total_changes', 0)}")
                        print(f"  相似度: {stats.get('similarity_score', 0)}%")
                else:
                    print(f"❌ 对比失败: {result.get('error', '未知错误')}")
            except:
                print(f"响应内容: {response.text[:200]}")
        else:
            print(f"HTTP错误: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（180秒）")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
    except Exception as e:
        print(f"❌ 异常: {e}")

print("\n" + "=" * 50)
print("测试完成")