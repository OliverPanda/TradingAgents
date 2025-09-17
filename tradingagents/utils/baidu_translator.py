#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度翻译API翻译服务
国内稳定快速的翻译解决方案
"""

import os
import re
import time
import hashlib
import random
import requests
from typing import Optional, Dict, Any
import logging

# 修复Windows Unicode编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

class BaiduTranslator:
    """百度翻译API翻译器"""
    
    def __init__(self):
        self.cache = {}  # 翻译缓存
        self.rate_limit_delay = 0.3  # 请求间隔（秒）
        self.last_request_time = 0
        
        # 百度翻译API配置
        self.app_id = os.getenv('BAIDU_APP_ID')
        self.secret_key = os.getenv('BAIDU_SECRET_KEY')
        self.api_url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
        
        if not self.app_id or not self.secret_key:
            logger.warning("百度翻译API密钥未设置，将使用DashScope作为备用")
    
    def translate_text(self, text: str, target_lang: str = "zh") -> str:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            target_lang: 目标语言，默认中文
            
        Returns:
            str: 翻译后的文本
        """
        if not text or not text.strip():
            return text
            
        # 检查缓存
        cache_key = f"{text[:100]}_{target_lang}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 检查是否包含中文，如果已经主要是中文则不需要翻译
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.sub(r'\s', '', text))
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            self.cache[cache_key] = text
            return text
        
        try:
            # 尝试百度翻译
            if self.app_id and self.secret_key:
                translated = self._translate_with_baidu(text, target_lang)
                if translated and translated != text:
                    self.cache[cache_key] = translated
                    return translated
            
            # 如果百度翻译失败，使用DashScope作为备用
            translated = self._translate_with_dashscope(text, target_lang)
            if translated and translated != text:
                self.cache[cache_key] = translated
                return translated
            
            # 如果都失败，返回原文
            self.cache[cache_key] = text
            return text
                
        except Exception as e:
            logger.warning(f"翻译失败: {e}")
            # 翻译失败时返回原文
            self.cache[cache_key] = text
            return text
    
    def _translate_with_baidu(self, text: str, target_lang: str) -> str:
        """使用百度翻译API翻译"""
        try:
            self._rate_limit()
            
            # 百度翻译API参数
            salt = str(random.randint(32768, 65536))
            sign_str = self.app_id + text + salt + self.secret_key
            sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
            
            params = {
                'q': text,
                'from': 'auto',
                'to': target_lang,
                'appid': self.app_id,
                'salt': salt,
                'sign': sign
            }
            
            response = requests.get(self.api_url, params=params, timeout=10)
            result = response.json()
            
            if 'trans_result' in result:
                translated_text = result['trans_result'][0]['dst']
                return translated_text
            else:
                raise Exception(f"百度翻译API错误: {result.get('error_msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"百度翻译失败: {e}")
            raise e
    
    def _translate_with_dashscope(self, text: str, target_lang: str) -> str:
        """使用DashScope作为备用翻译"""
        try:
            import dashscope
            from dashscope import Generation
            
            # 设置API密钥
            if not dashscope.api_key:
                dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
            
            if not dashscope.api_key:
                raise Exception("DashScope API密钥未设置")
            
            # 构建翻译提示
            prompt = f"""请将以下英文文本翻译成中文，保持原有的格式和结构，包括markdown格式：

{text}

翻译要求：
1. 保持原文的markdown格式（如标题、列表、表格等）
2. 保持专业术语的准确性
3. 保持原文的逻辑结构
4. 只返回翻译后的中文文本，不要添加其他内容"""
            
            # 调用DashScope API
            response = Generation.call(
                model='qwen-turbo',
                prompt=prompt,
                max_tokens=4000,
                temperature=0.1
            )
            
            if response.status_code == 200:
                translated_text = response.output.text.strip()
                return translated_text
            else:
                raise Exception(f"DashScope API调用失败: {response.message}")
                
        except Exception as e:
            logger.error(f"DashScope翻译失败: {e}")
            raise e
    
    def _rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def translate_report_section(self, section_name: str, content: str) -> str:
        """
        翻译报告章节
        
        Args:
            section_name: 章节名称
            content: 章节内容
            
        Returns:
            str: 翻译后的内容
        """
        if not content or not content.strip():
            return content
        
        try:
            # 翻译内容
            translated_content = self.translate_text(content)
            
            # 翻译章节标题（如果有）
            if section_name in ["market_report", "sentiment_report", "news_report", "fundamentals_report"]:
                # 这些是分析师报告，保持原有结构
                pass
            elif section_name == "investment_plan":
                # 研究团队决策
                translated_content = self._translate_section_title(translated_content, "Research Team Decision", "研究团队决策")
            elif section_name == "trader_investment_plan":
                # 交易团队计划
                translated_content = self._translate_section_title(translated_content, "Trading Team Plan", "交易团队计划")
            elif section_name == "final_trade_decision":
                # 投资组合管理决策
                translated_content = self._translate_section_title(translated_content, "Portfolio Management Decision", "投资组合管理决策")
            
            return translated_content
            
        except Exception as e:
            logger.error(f"翻译报告章节失败 {section_name}: {e}")
            return content
    
    def _translate_section_title(self, content: str, english_title: str, chinese_title: str) -> str:
        """翻译章节标题"""
        if english_title in content:
            content = content.replace(english_title, chinese_title)
        return content

# 全局实例
_translator = None

def get_translator() -> BaiduTranslator:
    """获取翻译器实例"""
    global _translator
    if _translator is None:
        _translator = BaiduTranslator()
    return _translator

def translate_report_content(content: str, target_lang: str = "zh") -> str:
    """翻译报告内容（对外接口）"""
    translator = get_translator()
    return translator.translate_text(content, target_lang)

def translate_report_section(section_name: str, content: str) -> str:
    """翻译报告章节（对外接口）"""
    translator = get_translator()
    return translator.translate_report_section(section_name, content)

