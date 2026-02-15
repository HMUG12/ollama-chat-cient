#!/usr/bin/env python3
"""
测试所有导入是否正常
"""

print("开始测试导入...")

# 测试核心模块
try:
    import customtkinter as ctk
    print("✓ customtkinter 导入成功")
except Exception as e:
    print(f"✗ customtkinter 导入失败: {e}")

try:
    import threading
    print("✓ threading 导入成功")
except Exception as e:
    print(f"✗ threading 导入失败: {e}")

try:
    import time
    print("✓ time 导入成功")
except Exception as e:
    print(f"✗ time 导入失败: {e}")

try:
    from tkinter import scrolledtext
    print("✓ scrolledtext 导入成功")
except Exception as e:
    print(f"✗ scrolledtext 导入失败: {e}")

try:
    import requests
    print("✓ requests 导入成功")
except Exception as e:
    print(f"✗ requests 导入失败: {e}")

try:
    from typing import List, Dict
    print("✓ typing 导入成功")
except Exception as e:
    print(f"✗ typing 导入失败: {e}")

try:
    import flask
    print("✓ flask 导入成功")
except Exception as e:
    print(f"✗ flask 导入失败: {e}")

try:
    import json
    print("✓ json 导入成功")
except Exception as e:
    print(f"✗ json 导入失败: {e}")

try:
    import os
    print("✓ os 导入成功")
except Exception as e:
    print(f"✗ os 导入失败: {e}")

try:
    import uuid
    print("✓ uuid 导入成功")
except Exception as e:
    print(f"✗ uuid 导入失败: {e}")

try:
    from datetime import datetime, timedelta
    print("✓ datetime 导入成功")
except Exception as e:
    print(f"✗ datetime 导入失败: {e}")

try:
    import configparser
    print("✓ configparser 导入成功")
except Exception as e:
    print(f"✗ configparser 导入失败: {e}")

try:
    from collections import deque
    print("✓ deque 导入成功")
except Exception as e:
    print(f"✗ deque 导入失败: {e}")

try:
    import gc
    print("✓ gc 导入成功")
except Exception as e:
    print(f"✗ gc 导入失败: {e}")

try:
    import psutil
    print(f"✓ psutil 导入成功，版本: {psutil.__version__}")
except Exception as e:
    print(f"✗ psutil 导入失败: {e}")

print("\n所有导入测试完成！")