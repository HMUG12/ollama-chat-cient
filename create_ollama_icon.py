#!/usr/bin/env python3
"""
创建Ollama风格的蓝色"O"字图标
"""

from PIL import Image, ImageDraw
import os

# 创建图标
width, height = 64, 64
image = Image.new('RGB', (width, height), color='#2c3e50')
draw = ImageDraw.Draw(image)

# 绘制蓝色圆形
circle_radius = 24
circle_center = (width // 2, height // 2)
draw.ellipse(
    [
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    ],
    fill='#3498db'
)

# 绘制白色"O"字
text = "O"
font_size = 28
inner_radius = 12  # 默认值

try:
    from PIL import ImageFont
    font = ImageFont.truetype('arial.ttf', font_size)
    # 计算文字位置
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = circle_center[0] - text_width // 2
    text_y = circle_center[1] - text_height // 2
    draw.text((text_x, text_y), text, font=font, fill='white')
except:
    # 如果没有字体，使用简单的圆形镂空
    draw.ellipse(
        [
            circle_center[0] - inner_radius,
            circle_center[1] - inner_radius,
            circle_center[0] + inner_radius,
            circle_center[1] + inner_radius
        ],
        fill='#2c3e50'
    )

# 保存为图标
icon_path = 'ollama_icon.ico'
image.save(icon_path, format='ICO')

print(f"Ollama风格图标已创建: {icon_path}")
print(f"文件大小: {os.path.getsize(icon_path)} 字节")
