#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能股票名称解析器
通过多个数据源自动获取股票名称，无需手动维护映射表
"""

import os
import sys
import time
import random
from typing import Optional, Dict, Any
import logging

# 修复Windows Unicode编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

class StockNameResolver:
    """智能股票名称解析器"""
    
    def __init__(self):
        self.cache = {}  # 内存缓存
        self.rate_limit_delay = 1  # 请求间隔（秒）
        self.last_request_time = 0
        
    def get_stock_name(self, stock_code: str) -> str:
        """
        获取股票名称（多数据源自动降级）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            str: 股票名称
        """
        # 1. 检查内存缓存
        if stock_code in self.cache:
            return self.cache[stock_code]
        
        # 2. 尝试多个数据源
        name = None
        
        # 2.1 尝试Yahoo Finance（带重试机制）
        name = self._get_from_yahoo_finance(stock_code)
        if name and name != f'股票{stock_code}':
            self.cache[stock_code] = name
            return name
        
        # 2.2 尝试东方财富API
        name = self._get_from_eastmoney(stock_code)
        if name and name != f'股票{stock_code}':
            self.cache[stock_code] = name
            return name
        
        # 2.3 尝试新浪财经API
        name = self._get_from_sina_finance(stock_code)
        if name and name != f'股票{stock_code}':
            self.cache[stock_code] = name
            return name
        
        # 2.4 尝试腾讯财经API
        name = self._get_from_tencent_finance(stock_code)
        if name and name != f'股票{stock_code}':
            self.cache[stock_code] = name
            return name
        
        # 3. 如果所有数据源都失败，返回默认格式
        default_name = f'股票{stock_code}'
        self.cache[stock_code] = default_name
        return default_name
    
    def _rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_from_yahoo_finance(self, stock_code: str) -> Optional[str]:
        """从Yahoo Finance获取股票名称"""
        try:
            self._rate_limit()
            import yfinance as yf
            
            # 构建Yahoo Finance代码
            if stock_code.startswith(('000', '002', '300')):
                yf_code = f"{stock_code}.SZ"  # 深圳市场
            elif stock_code.startswith(('600', '601', '603', '605', '688')):
                yf_code = f"{stock_code}.SS"  # 上海市场
            else:
                return None
            
            ticker = yf.Ticker(yf_code)
            info = ticker.info
            
            # 尝试多个可能的名称字段
            name_fields = ['longName', 'shortName', 'symbol', 'name']
            for field in name_fields:
                if field in info and info[field]:
                    name = str(info[field]).strip()
                    if name and name != yf_code and len(name) > 1:
                        return name
            
            return None
            
        except Exception as e:
            logger.debug(f"Yahoo Finance获取失败 {stock_code}: {e}")
            return None
    
    def _get_from_eastmoney(self, stock_code: str) -> Optional[str]:
        """从东方财富API获取股票名称"""
        try:
            self._rate_limit()
            import requests
            
            # 东方财富API
            url = f"http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': self._get_eastmoney_secid(stock_code),
                'fields': 'f57,f58,f127,f116,f60'
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and data['data'].get('f58'):
                    return data['data']['f58'].strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"东方财富API获取失败 {stock_code}: {e}")
            return None
    
    def _get_from_sina_finance(self, stock_code: str) -> Optional[str]:
        """从新浪财经API获取股票名称"""
        try:
            self._rate_limit()
            import requests
            
            # 新浪财经API
            if stock_code.startswith(('000', '002', '300')):
                sina_code = f"sz{stock_code}"
            elif stock_code.startswith(('600', '601', '603', '605', '688')):
                sina_code = f"sh{stock_code}"
            else:
                return None
            
            url = f"http://hq.sinajs.cn/list={sina_code}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                # 解析返回的数据
                if '=' in content and '"' in content:
                    data_part = content.split('=')[1].strip('"')
                    parts = data_part.split(',')
                    if len(parts) > 0 and parts[0]:
                        return parts[0].strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"新浪财经API获取失败 {stock_code}: {e}")
            return None
    
    def _get_from_tencent_finance(self, stock_code: str) -> Optional[str]:
        """从腾讯财经API获取股票名称"""
        try:
            self._rate_limit()
            import requests
            
            # 腾讯财经API
            if stock_code.startswith(('000', '002', '300')):
                tencent_code = f"s_sz{stock_code}"
            elif stock_code.startswith(('600', '601', '603', '605', '688')):
                tencent_code = f"s_sh{stock_code}"
            else:
                return None
            
            url = f"http://qt.gtimg.cn/q={tencent_code}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                # 解析返回的数据
                if '=' in content and '"' in content:
                    data_part = content.split('=')[1].strip('"')
                    parts = data_part.split('~')
                    if len(parts) > 1 and parts[1]:
                        return parts[1].strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"腾讯财经API获取失败 {stock_code}: {e}")
            return None
    
    def _get_eastmoney_secid(self, stock_code: str) -> str:
        """获取东方财富的secid格式"""
        if stock_code.startswith(('000', '002', '300')):
            return f"0.{stock_code}"  # 深圳市场
        elif stock_code.startswith(('600', '601', '603', '605', '688')):
            return f"1.{stock_code}"  # 上海市场
        else:
            return f"0.{stock_code}"  # 默认深圳市场

# 全局实例
_stock_name_resolver = None

def get_stock_name_resolver() -> StockNameResolver:
    """获取股票名称解析器实例"""
    global _stock_name_resolver
    if _stock_name_resolver is None:
        _stock_name_resolver = StockNameResolver()
    return _stock_name_resolver

def get_stock_name_smart(stock_code: str) -> str:
    """智能获取股票名称（对外接口）"""
    resolver = get_stock_name_resolver()
    return resolver.get_stock_name(stock_code)
