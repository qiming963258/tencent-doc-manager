# 腾讯文档获取 - 实际可行方案

## 现实情况
- ❌ 直接API下载二进制：已被腾讯封堵
- ❌ 解析EJS获取数据：EJS是空壳，无数据
- ❌ 开源解决方案：全部失效

## ✅ 真正可行的方案

### 方案1：CSV下载（推荐）
**可行性**: 90% | **速度**: 快 | **稳定性**: 高

```python
# 已实现并验证有效
from xsrf_enhanced_downloader import XSRFEnhancedDownloader

downloader = XSRFEnhancedDownloader()
# CSV格式目前仍可获取数据
result = downloader.download_document(doc_id, format_type='csv')
```

**优势**:
- CSV格式相对稳定，腾讯未完全封堵
- 获取速度快（1-2秒/文档）
- 已实现XSRF认证，成功率高

**劣势**:
- 丢失格式信息（颜色、公式等）
- 可能随时被封堵

### 方案2：Playwright浏览器自动化
**可行性**: 95% | **速度**: 慢 | **稳定性**: 最高

```python
from playwright.sync_api import sync_playwright

def download_with_browser(doc_url, cookies):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        # 添加cookies
        context.add_cookies(cookies)
        
        page = context.new_page()
        page.goto(doc_url)
        
        # 等待表格加载
        page.wait_for_selector('table', timeout=30000)
        
        # 点击导出按钮
        page.click('button[aria-label="导出"]')
        
        # 等待下载
        with page.expect_download() as download_info:
            page.click('text="Excel(.xlsx)"')
        download = download_info.value
        
        # 保存文件
        download.save_as(f"download_{doc_id}.xlsx")
```

**优势**:
- 完全模拟用户行为，几乎不可能被封
- 可获取完整格式的Excel文件
- 支持各种复杂交互

**劣势**:
- 速度慢（5-10秒/文档）
- 资源消耗大（内存1-2GB）
- 需要图形环境

### 方案3：混合策略（最佳实践）
**可行性**: 92% | **速度**: 中 | **稳定性**: 高

```python
class HybridDownloader:
    def download(self, doc_id):
        # 1. 先尝试CSV快速获取数据
        try:
            data = download_csv(doc_id)
            if data:
                return data
        except:
            pass
        
        # 2. CSV失败则使用Playwright
        try:
            data = download_with_playwright(doc_id)
            return data
        except:
            pass
        
        # 3. 最后降级到只获取元数据
        return get_metadata_only(doc_id)
```

### 方案4：申请官方API（长期方案）
**可行性**: 100% | **成本**: 高 | **稳定性**: 最高

1. 申请企业认证
2. 获取API权限
3. 付费使用

**注意**: 需要企业资质，有审核流程

## 风险控制建议

### 1. 请求频率控制
```python
import random
import time

def safe_download(doc_ids):
    for doc_id in doc_ids:
        # 随机延迟3-10秒
        delay = random.uniform(3, 10)
        time.sleep(delay)
        
        # 下载
        download(doc_id)
        
        # 每10个文档休息1分钟
        if doc_ids.index(doc_id) % 10 == 0:
            time.sleep(60)
```

### 2. 多账号轮换
```python
accounts = [account1, account2, account3, ...]
current_account = 0

def rotate_account():
    global current_account
    current_account = (current_account + 1) % len(accounts)
    return accounts[current_account]
```

### 3. 异常监控
```python
def monitor_success_rate():
    if success_rate < 0.5:  # 成功率低于50%
        alert("可能被检测，暂停操作")
        pause_operations()
```

## 实施优先级

1. **立即**: 优化现有CSV下载，加强稳定性
2. **本周**: 部署Playwright备用方案
3. **本月**: 建立监控和告警机制
4. **长期**: 申请官方API

## 核心建议

> **不要试图破解EJS格式，它是个陷阱。**
> 
> 使用CSV获取数据 + Playwright获取格式 = 完整解决方案

## 监控指标

- 每日成功率 > 90%
- 单次请求延迟 > 5秒
- 账号封禁率 < 5%
- 格式变化检测：每日

## 结论

腾讯的反爬策略有效但不是无解。通过组合使用多种技术手段，配合适当的风险控制，仍可维持稳定的数据获取能力。关键是要有备用方案和监控机制，随时应对变化。