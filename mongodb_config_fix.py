#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB配置修复脚本
直接修改数据库管理器的默认配置
"""

import os
import sys

# 设置环境变量
os.environ['MONGODB_ENABLED'] = 'true'
os.environ['MONGODB_HOST'] = 'localhost'
os.environ['MONGODB_PORT'] = '27017'
os.environ['MONGODB_DATABASE'] = 'tradingagents'
os.environ['MONGODB_USERNAME'] = ''
os.environ['MONGODB_PASSWORD'] = ''
os.environ['MONGODB_AUTH_SOURCE'] = 'admin'

print("🔧 MongoDB配置修复")
print("=" * 50)

# 清除所有全局实例
import tradingagents.config.database_manager
tradingagents.config.database_manager._database_manager = None

import tradingagents.dataflows.stock_data_service
tradingagents.dataflows.stock_data_service._stock_data_service = None

# 测试MongoDB连接
print("📦 测试MongoDB连接...")
try:
    from tradingagents.config.database_manager import get_database_manager
    db_manager = get_database_manager()
    
    print(f"MongoDB配置: {db_manager.mongodb_config}")
    print(f"MongoDB可用性: {db_manager.is_mongodb_available()}")
    
    if db_manager.is_mongodb_available():
        print("✅ MongoDB连接成功！")
        
        # 测试股票数据服务
        print("\n📊 测试股票数据服务...")
        from tradingagents.dataflows.stock_data_service import get_stock_data_service
        service = get_stock_data_service()
        
        if service.db_manager and service.db_manager.is_mongodb_available():
            print("✅ 股票数据服务MongoDB功能正常！")
            
            # 测试股票查询
            result = service.get_stock_basic_info('000001')
            print(f"📈 股票查询结果: {result}")
            
            print("\n🎉 MongoDB配置完成！")
            print("💡 现在股票查询系统使用MongoDB作为主要数据源")
        else:
            print("❌ 股票数据服务MongoDB功能异常")
    else:
        print("❌ MongoDB连接失败")
        
except Exception as e:
    print(f"❌ 配置失败: {e}")
    import traceback
    traceback.print_exc()
