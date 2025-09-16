#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用真实Cookie测试对比系统
"""

import requests
import json

# 您提供的完整Cookie
real_cookie = """fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; dark_mode_setting=system; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; backup_cdn_domain=docs.gtimg.com; traceid=e6181a4de6; TOK=e6181a4de6f675a1; hashkey=e6181a4d; language=zh-CN"""

print(f"Cookie长度: {len(real_cookie)} 字符")

# 测试数据 - 使用项目中配置的真实文档
test_data = {
    "baseline_type": "url",
    "baseline_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",  # 测试版本-小红书部门
    "baseline_cookie": real_cookie,
    "target_url": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",  # 副本-测试版本-回国销售计划表
    "target_cookie": real_cookie
}

# 发送请求
url = "http://localhost:8094/api/compare"
print(f"\n发送请求到: {url}")
print("请等待（最多30秒）...")

try:
    # 使用FormData格式（因为前端使用FormData）
    response = requests.post(url, data=test_data, timeout=35)
    
    print(f"\n响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get('success'):
            print("\n✅ 对比成功！")
            if result.get('comparison_stats'):
                stats = result['comparison_stats']
                print(f"  - 总变更数: {stats.get('total_changes', 0)}")
                print(f"  - 新增行数: {stats.get('added_rows', 0)}")
                print(f"  - 删除行数: {stats.get('deleted_rows', 0)}")
                print(f"  - 相似度: {stats.get('similarity_score', 0)}%")
        else:
            print(f"\n❌ 对比失败: {result.get('error', '未知错误')}")
    else:
        print(f"\n❌ HTTP错误: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.Timeout:
    print("\n❌ 请求超时（超过35秒）")
except Exception as e:
    print(f"\n❌ 错误: {e}")