#!/usr/bin/env python3
"""
创建一个简单的图标文件
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 创建图标
width, height = 64, 64
image = Image.new('RGB', (width, height), color='#2980b9')
draw = ImageDraw.Draw(image)

# 添加文字
try:
    font = ImageFont.truetype('arial.ttf', 24)
except:
    font = ImageFont.load_default()

text = "🤖"
draw.text((16, 16), text, font=font, fill='white')

# 保存为图标
icon_path = 'app_icon.ico'
image.save(icon_path, format='ICO')

print(f"图标文件已创建: {icon_path}")
print(f"文件大小: {os.path.getsize(icon_path)} 字节")
