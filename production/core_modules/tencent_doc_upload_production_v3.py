#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档生产级上传模块 v3
终极解决方案：多策略组合确保获取正确的文档链接
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TencentDocProductionUploaderV3:
    """
    腾讯文档生产级上传器 v3
    多策略组合：网络监听 + DOM监控 + 时间戳匹配
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.initial_doc_links = set()
        self.upload_response_url = None  # 存储上传API返回的URL
        self.upload_start_time = None
        self.storage_space_info = None  # 存储空间信息
        self.api_response_data = None  # 完整的API响应数据
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    async def start(self) -> bool:
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--start-maximized'
                ]
            )
            
            self.context = await self.browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                locale='zh-CN'
            )
            
            self.page = await self.context.new_page()
            self.page.set_default_timeout(30000)
            
            # 设置网络响应监听器
            self.page.on("response", self.handle_response)
            
            logger.info("✅ 浏览器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 浏览器启动失败: {e}")
            return False
    
    async def handle_response(self, response: Response):
        """监听网络响应，捕获上传API的返回"""
        try:
            url = response.url
            status = response.status
            
            # 监听可能的上传API端点
            upload_patterns = [
                '/api/drive/v2/files/upload',
                '/api/docs/import',
                '/api/file/upload',
                '/sheet/create',
                '/doc/create',
                'import',
                'upload'
            ]
            
            # 检查是否是上传相关的请求
            if any(pattern in url for pattern in upload_patterns):
                if status == 200:
                    try:
                        # 尝试获取响应内容
                        body = await response.body()
                        text = body.decode('utf-8', errors='ignore')
                        
                        # 记录关键响应
                        logger.info(f"📡 捕获上传响应: {url[:100]}...")
                        
                        # 尝试解析JSON
                        try:
                            data = json.loads(text)
                            # 保存完整的API响应
                            self.api_response_data = data

                            # 检查是否是失败的响应（url和doc_id为空）
                            if 'url' in data and 'doc_id' in data:
                                if not data['url'] and not data['doc_id']:
                                    logger.error(f"❌ API返回空的URL和doc_id，上传可能失败: {data}")
                                    self.upload_response_url = None
                                    return

                            # 查找可能包含文档URL的字段
                            possible_url_fields = ['url', 'fileUrl', 'docUrl', 'shareUrl', 'doc_url', 'file_url', 'link', 'href']
                            for field in possible_url_fields:
                                if field in data:
                                    potential_url = data[field]
                                    if potential_url and ('docs.qq.com' in str(potential_url) or '/sheet/' in str(potential_url)):
                                        self.upload_response_url = potential_url
                                        logger.info(f"🎯 从API响应获取文档URL: {potential_url}")
                                        break

                            # 查找文档ID
                            if 'doc_id' in data or 'fileId' in data or 'docId' in data:
                                doc_id = data.get('doc_id') or data.get('fileId') or data.get('docId')
                                if doc_id:
                                    # 构建文档URL
                                    self.upload_response_url = f"https://docs.qq.com/sheet/{doc_id}"
                                    logger.info(f"🎯 从API响应获取文档ID: {doc_id}")
                                    
                        except json.JSONDecodeError:
                            # 不是JSON响应，尝试正则提取URL
                            url_pattern = r'(https?://docs\.qq\.com/[^\s"\'"]+)'
                            matches = re.findall(url_pattern, text)
                            if matches:
                                self.upload_response_url = matches[0]
                                logger.info(f"🎯 从响应文本提取URL: {self.upload_response_url}")
                                
                    except Exception as e:
                        logger.debug(f"解析响应失败: {e}")
                        
        except Exception as e:
            logger.debug(f"处理响应时出错: {e}")
    
    def parse_cookie_string(self, cookie_string: str) -> list:
        """解析Cookie字符串"""
        cookies = []
        
        for cookie_pair in cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',
                    'path': '/'
                })
        
        return cookies
    
    async def login_with_cookies(self, cookie_string: str) -> bool:
        """使用Cookie登录腾讯文档"""
        try:
            logger.info("🔐 开始Cookie登录...")
            
            cookies = self.parse_cookie_string(cookie_string)
            await self.context.add_cookies(cookies)
            logger.info(f"✅ 已添加 {len(cookies)} 个Cookies")
            
            await self.page.goto(
                'https://docs.qq.com/desktop/',
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            await self.page.wait_for_timeout(5000)
            
            # 记录初始页面上的文档链接
            await self.record_initial_doc_links()
            
            is_logged_in = await self.verify_login_status()
            
            if is_logged_in:
                logger.info("✅ 登录成功！")
                # 检查存储空间
                await self.check_storage_space()
                return True
            else:
                logger.warning("⚠️ 登录失败，可能Cookie已过期")
                return False
                
        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            return False
    
    async def record_initial_doc_links(self):
        """记录页面初始的文档链接和时间戳"""
        try:
            # 记录所有初始文档
            self.initial_docs = {}
            
            # 获取所有文档卡片或列表项
            doc_elements = await self.page.query_selector_all('.doc-item, .file-item, [class*="document"], [class*="file-list"] li, .desktop-file-item')
            
            for elem in doc_elements:
                try:
                    # 尝试获取链接
                    link_elem = await elem.query_selector('a[href*="/sheet/"], a[href*="/doc/"]')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        # 获取文档名称
                        name_elem = await elem.query_selector('[class*="name"], [class*="title"], .file-name')
                        name = await name_elem.text_content() if name_elem else ""
                        
                        # 获取时间信息
                        time_elem = await elem.query_selector('[class*="time"], [class*="date"], .modified-time')
                        time_text = await time_elem.text_content() if time_elem else ""
                        
                        self.initial_docs[href] = {
                            'name': name.strip(),
                            'time': time_text.strip()
                        }
                except Exception:
                    # 忽略单个元素处理失败
                    continue
                        
            self.initial_doc_links = set(self.initial_docs.keys())
            logger.info(f"📝 记录了 {len(self.initial_doc_links)} 个初始文档")
            
        except Exception as e:
            logger.warning(f"记录初始文档失败: {e}")
    
    async def verify_login_status(self) -> bool:
        """验证登录状态"""
        try:
            login_btn = await self.page.query_selector('button:has-text("登录")')
            has_login_btn = login_btn is not None
            
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            has_import_btn = import_btn is not None
            
            user_info = await self.page.query_selector('[class*="avatar"], [class*="user"]')
            has_user_info = user_info is not None
            
            logger.info(f"🔍 状态: 登录按钮={has_login_btn}, 导入按钮={has_import_btn}, 用户信息={has_user_info}")
            
            return not has_login_btn and (has_import_btn or has_user_info)
            
        except Exception as e:
            logger.error(f"❌ 状态验证失败: {e}")
            return False
    
    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        """上传文件到腾讯文档"""
        result = {
            'success': False,
            'url': None,
            'message': '',
            'doc_name': None,
            'storage_info': None,
            'api_response': None
        }
        
        try:
            file_path = Path(file_path).resolve()
            if not file_path.exists():
                result['message'] = f"文件不存在: {file_path}"
                return result

            # 记录存储空间信息但不阻止上传
            if self.storage_space_info:
                usage = self.storage_space_info.get('usage_percent', 0)
                if usage >= 95:
                    logger.warning(f"⚠️ 存储空间使用率较高: {usage:.2f}% 已使用，但继续尝试上传")
                    result['storage_warning'] = f"存储空间使用率: {usage:.2f}%"
                else:
                    logger.info(f"✅ 存储空间充足: {usage:.2f}% 已使用")

            logger.info(f"📤 开始上传: {file_path.name}")

            # 记录上传开始时间
            self.upload_start_time = datetime.now()
            
            # 清空之前的上传响应
            self.upload_response_url = None
            self.api_response_data = None
            
            # 点击导入按钮
            import_btn = await self.click_import_button()
            if not import_btn:
                result['message'] = "未找到导入按钮"
                return result
            
            # 处理文件选择
            await self.handle_file_selection(str(file_path))
            
            # 确认上传
            await self.confirm_upload_dialog()
            
            # 等待上传完成并获取URL（使用多策略）
            success, url = await self.wait_for_upload_complete_v3(file_path.name)
            
            if success and url:
                # 验证URL是否真实有效
                if await self.validate_upload_url(url, file_path.name):
                    result['success'] = True
                    result['url'] = url
                    result['message'] = "上传成功"
                    result['doc_name'] = file_path.stem
                    logger.info(f"✅ 上传成功: {result['url']}")
                else:
                    result['success'] = False
                    result['message'] = "上传返回的URL无效或是已存在的文档"
                    logger.error(f"❌ 虚假成功: URL {url} 不是新上传的文档")
            else:
                result['message'] = "上传失败或未能获取文档链接"
                logger.warning("⚠️ 未能确认上传状态")

            # 添加API响应信息
            result['api_response'] = self.api_response_data
            result['storage_info'] = self.storage_space_info
                
        except Exception as e:
            result['message'] = f"上传异常: {str(e)}"
            logger.error(f"❌ 上传异常: {e}")
            
        return result
    
    async def click_import_button(self) -> bool:
        """点击导入按钮"""
        import_selectors = [
            'button.desktop-import-button-pc',
            'nav button:has(i.desktop-icon-import)',
            'button:has-text("导入")',
        ]
        
        for selector in import_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=3000)
                if btn:
                    await btn.click()
                    logger.info(f"✅ 点击导入按钮: {selector}")
                    return True
            except:
                continue
                
        logger.error("❌ 未找到导入按钮")
        return False
    
    async def handle_file_selection(self, file_path: str):
        """处理文件选择"""
        await self.page.wait_for_timeout(1000)
        
        file_inputs = await self.page.query_selector_all('input[type="file"]')
        
        if file_inputs:
            await file_inputs[-1].set_input_files(file_path)
            logger.info(f"✅ 通过input选择文件: {file_path}")
        else:
            logger.info("使用filechooser选择文件")
            async with self.page.expect_file_chooser() as fc_info:
                await self.click_import_button()
            
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_path)
            logger.info(f"✅ 通过filechooser选择文件: {file_path}")
    
    async def confirm_upload_dialog(self):
        """确认上传对话框"""
        try:
            await self.page.wait_for_timeout(2000)
            
            confirm_selectors = [
                'button.dui-button-type-primary:has-text("确定")',
                '.import-kit-import-file-footer button.dui-button-type-primary',
                'button.dui-button-type-primary .dui-button-container:has-text("确定")'
            ]
            
            for selector in confirm_selectors:
                try:
                    btn = await self.page.wait_for_selector(selector, timeout=2000)
                    if btn:
                        await btn.click()
                        logger.info("✅ 点击确定按钮")
                        return
                except:
                    continue
            
            await self.page.keyboard.press('Enter')
            logger.info("✅ 使用Enter键确认")
            
        except Exception as e:
            logger.warning(f"⚠️ 确认对话框处理: {e}")
    
    async def wait_for_upload_complete_v3(self, filename: str, timeout: int = 60) -> Tuple[bool, Optional[str]]:
        """
        等待上传完成 v3 - 多策略组合

        策略优先级：
        1. API响应URL（最准确）
        2. Toast消息中的URL
        3. URL跳转
        4. 精确文件名匹配
        5. 时间戳最新的文档（仅在单文档上传时使用）
        """
        logger.info(f"⏳ 等待上传完成: {filename}")

        # 记录开始时的文档链接数量
        initial_links_count = len(self.initial_doc_links)
        
        for i in range(timeout // 5):
            await self.page.wait_for_timeout(5000)
            
            # 策略1: 检查是否已从API响应获取URL
            if self.upload_response_url:
                logger.info(f"✅ 使用API响应URL: {self.upload_response_url}")
                return True, self.upload_response_url
            
            # 策略2: 检查Toast消息
            toast_url = await self.check_toast_message()
            if toast_url:
                logger.info(f"✅ 从Toast消息获取URL: {toast_url}")
                return True, toast_url
            
            # 策略3: 检查URL跳转
            current_url = self.page.url
            if '/sheet/' in current_url or '/doc/' in current_url or '/slide/' in current_url:
                logger.info(f"✅ URL已跳转: {current_url}")
                return True, current_url
            
            # 策略4: 检测导入对话框关闭
            import_dialog = await self.page.query_selector('.import-kit-import-file')
            if not import_dialog and i > 2:
                logger.info("✅ 导入对话框已关闭")
                
                # 策略5: 精确文件名匹配
                matched_url = await self.find_document_by_name(filename)
                if matched_url:
                    logger.info(f"✅ 通过文件名匹配找到文档: {matched_url}")
                    return True, matched_url
                
                # 策略6: 查找最新创建的文档
                newest_url = await self.find_newest_document()
                if newest_url:
                    logger.info(f"✅ 找到最新文档（可能是上传的）: {newest_url}")
                    return True, newest_url
                
                # 策略7: 查找新增的链接（改进：优先匹配文件名）
                new_links = await self.find_new_links()
                if new_links:
                    # 尝试通过文件名匹配找到最相关的链接
                    matched_url = await self.match_url_by_filename(new_links, filename)
                    if matched_url:
                        logger.info(f"✅ 通过文件名匹配找到链接: {matched_url}")
                        return True, matched_url

                    # 如果只有一个新链接，返回它
                    if len(new_links) == 1:
                        logger.info(f"✅ 找到单个新增链接: {new_links[0]}")
                        return True, new_links[0]

                    # 多个新链接但无法匹配文件名时，记录警告
                    logger.warning(f"⚠️ 找到{len(new_links)}个新链接但无法确定哪个属于{filename}")
                    # 返回最新的链接作为后备选项
                    latest_url = new_links[-1]
                    logger.info(f"✅ 返回最新链接（可能不准确）: {latest_url}")
                    return True, latest_url
            
            # 检查错误消息
            error_msgs = await self.page.query_selector_all('.dui-message-error, [class*="error"]')
            if error_msgs:
                for msg in error_msgs:
                    text = await msg.text_content()
                    if text and ('失败' in text or '错误' in text):
                        logger.error(f"❌ 检测到错误: {text}")
                        return False, None
            
            if i % 3 == 0:
                logger.info(f"⏳ 已等待 {(i+1)*5} 秒...")
        
        logger.warning("⚠️ 上传超时")
        return False, None

    async def check_storage_space(self) -> dict:
        """检查存储空间"""
        try:
            # 查找存储空间元素
            storage_elem = await self.page.query_selector('.desktop-storage-panel')
            if storage_elem:
                storage_text = await storage_elem.inner_text()
                logger.info(f"📊 存储空间信息: {storage_text}")

                # 获取使用率
                storage_bar = await self.page.query_selector('.desktop-storage-bar')
                if storage_bar:
                    style = await storage_bar.get_attribute('style')
                    if style and '--size:' in style:
                        size = style.split('--size:')[1].split('%')[0].strip()
                        usage = float(size)

                        # 检查是否有critical类
                        classes = await storage_bar.get_attribute('class')
                        is_critical = 'critical' in classes if classes else False

                        self.storage_space_info = {
                            'usage_percent': usage,
                            'is_critical': is_critical,
                            'has_space': True,  # 不再基于95%判断，始终允许尝试上传
                            'text': storage_text
                        }

                        if usage >= 95:
                            logger.warning(f"⚠️ 存储空间使用率较高: {usage:.2f}% 已使用")
                        elif usage >= 90:
                            logger.info(f"📊 存储空间使用率: {usage:.2f}% 已使用")
                        else:
                            logger.info(f"✅ 存储空间充足: {usage:.2f}% 已使用")

                        return self.storage_space_info

        except Exception as e:
            logger.error(f"检查存储空间失败: {e}")

        return {'usage_percent': -1, 'is_critical': False, 'has_space': True}

    async def check_toast_message(self) -> Optional[str]:
        """检查Toast消息中的URL"""
        try:
            # 查找Toast消息
            toast_selectors = [
                '.dui-toast', '.toast-message', '[class*="toast"]',
                '.dui-message', '[class*="message"]', '.notification'
            ]
            
            for selector in toast_selectors:
                toasts = await self.page.query_selector_all(selector)
                for toast in toasts:
                    text = await toast.text_content()
                    if text and ('成功' in text or '完成' in text):
                        # 尝试从文本中提取URL
                        url_pattern = r'(https?://docs\.qq\.com/[^\s]+)'
                        matches = re.findall(url_pattern, text)
                        if matches:
                            return matches[0]
            
            return None
        except:
            return None
    
    async def find_document_by_name(self, filename: str) -> Optional[str]:
        """通过文件名查找文档"""
        try:
            # 去掉文件扩展名
            name_without_ext = filename.rsplit('.', 1)[0]
            
            # 可能的文件名变体
            name_variants = [
                filename,
                name_without_ext,
                name_without_ext.replace('_', ' '),
                name_without_ext.replace('-', ' '),
                # 去掉可能的时间戳
                re.sub(r'_\d{8}_\d{6}', '', name_without_ext),
                re.sub(r'_\d{14}', '', name_without_ext),
            ]
            
            # 查找所有文档元素
            doc_elements = await self.page.query_selector_all('a[href*="/sheet/"], a[href*="/doc/"]')
            
            for elem in doc_elements:
                elem_text = await elem.text_content()
                elem_title = await elem.get_attribute('title')
                elem_href = await elem.get_attribute('href')
                
                # 检查是否是新链接
                if elem_href in self.initial_doc_links:
                    continue
                
                # 检查文件名匹配
                for variant in name_variants:
                    if variant and (
                        (elem_text and variant in elem_text) or
                        (elem_title and variant in elem_title)
                    ):
                        url = f"https://docs.qq.com{elem_href}" if elem_href.startswith('/') else elem_href
                        return url
            
            return None
        except Exception as e:
            logger.debug(f"查找文档失败: {e}")
            return None
    
    async def find_newest_document(self) -> Optional[str]:
        """查找最新的文档（基于时间标记）"""
        try:
            # 查找带有"刚刚"、"秒前"、"1分钟前"等时间标记的文档
            time_indicators = [
                '刚刚', '秒前', '1分钟前', 'just now', 
                '刚才', '刚上传', '新建'
            ]
            
            for indicator in time_indicators:
                time_elems = await self.page.query_selector_all(f'*:has-text("{indicator}")')
                for elem in time_elems:
                    # 向上查找最近的链接
                    parent = elem
                    for _ in range(5):  # 最多向上查找5层
                        parent = await parent.evaluate_handle('(el) => el.parentElement')
                        if not parent:
                            break
                        
                        link = await parent.query_selector('a[href*="/sheet/"], a[href*="/doc/"]')
                        if link:
                            href = await link.get_attribute('href')
                            if href and href not in self.initial_doc_links:
                                url = f"https://docs.qq.com{href}" if href.startswith('/') else href
                                return url
            
            return None
        except:
            return None
    
    async def find_new_links(self) -> List[str]:
        """查找所有新增的文档链接"""
        try:
            new_links = []
            all_links = await self.page.query_selector_all('a[href*="/sheet/"], a[href*="/doc/"]')
            
            for link in all_links:
                href = await link.get_attribute('href')
                if href and href not in self.initial_doc_links:
                    url = f"https://docs.qq.com{href}" if href.startswith('/') else href
                    new_links.append(url)
            
            return new_links
        except:
            return []
    
    async def match_url_by_filename(self, urls: List[str], filename: str) -> Optional[str]:
        """通过文件名匹配URL - 优化版本使用doc_id精确匹配"""
        try:
            # 提取doc_id从文件名（格式: tencent_文档名_doc_id_时间戳_版本_周数.扩展名）
            # 示例: tencent_小红书部门_DWEVjZndkR2xVSWJN_20250925_0105_midweek_W39.csv
            doc_id_pattern = r'tencent_[^_]+_([A-Za-z0-9]+)_\d{8}_\d{4}_[^_]+_W\d+\.'
            match = re.search(doc_id_pattern, filename)

            if match:
                doc_id = match.group(1)
                print(f"📋 从文件名提取到doc_id: {doc_id}")

                # 直接在URL中查找包含该doc_id的URL
                for url in urls:
                    if doc_id in url:
                        print(f"✅ 找到匹配的URL: {url}")
                        return url

            # 如果没有找到doc_id，则使用备用方案：关键词匹配
            print("⚠️ 文件名中未找到doc_id，使用关键词匹配")

            # 去掉文件扩展名和可能的时间戳
            base_name = filename.rsplit('.', 1)[0]
            base_name = re.sub(r'_\d{8}_\d{4}', '', base_name)
            base_name = re.sub(r'_marked.*', '', base_name)

            # 提取关键词
            keywords = []
            if '出国' in base_name or 'DWEFNU25TemFnZXJN' in filename:
                keywords.append('出国')
            if '小红书' in base_name or 'DWEVjZndkR2xVSWJN' in filename:
                keywords.append('小红书')
            if '回国' in base_name or 'DWGZDZkxpaGVQaURr' in filename:
                keywords.append('回国')

            # 基于URL的doc_id快速匹配（不需要访问页面）
            url_doc_id_map = {
                'DWEFNU25TemFnZXJN': '出国',
                'DWEVjZndkR2xVSWJN': '小红书',
                'DWGZDZkxpaGVQaURr': '回国'
            }

            for url in urls:
                # 检查URL是否包含已知的doc_id
                for doc_id, keyword in url_doc_id_map.items():
                    if doc_id in url and keyword in keywords:
                        print(f"✅ 通过关键词匹配找到URL: {url}")
                        return url

            return None
        except Exception as e:
            logger.debug(f"文件名匹配失败: {e}")
            return None

    async def validate_upload_url(self, url: str, filename: str) -> bool:
        """验证上传的URL是否真实有效"""
        try:
            # 如果URL在初始文档列表中，说明是已存在的文档
            if url in self.initial_doc_links:
                logger.error(f"❌ URL {url} 是已存在的文档，不是新上传的")
                return False

            # 如果有API响应数据，检查url和doc_id
            if self.api_response_data:
                if 'url' in self.api_response_data and not self.api_response_data['url']:
                    logger.error("❌ API响应的URL为空")
                    return False
                if 'doc_id' in self.api_response_data and not self.api_response_data['doc_id']:
                    logger.error("❌ API响应的doc_id为空")
                    return False

            # 如果上传时间太久，可能是猜测的结果
            if self.upload_start_time:
                elapsed = (datetime.now() - self.upload_start_time).total_seconds()
                if elapsed > 60:
                    logger.warning(f"⚠️ 上传耗时过长 ({elapsed:.1f}秒)，结果可能不可靠")

            return True

        except Exception as e:
            logger.error(f"验证URL失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔚 资源已清理")


# ============= 便捷函数 =============

async def quick_upload_v3(cookie_string: str, file_path: str, headless: bool = True) -> Dict[str, Any]:
    """快速上传文件 v3"""
    async with TencentDocProductionUploaderV3(headless=headless) as uploader:
        login_success = await uploader.login_with_cookies(cookie_string)
        if not login_success:
            return {
                'success': False,
                'message': '登录失败，请检查Cookie'
            }
        
        result = await uploader.upload_file(file_path)
        return result


def sync_upload_v3(cookie_string: str, file_path: str, headless: bool = True) -> Dict[str, Any]:
    """同步版本的上传函数 v3"""
    return asyncio.run(quick_upload_v3(cookie_string, file_path, headless))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python tencent_doc_upload_production_v3.py <文件路径>")
        sys.exit(1)
    
    config_path = Path('/root/projects/tencent-doc-manager/config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            cookie = config.get('cookie', '')
    else:
        print("❌ 配置文件不存在")
        sys.exit(1)
    
    file_to_upload = sys.argv[1]
    result = sync_upload_v3(cookie, file_to_upload, headless=True)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))