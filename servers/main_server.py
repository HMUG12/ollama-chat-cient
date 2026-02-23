import threading
import time
from flask import Flask, request, jsonify
from communication.websocket_server import WebSocketServer
from communication.websocket_client import WebSocketClient
from config.ports import PortConfig
from config.environment import EnvironmentConfig

class MainServer:
    """主服务器，负责处理客户端请求和管理与其他服务器的通信"""
    
    def __init__(self):
        """初始化主服务器"""
        self.port = PortConfig.get_main_server_port()
        self.flask_app = Flask(__name__)
        self.websocket_server = None
        self.running = False
        self.connected_servers = {}
        
        # 初始化Flask路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置Flask路由"""
        @self.flask_app.route('/api/chat', methods=['POST'])
        def chat():
            """处理聊天请求"""
            try:
                data = request.json
                message = data.get('message')
                model = data.get('model')
                
                if not message:
                    return jsonify({'error': 'Missing message'}), 400
                
                # 处理消息并返回响应
                response = self.process_message(message, model)
                return jsonify({'response': response})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/models', methods=['GET'])
        def get_models():
            """获取可用模型列表"""
            try:
                models = self.get_available_models()
                return jsonify({'models': models})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/status', methods=['GET'])
        def get_status():
            """获取服务器状态"""
            try:
                status = self.get_status()
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start(self):
        """启动主服务器"""
        if self.running:
            print("主服务器已经在运行中")
            return
        
        self.running = True
        
        # 启动WebSocket服务器
        self.websocket_server = WebSocketServer('0.0.0.0', self.port)
        self.websocket_server.on_message = self._on_websocket_message
        self.websocket_server.start()
        
        # 启动Flask服务器
        self.flask_thread = threading.Thread(
            target=self.flask_app.run,
            kwargs={'host': '0.0.0.0', 'port': self.port + 1, 'debug': False, 'use_reloader': False},
            daemon=True
        )
        self.flask_thread.start()
        
        print(f"主服务器启动成功，WebSocket端口: {self.port}, HTTP端口: {self.port + 1}")
        
        # 连接其他服务器
        self.connect_to_other_servers()
    
    def stop(self):
        """停止主服务器"""
        if not self.running:
            print("主服务器未运行")
            return
        
        self.running = False
        
        # 停止WebSocket服务器
        if self.websocket_server:
            self.websocket_server.stop()
        
        # 断开与其他服务器的连接
        for server_name, client in self.connected_servers.items():
            try:
                client.close()
            except:
                pass
        self.connected_servers.clear()
        
        print("主服务器已停止")
    
    def connect_to_other_servers(self):
        """连接到其他服务器"""
        # 连接记忆服务器
        memory_port = PortConfig.get_memory_server_port()
        memory_ws_url = f"ws://localhost:{memory_port}"
        self.connected_servers['memory'] = WebSocketClient(
            memory_ws_url,
            on_message=self._on_memory_server_message,
            on_open=lambda: print(f"已连接到记忆服务器: {memory_ws_url}")
        )
        
        # 连接智能体服务器
        # 注意：智能体服务器端口需要根据实际配置调整
        agent_port = PortConfig.get_tool_server_port()
        agent_ws_url = f"ws://localhost:{agent_port}"
        self.connected_servers['agent'] = WebSocketClient(
            agent_ws_url,
            on_message=self._on_agent_server_message,
            on_open=lambda: print(f"已连接到智能体服务器: {agent_ws_url}")
        )
        
        # 连接监控服务器
        monitor_port = PortConfig.get_monitor_server_port()
        monitor_ws_url = f"ws://localhost:{monitor_port}"
        self.connected_servers['monitor'] = WebSocketClient(
            monitor_ws_url,
            on_message=self._on_monitor_server_message,
            on_open=lambda: print(f"已连接到监控服务器: {monitor_ws_url}")
        )
    
    def _on_websocket_message(self, client, message):
        """处理WebSocket消息"""
        print(f"收到WebSocket消息: {message}")
        
        # 处理消息并发送响应
        try:
            if isinstance(message, dict):
                message_type = message.get('type')
                if message_type == 'chat':
                    response = self.process_message(message.get('content'), message.get('model'))
                    self.websocket_server.send_to_client(client, {'type': 'chat_response', 'content': response})
                elif message_type == 'get_models':
                    models = self.get_available_models()
                    self.websocket_server.send_to_client(client, {'type': 'models_response', 'models': models})
                elif message_type == 'status':
                    status = self.get_server_status()
                    self.websocket_server.send_to_client(client, {'type': 'status_response', 'status': status})
        except Exception as e:
            self.websocket_server.send_to_client(client, {'type': 'error', 'message': str(e)})
    
    def _on_memory_server_message(self, message):
        """处理来自记忆服务器的消息"""
        print(f"收到记忆服务器消息: {message}")
    
    def _on_agent_server_message(self, message):
        """处理来自智能体服务器的消息"""
        print(f"收到智能体服务器消息: {message}")
    
    def _on_monitor_server_message(self, message):
        """处理来自监控服务器的消息"""
        print(f"收到监控服务器消息: {message}")
    
    def process_message(self, message, model=None):
        """处理聊天消息
        
        Args:
            message: 聊天消息内容
            model: 要使用的模型
            
        Returns:
            处理后的响应
        """
        # 这里是消息处理逻辑
        # 实际应用中，应该将消息发送给智能体服务器处理
        return f"主服务器收到消息: {message}"
    
    def get_available_models(self):
        """获取可用模型列表
        
        Returns:
            模型列表
        """
        # 这里应该从智能体服务器获取模型列表
        return ["llama2", "mistral", "codellama"]
    
    def get_server_status(self):
        """获取服务器状态
        
        Returns:
            服务器状态字典
        """
        return {
            'running': self.running,
            'port': self.port,
            'connected_servers': list(self.connected_servers.keys()),
            'timestamp': time.time()
        }
