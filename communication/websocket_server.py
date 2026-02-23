import websocket
import json
import threading
import time
from typing import Dict, Any, List, Callable

class WebSocketServer:
    """WebSocket服务器，用于处理客户端连接和消息"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8765):
        """
        初始化WebSocket服务器
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
        """
        self.host = host
        self.port = port
        self.server = None
        self.clients: List[websocket.WebSocket] = []
        self.clients_lock = threading.Lock()
        self.running = False
        
        # 回调函数
        self.on_client_connect = self.default_on_client_connect
        self.on_client_disconnect = self.default_on_client_disconnect
        self.on_message = self.default_on_message
    
    def start(self):
        """启动WebSocket服务器"""
        if self.running:
            print("服务器已经在运行中")
            return
        
        self.running = True
        
        # 启动服务器线程
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        
        print(f"WebSocket服务器启动在 ws://{self.host}:{self.port}")
    
    def _run_server(self):
        """运行WebSocket服务器"""
        try:
            # 创建WebSocket服务器
            from websocket import WebSocketServer as WSServer
            
            def new_client(client, server):
                """新客户端连接处理"""
                with self.clients_lock:
                    self.clients.append(client)
                self.on_client_connect(client)
            
            def client_left(client, server):
                """客户端断开连接处理"""
                with self.clients_lock:
                    if client in self.clients:
                        self.clients.remove(client)
                self.on_client_disconnect(client)
            
            def message_received(client, server, message):
                """消息接收处理"""
                try:
                    # 尝试解析JSON消息
                    data = json.loads(message)
                    self.on_message(client, data)
                except json.JSONDecodeError:
                    self.on_message(client, message)
            
            # 创建并启动服务器
            self.server = WSServer(
                host=self.host,
                port=self.port,
                new_client=new_client,
                client_left=client_left,
                message_received=message_received
            )
            
            # 运行服务器
            self.server.run_forever()
        except ImportError:
            print("错误: websocket-server库未安装")
            print("请运行: pip install websocket-server")
            self.running = False
        except Exception as e:
            print(f"WebSocket服务器错误: {str(e)}")
            self.running = False
    
    def stop(self):
        """停止WebSocket服务器"""
        if not self.running:
            print("服务器未运行")
            return
        
        self.running = False
        
        if self.server:
            self.server.shutdown_gracefully()
        
        # 清理客户端连接
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        print("WebSocket服务器已停止")
    
    def send_to_all(self, message: Dict[str, Any]):
        """向所有客户端发送消息
        
        Args:
            message: 要发送的消息字典
        """
        if not self.running:
            return
        
        try:
            json_message = json.dumps(message)
            with self.clients_lock:
                for client in self.clients:
                    try:
                        self.server.send_message(client, json_message)
                    except Exception as e:
                        print(f"发送消息失败: {str(e)}")
        except Exception as e:
            print(f"消息序列化失败: {str(e)}")
    
    def send_to_client(self, client, message: Dict[str, Any]):
        """向指定客户端发送消息
        
        Args:
            client: 客户端连接
            message: 要发送的消息字典
        """
        if not self.running:
            return
        
        try:
            json_message = json.dumps(message)
            self.server.send_message(client, json_message)
        except Exception as e:
            print(f"发送消息失败: {str(e)}")
    
    def broadcast(self, message: Dict[str, Any], exclude_client=None):
        """广播消息给除指定客户端外的所有客户端
        
        Args:
            message: 要发送的消息字典
            exclude_client: 要排除的客户端
        """
        if not self.running:
            return
        
        try:
            json_message = json.dumps(message)
            with self.clients_lock:
                for client in self.clients:
                    if client != exclude_client:
                        try:
                            self.server.send_message(client, json_message)
                        except Exception as e:
                            print(f"发送消息失败: {str(e)}")
        except Exception as e:
            print(f"消息序列化失败: {str(e)}")
    
    # 默认回调函数
    def default_on_client_connect(self, client):
        """默认客户端连接回调"""
        print(f"客户端连接: {client}")
    
    def default_on_client_disconnect(self, client):
        """默认客户端断开连接回调"""
        print(f"客户端断开连接: {client}")
    
    def default_on_message(self, client, message):
        """默认消息接收回调"""
        print(f"收到消息: {message}")
