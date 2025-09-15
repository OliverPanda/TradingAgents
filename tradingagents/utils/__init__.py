# -*- coding: utf-8 -*-
"""
TradingAgents工具模块
"""

# 确保编码设置在所有模块导入之前
import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 如果可能，重新配置标准输出流
if sys.platform.startswith('win'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # 如果重新配置失败，继续执行
