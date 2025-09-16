# 📋 Windows环境快速启动指南

## 🚀 环境准备 (必须先完成)

```bash
# 1. 安装Python依赖
pip install playwright asyncio pathlib

# 2. 安装Chromium浏览器
playwright install chromium

# 3. 验证安装
python -c "import playwright; print('✅ Playwright安装成功')"
```

## ⭐ 推荐执行顺序

### 第1步: 基础测试
```bash
python windows_observable_downloader.py
```
**重点观察**: 页面加载、用户状态、Cloud Docs按钮

### 第2步: 如果第1步有问题，尝试简化版本
```bash  
python smart_downloader.py
```
**重点观察**: 元素查找、导航跳转

### 第3步: 如果需要详细分析，重新运行页面分析
```bash
python analyze_page.py
```
**会生成**: 新的page_analysis.html和ui_selectors.txt

## 🔧 调试技巧

### 如果Cookie过期
1. 手动访问 https://docs.qq.com/desktop
2. F12→Application→Cookies→复制新的Cookie字符串
3. 替换脚本中的cookie_string变量

### 如果元素找不到
1. F12→Elements→右键→Copy selector
2. 记录正确的CSS选择器
3. 反馈给用户进行代码修正

### 如果下载不工作
1. 手动测试一次完整下载流程
2. 记录每步的确切操作
3. 特别注意右键菜单的选项文本

## ❓ 关键观察点

- [ ] 页面右上角显示真实用户名还是"guest"？
- [ ] Cloud Docs按钮在哪个位置？可点击吗？
- [ ] 点击后跳转到什么URL？
- [ ] 能看到文档列表吗？文档长什么样？
- [ ] 右键菜单有哪些选项？"下载"的确切文本是什么？

## 📞 问题反馈模板

请按以下格式反馈观察结果：

```
🔍 观察结果:
页面状态: [正常/异常] - [具体描述]
用户信息: [显示xxx/显示guest/不显示]  
Cloud Docs: [可见可点击/可见不可点击/不可见]
导航结果: [成功跳转到xxx/失败超时/其他]
文档列表: [看到N个文档/看不到文档/页面空白]
下载测试: [成功/失败] - [具体现象]

💡 发现的问题:
[详细描述遇到的问题]

🎯 需要调整的地方:
[建议修改的代码位置或逻辑]
```

祝你调试顺利！🍀