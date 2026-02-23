import socket
from typing import Optional
from .environment import EnvironmentConfig

class PortConfig:
    """端口配置管理"""
    
    # 默认端口配置
    DEFAULT_MAIN_SERVER_PORT = 48911
    DEFAULT_MEMORY_SERVER_PORT = 48912
    DEFAULT_MONITOR_SERVER_PORT = 48913
    DEFAULT_TOOL_SERVER_PORT = 48915
    
    @classmethod
    def get_main_server_port(cls) -> int:
        """获取主服务器端口
        
        Returns:
            主服务器端口
        """
        return EnvironmentConfig.get_int(
            EnvironmentConfig.MAIN_SERVER_PORT, 
            cls.DEFAULT_MAIN_SERVER_PORT
        )
    
    @classmethod
    def get_memory_server_port(cls) -> int:
        """获取记忆服务器端口
        
        Returns:
            记忆服务器端口
        """
        return EnvironmentConfig.get_int(
            EnvironmentConfig.MEMORY_SERVER_PORT, 
            cls.DEFAULT_MEMORY_SERVER_PORT
        )
    
    @classmethod
    def get_monitor_server_port(cls) -> int:
        """获取监控服务器端口
        
        Returns:
            监控服务器端口
        """
        return EnvironmentConfig.get_int(
            EnvironmentConfig.MONITOR_SERVER_PORT, 
            cls.DEFAULT_MONITOR_SERVER_PORT
        )
    
    @classmethod
    def get_tool_server_port(cls) -> int:
        """获取工具服务器端口
        
        Returns:
            工具服务器端口
        """
        return EnvironmentConfig.get_int(
            EnvironmentConfig.TOOL_SERVER_PORT, 
            cls.DEFAULT_TOOL_SERVER_PORT
        )
    
    @staticmethod
    def is_port_available(port: int) -> bool:
        """检查端口是否可用
        
        Args:
            port: 要检查的端口
            
        Returns:
            端口是否可用
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind(('localhost', port))
            return True
        except socket.error:
            return False
    
    @staticmethod
    def find_available_port(start_port: int, max_attempts: int = 100) -> Optional[int]:
        """查找可用端口
        
        Args:
            start_port: 起始端口
            max_attempts: 最大尝试次数
            
        Returns:
            可用端口或None
        """
        for port in range(start_port, start_port + max_attempts):
            if PortConfig.is_port_available(port):
                return port
        return None
    
    @classmethod
    def get_all_ports(cls) -> dict:
        """获取所有服务器端口配置
        
        Returns:
            端口配置字典
        """
        return {
            'main_server': cls.get_main_server_port(),
            'memory_server': cls.get_memory_server_port(),
            'monitor_server': cls.get_monitor_server_port(),
            'tool_server': cls.get_tool_server_port()
        }
    
    @classmethod
    def validate_ports(cls) -> bool:
        """验证所有端口配置
        
        Returns:
            端口配置是否有效
        """
        ports = cls.get_all_ports()
        all_available = True
        
        for server_name, port in ports.items():
            if not cls.is_port_available(port):
                print(f"警告: {server_name} 端口 {port} 已被占用")
                all_available = False
        
        return all_available
    
    @classmethod
    def set_ports(cls, main_port: int, memory_port: int, monitor_port: int, tool_port: int):
        """设置所有服务器端口
        
        Args:
            main_port: 主服务器端口
            memory_port: 记忆服务器端口
            monitor_port: 监控服务器端口
            tool_port: 工具服务器端口
        """
        EnvironmentConfig.set(EnvironmentConfig.MAIN_SERVER_PORT, str(main_port))
        EnvironmentConfig.set(EnvironmentConfig.MEMORY_SERVER_PORT, str(memory_port))
        EnvironmentConfig.set(EnvironmentConfig.MONITOR_SERVER_PORT, str(monitor_port))
        EnvironmentConfig.set(EnvironmentConfig.TOOL_SERVER_PORT, str(tool_port))
