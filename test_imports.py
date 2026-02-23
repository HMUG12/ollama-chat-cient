#!/usr/bin/env python3
"""测试导入是否成功"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("测试导入main模块...")
    import main
    print("✓ main模块导入成功")
    
    print("测试创建OllamaChatGUI实例...")
    app = main.OllamaChatGUI()
    print("✓ OllamaChatGUI实例创建成功")
    
    print("测试本地搭建管理器...")
    if hasattr(app, 'setup_manager'):
        print("✓ 本地搭建管理器初始化成功")
    else:
        print("✗ 本地搭建管理器未初始化")
    
    print("测试服务器实例...")
    if hasattr(app, 'servers'):
        print("✓ 服务器实例初始化成功")
        print(f"  服务器列表: {list(app.servers.keys())}")
    else:
        print("✗ 服务器实例未初始化")
    
    print("测试配置保存...")
    try:
        app.save_config()
        print("✓ 配置保存成功")
    except Exception as e:
        print(f"✗ 配置保存失败: {e}")
    
    print("\n所有测试完成！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
