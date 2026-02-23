import websocket
import json
import threading
import time
from typing import Optional, Callable, Dict, Any

class WebSocketClient:
    """WebSocket客户端，用于与服务器建立连接"""
    
    def __init__(self, url: str, on_message: Optional[Callable] = None, 
                 on_error: Optional[Callable] = None, 
                 on_close: Optional[Callable] = None, 
                 on_open: Optional[Callable] = None):
        """
        初始化WebSocket客户端
        
        Args:
            url: WebSocket服务器地址
            on_message: 消息接收回调函数
            on_error: 错误回调函数
            on_close: 连接关闭回调函数
            on_open: 连接打开回调函数
        """
        self.url = url
        self.ws = None
        self.connected = False
        self.reconnect_interval = 5  # 重连间隔（秒）
        self.max_reconnect_attempts = 10  # 最大重连次数
        self.reconnect_attempts = 0
        
        # 回调函数
        self.on_message = on_message or self.default_on_message
        self.on_error = on_error or self.default_on_error
        self.on_close = on_close or self.default_on_close
        self.on_open = on_open or self.default_on_open
        
        # 启动连接
        self.connect()
    
    def connect(self):
        """建立WebSocket连接"""
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # 启动WebSocket线程
            self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self.ws_thread.start()
        except Exception as e:
            print(f"WebSocket连接失败: {str(e)}")
            self._reconnect()
    
    def _on_message(self, ws, message):
        """消息接收处理"""
        try:
            # 尝试解析JSON消息
            data = json.loads(message)
            self.on_message(data)
        except json.JSONDecodeError:
            self.on_message(message)
    
    def _on_error(self, ws, error):
        """错误处理"""
        self.on_error(error)
        self._reconnect()
    
    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭处理"""
        self.connected = False
        self.on_close(close_status_code, close_msg)
        self._reconnect()
    
    def _on_open(self, ws):
        """连接打开处理"""
        self.connected = True
        self.reconnect_attempts = 0
        self.on_open()
    
    def _reconnect(self):
        """重连处理"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            print(f"尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
            time.sleep(self.reconnect_interval)
            self.connect()
        else:
            print("达到最大重连次数，停止重连")
    
    def send(self, message: Dict[str, Any]):
        """发送消息
        
        Args:
            message: 要发送的消息字典
        """
        if self.connected and self.ws:
            try:
                json_message = json.dumps(message)
                self.ws.send(json_message)
                return True
            except Exception as e:
                print(f"发送消息失败: {str(e)}")
                return False
        return False
    
    def close(self):
        """关闭WebSocket连接"""
        if self.ws:
            self.ws.close()
            self.connected = False
    
    # 默认回调函数
    def default_on_message(self, message):
        """默认消息接收回调"""
        print(f"收到消息: {message}")
    
    def default_on_error(self, error):
        """默认错误回调"""
        print(f"WebSocket错误: {str(error)}")
    
    def default_on_close(self, close_status_code, close_msg):
        """默认连接关闭回调"""
        print(f"WebSocket连接关闭: {close_status_code} - {close_msg}")
    
    def default_on_open(self):
        """默认连接打开回调"""
        print(f"WebSocket连接已打开: {self.url}")
