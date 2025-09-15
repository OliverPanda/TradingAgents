#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 自动配置MongoDB环境变量
"""

import os
import sys

# 设置MongoDB环境变量
os.environ['MONGODB_ENABLED'] = 'true'
os.environ['MONGODB_HOST'] = 'localhost'
os.environ['MONGODB_PORT'] = '27017'
os.environ['MONGODB_DATABASE'] = 'tradingagents'
os.environ['MONGODB_USERNAME'] = ''
os.environ['MONGODB_PASSWORD'] = ''
os.environ['MONGODB_AUTH_SOURCE'] = 'admin'

print("🚀 启动TradingAgents with MongoDB")
print("=" * 50)
print("📋 MongoDB配置:")
print(f"   启用: {os.getenv('MONGODB_ENABLED')}")
print(f"   主机: {os.getenv('MONGODB_HOST')}")
print(f"   端口: {os.getenv('MONGODB_PORT')}")
print(f"   数据库: {os.getenv('MONGODB_DATABASE')}")
print(f"   用户名: {os.getenv('MONGODB_USERNAME') or '(空)'}")
print(f"   密码: {os.getenv('MONGODB_PASSWORD') or '(空)'}")

# 清除全局实例
import tradingagents.config.database_manager
tradingagents.config.database_manager._database_manager = None

import tradingagents.dataflows.stock_data_service
tradingagents.dataflows.stock_data_service._stock_data_service = None

# 测试MongoDB连接
print("\n🧪 测试MongoDB连接...")
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
            print("💡 现在可以运行: python -m cli.main")
        else:
            print("❌ 股票数据服务MongoDB功能异常")
    else:
        print("❌ MongoDB连接失败")
        
except Exception as e:
    print(f"❌ 配置失败: {e}")
    import traceback
    traceback.print_exc()

# 如果直接运行此脚本，启动CLI
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        print("\n🚀 启动CLI...")
        import subprocess
        subprocess.run([sys.executable, "-m", "cli.main"])
