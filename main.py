import customtkinter as ctk
import threading
import time
from tkinter import scrolledtext
import requests
from typing import List, Dict
import flask
import json
import os
import uuid
from datetime import datetime, timedelta
import configparser
from collections import deque
import gc
import psutil


class OllamaChatGUI:
    def __init__(self):
        # 初始化窗口
        ctk.set_appearance_mode("dark")  # 深色模式
        ctk.set_default_color_theme("blue")  # 蓝色主题

        self.window = ctk.CTk()
        self.window.title("Ollama Chat Client - 本地AI助手")
        self.window.geometry("1050x700")

        # Ollama配置
        self.base_url = "http://localhost:11434"  # Ollama默认地址
        self._cached_models = self.get_available_models()
        self.current_model = self._cached_models[0] if self._cached_models else ""

        # API服务配置
        self.api_server_enabled = False
        self.api_server_port = 5000
        self.api_keys = self.load_api_keys()
        self.api_server = None
        # API Key调用统计
        self.api_key_stats = self.load_api_key_stats()

        # 对话历史管理
        self.max_history_rounds = 20  # 最大对话轮数
        # 为每个API Key创建独立的对话历史
        self.conversation_histories = {}  # {api_key: deque}
        # 全局对话历史（用于GUI）
        self.conversation_history = deque(maxlen=self.max_history_rounds)

        # API请求处理配置
        self.max_concurrent_requests = 5  # 最大并发请求数
        self.request_timeout = 60  # 请求超时时间（秒）
        # 请求队列控制
        self.request_semaphore = threading.Semaphore(self.max_concurrent_requests)

        # 内存管理配置
        self.memory_check_interval = 60  # 内存检查间隔（秒）
        self.max_memory_usage = 80  # 最大内存使用率
        # GPU内存管理配置
        self.gpu_memory_check_enabled = True  # 是否启用GPU内存监控
        self.max_gpu_memory_usage = 80  # 最大GPU内存使用率
        # 启动内存监控线程
        self.memory_monitor_thread = threading.Thread(target=self.monitor_memory, daemon=True)
        self.memory_monitor_thread.start()

        # 是否正在等待AI回复
        self._waiting_response = False
        # 加载动画状态
        self.loading_animation_running = False

        # 加载配置
        self.load_config()

        # 重新初始化依赖配置的组件
        # 重新初始化请求信号量
        self.request_semaphore = threading.Semaphore(self.max_concurrent_requests)
        # 重新初始化全局对话历史
        self.conversation_history = deque(maxlen=self.max_history_rounds)

        self.setup_ui()
        self.test_connection()

    def setup_ui(self):
        """设置用户界面"""
        # 创建网格布局
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(0, weight=1)

        # 添加按钮动画效果的函数
        def add_button_animation(button):
            original_fg = button.cget("fg_color")
            original_hover = button.cget("hover_color")
            
            def on_enter(event):
                # 悬停时的动画效果
                for i in range(10):
                    alpha = i / 10
                    new_color = self._blend_colors(original_fg, original_hover, alpha)
                    def update_color(c):
                        button.configure(fg_color=c)
                    self.window.after(i * 10, update_color, new_color)
            
            def on_leave(event):
                # 离开时的动画效果
                for i in range(10):
                    alpha = (10 - i) / 10
                    new_color = self._blend_colors(original_fg, original_hover, alpha)
                    def update_color(c):
                        button.configure(fg_color=c)
                    self.window.after(i * 10, update_color, new_color)
            
            def on_click(event):
                # 点击时的动画效果
                button.configure(fg_color="#1f618d")
                self.window.after(100, lambda: button.configure(fg_color=original_hover))
            
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
            button.bind("<Button-1>", on_click)

        # 左侧边栏
        sidebar_frame = ctk.CTkFrame(self.window, width=250, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(10, weight=1)

        # 标题
        title_label = ctk.CTkLabel(
            sidebar_frame,
            text="Ollama Chat",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=20)

        # 模型选择
        model_label = ctk.CTkLabel(sidebar_frame, text="选择模型:")
        model_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.model_var = ctk.StringVar(value=self.current_model)
        self.model_dropdown = ctk.CTkComboBox(
            sidebar_frame,
            values=self._cached_models,
            variable=self.model_var,
            command=self.change_model
        )
        self.model_dropdown.grid(row=2, column=0, padx=20, pady=(0, 10))

        # 刷新模型按钮
        refresh_btn = ctk.CTkButton(
            sidebar_frame,
            text="刷新模型列表",
            command=self.refresh_models,
            hover_color="#27ae60",
            fg_color="#229954",
            border_color="#27ae60",
            border_width=2,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        refresh_btn.grid(row=3, column=0, padx=20, pady=10)
        # 应用按钮动画
        add_button_animation(refresh_btn)

        # API服务管理区域
        api_server_frame = ctk.CTkFrame(sidebar_frame, corner_radius=10)
        api_server_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        api_server_frame.grid_columnconfigure(0, weight=1)

        api_server_title = ctk.CTkLabel(
            api_server_frame,
            text="API服务管理",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        api_server_title.grid(row=0, column=0, padx=10, pady=(10, 5))

        # API服务启用/禁用
        self.api_server_var = ctk.BooleanVar(value=self.api_server_enabled)
        api_server_switch = ctk.CTkSwitch(
            api_server_frame,
            text="启用API服务",
            variable=self.api_server_var,
            command=self.toggle_api_server
        )
        api_server_switch.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # API服务端口设置
        api_port_label = ctk.CTkLabel(api_server_frame, text="服务端口:")
        api_port_label.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")

        self.api_port_entry = ctk.CTkEntry(
            api_server_frame,
            placeholder_text="输入端口号"
        )
        self.api_port_entry.insert(0, str(self.api_server_port))
        self.api_port_entry.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        # 生成API Key按钮
        generate_api_key_btn = ctk.CTkButton(
            api_server_frame,
            text="生成新API Key",
            command=self.generate_api_key
        )
        generate_api_key_btn.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # 查看API Keys按钮
        view_api_keys_btn = ctk.CTkButton(
            api_server_frame,
            text="API Key管理控制台",
            command=self.open_api_key_console
        )
        view_api_keys_btn.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        # API服务状态
        self.api_server_status = ctk.CTkLabel(api_server_frame, text="API服务状态: 未启动")
        self.api_server_status.grid(row=6, column=0, padx=10, pady=(10, 10))

        # 清除对话按钮
        self.clear_btn = ctk.CTkButton(
            sidebar_frame,
            text="清除对话",
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
            border_color="#95a5a6",
            hover_color="#7f8c8d",
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.clear_conversation
        )
        self.clear_btn.grid(row=5, column=0, padx=20, pady=10)
        # 应用按钮动画
        add_button_animation(self.clear_btn)

        # 退出按钮
        exit_btn = ctk.CTkButton(
            sidebar_frame,
            text="退出",
            command=self.window.quit,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            border_color="#e74c3c",
            border_width=2,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        exit_btn.grid(row=7, column=0, padx=20, pady=20)
        # 应用按钮动画
        add_button_animation(exit_btn)

        # 状态标签
        self.status_label = ctk.CTkLabel(sidebar_frame, text="状态: 等待连接")
        self.status_label.grid(row=6, column=0, padx=20, pady=20)

        # 主对话区域
        main_frame = ctk.CTkFrame(self.window, corner_radius=0)
        main_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # 对话显示框
        self.conversation_text = scrolledtext.ScrolledText(
            main_frame,
            wrap="word",
            bg="#2b2b2b",
            fg="white",
            font=("Microsoft YaHei", 12),
            padx=15,
            pady=15,
            state="disabled"
        )
        self.conversation_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 预设文字样式标签（避免每次添加消息时重复配置）
        self.conversation_text.tag_config("timestamp_user", foreground="#4CAF50", font=("Arial", 10, "bold"))
        self.conversation_text.tag_config("message_user", foreground="white", font=("Microsoft YaHei", 11))
        self.conversation_text.tag_config("timestamp_assistant", foreground="#2196F3", font=("Arial", 10, "bold"))
        self.conversation_text.tag_config("message_assistant", foreground="white", font=("Microsoft YaHei", 11))
        self.conversation_text.tag_config("timestamp_system", foreground="#FF9800", font=("Arial", 10, "bold"))
        self.conversation_text.tag_config("message_system", foreground="white", font=("Microsoft YaHei", 11))

        # 底部输入区域
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)

        # 输入框
        self.input_text = ctk.CTkTextbox(bottom_frame, height=80)
        self.input_text.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # 发送按钮和加载指示器容器
        send_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        send_frame.grid(row=0, column=1, padx=5, pady=5)
        send_frame.grid_columnconfigure(0, weight=1)

        # 发送按钮
        self.send_btn = ctk.CTkButton(
            send_frame,
            text="发送",
            width=100,
            command=self.send_message,
            hover_color="#3498db",
            fg_color="#2980b9",
            border_color="#3498db",
            border_width=2,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.send_btn.grid(row=0, column=0, padx=5, pady=5)

        # 加载指示器
        self.loading_indicator = ctk.CTkLabel(
            send_frame,
            text="",
            font=ctk.CTkFont(size=16)
        )
        self.loading_indicator.grid(row=0, column=0, padx=5, pady=5)
        self.loading_indicator.grid_remove()  # 初始隐藏

        # 应用按钮动画
        add_button_animation(self.send_btn)

        # 绑定快捷键：Enter 发送，Shift+Enter 换行
        self.input_text.bind("<Return>", self._on_enter)
        self.input_text.bind("<Shift-Return>", lambda e: None)  # 允许换行

    def _on_enter(self, event=None):
        """Enter 键发送消息"""
        self.send_message()
        return "break"  # 阻止插入换行符

    def _blend_colors(self, color1, color2, alpha):
        """混合两种颜色"""
        # 解析颜色值
        def parse_color(color):
            if color.startswith('#'):
                color = color[1:]
            if len(color) == 6:
                return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            return (0, 0, 0)
        
        # 混合颜色
        r1, g1, b1 = parse_color(color1)
        r2, g2, b2 = parse_color(color2)
        
        r = int(r1 * (1 - alpha) + r2 * alpha)
        g = int(g1 * (1 - alpha) + g2 * alpha)
        b = int(b1 * (1 - alpha) + b2 * alpha)
        
        return f"#{r:02x}{g:02x}{b:02x}"

    def get_available_models(self):
        """获取可用的Ollama模型"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except (requests.RequestException, ValueError, KeyError):
            pass
        return ["llama2", "mistral", "codellama"]  # 默认模型列表

    def test_connection(self):
        """测试Ollama连接"""

        def test():
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    self.window.after(0, self.status_label.configure,
                        {"text": "状态: 已连接 ✅", "text_color": "lightgreen"}
                    )
                    self.add_message("system", "系统", "已连接到Ollama，可以开始对话了！")
                else:
                    self.window.after(0, self.status_label.configure,
                        {"text": "状态: 连接失败 ❌", "text_color": "red"}
                    )
            except requests.RequestException:
                self.window.after(0, self.status_label.configure,
                    {"text": "状态: Ollama未运行 ❌", "text_color": "red"}
                )
                self.add_message("system", "系统",
                                 "无法连接到Ollama，请确保Ollama服务正在运行。\n"
                                 "在终端运行: ollama serve")

        threading.Thread(target=test, daemon=True).start()

    def change_model(self, choice):
        """切换模型"""
        self.current_model = choice
        self.add_message("system", "系统", f"已切换到模型: {choice}")

    def refresh_models(self):
        """刷新模型列表"""
        models = self.get_available_models()
        self._cached_models = models
        self.model_dropdown.configure(values=models)
        if models:
            self.model_dropdown.set(models[0])
            self.current_model = models[0]

    def clear_conversation(self):
        """清除对话历史"""
        self.conversation_history = []
        self.conversation_text.configure(state="normal")
        self.conversation_text.delete(1.0, "end")
        self.conversation_text.configure(state="disabled")
        self.add_message("system", "系统", "对话历史已清除")

    def send_message(self):
        """发送消息"""
        if self._waiting_response:
            return

        message = self.input_text.get("1.0", "end-1c").strip()
        if not message or not self.current_model:
            return

        # 清空输入框并禁用发送按钮
        self.input_text.delete("1.0", "end")
        self._set_sending_state(True)

        # 显示用户消息
        self.add_message("user", "你", message)

        # 发送到Ollama
        threading.Thread(target=self.get_ai_response, args=(message,), daemon=True).start()

    def _update_connection_status(self, connected: bool, error_msg: str = ""):
        """根据实际连接结果更新状态标签"""
        if connected:
            self.status_label.configure(text="状态: 已连接 ✅", text_color="lightgreen")
        elif error_msg:
            self.status_label.configure(text=f"状态: {error_msg}", text_color="red")
        else:
            self.status_label.configure(text="状态: 未连接 ❌", text_color="red")

    def _set_sending_state(self, sending, connected=True, error_msg=""):
        """设置发送状态，防止重复发送"""
        self._waiting_response = sending
        if sending:
            # 显示加载动画
            self.send_btn.grid_remove()
            self.loading_indicator.grid()
            self.loading_indicator.configure(text="🤖")
            self.clear_btn.configure(state="disabled")
            self.status_label.configure(text="状态: AI思考中...", text_color="yellow")
            
            # 启动加载动画
            self.loading_animation_running = True
            self._animate_loading()
        else:
            # 隐藏加载动画
            self.loading_animation_running = False
            self.loading_indicator.grid_remove()
            self.send_btn.grid()
            self.send_btn.configure(state="normal", text="发送")
            self.clear_btn.configure(state="normal")
            self._update_connection_status(connected, error_msg)

    def _animate_loading(self):
        """加载动画效果"""
        if not self.loading_animation_running:
            return
        
        # 旋转动画（使用不同的表情或字符）
        loading_frames = ["🤖", "🤔", "🧠", "💭", "🤖"]
        
        def animate(frame=0):
            if self.loading_animation_running:
                self.loading_indicator.configure(text=loading_frames[frame])
                next_frame = (frame + 1) % len(loading_frames)
                self.window.after(300, animate, next_frame)
        
        animate()

    def get_ai_response(self, message):
        """获取AI响应（使用 /api/chat 支持多轮对话）"""
        connected = True
        error_msg = ""
        try:
            # 限制消息长度，避免过长消息占用过多内存
            max_message_length = 10000  # 10KB
            if len(message) > max_message_length:
                message = message[:max_message_length] + "...（消息过长，已截断）"
                print("用户消息过长，已截断")

            # 将用户消息加入历史
            self.conversation_history.append({
                "role": "user",
                "content": message
            })

            # 构建请求时对历史做快照，避免与主线程竞争
            messages_snapshot = list(self.conversation_history)

            data = {
                "model": self.current_model,
                "messages": messages_snapshot,
                "stream": False
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=data,
                timeout=self.request_timeout
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("message", {}).get("content", "")

                # 限制AI回复长度
                if len(ai_response) > max_message_length:
                    ai_response = ai_response[:max_message_length] + "...（回复过长，已截断）"
                    print("AI回复过长，已截断")

                # 将AI回复也加入历史
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response
                })

                self.add_message("assistant", "AI", ai_response)
            else:
                # 请求失败，安全回滚用户消息
                if self.conversation_history and self.conversation_history[-1].get("role") == "user":
                    self.conversation_history.pop()
                self.add_message("system", "系统", f"错误: {response.status_code}")
                connected = False
                error_msg = f"请求错误 ({response.status_code})"

        except requests.RequestException as e:
            # 网络异常，安全回滚用户消息
            if self.conversation_history and self.conversation_history[-1].get("role") == "user":
                self.conversation_history.pop()
            self.add_message("system", "系统", f"请求失败: {str(e)}")
            connected = False
            error_msg = "连接失败 ❌"
        finally:
            self.window.after(0, self._set_sending_state, False, connected, error_msg)

    def add_message(self, sender, name, message):
        """添加消息到对话框"""
        self.window.after(0, self._add_message_gui, sender, name, message)

    def _add_message_gui(self, sender, name, message):
        """在GUI线程中添加消息"""
        self.conversation_text.configure(state="normal")

        # 添加时间戳
        timestamp = time.strftime("%H:%M:%S")

        # 设置消息前缀图标
        if sender == "user":
            prefix = "👤"
        elif sender == "assistant":
            prefix = "🤖"
        else:
            prefix = "⚙️"

        # 保存当前插入位置
        current_pos = self.conversation_text.index("end")

        # 插入消息
        self.conversation_text.insert("end", f"\n[{timestamp}] {prefix} {name}:\n", f"timestamp_{sender}")
        self.conversation_text.insert("end", f"{message}\n", f"message_{sender}")
        self.conversation_text.insert("end", "-" * 50 + "\n")

        # 滚动到底部
        self.conversation_text.see("end")
        self.conversation_text.configure(state="disabled")

        # 添加简单的淡入效果（通过颜色渐变实现）
        def fade_in(start_pos, end_pos, step=0, max_steps=20):
            if step <= max_steps:
                # 计算透明度
                alpha = step / max_steps
                # 设置文本颜色，根据发送者类型
                if sender == "user":
                    fg_color = f"#{int(76 * alpha):02x}{int(175 * alpha):02x}{int(80 * alpha):02x}"
                elif sender == "assistant":
                    fg_color = f"#{int(33 * alpha):02x}{int(150 * alpha):02x}{int(243 * alpha):02x}"
                else:
                    fg_color = f"#{int(255 * alpha):02x}{int(152 * alpha):02x}{int(0 * alpha):02x}"
                
                # 重新配置标签颜色
                self.conversation_text.tag_config(f"timestamp_{sender}", foreground=fg_color)
                self.conversation_text.tag_config(f"message_{sender}", foreground=f"#{int(255 * alpha):02x}{int(255 * alpha):02x}{int(255 * alpha):02x}")
                
                # 继续动画
                self.window.after(20, fade_in, start_pos, end_pos, step + 1, max_steps)

        # 启动淡入动画
        fade_in(current_pos, self.conversation_text.index("end"))

    def load_config(self):
        """从文件加载配置"""
        # 优先从config.ini加载配置
        config_ini_path = os.path.join(os.path.dirname(__file__), "config.ini")
        config_json_path = os.path.join(os.path.dirname(__file__), "config.json")
        
        try:
            # 加载config.ini
            if os.path.exists(config_ini_path):
                # 创建一个自定义的ConfigParser，忽略值中的注释
                class ConfigParserWithComments(configparser.ConfigParser):
                    def get(self, section, option, *, raw=False, vars=None, fallback=configparser._UNSET):
                        value = super().get(section, option, raw=raw, vars=vars, fallback=fallback)
                        # 去除注释部分
                        if isinstance(value, str):
                            value = value.split('#')[0].strip()
                        return value
                    
                    def getint(self, section, option, *, raw=False, vars=None, fallback=configparser._UNSET):
                        value = self.get(section, option, raw=raw, vars=vars, fallback=fallback)
                        if value != configparser._UNSET:
                            try:
                                return int(value)
                            except ValueError:
                                return fallback
                        return fallback
                    
                    def getboolean(self, section, option, *, raw=False, vars=None, fallback=configparser._UNSET):
                        value = self.get(section, option, raw=raw, vars=vars, fallback=fallback)
                        if value != configparser._UNSET:
                            if isinstance(value, str):
                                value = value.lower()
                                return value in ('true', '1', 'yes', 'on')
                            return bool(value)
                        return fallback
                
                config = ConfigParserWithComments()
                config.read(config_ini_path, encoding="utf-8")
                
                # 服务器配置
                if config.has_section("Server"):
                    self.api_server_enabled = config.getboolean("Server", "enable_api_server", fallback=False)
                    self.api_server_port = config.getint("Server", "api_server_port", fallback=5000)
                
                # Ollama配置
                if config.has_section("Ollama"):
                    self.base_url = config.get("Ollama", "base_url", fallback="http://localhost:11434")
                    default_model = config.get("Ollama", "default_model", fallback="llama2")
                    if default_model:
                        self.current_model = default_model
                
                # API配置
                if config.has_section("API"):
                    self.use_api_key = config.getboolean("API", "enable_external_api", fallback=False)
                    self.api_base_url = config.get("API", "external_api_base_url", fallback="https://api.openai.com/v1")
                
                # 性能配置
                if config.has_section("Performance"):
                    self.max_concurrent_requests = config.getint("Performance", "max_concurrent_requests", fallback=5)
                    self.request_timeout = config.getint("Performance", "request_timeout", fallback=60)
                    self.max_history_rounds = config.getint("Performance", "max_history_rounds", fallback=20)
                    self.memory_check_interval = config.getint("Performance", "memory_check_interval", fallback=60)
                    self.max_memory_usage = config.getint("Performance", "max_memory_usage", fallback=80)
                    # GPU内存管理配置
                    self.gpu_memory_check_enabled = config.getboolean("Performance", "gpu_memory_check_enabled", fallback=True)
                    self.max_gpu_memory_usage = config.getint("Performance", "max_gpu_memory_usage", fallback=80)
            
            # 从config.json加载（保持向后兼容）
            elif os.path.exists(config_json_path):
                with open(config_json_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.api_server_enabled = config.get("api_server_enabled", False)
                    self.api_server_port = config.get("api_server_port", 5000)
                    if "current_model" in config:
                        self.current_model = config["current_model"]
        except Exception as e:
            print(f"加载配置失败: {e}")

    def save_config(self):
        """保存配置到文件"""
        config = {
            "api_server_enabled": self.api_server_enabled,
            "api_server_port": self.api_server_port,
            "current_model": self.current_model
        }
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def load_api_keys(self):
        """加载API Keys"""
        api_keys_path = os.path.join(os.path.dirname(__file__), "api_keys.json")
        try:
            if os.path.exists(api_keys_path):
                with open(api_keys_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载API Keys失败: {e}")
        return []

    def save_api_keys(self):
        """保存API Keys"""
        api_keys_path = os.path.join(os.path.dirname(__file__), "api_keys.json")
        try:
            with open(api_keys_path, "w", encoding="utf-8") as f:
                json.dump(self.api_keys, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存API Keys失败: {e}")

    def generate_api_key(self):
        """生成新的API Key"""
        # 创建自定义过期时间窗口
        window = ctk.CTkToplevel(self.window)
        window.title("生成API Key")
        window.geometry("400x300")
        window.transient(self.window)
        window.grab_set()
        
        # 布局
        window.grid_columnconfigure(0, weight=1)
        
        # 标题
        title_label = ctk.CTkLabel(
            window,
            text="生成新API Key",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=20)
        
        # 过期时间设置
        expire_label = ctk.CTkLabel(window, text="过期时间设置:")
        expire_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        # 过期时间选项
        self.expire_var = ctk.StringVar(value="365")
        expire_options = ["7", "30", "90", "180", "365", "自定义"]
        expire_dropdown = ctk.CTkComboBox(
            window,
            values=expire_options,
            variable=self.expire_var
        )
        expire_dropdown.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # 自定义天数输入
        self.custom_days_var = ctk.StringVar(value="365")
        custom_days_frame = ctk.CTkFrame(window)
        custom_days_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        custom_days_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(custom_days_frame, text="自定义天数:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        custom_days_entry = ctk.CTkEntry(
            custom_days_frame,
            textvariable=self.custom_days_var
        )
        custom_days_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(custom_days_frame, text="天").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # 按钮
        button_frame = ctk.CTkFrame(window)
        button_frame.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # 取消按钮
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            command=window.destroy
        )
        cancel_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # 生成按钮
        def generate_with_expire():
            # 获取过期天数
            expire_value = self.expire_var.get()
            if expire_value == "自定义":
                try:
                    days = int(self.custom_days_var.get())
                except:
                    days = 365
            else:
                days = int(expire_value)
            
            # 生成随机API Key
            api_key = str(uuid.uuid4()) + "-" + str(uuid.uuid4())
            # 添加到API Keys列表
            self.api_keys.append({
                "key": api_key,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=days)).isoformat()
            })
            # 保存API Keys
            self.save_api_keys()
            # 显示生成的API Key
            self.add_message("system", "系统", f"生成的新API Key: {api_key}")
            # 关闭窗口
            window.destroy()
        
        generate_btn = ctk.CTkButton(
            button_frame,
            text="生成",
            command=generate_with_expire
        )
        generate_btn.grid(row=0, column=1, padx=5, pady=5)

    def view_api_keys(self):
        """查看已有的API Keys"""
        if not self.api_keys:
            self.add_message("system", "系统", "没有已生成的API Keys")
            return
        
        keys_info = "已生成的API Keys:\n"
        for i, key_info in enumerate(self.api_keys, 1):
            keys_info += f"\n{i}. Key: {key_info['key']}\n"
            keys_info += f"   创建时间: {key_info['created_at']}\n"
            keys_info += f"   过期时间: {key_info['expires_at']}\n"
        
        self.add_message("system", "系统", keys_info)

    def create_api_app(self):
        """创建API应用，支持阿里API调用方式"""
        app = flask.Flask(__name__)
        
        # API认证中间件
        @app.before_request
        def authenticate():
            # 跳过OPTIONS请求
            if flask.request.method == 'OPTIONS':
                return
            
            # 获取API Key（支持多种认证方式）
            api_key = None
            
            # 方式1: Bearer token（标准方式）
            auth_header = flask.request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                api_key = auth_header[7:]
            
            # 方式2: 阿里API方式（通过公共参数）
            if not api_key:
                # 从查询参数或表单获取
                api_key = flask.request.args.get('AccessKeyId') or flask.request.form.get('AccessKeyId')
                
            # 方式3: 从JSON请求体获取（阿里API可能的方式）
            if not api_key:
                try:
                    data = flask.request.json
                    if data:
                        api_key = data.get('AccessKeyId')
                except:
                    pass
            
            if not api_key:
                return flask.jsonify({"code": 401, "message": "Missing API Key", "data": None}), 401
            
            # 验证API Key
            valid = False
            for key_info in self.api_keys:
                if key_info['key'] == api_key:
                    # 检查是否过期
                    expires_at = datetime.fromisoformat(key_info['expires_at'])
                    if datetime.now() < expires_at:
                        valid = True
                    break
            
            if not valid:
                return flask.jsonify({"code": 401, "message": "Invalid or expired API Key", "data": None}), 401
            
            # 确保为该API Key创建对话历史
            if api_key not in self.conversation_histories:
                self.conversation_histories[api_key] = deque(maxlen=self.max_history_rounds)
            
            # 记录API调用统计
            self.record_api_call(api_key)
        
        # 聊天API端点（支持阿里API格式）
        @app.route('/api/chat', methods=['POST'])
        def chat():
            try:
                # 检查是否超过最大并发请求数
                if not self.request_semaphore.acquire(blocking=False):
                    return flask.jsonify({"code": 429, "message": "Too many concurrent requests", "data": None}), 429
                
                try:
                    # 获取API Key
                    api_key = None
                    
                    # 从请求中获取API Key
                    if flask.request.is_json:
                        data = flask.request.json
                        api_key = data.get('AccessKeyId')
                    if not api_key:
                        api_key = flask.request.args.get('AccessKeyId') or flask.request.form.get('AccessKeyId')
                    if not api_key:
                        auth_header = flask.request.headers.get('Authorization')
                        if auth_header and auth_header.startswith('Bearer '):
                            api_key = auth_header[7:]
                    
                    # 解析请求（支持多种格式）
                    message = None
                    model = self.current_model
                    
                    # 方式1: 标准JSON格式
                    if flask.request.is_json:
                        data = flask.request.json
                        message = data.get('message') or data.get('Message')  # 支持阿里API的参数名
                        model = data.get('model', self.current_model) or data.get('Model', self.current_model)
                    
                    # 方式2: 表单格式（阿里API可能使用）
                    if not message:
                        message = flask.request.form.get('message') or flask.request.form.get('Message')
                        model = flask.request.form.get('model', self.current_model) or flask.request.form.get('Model', self.current_model)
                    
                    # 方式3: 查询参数（阿里API可能使用）
                    if not message:
                        message = flask.request.args.get('message') or flask.request.args.get('Message')
                        model = flask.request.args.get('model', self.current_model) or flask.request.args.get('Model', self.current_model)
                    
                    if not message:
                        return flask.jsonify({"code": 400, "message": "Missing message", "data": None}), 400
                    
                    # 使用同步版本获取回复，传入API Key，添加超时
                    import threading
                    import queue
                    
                    # 创建结果队列
                    result_queue = queue.Queue()
                    
                    # 定义工作函数
                    def worker():
                        try:
                            result = self.get_ai_response_sync(message, model, api_key)
                            result_queue.put((True, result))
                        except Exception as e:
                            result_queue.put((False, str(e)))
                    
                    # 启动工作线程
                    thread = threading.Thread(target=worker)
                    thread.daemon = True
                    thread.start()
                    
                    # 等待结果，设置超时
                    try:
                        success, result = result_queue.get(timeout=self.request_timeout)
                        if success:
                            response = result
                        else:
                            return flask.jsonify({"code": 500, "message": result, "data": None}), 500
                    except queue.Empty:
                        return flask.jsonify({"code": 408, "message": "Request timeout", "data": None}), 408
                    
                    # 返回阿里API标准格式
                    return flask.jsonify({
                        "code": 200,
                        "message": "Success",
                        "data": {
                            "response": response
                        }
                    })
                finally:
                    # 释放信号量
                    self.request_semaphore.release()
            except Exception as e:
                # 确保释放信号量
                try:
                    self.request_semaphore.release()
                except:
                    pass
                return flask.jsonify({"code": 500, "message": str(e), "data": None}), 500
        
        # 模型列表API端点（支持阿里API格式）
        @app.route('/api/models', methods=['GET'])
        def models():
            try:
                models = self.get_available_models()
                # 返回阿里API标准格式
                return flask.jsonify({
                    "code": 200,
                    "message": "Success",
                    "data": {
                        "models": models
                    }
                })
            except Exception as e:
                return flask.jsonify({"code": 500, "message": str(e), "data": None}), 500
        
        return app

    def get_ai_response_sync(self, message, model=None, api_key=None):
        """同步获取AI响应"""
        if model:
            self.current_model = model
        
        # 选择对话历史
        if api_key:
            # 使用API Key对应的对话历史
            history = self.conversation_histories.get(api_key)
            if not history:
                history = deque(maxlen=self.max_history_rounds)
                self.conversation_histories[api_key] = history
        else:
            # 使用全局对话历史（用于GUI）
            history = self.conversation_history
        
        # 限制消息长度，避免过长消息占用过多内存
        max_message_length = 10000  # 10KB
        if len(message) > max_message_length:
            message = message[:max_message_length] + "...（消息过长，已截断）"
            print("用户消息过长，已截断")

        # 将用户消息加入历史
        history.append({
            "role": "user",
            "content": message
        })

        # 构建请求时对历史做快照，避免与主线程竞争
        messages_snapshot = list(history)

        data = {
            "model": self.current_model,
            "messages": messages_snapshot,
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=data,
                timeout=300
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("message", {}).get("content", "")

                # 限制AI回复长度
                if len(ai_response) > max_message_length:
                    ai_response = ai_response[:max_message_length] + "...（回复过长，已截断）"
                    print("AI回复过长，已截断")

                # 将AI回复也加入历史
                history.append({
                    "role": "assistant",
                    "content": ai_response
                })

                return ai_response
            else:
                # 请求失败，安全回滚用户消息
                if history and history[-1].get("role") == "user":
                    history.pop()
                return f"错误: {response.status_code}"
        except Exception as e:
            # 网络异常，安全回滚用户消息
            if history and history[-1].get("role") == "user":
                history.pop()
            return f"错误: {str(e)}"

    def start_api_server(self):
        """启动API服务"""
        try:
            # 获取端口
            port = int(self.api_port_entry.get())
            self.api_server_port = port
            
            # 创建API应用
            self.api_server = self.create_api_app()
            
            # 在后台线程中运行API服务
            def run_server():
                self.api_server.run(host='0.0.0.0', port=port, debug=False)
            
            threading.Thread(target=run_server, daemon=True).start()
            
            # 更新状态
            self.api_server_enabled = True
            self.api_server_status.configure(text=f"API服务状态: 已启动 (端口: {port})", text_color="lightgreen")
            self.add_message("system", "系统", f"API服务已启动，端口: {port}")
            
            # 保存配置
            self.save_config()
        except Exception as e:
            self.api_server_status.configure(text=f"API服务状态: 启动失败", text_color="red")
            self.add_message("system", "系统", f"API服务启动失败: {str(e)}")

    def stop_api_server(self):
        """停止API服务"""
        # 注意：Flask的开发服务器不支持优雅停止
        # 这里我们只是标记为已停止
        self.api_server_enabled = False
        self.api_server_status.configure(text="API服务状态: 已停止", text_color="red")
        self.add_message("system", "系统", "API服务已停止")
        self.api_server = None
        
        # 保存配置
        self.save_config()

    def toggle_api_server(self):
        """切换API服务状态"""
        if self.api_server_var.get():
            self.start_api_server()
        else:
            self.stop_api_server()

    def load_api_key_stats(self):
        """加载API Key调用统计数据"""
        stats_path = os.path.join(os.path.dirname(__file__), "api_key_stats.json")
        try:
            if os.path.exists(stats_path):
                with open(stats_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载API Key统计数据失败: {e}")
        return {}

    def save_api_key_stats(self):
        """保存API Key调用统计数据"""
        stats_path = os.path.join(os.path.dirname(__file__), "api_key_stats.json")
        try:
            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump(self.api_key_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存API Key统计数据失败: {e}")

    def record_api_call(self, api_key):
        """记录API调用"""
        # 初始化统计数据
        if api_key not in self.api_key_stats:
            self.api_key_stats[api_key] = {
                "total_calls": 0,
                "last_call": None,
                "calls_today": 0,
                "today": datetime.now().strftime("%Y-%m-%d")
            }
        
        # 更新统计数据
        stats = self.api_key_stats[api_key]
        stats["total_calls"] += 1
        stats["last_call"] = datetime.now().isoformat()
        
        # 更新今日调用次数
        today = datetime.now().strftime("%Y-%m-%d")
        if stats["today"] != today:
            stats["today"] = today
            stats["calls_today"] = 1
        else:
            stats["calls_today"] += 1
        
        # 保存统计数据
        self.save_api_key_stats()

    def open_api_key_console(self):
        """打开API Key管理控制台"""
        # 创建控制台窗口
        console_window = ctk.CTkToplevel(self.window)
        console_window.title("API Key管理控制台")
        console_window.geometry("800x600")
        console_window.transient(self.window)
        console_window.grab_set()
        
        # 创建标签页
        tabview = ctk.CTkTabview(console_window)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # API Key管理标签
        key_management_tab = tabview.add("API Key管理")
        key_management_tab.grid_columnconfigure(0, weight=1)
        key_management_tab.grid_rowconfigure(0, weight=1)
        
        # API Key列表
        key_list_frame = ctk.CTkScrollableFrame(key_management_tab)
        key_list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        key_list_frame.grid_columnconfigure(0, weight=1)
        
        # 标题行
        title_frame = ctk.CTkFrame(key_list_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=5)
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=1)
        title_frame.grid_columnconfigure(2, weight=1)
        title_frame.grid_columnconfigure(3, weight=1)
        title_frame.grid_columnconfigure(4, weight=1)
        
        ctk.CTkLabel(title_frame, text="API Key", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(title_frame, text="创建时间", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(title_frame, text="过期时间", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkLabel(title_frame, text="总调用次数", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkLabel(title_frame, text="操作", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=5, pady=5)
        
        # API Key列表
        for i, key_info in enumerate(self.api_keys, 1):
            key = key_info["key"]
            created_at = key_info["created_at"]
            expires_at = key_info["expires_at"]
            
            # 获取调用统计
            total_calls = 0
            if key in self.api_key_stats:
                total_calls = self.api_key_stats[key].get("total_calls", 0)
            
            # 创建行
            row_frame = ctk.CTkFrame(key_list_frame)
            row_frame.grid(row=i, column=0, sticky="ew", pady=5)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            row_frame.grid_columnconfigure(4, weight=1)
            
            # 添加数据
            ctk.CTkLabel(row_frame, text=key[:20] + "...").grid(row=0, column=0, padx=5, pady=5)
            ctk.CTkLabel(row_frame, text=created_at[:19]).grid(row=0, column=1, padx=5, pady=5)
            ctk.CTkLabel(row_frame, text=expires_at[:19]).grid(row=0, column=2, padx=5, pady=5)
            ctk.CTkLabel(row_frame, text=str(total_calls)).grid(row=0, column=3, padx=5, pady=5)
            
            # 操作按钮
            button_frame = ctk.CTkFrame(row_frame)
            button_frame.grid(row=0, column=4, padx=5, pady=5)
            
            # 测试按钮
            test_btn = ctk.CTkButton(
                button_frame,
                text="测试",
                fg_color="#4CAF50",
                hover_color="#45a049",
                width=60,
                command=lambda k=key: self.test_api_key(k)
            )
            test_btn.pack(side="left", padx=2)
            
            # 删除按钮
            delete_btn = ctk.CTkButton(
                button_frame,
                text="删除",
                fg_color="#FF5555",
                hover_color="#FF3333",
                width=60,
                command=lambda k=key: self.delete_api_key(k, console_window)
            )
            delete_btn.pack(side="left", padx=2)
        
        # 调用统计标签
        stats_tab = tabview.add("调用统计")
        stats_tab.grid_columnconfigure(0, weight=1)
        stats_tab.grid_rowconfigure(0, weight=1)
        
        # 统计数据
        stats_frame = ctk.CTkScrollableFrame(stats_tab)
        stats_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        stats_frame.grid_columnconfigure(0, weight=1)
        
        # 标题行
        stats_title_frame = ctk.CTkFrame(stats_frame)
        stats_title_frame.grid(row=0, column=0, sticky="ew", pady=5)
        stats_title_frame.grid_columnconfigure(0, weight=1)
        stats_title_frame.grid_columnconfigure(1, weight=1)
        stats_title_frame.grid_columnconfigure(2, weight=1)
        stats_title_frame.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(stats_title_frame, text="API Key", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(stats_title_frame, text="总调用次数", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(stats_title_frame, text="今日调用次数", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkLabel(stats_title_frame, text="最后调用时间", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=5, pady=5)
        
        # 统计数据列表
        for i, (key, stats) in enumerate(self.api_key_stats.items(), 1):
            # 创建行
            stats_row_frame = ctk.CTkFrame(stats_frame)
            stats_row_frame.grid(row=i, column=0, sticky="ew", pady=5)
            stats_row_frame.grid_columnconfigure(0, weight=1)
            stats_row_frame.grid_columnconfigure(1, weight=1)
            stats_row_frame.grid_columnconfigure(2, weight=1)
            stats_row_frame.grid_columnconfigure(3, weight=1)
            
            # 添加数据
            ctk.CTkLabel(stats_row_frame, text=key[:20] + "...").grid(row=0, column=0, padx=5, pady=5)
            ctk.CTkLabel(stats_row_frame, text=str(stats.get("total_calls", 0))).grid(row=0, column=1, padx=5, pady=5)
            ctk.CTkLabel(stats_row_frame, text=str(stats.get("calls_today", 0))).grid(row=0, column=2, padx=5, pady=5)
            last_call = stats.get("last_call", "-").split('.')[0]
            ctk.CTkLabel(stats_row_frame, text=last_call).grid(row=0, column=3, padx=5, pady=5)

    def delete_api_key(self, api_key, console_window):
        """删除API Key"""
        # 从列表中删除
        self.api_keys = [key_info for key_info in self.api_keys if key_info['key'] != api_key]
        # 从统计数据中删除
        if api_key in self.api_key_stats:
            del self.api_key_stats[api_key]
        # 保存
        self.save_api_keys()
        self.save_api_key_stats()
        # 关闭并重新打开控制台
        console_window.destroy()
        self.open_api_key_console()
        # 显示消息
        self.add_message("system", "系统", f"已删除API Key")

    def test_api_key(self, api_key):
        """测试API Key"""
        # 创建测试窗口
        window = ctk.CTkToplevel(self.window)
        window.title("测试API Key")
        window.geometry("500x400")
        window.transient(self.window)
        window.grab_set()
        
        # 布局
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(2, weight=1)
        
        # API Key显示
        key_frame = ctk.CTkFrame(window)
        key_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(key_frame, text="API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(key_frame, text=api_key[:30] + "...").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 测试消息输入
        msg_frame = ctk.CTkFrame(window)
        msg_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(msg_frame, text="测试消息:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        test_message = ctk.CTkTextbox(msg_frame, height=100)
        test_message.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        test_message.insert("0.0", "你好，这是一个API Key测试消息")
        
        # 测试结果显示
        result_frame = ctk.CTkScrollableFrame(window)
        result_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        result_label = ctk.CTkLabel(
            result_frame,
            text="测试结果将显示在这里...",
            justify="left"
        )
        result_label.pack(padx=10, pady=10)
        
        # 测试按钮
        def run_test():
            message = test_message.get("0.0", "end-1c").strip()
            if not message:
                result_label.configure(text="错误: 测试消息不能为空")
                return
            
            result_label.configure(text="测试中...")
            
            try:
                # 构建测试请求
                import json
                import http.client
                
                # 连接本地API服务
                conn = http.client.HTTPConnection("localhost", self.api_server_port)
                
                # 构建请求数据
                data = {
                    "AccessKeyId": api_key,
                    "Message": message,
                    "Model": self.current_model
                }
                
                # 发送请求
                headers = {
                    "Content-Type": "application/json"
                }
                conn.request("POST", "/api/chat", json.dumps(data), headers)
                
                # 获取响应
                response = conn.getresponse()
                response_data = response.read().decode()
                conn.close()
                
                # 解析响应
                response_json = json.loads(response_data)
                
                if response.status == 200 and response_json.get("code") == 200:
                    result = response_json.get("data", {}).get("response", "")
                    result_label.configure(
                        text=f"测试成功!\n\n响应:\n{result}"
                    )
                else:
                    error_msg = response_json.get("message", "未知错误")
                    result_label.configure(
                        text=f"测试失败!\n\n错误: {error_msg}"
                    )
                    
            except Exception as e:
                result_label.configure(
                    text=f"测试失败!\n\n错误: {str(e)}"
                )
        
        test_btn = ctk.CTkButton(
            window,
            text="运行测试",
            command=run_test
        )
        test_btn.grid(row=3, column=0, padx=20, pady=20)

    def monitor_memory(self):
        """监控内存使用情况"""
        import psutil
        import time
        
        while True:
            try:
                # 获取当前进程的内存使用情况
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                
                # 检查内存使用率
                if memory_percent > self.max_memory_usage:
                    self.release_resources()
                    print(f"内存使用率过高 ({memory_percent:.2f}%%)，已释放部分资源")
                
                # 监控GPU内存使用情况
                if self.gpu_memory_check_enabled:
                    gpu_memory_percent = self.get_gpu_memory_usage()
                    if gpu_memory_percent > self.max_gpu_memory_usage:
                        self.release_resources()
                        print(f"GPU内存使用率过高 ({gpu_memory_percent:.2f}%%)，已释放部分资源")
            except Exception as e:
                print(f"内存监控错误: {str(e)}")
            
            # 等待下一次检查
            time.sleep(self.memory_check_interval)
    
    def get_gpu_memory_usage(self):
        """获取GPU内存使用情况"""
        try:
            # 尝试使用pynvml库
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                total_memory = 0
                used_memory = 0
                
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    total_memory += info.total
                    used_memory += info.used
                
                pynvml.nvmlShutdown()
                
                if total_memory > 0:
                    return (used_memory / total_memory) * 100
            except ImportError:
                # pynvml未安装，尝试使用nvidia-smi命令
                import subprocess
                import re
                
                result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total,memory.used', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    total_memory = 0
                    used_memory = 0
                    
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split(',')
                            if len(parts) == 2:
                                try:
                                    total = int(parts[0].strip())
                                    used = int(parts[1].strip())
                                    total_memory += total
                                    used_memory += used
                                except ValueError:
                                    pass
                    
                    if total_memory > 0:
                        return (used_memory / total_memory) * 100
        except Exception as e:
            print(f"GPU内存监控错误: {str(e)}")
        
        return 0

    def release_resources(self):
        """释放资源"""
        try:
            # 1. 清理不活跃的对话历史
            # 检查API Key的最后使用时间，清理长时间未使用的
            current_time = datetime.now()
            inactive_keys = []
            
            for api_key, stats in self.api_key_stats.items():
                last_call = stats.get("last_call")
                if last_call:
                    last_call_time = datetime.fromisoformat(last_call)
                    # 如果超过12小时未使用，清理对话历史
                    if (current_time - last_call_time).total_seconds() > 12 * 3600:
                        inactive_keys.append(api_key)
                else:
                    # 如果从未使用过，也清理
                    inactive_keys.append(api_key)
            
            # 清理不活跃的对话历史
            for api_key in inactive_keys:
                if api_key in self.conversation_histories:
                    del self.conversation_histories[api_key]
                    print(f"清理不活跃的API Key对话历史: {api_key}")
            
            # 2. 清理全局对话历史（更激进）
            if len(self.conversation_history) > 5:
                # 保留最近5轮对话
                from collections import deque
                new_history = deque(maxlen=self.max_history_rounds)
                # 复制最近的对话
                for msg in list(self.conversation_history)[-5:]:
                    new_history.append(msg)
                self.conversation_history = new_history
                print("清理全局对话历史，保留最近5轮")
            
            # 3. 清理所有对话历史（如果内存仍然紧张）
            # 这里可以根据实际情况调整触发条件
            
            # 4. 尝试清理Python垃圾回收
            import gc
            gc.collect()
            print("执行垃圾回收")
            
            # 5. 限制并发请求数（临时降低）
            # 注意：这只是临时措施，下次启动会恢复配置值
            if self.max_concurrent_requests > 3:
                self.max_concurrent_requests = 3
                # 重新初始化信号量
                import threading
                self.request_semaphore = threading.Semaphore(self.max_concurrent_requests)
                print("临时降低最大并发请求数到3")
                
        except Exception as e:
            print(f"释放资源错误: {str(e)}")

    def run(self):
        """运行应用"""
        self.window.mainloop()


if __name__ == "__main__":
    app = OllamaChatGUI()
    app.run()
