import threading
import time
import psutil
from communication.websocket_server import WebSocketServer
from config.ports import PortConfig

class MonitorServer:
    """监控服务器，负责监控系统状态和提供多端同步功能"""
    
    def __init__(self):
        """初始化监控服务器"""
        self.port = PortConfig.get_monitor_server_port()
        self.websocket_server = None
        self.running = False
        self.connected_clients = []
        self.system_stats = {}
        self.server_status = {}
        
        # 启动系统监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_system(self):
        """监控系统状态"""
        while True:
            try:
                # 获取CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # 获取内存使用情况
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used = memory.used / 1024 / 1024 / 1024  # GB
                memory_total = memory.total / 1024 / 1024 / 1024  # GB
                
                # 获取磁盘使用情况
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                disk_used = disk.used / 1024 / 1024 / 1024  # GB
                disk_total = disk.total / 1024 / 1024 / 1024  # GB
                
                # 获取网络使用情况
                net_io = psutil.net_io_counters()
                net_sent = net_io.bytes_sent / 1024 / 1024  # MB
                net_recv = net_io.bytes_recv / 1024 / 1024  # MB
                
                # 更新系统状态
                self.system_stats = {
                    'cpu': {
                        'percent': cpu_percent
                    },
                    'memory': {
                        'percent': memory_percent,
                        'used': round(memory_used, 2),
                        'total': round(memory_total, 2)
                    },
                    'disk': {
                        'percent': disk_percent,
                        'used': round(disk_used, 2),
                        'total': round(disk_total, 2)
                    },
                    'network': {
                        'sent': round(net_sent, 2),
                        'recv': round(net_recv, 2)
                    },
                    'timestamp': time.time(),
                    'datetime': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 每5秒更新一次
                time.sleep(5)
            except Exception as e:
                print(f"系统监控错误: {str(e)}")
                time.sleep(5)
    
    def start(self):
        """启动监控服务器"""
        if self.running:
            print("监控服务器已经在运行中")
            return
        
        self.running = True
        
        # 启动WebSocket服务器
        self.websocket_server = WebSocketServer('0.0.0.0', self.port)
        self.websocket_server.on_message = self._on_websocket_message
        self.websocket_server.on_client_connect = self._on_client_connect
        self.websocket_server.on_client_disconnect = self._on_client_disconnect
        self.websocket_server.start()
        
        print(f"监控服务器启动成功，端口: {self.port}")
        
        # 启动状态广播线程
        self.broadcast_thread = threading.Thread(target=self._broadcast_status, daemon=True)
        self.broadcast_thread.start()
    
    def stop(self):
        """停止监控服务器"""
        if not self.running:
            print("监控服务器未运行")
            return
        
        self.running = False
        
        # 停止WebSocket服务器
        if self.websocket_server:
            self.websocket_server.stop()
        
        # 清理客户端连接
        self.connected_clients.clear()
        
        print("监控服务器已停止")
    
    def _on_client_connect(self, client):
        """客户端连接处理"""
        self.connected_clients.append(client)
        print(f"客户端连接: {client}")
        
        # 发送当前系统状态
        self.websocket_server.send_to_client(
            client, 
            {'type': 'system_status', 'status': self.system_stats}
        )
    
    def _on_client_disconnect(self, client):
        """客户端断开连接处理"""
        if client in self.connected_clients:
            self.connected_clients.remove(client)
        print(f"客户端断开连接: {client}")
    
    def _on_websocket_message(self, client, message):
        """处理WebSocket消息"""
        print(f"监控服务器收到消息: {message}")
        
        try:
            if isinstance(message, dict):
                message_type = message.get('type')
                
                if message_type == 'get_system_status':
                    # 返回系统状态
                    self.websocket_server.send_to_client(
                        client, 
                        {'type': 'system_status', 'status': self.system_stats}
                    )
                
                elif message_type == 'get_server_status':
                    # 返回服务器状态
                    self.websocket_server.send_to_client(
                        client, 
                        {'type': 'server_status', 'status': self.server_status}
                    )
                
                elif message_type == 'sync_data':
                    # 处理同步数据
                    data = message.get('data')
                    if data:
                        # 广播同步数据给其他客户端
                        self.broadcast_sync_data(data, exclude_client=client)
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'sync_data_response', 'success': True}
                        )
                    else:
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'sync_data_response', 'success': False, 'error': 'Missing data'}
                        )
        except Exception as e:
            self.websocket_server.send_to_client(
                client, 
                {'type': 'error', 'message': str(e)}
            )
    
    def _broadcast_status(self):
        """广播系统状态"""
        while self.running:
            # 每10秒广播一次系统状态
            time.sleep(10)
            
            if self.running and self.connected_clients:
                try:
                    # 广播系统状态
                    self.websocket_server.send_to_all(
                        {'type': 'system_status', 'status': self.system_stats}
                    )
                except Exception as e:
                    print(f"广播系统状态错误: {str(e)}")
    
    def broadcast_sync_data(self, data, exclude_client=None):
        """广播同步数据
        
        Args:
            data: 要同步的数据
            exclude_client: 排除的客户端
        """
        if not self.running:
            return
        
        try:
            # 广播同步数据
            self.websocket_server.broadcast(
                {'type': 'sync_data', 'data': data}, 
                exclude_client=exclude_client
            )
        except Exception as e:
            print(f"广播同步数据错误: {str(e)}")
    
    def update_server_status(self, server_name: str, status: dict):
        """更新服务器状态
        
        Args:
            server_name: 服务器名称
            status: 服务器状态
        """
        self.server_status[server_name] = {
            **status,
            'last_updated': time.time(),
            'last_updated_datetime': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 广播服务器状态更新
        if self.running and self.connected_clients:
            try:
                self.websocket_server.send_to_all(
                    {'type': 'server_status', 'status': self.server_status}
                )
            except Exception as e:
                print(f"广播服务器状态错误: {str(e)}")
    
    def get_system_status(self):
        """获取系统状态
        
        Returns:
            系统状态字典
        """
        return self.system_stats
    
    def get_server_status(self):
        """获取服务器状态
        
        Returns:
            服务器状态字典
        """
        return self.server_status
