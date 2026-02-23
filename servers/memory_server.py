import threading
import time
import json
import os
from communication.websocket_server import WebSocketServer
from config.ports import PortConfig

class MemoryServer:
    """记忆服务器，负责存储和管理对话历史"""
    
    def __init__(self):
        """初始化记忆服务器"""
        self.port = PortConfig.get_memory_server_port()
        self.websocket_server = None
        self.running = False
        self.memory_store = {}
        self.memory_file = "memory_store.json"
        
        # 加载记忆数据
        self.load_memory()
    
    def load_memory(self):
        """从文件加载记忆数据"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory_store = json.load(f)
                print(f"已加载 {len(self.memory_store)} 条记忆数据")
        except Exception as e:
            print(f"加载记忆数据失败: {str(e)}")
            self.memory_store = {}
    
    def save_memory(self):
        """保存记忆数据到文件"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_store, f, ensure_ascii=False, indent=2)
            print(f"已保存 {len(self.memory_store)} 条记忆数据")
        except Exception as e:
            print(f"保存记忆数据失败: {str(e)}")
    
    def start(self):
        """启动记忆服务器"""
        if self.running:
            print("记忆服务器已经在运行中")
            return
        
        self.running = True
        
        # 启动WebSocket服务器
        self.websocket_server = WebSocketServer('0.0.0.0', self.port)
        self.websocket_server.on_message = self._on_websocket_message
        self.websocket_server.start()
        
        print(f"记忆服务器启动成功，端口: {self.port}")
        
        # 启动定期保存任务
        self.save_thread = threading.Thread(target=self._periodic_save, daemon=True)
        self.save_thread.start()
    
    def stop(self):
        """停止记忆服务器"""
        if not self.running:
            print("记忆服务器未运行")
            return
        
        self.running = False
        
        # 停止WebSocket服务器
        if self.websocket_server:
            self.websocket_server.stop()
        
        # 保存记忆数据
        self.save_memory()
        
        print("记忆服务器已停止")
    
    def _periodic_save(self):
        """定期保存记忆数据"""
        while self.running:
            time.sleep(60)  # 每分钟保存一次
            if self.running:
                self.save_memory()
    
    def _on_websocket_message(self, client, message):
        """处理WebSocket消息"""
        print(f"记忆服务器收到消息: {message}")
        
        try:
            if isinstance(message, dict):
                message_type = message.get('type')
                
                if message_type == 'store_memory':
                    # 存储记忆
                    user_id = message.get('user_id')
                    memory = message.get('memory')
                    if user_id and memory:
                        self.store_memory(user_id, memory)
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'store_memory_response', 'success': True}
                        )
                    else:
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'store_memory_response', 'success': False, 'error': 'Missing user_id or memory'}
                        )
                
                elif message_type == 'retrieve_memory':
                    # 检索记忆
                    user_id = message.get('user_id')
                    query = message.get('query', '')
                    limit = message.get('limit', 5)
                    
                    memories = self.retrieve_memory(user_id, query, limit)
                    self.websocket_server.send_to_client(
                        client, 
                        {'type': 'retrieve_memory_response', 'memories': memories}
                    )
                
                elif message_type == 'clear_memory':
                    # 清除记忆
                    user_id = message.get('user_id')
                    if user_id:
                        self.clear_memory(user_id)
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'clear_memory_response', 'success': True}
                        )
                    else:
                        self.websocket_server.send_to_client(
                            client, 
                            {'type': 'clear_memory_response', 'success': False, 'error': 'Missing user_id'}
                        )
                
                elif message_type == 'get_memory_stats':
                    # 获取记忆统计
                    stats = self.get_memory_stats()
                    self.websocket_server.send_to_client(
                        client, 
                        {'type': 'get_memory_stats_response', 'stats': stats}
                    )
        except Exception as e:
            self.websocket_server.send_to_client(
                client, 
                {'type': 'error', 'message': str(e)}
            )
    
    def store_memory(self, user_id: str, memory: dict):
        """存储记忆
        
        Args:
            user_id: 用户ID
            memory: 记忆数据字典
        """
        if user_id not in self.memory_store:
            self.memory_store[user_id] = []
        
        # 添加时间戳
        memory['timestamp'] = time.time()
        memory['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 存储记忆
        self.memory_store[user_id].append(memory)
        
        # 限制每个用户的记忆数量
        max_memories_per_user = 1000
        if len(self.memory_store[user_id]) > max_memories_per_user:
            self.memory_store[user_id] = self.memory_store[user_id][-max_memories_per_user:]
    
    def retrieve_memory(self, user_id: str, query: str = '', limit: int = 5):
        """检索记忆
        
        Args:
            user_id: 用户ID
            query: 检索查询
            limit: 返回数量限制
            
        Returns:
            记忆列表
        """
        if user_id not in self.memory_store:
            return []
        
        memories = self.memory_store[user_id]
        
        # 如果有查询，进行简单的关键词匹配
        if query:
            query_lower = query.lower()
            filtered_memories = []
            
            for memory in memories:
                # 检查记忆内容是否包含查询关键词
                content = str(memory.get('content', '')).lower()
                if query_lower in content:
                    filtered_memories.append(memory)
            
            memories = filtered_memories
        
        # 按时间戳排序，返回最新的
        memories.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return memories[:limit]
    
    def clear_memory(self, user_id: str):
        """清除用户记忆
        
        Args:
            user_id: 用户ID
        """
        if user_id in self.memory_store:
            del self.memory_store[user_id]
    
    def get_memory_stats(self):
        """获取记忆统计信息
        
        Returns:
            统计信息字典
        """
        total_memories = 0
        user_counts = {}
        
        for user_id, memories in self.memory_store.items():
            count = len(memories)
            total_memories += count
            user_counts[user_id] = count
        
        return {
            'total_users': len(self.memory_store),
            'total_memories': total_memories,
            'user_counts': user_counts
        }
