"""
上传验证器 - 确保上传真正成功
防止虚假成功的上传结果
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class UploadValidator:
    """验证上传是否真正成功"""

    @staticmethod
    async def validate_upload(upload_result: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """
        验证上传结果的真实性

        Args:
            upload_result: 上传模块返回的结果
            file_path: 上传的文件路径

        Returns:
            包含验证结果的字典
        """
        validation_result = {
            'is_valid': False,
            'actual_upload': False,
            'url': None,
            'reason': '',
            'suggestions': []
        }

        if not upload_result or not upload_result.get('success'):
            validation_result['reason'] = '上传模块返回失败'
            validation_result['suggestions'] = [
                '检查Cookie是否过期（当前已7天）',
                '手动登录腾讯文档更新Cookie',
                '检查网络连接'
            ]
            return validation_result

        url = upload_result.get('url')
        if not url:
            validation_result['reason'] = '没有返回URL'
            validation_result['suggestions'] = ['上传可能失败，请检查日志']
            return validation_result

        # 检查URL是否包含文件名相关信息
        file_name = Path(file_path).stem
        if file_name not in url and 'sheet/' in url:
            # URL可能是猜测的，不是真正上传的
            validation_result['is_valid'] = False
            validation_result['url'] = url
            validation_result['reason'] = 'URL可能是已存在的文档，非新上传'
            validation_result['suggestions'] = [
                '⚠️ 上传可能失败，返回的是已存在文档',
                '建议：手动检查腾讯文档是否有新文件',
                '建议：更新Cookie后重试'
            ]
            logger.warning(f"⚠️ 上传验证失败：URL可能不是新上传的文档")
        else:
            # URL看起来是新的
            validation_result['is_valid'] = True
            validation_result['actual_upload'] = True
            validation_result['url'] = url
            validation_result['reason'] = '上传成功'
            logger.info(f"✅ 上传验证成功：{url}")

        return validation_result

    @staticmethod
    def check_cookie_age(cookie_update_time: str) -> Dict[str, Any]:
        """
        检查Cookie年龄

        Args:
            cookie_update_time: Cookie更新时间（ISO格式）

        Returns:
            Cookie状态信息
        """
        from datetime import datetime

        try:
            update_time = datetime.fromisoformat(cookie_update_time)
            age_days = (datetime.now() - update_time).days

            status = {
                'age_days': age_days,
                'is_expired': age_days >= 14,
                'is_warning': age_days >= 7,
                'is_fresh': age_days < 3,
                'message': '',
                'action_required': False
            }

            if status['is_expired']:
                status['message'] = f'Cookie已过期（{age_days}天），必须更新'
                status['action_required'] = True
            elif status['is_warning']:
                status['message'] = f'Cookie即将过期（{age_days}天），建议更新'
                status['action_required'] = True
            elif status['is_fresh']:
                status['message'] = f'Cookie新鲜（{age_days}天）'
            else:
                status['message'] = f'Cookie正常（{age_days}天）'

            return status
        except Exception as e:
            logger.error(f"检查Cookie年龄失败: {e}")
            return {
                'age_days': -1,
                'is_expired': True,
                'message': 'Cookie格式错误',
                'action_required': True
            }

def enhance_upload_logging(original_upload_func):
    """
    装饰器：增强上传函数的日志记录
    """
    async def wrapper(*args, **kwargs):
        logger.info("="*60)
        logger.info("🚀 开始上传流程（增强版）")

        # 检查Cookie状态
        import json
        cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
        if cookie_file.exists():
            with open(cookie_file) as f:
                cookie_data = json.load(f)
                last_update = cookie_data.get('last_update', 'Unknown')
                cookie_status = UploadValidator.check_cookie_age(last_update)

                if cookie_status['action_required']:
                    logger.warning(f"⚠️ {cookie_status['message']}")
                else:
                    logger.info(f"✅ {cookie_status['message']}")

        # 执行原始上传
        result = await original_upload_func(*args, **kwargs)

        # 验证上传结果
        if len(args) >= 2:
            file_path = args[1] if len(args) > 1 else kwargs.get('file_path')
            if file_path:
                validation = await UploadValidator.validate_upload(result, file_path)

                if not validation['is_valid']:
                    logger.warning("⚠️ 上传验证失败")
                    logger.warning(f"   原因: {validation['reason']}")
                    for suggestion in validation['suggestions']:
                        logger.warning(f"   - {suggestion}")
                else:
                    logger.info(f"✅ 上传验证成功: {validation['url']}")

        logger.info("="*60)
        return result

    return wrapper


# 导出功能
__all__ = ['UploadValidator', 'enhance_upload_logging']