#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应UI处理器 - 应对腾讯文档页面结构变化
智能选择器更新和UI变化检测系统
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib
import re

logger = logging.getLogger(__name__)

@dataclass
class UIElement:
    """UI元素定义"""
    name: str
    selectors: List[str]
    fallback_selectors: List[str]
    element_type: str  # button, menu, input, etc.
    confidence_score: float
    last_working_time: datetime
    usage_count: int

@dataclass
class UIChangeDetection:
    """UI变化检测结果"""
    changed: bool
    change_type: str  # selector, structure, content
    affected_elements: List[str]
    confidence: float
    detected_at: datetime
    page_snapshot: Optional[str] = None

class AdaptiveUIHandler:
    """自适应UI处理器"""
    
    def __init__(self, config_dir: str = None):
        """初始化自适应UI处理器"""
        self.config_dir = config_dir or "/root/projects/tencent-doc-manager/config"
        self.ui_config_file = Path(self.config_dir) / "adaptive_ui_config.json"
        self.ui_history_file = Path(self.config_dir) / "ui_change_history.json"
        
        # UI元素定义（基于当前工作版本）
        self.ui_elements = {
            "menu_button": UIElement(
                name="menu_button",
                selectors=[
                    '.titlebar-icon.titlebar-icon-more',
                    'button[class*="menu"]',
                    '[aria-label*="菜单"]',
                    '.toolbar-more-btn',
                    'button[title*="更多"]'
                ],
                fallback_selectors=[
                    'button:has-text("⋯")',
                    'button:has-text("更多")',
                    '[data-testid*="menu"]',
                    '.menu-trigger',
                    'button[role="button"]:has-text("菜单")'
                ],
                element_type="button",
                confidence_score=0.9,
                last_working_time=datetime.now(),
                usage_count=0
            ),
            "export_submenu": UIElement(
                name="export_submenu",
                selectors=[
                    'li.dui-menu-item.dui-menu-submenu.mainmenu-submenu-exportAs',
                    'li[class*="export"]',
                    '[aria-label*="导出"]',
                    'li:has-text("导出为")',
                    '.menu-item-export'
                ],
                fallback_selectors=[
                    'li:has-text("导出")',
                    '[data-action="export"]',
                    '.export-option',
                    'li[role="menuitem"]:has-text("导出")',
                    'button:has-text("导出")'
                ],
                element_type="menuitem",
                confidence_score=0.85,
                last_working_time=datetime.now(),
                usage_count=0
            ),
            "csv_option": UIElement(
                name="csv_option",
                selectors=[
                    'li.dui-menu-item.mainmenu-item-export-csv',
                    'li:has-text("CSV")',
                    '[data-export="csv"]',
                    '.export-csv',
                    'button:has-text("CSV")'
                ],
                fallback_selectors=[
                    'li:contains("CSV")',
                    '[data-format="csv"]',
                    'button:contains("csv")',
                    'li[role="menuitem"]:has-text("CSV")',
                    '.csv-export-option'
                ],
                element_type="menuitem",
                confidence_score=0.9,
                last_working_time=datetime.now(),
                usage_count=0
            ),
            "excel_option": UIElement(
                name="excel_option",
                selectors=[
                    'li.dui-menu-item.mainmenu-item-export-local',
                    'li:has-text("Excel")',
                    '[data-export="excel"]',
                    '.export-excel',
                    'button:has-text("Excel")'
                ],
                fallback_selectors=[
                    'li:contains("Excel")',
                    'li:contains("xlsx")',
                    '[data-format="excel"]',
                    'button:contains("excel")',
                    'li[role="menuitem"]:has-text("Excel")'
                ],
                element_type="menuitem",
                confidence_score=0.9,
                last_working_time=datetime.now(),
                usage_count=0
            )
        }
        
        # 页面特征缓存
        self.page_signatures = {}
        self.change_history = []
        self.learning_enabled = True
        
        # 智能选择器生成器
        self.selector_generators = [
            self._generate_class_selectors,
            self._generate_text_selectors,
            self._generate_attribute_selectors,
            self._generate_structural_selectors,
            self._generate_ai_selectors
        ]
    
    async def detect_ui_changes(self, page) -> UIChangeDetection:
        """检测UI变化"""
        try:
            logger.info("🔍 开始检测UI变化...")
            
            # 获取当前页面特征
            current_signature = await self._get_page_signature(page)
            page_url = page.url
            
            # 比较页面特征
            if page_url in self.page_signatures:
                previous_signature = self.page_signatures[page_url]
                
                # 计算变化程度
                changes = await self._compare_page_signatures(
                    previous_signature, current_signature
                )
                
                if changes["change_score"] > 0.3:  # 30%以上变化认为是显著变化
                    change_detection = UIChangeDetection(
                        changed=True,
                        change_type=changes["primary_change_type"],
                        affected_elements=changes["affected_elements"],
                        confidence=changes["change_score"],
                        detected_at=datetime.now()
                    )
                    
                    # 保存页面快照
                    if changes["change_score"] > 0.5:  # 重大变化时保存快照
                        snapshot = await page.content()
                        change_detection.page_snapshot = snapshot[:5000]  # 前5KB
                    
                    logger.warning(f"⚠️ 检测到UI变化: {change_detection.change_type}, 置信度: {change_detection.confidence:.2f}")
                    
                    # 记录变化历史
                    await self._log_ui_change(change_detection)
                    
                    return change_detection
            
            # 更新页面特征缓存
            self.page_signatures[page_url] = current_signature
            
            return UIChangeDetection(
                changed=False,
                change_type="none",
                affected_elements=[],
                confidence=0.0,
                detected_at=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"❌ UI变化检测失败: {e}")
            return UIChangeDetection(
                changed=False,
                change_type="error",
                affected_elements=[],
                confidence=0.0,
                detected_at=datetime.now()
            )
    
    async def _get_page_signature(self, page) -> Dict[str, Any]:
        """获取页面特征签名"""
        try:
            # 收集页面结构信息
            signature = await page.evaluate('''() => {
                const getElementSignature = (element) => {
                    return {
                        tagName: element.tagName,
                        className: element.className || '',
                        id: element.id || '',
                        textContent: (element.textContent || '').substring(0, 100),
                        attributes: Array.from(element.attributes).map(attr => ({
                            name: attr.name,
                            value: attr.value
                        }))
                    };
                };
                
                // 收集关键元素
                const keySelectors = [
                    'button', 'li[role="menuitem"]', '[class*="menu"]',
                    '[class*="export"]', '[class*="toolbar"]', 
                    '[aria-label]', '[data-testid]'
                ];
                
                const signature = {
                    url: window.location.href,
                    title: document.title,
                    bodyClass: document.body.className,
                    keyElements: [],
                    structureHash: '',
                    timestamp: new Date().toISOString()
                };
                
                // 收集关键元素信息
                keySelectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach((element, index) => {
                            if (index < 20) {  // 限制数量
                                signature.keyElements.push({
                                    selector: selector,
                                    index: index,
                                    ...getElementSignature(element)
                                });
                            }
                        });
                    } catch (e) {
                        // 忽略选择器错误
                    }
                });
                
                // 生成结构哈希
                const structure = signature.keyElements.map(el => 
                    el.tagName + el.className + el.textContent
                ).join('|');
                
                signature.structureHash = btoa(structure).substring(0, 32);
                
                return signature;
            }''')
            
            return signature
        
        except Exception as e:
            logger.error(f"获取页面特征失败: {e}")
            return {
                "url": "",
                "title": "",
                "keyElements": [],
                "structureHash": "",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _compare_page_signatures(self, old_sig: Dict, new_sig: Dict) -> Dict[str, Any]:
        """比较页面特征"""
        try:
            changes = {
                "change_score": 0.0,
                "primary_change_type": "none",
                "affected_elements": [],
                "details": {}
            }
            
            # 结构哈希比较
            if old_sig.get("structureHash") != new_sig.get("structureHash"):
                changes["change_score"] += 0.5
                changes["primary_change_type"] = "structure"
            
            # 关键元素比较
            old_elements = {el.get("className", "") + el.get("textContent", ""): el 
                          for el in old_sig.get("keyElements", [])}
            new_elements = {el.get("className", "") + el.get("textContent", ""): el 
                          for el in new_sig.get("keyElements", [])}
            
            # 计算元素变化
            removed_elements = set(old_elements.keys()) - set(new_elements.keys())
            added_elements = set(new_elements.keys()) - set(old_elements.keys())
            
            element_change_score = (len(removed_elements) + len(added_elements)) / max(len(old_elements), 1)
            changes["change_score"] += element_change_score * 0.3
            
            if element_change_score > 0.2:
                changes["primary_change_type"] = "elements"
                changes["affected_elements"].extend(list(removed_elements)[:5])
                changes["affected_elements"].extend(list(added_elements)[:5])
            
            # 页面标题比较
            if old_sig.get("title") != new_sig.get("title"):
                changes["change_score"] += 0.1
            
            # Body class比较
            if old_sig.get("bodyClass") != new_sig.get("bodyClass"):
                changes["change_score"] += 0.1
            
            changes["details"] = {
                "removed_elements": list(removed_elements)[:10],
                "added_elements": list(added_elements)[:10],
                "title_changed": old_sig.get("title") != new_sig.get("title"),
                "structure_hash_changed": old_sig.get("structureHash") != new_sig.get("structureHash")
            }
            
            return changes
        
        except Exception as e:
            logger.error(f"页面特征比较失败: {e}")
            return {
                "change_score": 0.0,
                "primary_change_type": "error",
                "affected_elements": [],
                "details": {"error": str(e)}
            }
    
    async def adapt_to_ui_changes(self, page, change_detection: UIChangeDetection) -> bool:
        """适应UI变化"""
        try:
            logger.info("🔧 开始适应UI变化...")
            
            if not change_detection.changed:
                return True
            
            # 根据变化类型采取不同策略
            if change_detection.change_type == "structure":
                success = await self._adapt_structure_changes(page, change_detection)
            elif change_detection.change_type == "elements":
                success = await self._adapt_element_changes(page, change_detection)
            elif change_detection.change_type == "selectors":
                success = await self._adapt_selector_changes(page, change_detection)
            else:
                # 通用适应策略
                success = await self._adapt_generic_changes(page, change_detection)
            
            if success:
                logger.info("✅ UI适应成功")
                # 更新UI配置
                await self._update_ui_config()
                return True
            else:
                logger.warning("⚠️ UI适应失败，可能需要人工干预")
                return False
        
        except Exception as e:
            logger.error(f"❌ UI适应过程异常: {e}")
            return False
    
    async def _adapt_structure_changes(self, page, change_detection: UIChangeDetection) -> bool:
        """适应结构变化"""
        try:
            logger.info("🏗️ 适应页面结构变化...")
            
            # 重新学习页面结构
            for element_name, element in self.ui_elements.items():
                new_selectors = await self._discover_element_selectors(page, element)
                
                if new_selectors:
                    logger.info(f"🔍 为元素 {element_name} 发现新选择器: {new_selectors[:2]}")
                    
                    # 更新选择器列表
                    element.selectors = new_selectors + element.selectors
                    element.selectors = element.selectors[:10]  # 限制数量
                    element.confidence_score = 0.7  # 降低置信度，需要验证
                    element.last_working_time = datetime.now()
            
            return True
        
        except Exception as e:
            logger.error(f"结构变化适应失败: {e}")
            return False
    
    async def _adapt_element_changes(self, page, change_detection: UIChangeDetection) -> bool:
        """适应元素变化"""
        try:
            logger.info("🎯 适应元素变化...")
            
            # 对每个UI元素进行重新发现
            adaptation_success = True
            
            for element_name, element in self.ui_elements.items():
                # 测试当前选择器是否仍然有效
                working_selectors = await self._test_selectors(page, element.selectors)
                
                if not working_selectors:
                    # 当前选择器都无效，尝试重新发现
                    logger.warning(f"⚠️ 元素 {element_name} 的选择器全部失效，开始重新发现...")
                    
                    new_selectors = await self._discover_element_selectors(page, element)
                    
                    if new_selectors:
                        element.selectors = new_selectors
                        element.confidence_score = 0.6  # 新发现的选择器置信度较低
                        logger.info(f"✅ 元素 {element_name} 重新发现成功")
                    else:
                        logger.error(f"❌ 元素 {element_name} 重新发现失败")
                        adaptation_success = False
                else:
                    # 有些选择器仍然有效，重新排序
                    element.selectors = working_selectors + [s for s in element.selectors if s not in working_selectors]
                    element.confidence_score = min(0.9, element.confidence_score + 0.1)
                    logger.info(f"✅ 元素 {element_name} 选择器更新成功")
            
            return adaptation_success
        
        except Exception as e:
            logger.error(f"元素变化适应失败: {e}")
            return False
    
    async def _adapt_selector_changes(self, page, change_detection: UIChangeDetection) -> bool:
        """适应选择器变化"""
        try:
            logger.info("🎛️ 适应选择器变化...")
            
            # 这种情况下主要是CSS类名或属性的变化
            for element_name, element in self.ui_elements.items():
                # 生成新的智能选择器
                smart_selectors = await self._generate_smart_selectors(page, element)
                
                if smart_selectors:
                    # 将新选择器插入到列表前部
                    element.selectors = smart_selectors + element.selectors
                    element.selectors = list(dict.fromkeys(element.selectors))  # 去重
                    element.selectors = element.selectors[:15]  # 限制数量
                    
                    logger.info(f"🧠 为元素 {element_name} 生成智能选择器: {smart_selectors[:2]}")
            
            return True
        
        except Exception as e:
            logger.error(f"选择器变化适应失败: {e}")
            return False
    
    async def _adapt_generic_changes(self, page, change_detection: UIChangeDetection) -> bool:
        """通用适应策略"""
        try:
            logger.info("🔄 执行通用适应策略...")
            
            # 执行全面的元素重新发现
            success_count = 0
            
            for element_name, element in self.ui_elements.items():
                try:
                    # 测试现有选择器
                    working_count = await self._count_working_selectors(page, element.selectors)
                    
                    # 如果工作选择器少于50%，重新发现
                    if working_count / len(element.selectors) < 0.5:
                        new_selectors = await self._discover_element_selectors(page, element)
                        
                        if new_selectors:
                            # 合并新旧选择器
                            all_selectors = new_selectors + element.selectors + element.fallback_selectors
                            # 去重并重新测试
                            unique_selectors = list(dict.fromkeys(all_selectors))
                            working_selectors = await self._test_selectors(page, unique_selectors)
                            
                            if working_selectors:
                                element.selectors = working_selectors[:10]
                                success_count += 1
                
                except Exception as e:
                    logger.warning(f"元素 {element_name} 适应失败: {e}")
                    continue
            
            # 如果至少有一半元素适应成功，认为整体适应成功
            success_rate = success_count / len(self.ui_elements)
            logger.info(f"📊 通用适应成功率: {success_rate:.2f}")
            
            return success_rate >= 0.5
        
        except Exception as e:
            logger.error(f"通用适应策略失败: {e}")
            return False
    
    async def _discover_element_selectors(self, page, element: UIElement) -> List[str]:
        """为元素发现新选择器"""
        try:
            discovered_selectors = []
            
            # 使用不同的发现策略
            for generator in self.selector_generators:
                try:
                    new_selectors = await generator(page, element)
                    discovered_selectors.extend(new_selectors)
                except Exception as e:
                    logger.debug(f"选择器生成器失败: {generator.__name__}, 错误: {e}")
                    continue
            
            # 去重并测试
            unique_selectors = list(dict.fromkeys(discovered_selectors))
            working_selectors = await self._test_selectors(page, unique_selectors)
            
            return working_selectors[:5]  # 返回前5个有效选择器
        
        except Exception as e:
            logger.error(f"元素选择器发现失败: {e}")
            return []
    
    async def _generate_class_selectors(self, page, element: UIElement) -> List[str]:
        """生成基于类名的选择器"""
        try:
            # 基于元素类型和文本内容生成类选择器
            if element.element_type == "button":
                return await page.evaluate('''(elementType) => {
                    const selectors = [];
                    const buttons = document.querySelectorAll('button, [role="button"]');
                    
                    buttons.forEach(btn => {
                        const text = btn.textContent.trim().toLowerCase();
                        if (text.includes('菜单') || text.includes('更多') || text.includes('menu')) {
                            if (btn.className) {
                                selectors.push('.' + btn.className.split(' ').join('.'));
                            }
                        }
                    });
                    
                    return selectors;
                }''', element.element_type)
            
            elif element.element_type == "menuitem":
                return await page.evaluate('''(elementName) => {
                    const selectors = [];
                    const items = document.querySelectorAll('li, [role="menuitem"]');
                    
                    items.forEach(item => {
                        const text = item.textContent.trim().toLowerCase();
                        if (elementName.includes('export') && text.includes('导出')) {
                            if (item.className) {
                                selectors.push('.' + item.className.split(' ').join('.'));
                            }
                        } else if (elementName.includes('csv') && text.includes('csv')) {
                            if (item.className) {
                                selectors.push('.' + item.className.split(' ').join('.'));
                            }
                        } else if (elementName.includes('excel') && (text.includes('excel') || text.includes('xlsx'))) {
                            if (item.className) {
                                selectors.push('.' + item.className.split(' ').join('.'));
                            }
                        }
                    });
                    
                    return selectors;
                }''', element.name)
            
            return []
        
        except Exception as e:
            logger.debug(f"类选择器生成失败: {e}")
            return []
    
    async def _generate_text_selectors(self, page, element: UIElement) -> List[str]:
        """生成基于文本的选择器"""
        try:
            text_patterns = {
                "menu_button": ["菜单", "更多", "⋯", "menu", "more"],
                "export_submenu": ["导出", "导出为", "export"],
                "csv_option": ["CSV", "csv"],
                "excel_option": ["Excel", "xlsx", "excel"]
            }
            
            patterns = text_patterns.get(element.name, [])
            selectors = []
            
            for pattern in patterns:
                selectors.extend([
                    f'*:has-text("{pattern}")',
                    f'button:has-text("{pattern}")',
                    f'li:has-text("{pattern}")',
                    f'[aria-label*="{pattern}"]',
                    f'[title*="{pattern}"]'
                ])
            
            return selectors
        
        except Exception as e:
            logger.debug(f"文本选择器生成失败: {e}")
            return []
    
    async def _generate_attribute_selectors(self, page, element: UIElement) -> List[str]:
        """生成基于属性的选择器"""
        try:
            selectors = []
            
            # 基于元素名称生成属性选择器
            if "export" in element.name:
                selectors.extend([
                    '[data-action="export"]',
                    '[data-testid*="export"]',
                    '[class*="export"]',
                    '[id*="export"]'
                ])
            
            if "menu" in element.name:
                selectors.extend([
                    '[data-testid*="menu"]',
                    '[class*="menu"]',
                    '[role="button"][aria-label*="menu"]'
                ])
            
            if element.name == "csv_option":
                selectors.extend([
                    '[data-format="csv"]',
                    '[data-export="csv"]',
                    '[data-type="csv"]'
                ])
            
            if element.name == "excel_option":
                selectors.extend([
                    '[data-format="excel"]',
                    '[data-format="xlsx"]',
                    '[data-export="excel"]'
                ])
            
            return selectors
        
        except Exception as e:
            logger.debug(f"属性选择器生成失败: {e}")
            return []
    
    async def _generate_structural_selectors(self, page, element: UIElement) -> List[str]:
        """生成基于结构的选择器"""
        try:
            # 基于DOM结构位置生成选择器
            return await page.evaluate('''(elementName) => {
                const selectors = [];
                
                // 查找工具栏区域
                const toolbars = document.querySelectorAll('[class*="toolbar"], [class*="header"], [class*="top"]');
                
                toolbars.forEach(toolbar => {
                    if (elementName.includes('menu')) {
                        // 在工具栏中查找按钮
                        const buttons = toolbar.querySelectorAll('button');
                        buttons.forEach((btn, index) => {
                            if (btn.textContent.includes('菜单') || btn.textContent.includes('更多')) {
                                selectors.push(`[class*="toolbar"] button:nth-child(${index + 1})`);
                            }
                        });
                    }
                });
                
                // 查找菜单容器
                const menus = document.querySelectorAll('[class*="menu"], [role="menu"]');
                menus.forEach(menu => {
                    if (elementName.includes('export')) {
                        const exportItems = menu.querySelectorAll('li, [role="menuitem"]');
                        exportItems.forEach((item, index) => {
                            if (item.textContent.includes('导出')) {
                                selectors.push(`[class*="menu"] > li:nth-child(${index + 1})`);
                            }
                        });
                    }
                });
                
                return selectors;
            }''', element.name)
        
        except Exception as e:
            logger.debug(f"结构选择器生成失败: {e}")
            return []
    
    async def _generate_ai_selectors(self, page, element: UIElement) -> List[str]:
        """使用AI策略生成选择器"""
        try:
            # 基于机器学习或启发式算法生成选择器
            # 这里实现简化版的启发式策略
            
            selectors = []
            
            # 分析页面中的模式
            page_analysis = await page.evaluate('''() => {
                const analysis = {
                    buttonPatterns: [],
                    menuPatterns: [],
                    exportPatterns: []
                };
                
                // 分析按钮模式
                const buttons = document.querySelectorAll('button, [role="button"]');
                buttons.forEach(btn => {
                    if (btn.className && btn.textContent) {
                        analysis.buttonPatterns.push({
                            className: btn.className,
                            text: btn.textContent.trim(),
                            selector: btn.tagName.toLowerCase() + '.' + btn.className.split(' ').join('.')
                        });
                    }
                });
                
                // 分析菜单模式
                const menuItems = document.querySelectorAll('li[role="menuitem"], .menu-item, [class*="menu-item"]');
                menuItems.forEach(item => {
                    if (item.className && item.textContent) {
                        analysis.menuPatterns.push({
                            className: item.className,
                            text: item.textContent.trim(),
                            selector: item.tagName.toLowerCase() + '.' + item.className.split(' ').join('.')
                        });
                    }
                });
                
                return analysis;
            }''')
            
            # 基于分析结果生成智能选择器
            if element.element_type == "button":
                for pattern in page_analysis.get("buttonPatterns", []):
                    text = pattern.get("text", "").lower()
                    if any(keyword in text for keyword in ["菜单", "更多", "menu", "more"]):
                        selectors.append(pattern["selector"])
            
            elif element.element_type == "menuitem":
                for pattern in page_analysis.get("menuPatterns", []):
                    text = pattern.get("text", "").lower()
                    if "export" in element.name and "导出" in text:
                        selectors.append(pattern["selector"])
                    elif "csv" in element.name and "csv" in text:
                        selectors.append(pattern["selector"])
                    elif "excel" in element.name and ("excel" in text or "xlsx" in text):
                        selectors.append(pattern["selector"])
            
            return selectors[:3]  # 返回前3个最相关的
        
        except Exception as e:
            logger.debug(f"AI选择器生成失败: {e}")
            return []
    
    async def _test_selectors(self, page, selectors: List[str]) -> List[str]:
        """测试选择器有效性"""
        working_selectors = []
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        working_selectors.append(selector)
            except Exception:
                continue
        
        return working_selectors
    
    async def _count_working_selectors(self, page, selectors: List[str]) -> int:
        """计算有效选择器数量"""
        working_selectors = await self._test_selectors(page, selectors)
        return len(working_selectors)
    
    async def _generate_smart_selectors(self, page, element: UIElement) -> List[str]:
        """生成智能选择器"""
        try:
            all_selectors = []
            
            # 运行所有生成器
            for generator in self.selector_generators:
                try:
                    new_selectors = await generator(page, element)
                    all_selectors.extend(new_selectors)
                except Exception:
                    continue
            
            # 去重并测试
            unique_selectors = list(dict.fromkeys(all_selectors))
            working_selectors = await self._test_selectors(page, unique_selectors)
            
            return working_selectors[:5]
        
        except Exception as e:
            logger.error(f"智能选择器生成失败: {e}")
            return []
    
    async def find_element_with_adaptation(self, page, element_name: str) -> Optional[Any]:
        """使用适应性策略查找元素"""
        try:
            if element_name not in self.ui_elements:
                logger.warning(f"⚠️ 未知元素: {element_name}")
                return None
            
            element = self.ui_elements[element_name]
            
            # 尝试使用现有选择器
            for selector in element.selectors:
                try:
                    found_element = await page.query_selector(selector)
                    if found_element:
                        is_visible = await found_element.is_visible()
                        if is_visible:
                            # 更新使用统计
                            element.usage_count += 1
                            element.last_working_time = datetime.now()
                            element.confidence_score = min(1.0, element.confidence_score + 0.01)
                            
                            return found_element
                except Exception:
                    continue
            
            # 现有选择器无效，尝试自适应
            logger.info(f"🔄 元素 {element_name} 现有选择器无效，开始自适应...")
            
            # 检测UI变化
            change_detection = await self.detect_ui_changes(page)
            
            if change_detection.changed:
                # 尝试适应变化
                adaptation_success = await self.adapt_to_ui_changes(page, change_detection)
                
                if adaptation_success:
                    # 重新尝试查找
                    for selector in element.selectors:
                        try:
                            found_element = await page.query_selector(selector)
                            if found_element:
                                is_visible = await found_element.is_visible()
                                if is_visible:
                                    return found_element
                        except Exception:
                            continue
            
            # 最后尝试备用选择器
            for selector in element.fallback_selectors:
                try:
                    found_element = await page.query_selector(selector)
                    if found_element:
                        is_visible = await found_element.is_visible()
                        if is_visible:
                            # 将有效的备用选择器提升为主选择器
                            element.selectors.insert(0, selector)
                            return found_element
                except Exception:
                    continue
            
            logger.error(f"❌ 元素 {element_name} 查找失败，所有策略都无效")
            return None
        
        except Exception as e:
            logger.error(f"❌ 自适应元素查找异常: {e}")
            return None
    
    async def _log_ui_change(self, change_detection: UIChangeDetection):
        """记录UI变化"""
        try:
            change_record = {
                "timestamp": change_detection.detected_at.isoformat(),
                "change_type": change_detection.change_type,
                "affected_elements": change_detection.affected_elements,
                "confidence": change_detection.confidence,
                "snapshot_length": len(change_detection.page_snapshot) if change_detection.page_snapshot else 0
            }
            
            self.change_history.append(change_record)
            
            # 保持历史记录不超过100条
            if len(self.change_history) > 100:
                self.change_history = self.change_history[-100:]
            
            # 保存到文件
            await self._save_ui_history()
        
        except Exception as e:
            logger.error(f"❌ UI变化记录失败: {e}")
    
    async def _update_ui_config(self):
        """更新UI配置文件"""
        try:
            config_data = {
                "last_updated": datetime.now().isoformat(),
                "ui_elements": {}
            }
            
            for name, element in self.ui_elements.items():
                config_data["ui_elements"][name] = {
                    "selectors": element.selectors,
                    "fallback_selectors": element.fallback_selectors,
                    "element_type": element.element_type,
                    "confidence_score": element.confidence_score,
                    "last_working_time": element.last_working_time.isoformat(),
                    "usage_count": element.usage_count
                }
            
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.ui_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ UI配置已更新: {self.ui_config_file}")
        
        except Exception as e:
            logger.error(f"❌ UI配置更新失败: {e}")
    
    async def _save_ui_history(self):
        """保存UI变化历史"""
        try:
            history_data = {
                "last_updated": datetime.now().isoformat(),
                "total_changes": len(self.change_history),
                "changes": self.change_history
            }
            
            with open(self.ui_history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"❌ UI历史保存失败: {e}")
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """获取适应性统计信息"""
        try:
            stats = {
                "total_elements": len(self.ui_elements),
                "total_ui_changes": len(self.change_history),
                "element_stats": {},
                "recent_changes": [],
                "adaptation_success_rate": 0.0
            }
            
            # 元素统计
            for name, element in self.ui_elements.items():
                stats["element_stats"][name] = {
                    "confidence_score": element.confidence_score,
                    "usage_count": element.usage_count,
                    "selector_count": len(element.selectors),
                    "last_working": element.last_working_time.isoformat()
                }
            
            # 最近变化
            stats["recent_changes"] = self.change_history[-10:] if self.change_history else []
            
            # 计算适应成功率
            if self.change_history:
                # 这里可以基于实际的成功/失败记录计算
                # 暂时使用简化计算
                avg_confidence = sum(element.confidence_score for element in self.ui_elements.values()) / len(self.ui_elements)
                stats["adaptation_success_rate"] = avg_confidence
            
            return stats
        
        except Exception as e:
            logger.error(f"❌ 获取适应性统计失败: {e}")
            return {"error": str(e)}


# 全局自适应UI处理器实例
_adaptive_ui_handler_instance = None

def get_adaptive_ui_handler() -> AdaptiveUIHandler:
    """获取自适应UI处理器单例"""
    global _adaptive_ui_handler_instance
    if _adaptive_ui_handler_instance is None:
        _adaptive_ui_handler_instance = AdaptiveUIHandler()
    return _adaptive_ui_handler_instance


# 测试接口
async def test_adaptive_ui():
    """测试自适应UI处理器"""
    try:
        print("=== 自适应UI处理器测试 ===")
        
        handler = get_adaptive_ui_handler()
        
        # 获取统计信息
        stats = handler.get_adaptation_statistics()
        print(f"适应性统计: {stats}")
        
        print("=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    asyncio.run(test_adaptive_ui())