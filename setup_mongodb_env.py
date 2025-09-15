#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB环境变量设置脚本
运行此脚本来设置正确的MongoDB环境变量
"""

import os

def setup_mongodb_environment():
    """设置MongoDB环境变量"""
    print("🔧 设置MongoDB环境变量...")
    
    # 设置MongoDB环境变量
    os.environ['MONGODB_ENABLED'] = 'true'
    os.environ['MONGODB_HOST'] = 'localhost'
    os.environ['MONGODB_PORT'] = '27017'
    os.environ['MONGODB_DATABASE'] = 'tradingagents'
    os.environ['MONGODB_USERNAME'] = ''
    os.environ['MONGODB_PASSWORD'] = ''
    os.environ['MONGODB_AUTH_SOURCE'] = 'admin'
    
    print("✅ MongoDB环境变量设置完成！")
    print("📋 当前配置:")
    print(f"   MONGODB_ENABLED: {os.getenv('MONGODB_ENABLED')}")
    print(f"   MONGODB_HOST: {os.getenv('MONGODB_HOST')}")
    print(f"   MONGODB_PORT: {os.getenv('MONGODB_PORT')}")
    print(f"   MONGODB_DATABASE: {os.getenv('MONGODB_DATABASE')}")
    print(f"   MONGODB_USERNAME: {os.getenv('MONGODB_USERNAME') or '(空)'}")
    print(f"   MONGODB_PASSWORD: {os.getenv('MONGODB_PASSWORD') or '(空)'}")

def test_mongodb_connection():
    """测试MongoDB连接"""
    print("\n🧪 测试MongoDB连接...")
    
    try:
        # 清除全局数据库管理器实例
        import tradingagents.config.database_manager
        tradingagents.config.database_manager._database_manager = None
        
        # 清除股票数据服务的全局实例
        import tradingagents.dataflows.stock_data_service
        tradingagents.dataflows.stock_data_service._stock_data_service = None
        
        # 测试数据库管理器
        from tradingagents.config.database_manager import get_database_manager
        db_manager = get_database_manager()
        
        if db_manager.is_mongodb_available():
            print("✅ MongoDB连接成功！")
            
            # 测试股票数据服务
            from tradingagents.dataflows.stock_data_service import get_stock_data_service
            service = get_stock_data_service()
            
            if service.db_manager and service.db_manager.is_mongodb_available():
                print("✅ 股票数据服务MongoDB功能正常！")
                
                # 测试股票查询
                result = service.get_stock_basic_info('000001')
                print(f"📊 股票查询结果: {result}")
                
                return True
            else:
                print("❌ 股票数据服务MongoDB功能异常")
                return False
        else:
            print("❌ MongoDB连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MongoDB配置脚本")
    print("=" * 50)
    
    # 设置环境变量
    setup_mongodb_environment()
    
    # 测试连接
    if test_mongodb_connection():
        print("\n🎉 MongoDB配置完成！股票查询系统现在使用MongoDB作为主要数据源。")
    else:
        print("\n⚠️ MongoDB配置有问题，请检查MongoDB服务是否正在运行。")
