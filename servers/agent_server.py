import threading
import time
from communication.websocket_server import WebSocketServer
from communication.websocket_client import WebSocketClient
from config.ports import PortConfig
from config.environment import EnvironmentConfig

class AgentServer:
    """智能体服务器，负责处理AI模型调用和智能体功能"""
    
    def __init__(self):
        """初始化智能体服务器"""
        self.port = PortConfig.get_tool_server_port()
        self.websocket_server = None
        self.running = False
        self.connected_clients = []
        self.available_models = []
        
        # 初始化可用模型
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化可用模型列表"""
        # 从环境变量获取模型配置
        summary_model = EnvironmentConfig.get(EnvironmentConfig.SUMMARY_MODEL, "qwen-plus")
        correction_model = EnvironmentConfig.get(EnvironmentConfig.CORRECTION_MODEL, "qwen-max")
        emotion_model = EnvironmentConfig.get(EnvironmentConfig.EMOTION_MODEL, "qwen-turbo")
        vision_model = EnvironmentConfig.get(EnvironmentConfig.VISION_MODEL, "qwen3-vl-plus-2025-09-23")
        
        # 构建模型列表
        self.available_models = [
            summary_model,
            correction_model,
            emotion_model,
            vision_model,
            "llama2",
            "mistral",
            "codellama"
        ]
        
        # 去重
        self.available_models = list(set(self.available_models))
    
    def start(self):
        """启动智能体服务器"""
        if self.running:
            print("智能体服务器已经在运行中")
            return
        
        self.running = True
        
        # 启动WebSocket服务器
        self.websocket_server = WebSocketServer('0.0.0.0', self.port)
        self.websocket_server.on_message = self._on_websocket_message
        self.websocket_server.on_client_connect = self._on_client_connect
        self.websocket_server.on_client_disconnect = self._on_client_disconnect
        self.websocket_server.start()
        
        print(f"智能体服务器启动成功，端口: {self.port}")
        print(f"可用模型: {self.available_models}")
    
    def stop(self):
        """停止智能体服务器"""
        if not self.running:
            print("智能体服务器未运行")
            return
        
        self.running = False
        
        # 停止WebSocket服务器
        if self.websocket_server:
            self.websocket_server.stop()
        
        # 清理客户端连接
        self.connected_clients.clear()
        
        print("智能体服务器已停止")
    
    def _on_client_connect(self, client):
        """客户端连接处理"""
        self.connected_clients.append(client)
        print(f"客户端连接: {client}")
    
    def _on_client_disconnect(self, client):
        """客户端断开连接处理"""
        if client in self.connected_clients:
            self.connected_clients.remove(client)
        print(f"客户端断开连接: {client}")
    
    def _on_websocket_message(self, client, message):
        """处理WebSocket消息"""
        print(f"智能体服务器收到消息: {message}")
        
        try:
            if isinstance(message, dict):
                message_type = message.get('type')
                
                if message_type == 'get_models':
                    # 返回可用模型列表
                    self.websocket_server.send_to_client(
                        client, 
                        {'type': 'get_models_response', 'models': self.available_models}
                    )
                
                elif message_type == 'chat_completion':
                    # 处理聊天完成请求
                    model = message.get('model', self.available_models[0])
                    messages = message.get('messages', [])
                    
                    if messages:
                        response = self.generate_response(model, messages)
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'chat_completion_response', 'response': response}
                        )
                    else:
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'error', 'message': 'Missing messages'}
                        )
                
                elif message_type == 'summarize':
                    # 处理摘要请求
                    text = message.get('text', '')
                    if text:
                        summary = self.summarize_text(text)
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'summarize_response', 'summary': summary}
                        )
                    else:
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'error', 'message': 'Missing text'}
                        )
                
                elif message_type == 'analyze_emotion':
                    # 处理情感分析请求
                    text = message.get('text', '')
                    if text:
                        emotion = self.analyze_emotion(text)
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'analyze_emotion_response', 'emotion': emotion}
                        )
                    else:
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'error', 'message': 'Missing text'}
                        )
        except Exception as e:
            self.websocket_server.send_to_client(
                client, 
                {'type': 'error', 'message': str(e)}
            )
    
    def generate_response(self, model: str, messages: list):
        """生成AI响应
        
        Args:
            model: 模型名称
            messages: 消息列表
            
        Returns:
            AI响应文本
        """
        # 这里是生成响应的逻辑
        # 实际应用中，应该调用真实的AI模型API
        
        # 简单的模拟响应
        user_message = ""
        for msg in messages:
            if msg.get('role') == 'user':
                user_message = msg.get('content', '')
                break
        
        response = f"智能体服务器 ({model}) 响应: 你说的是 '{user_message}'"
        return response
    
    def summarize_text(self, text: str):
        """文本摘要
        
        Args:
            text: 要摘要的文本
            
        Returns:
            摘要文本
        """
        # 简单的摘要逻辑
        # 实际应用中，应该使用专门的摘要模型
        
        # 限制摘要长度
        max_length = 100
        if len(text) <= max_length:
            return text
        
        # 简单截取开头和结尾
        summary = text[:max_length // 2] + "... " + text[-max_length // 2:]
        return summary
    
    def analyze_emotion(self, text: str):
        """情感分析
        
        Args:
            text: 要分析的文本
            
        Returns:
            情感分析结果
        """
        # 简单的情感分析逻辑
        # 实际应用中，应该使用专门的情感分析模型
        
        # 关键词匹配
        positive_words = ['好', '棒', '优秀', '喜欢', '满意', '高兴', '开心', '快乐']
        negative_words = ['坏', '差', '糟糕', '讨厌', '不满意', '难过', '伤心', '生气']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            emotion = 'positive'
        elif negative_count > positive_count:
            emotion = 'negative'
        else:
            emotion = 'neutral'
        
        return {
            'emotion': emotion,
            'positive_score': positive_count,
            'negative_score': negative_count
        }
    
    def get_available_models(self):
        """获取可用模型列表
        
        Returns:
            模型列表
        """
        return self.available_models
