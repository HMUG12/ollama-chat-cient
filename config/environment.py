import os
from typing import Dict, Optional

class EnvironmentConfig:
    """环境变量配置管理"""
    
    # 服务器端口环境变量
    MAIN_SERVER_PORT = "NEKO_MAIN_SERVER_PORT"
    MEMORY_SERVER_PORT = "NEKO_MEMORY_SERVER_PORT"
    MONITOR_SERVER_PORT = "NEKO_MONITOR_SERVER_PORT"
    TOOL_SERVER_PORT = "NEKO_TOOL_SERVER_PORT"
    
    # API配置环境变量
    CORE_API_KEY = "NEKO_CORE_API_KEY"
    CORE_API = "NEKO_CORE_API"
    ASSIST_API = "NEKO_ASSIST_API"
    ASSIST_API_KEY_QWEN = "NEKO_ASSIST_API_KEY_QWEN"
    ASSIST_API_KEY_OPENAI = "NEKO_ASSIST_API_KEY_OPENAI"
    ASSIST_API_KEY_GLM = "NEKO_ASSIST_API_KEY_GLM"
    ASSIST_API_KEY_STEP = "NEKO_ASSIST_API_KEY_STEP"
    ASSIST_API_KEY_SILICON = "NEKO_ASSIST_API_KEY_SILICON"
    MCP_TOKEN = "NEKO_MCP_TOKEN"
    
    # 模型配置环境变量
    SUMMARY_MODEL = "NEKO_SUMMARY_MODEL"
    CORRECTION_MODEL = "NEKO_CORRECTION_MODEL"
    EMOTION_MODEL = "NEKO_EMOTION_MODEL"
    VISION_MODEL = "NEKO_VISION_MODEL"
    
    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量值
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            环境变量值或默认值
        """
        return os.environ.get(key, default)
    
    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """获取整型环境变量值
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            整型环境变量值或默认值
        """
        try:
            value = os.environ.get(key)
            if value is not None:
                return int(value)
        except ValueError:
            pass
        return default
    
    @classmethod
    def set(cls, key: str, value: str):
        """设置环境变量值
        
        Args:
            key: 环境变量名
            value: 环境变量值
        """
        os.environ[key] = value
    
    @classmethod
    def get_all(cls) -> Dict[str, str]:
        """获取所有相关环境变量
        
        Returns:
            环境变量字典
        """
        env_vars = {}
        
        # 服务器端口
        env_vars[cls.MAIN_SERVER_PORT] = cls.get(cls.MAIN_SERVER_PORT)
        env_vars[cls.MEMORY_SERVER_PORT] = cls.get(cls.MEMORY_SERVER_PORT)
        env_vars[cls.MONITOR_SERVER_PORT] = cls.get(cls.MONITOR_SERVER_PORT)
        env_vars[cls.TOOL_SERVER_PORT] = cls.get(cls.TOOL_SERVER_PORT)
        
        # API配置
        env_vars[cls.CORE_API_KEY] = cls.get(cls.CORE_API_KEY)
        env_vars[cls.CORE_API] = cls.get(cls.CORE_API)
        env_vars[cls.ASSIST_API] = cls.get(cls.ASSIST_API)
        env_vars[cls.ASSIST_API_KEY_QWEN] = cls.get(cls.ASSIST_API_KEY_QWEN)
        env_vars[cls.ASSIST_API_KEY_OPENAI] = cls.get(cls.ASSIST_API_KEY_OPENAI)
        env_vars[cls.ASSIST_API_KEY_GLM] = cls.get(cls.ASSIST_API_KEY_GLM)
        env_vars[cls.ASSIST_API_KEY_STEP] = cls.get(cls.ASSIST_API_KEY_STEP)
        env_vars[cls.ASSIST_API_KEY_SILICON] = cls.get(cls.ASSIST_API_KEY_SILICON)
        env_vars[cls.MCP_TOKEN] = cls.get(cls.MCP_TOKEN)
        
        # 模型配置
        env_vars[cls.SUMMARY_MODEL] = cls.get(cls.SUMMARY_MODEL)
        env_vars[cls.CORRECTION_MODEL] = cls.get(cls.CORRECTION_MODEL)
        env_vars[cls.EMOTION_MODEL] = cls.get(cls.EMOTION_MODEL)
        env_vars[cls.VISION_MODEL] = cls.get(cls.VISION_MODEL)
        
        return env_vars
    
    @classmethod
    def load_from_file(cls, file_path: str):
        """从文件加载环境变量
        
        Args:
            file_path: 环境变量文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            cls.set(key, value)
        except Exception as e:
            print(f"加载环境变量文件失败: {str(e)}")
    
    @classmethod
    def save_to_file(cls, file_path: str):
        """保存环境变量到文件
        
        Args:
            file_path: 环境变量文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# NOKE环境变量配置\n\n")
                
                # 服务器端口
                f.write("# 服务器端口配置\n")
                f.write(f"{cls.MAIN_SERVER_PORT}={cls.get(cls.MAIN_SERVER_PORT, '')}\n")
                f.write(f"{cls.MEMORY_SERVER_PORT}={cls.get(cls.MEMORY_SERVER_PORT, '')}\n")
                f.write(f"{cls.MONITOR_SERVER_PORT}={cls.get(cls.MONITOR_SERVER_PORT, '')}\n")
                f.write(f"{cls.TOOL_SERVER_PORT}={cls.get(cls.TOOL_SERVER_PORT, '')}\n\n")
                
                # API配置
                f.write("# API配置\n")
                f.write(f"{cls.CORE_API_KEY}={cls.get(cls.CORE_API_KEY, '')}\n")
                f.write(f"{cls.CORE_API}={cls.get(cls.CORE_API, '')}\n")
                f.write(f"{cls.ASSIST_API}={cls.get(cls.ASSIST_API, '')}\n")
                f.write(f"{cls.ASSIST_API_KEY_QWEN}={cls.get(cls.ASSIST_API_KEY_QWEN, '')}\n")
                f.write(f"{cls.ASSIST_API_KEY_OPENAI}={cls.get(cls.ASSIST_API_KEY_OPENAI, '')}\n")
                f.write(f"{cls.ASSIST_API_KEY_GLM}={cls.get(cls.ASSIST_API_KEY_GLM, '')}\n")
                f.write(f"{cls.ASSIST_API_KEY_STEP}={cls.get(cls.ASSIST_API_KEY_STEP, '')}\n")
                f.write(f"{cls.ASSIST_API_KEY_SILICON}={cls.get(cls.ASSIST_API_KEY_SILICON, '')}\n")
                f.write(f"{cls.MCP_TOKEN}={cls.get(cls.MCP_TOKEN, '')}\n\n")
                
                # 模型配置
                f.write("# 模型配置\n")
                f.write(f"{cls.SUMMARY_MODEL}={cls.get(cls.SUMMARY_MODEL, '')}\n")
                f.write(f"{cls.CORRECTION_MODEL}={cls.get(cls.CORRECTION_MODEL, '')}\n")
                f.write(f"{cls.EMOTION_MODEL}={cls.get(cls.EMOTION_MODEL, '')}\n")
                f.write(f"{cls.VISION_MODEL}={cls.get(cls.VISION_MODEL, '')}\n")
        except Exception as e:
            print(f"保存环境变量文件失败: {str(e)}")
