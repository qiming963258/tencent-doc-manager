# 腾讯文档批量下载 - 技术要点总结

## ✅ 成功的关键发现

### 1. 必须通过主页筛选界面
- **错误方式**: 直接访问 `https://docs.qq.com/sheet/{doc_id}` 单个下载
- **正确方式**: 从 `https://docs.qq.com/desktop` 主页进入，使用筛选功能

### 2. 筛选菜单的准确定位

#### 所有者部分（3个选项）
```
1. 全部
2. 我所有的 ← 选这个
3. 他人所有
```

#### 查看时间部分（4个选项）
```
1. 全部时间
2. 近7天
3. 近1个月 ← 选这个
4. 自定义时间范围
```

### 3. 关键DOM结构
```html
<!-- 筛选按钮 -->
<button class="desktop-filter-button-inner-pc">
  <label>筛选</label>
</button>

<!-- 所有者section -->
<header class="desktop-filter-section-title-pc">所有者</header>
<div class="desktop-filter-radio-group-pc">
  <div class="dui-radio">
    <div class="dui-radio-label">我所有的</div>
    <input type="radio" class="dui-radio-input">
  </div>
</div>

<!-- 查看时间section -->
<header class="desktop-filter-section-title-pc">查看时间</header>
<div class="desktop-filter-radio-group-pc">
  <div class="dui-radio">
    <div class="dui-radio-label">近1个月</div>
    <input type="radio" class="dui-radio-input">
  </div>
</div>
```

## ⚠️ 易错点分析

### 1. 混淆所有者和查看时间
- **问题**: 两个section结构相同，都是radio group
- **解决**: 通过header文本定位到正确的section

### 2. 动态类名问题
- **问题**: React生成的类名带有hash后缀
- **解决**: 使用contains选择器或部分匹配

### 3. 滚动加载
- **问题**: 文档列表是懒加载的
- **解决**: 反复滚动到底部直到没有新内容

### 4. 单个下载限制
- **问题**: 多选无法下载
- **解决**: 必须逐个右键点击下载

## 🛡️ 反检测技术

### 1. 使用 undetected-chromedriver
```python
import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
driver = uc.Chrome(options=options)
```

### 2. 移除webdriver特征
```javascript
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
```

### 3. 模拟人类行为
- 随机延迟: 0.5-2秒
- 平滑滚动
- 鼠标移动轨迹
- 间歇性休息

## 📋 完整操作流程

```python
# 1. 访问主页
driver.get("https://docs.qq.com/desktop")

# 2. 加载Cookie
add_cookies(cookie_string)

# 3. 点击筛选按钮
click("button.desktop-filter-button-inner-pc")

# 4. 选择"我所有"
click("//div[text()='我所有的']/../input")

# 5. 选择"近1个月"  
click("//div[contains(text(), '近1个月')]/../input")

# 6. 滚动加载
scroll_to_bottom_repeatedly()

# 7. 获取文档列表
documents = find_all("[class*='file-list-item']")

# 8. 从下往上逐个下载
for doc in reversed(documents):
    right_click(doc)
    click("//div[contains(., '下载')]")
    wait(3)
```

## 🔍 调试技巧

### 1. 元素定位验证
```javascript
// 在浏览器控制台测试选择器
document.querySelector("button.desktop-filter-button-inner-pc")
document.querySelectorAll("[class*='dui-radio-label']")
```

### 2. 检查Cookie有效性
```javascript
// 检查关键Cookie
document.cookie.includes('DOC_SID')
document.cookie.includes('uid')
```

### 3. 监控网络请求
- 打开开发者工具Network标签
- 观察下载请求的URL格式
- 检查是否有特殊的请求头

## 💾 服务器端自动化

### 最佳实践：Linux服务器 + 虚拟显示
```bash
# 安装虚拟显示
apt-get install xvfb

# 启动虚拟显示
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# 运行脚本
python3 stealth_batch_downloader.py
```

### 定时任务
```cron
# 每天凌晨3点执行
0 3 * * * cd /root/projects/tencent-doc-manager && python3 stealth_batch_downloader.py
```

## 📊 成功率提升要点

1. **使用真实Cookie**: 从浏览器复制完整Cookie字符串
2. **保持登录状态**: 使用持久化浏览器配置
3. **合理间隔**: 文档间隔3-5秒，每10个休息30秒
4. **错误重试**: 失败的文档记录并重试
5. **监控日志**: 详细记录每步操作

## 🚀 下一步优化

1. **并行下载**: 开多个标签页同时下载不同文档
2. **断点续传**: 记录已下载文档，支持中断恢复
3. **智能调度**: 根据服务器负载自动调整下载速度
4. **格式转换**: 下载后自动转换为需要的格式
5. **自动上传**: 下载完成后自动上传到指定服务器

---

**关键结论**: 腾讯文档的批量下载必须通过主页筛选界面，不能直接访问单个文档URL。这是之前所有方案失败的根本原因。