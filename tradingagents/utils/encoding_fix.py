#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码修复工具
解决Windows系统上的Unicode编码问题
"""

import os
import sys
import io


def fix_encoding():
    """修复编码问题"""
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 在Windows系统上重新配置标准输出流
    if sys.platform.startswith('win'):
        try:
            # 重新配置标准输出流
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stdin, 'reconfigure'):
                sys.stdin.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # 如果重新配置失败，使用备用方案
            try:
                # 创建新的UTF-8编码的输出流
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, 
                    encoding='utf-8', 
                    errors='replace'
                )
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, 
                    encoding='utf-8', 
                    errors='replace'
                )
            except Exception:
                pass  # 如果都失败了，继续执行


def safe_print(*args, **kwargs):
    """安全的打印函数"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 如果编码失败，替换问题字符
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # 替换常见的Unicode字符
                safe_arg = arg.replace('🧿', '[特殊字符]')
                safe_arg = safe_arg.replace('📊', '[图表]')
                safe_arg = safe_arg.replace('📈', '[上升]')
                safe_arg = safe_arg.replace('🔍', '[搜索]')
                safe_arg = safe_arg.replace('📋', '[列表]')
                safe_arg = safe_arg.replace('💰', '[金钱]')
                safe_arg = safe_arg.replace('📰', '[新闻]')
                safe_arg = safe_arg.replace('🎯', '[目标]')
                safe_arg = safe_arg.replace('⚠️', '[警告]')
                safe_arg = safe_arg.replace('❌', '[错误]')
                safe_arg = safe_arg.replace('✅', '[成功]')
                safe_arg = safe_arg.replace('¥', 'Y')
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)


# 自动修复编码
fix_encoding()
