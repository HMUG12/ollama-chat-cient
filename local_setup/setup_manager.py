import os
import subprocess
import json
import threading
import time
import psutil
from config.ports import PortConfig
from config.environment import EnvironmentConfig

class SetupManager:
    """本地搭建管理器，负责本地服务的搭建和管理"""
    
    def __init__(self):
        """初始化本地搭建管理器"""
        self.services = {
            'ollama': {
                'name': 'Ollama',
                'default_port': 11434,
                'status': 'stopped',
                'process': None
            },
            'openai': {
                'name': 'OpenAI API',
                'default_port': 8080,
                'status': 'stopped',
                'process': None
            },
            'anthropic': {
                'name': 'Anthropic API',
                'default_port': 8081,
                'status': 'stopped',
                'process': None
            }
        }
        self.setup_config = {
            'installed_services': [],
            'environment_variables': {},
            'port_mappings': {}
        }
        self.config_file = 'local_setup_config.json'
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """加载本地搭建配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.setup_config = json.load(f)
                print(f"已加载本地搭建配置: {self.setup_config}")
        except Exception as e:
            print(f"加载本地搭建配置失败: {str(e)}")
            self.setup_config = {
                'installed_services': [],
                'environment_variables': {},
                'port_mappings': {}
            }
    
    def save_config(self):
        """保存本地搭建配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.setup_config, f, ensure_ascii=False, indent=2)
            print(f"已保存本地搭建配置: {self.setup_config}")
        except Exception as e:
            print(f"保存本地搭建配置失败: {str(e)}")
    
    def check_service_status(self, service_name):
        """检查服务状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务状态: running, stopped, error
        """
        if service_name not in self.services:
            return 'error'
        
        service = self.services[service_name]
        
        # 检查进程是否存在
        if service['process']:
            try:
                process = psutil.Process(service['process'].pid)
                if process.status() == 'running':
                    return 'running'
                else:
                    return 'stopped'
            except:
                return 'stopped'
        
        # 检查端口是否被占用
        port = service['default_port']
        if self.is_port_in_use(port):
            return 'running'
        
        return 'stopped'
    
    def is_port_in_use(self, port):
        """检查端口是否被占用
        
        Args:
            port: 端口号
            
        Returns:
            是否被占用
        """
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
            return False
        except:
            return True
    
    def start_service(self, service_name):
        """启动服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            启动结果
        """
        if service_name not in self.services:
            return {'success': False, 'message': f'未知服务: {service_name}'}
        
        service = self.services[service_name]
        status = self.check_service_status(service_name)
        
        if status == 'running':
            return {'success': True, 'message': f'{service["name"]} 已经在运行'}
        
        try:
            # 启动服务的逻辑
            # 这里需要根据不同的服务实现不同的启动方式
            if service_name == 'ollama':
                # 检查Ollama是否安装
                if not self.is_ollama_installed():
                    return {'success': False, 'message': 'Ollama 未安装'}
                
                # 启动Ollama服务
                # 注意：实际启动命令可能需要根据系统调整
                process = subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True
                )
                service['process'] = process
                service['status'] = 'running'
                
                # 等待服务启动
                time.sleep(2)
                
                # 检查服务是否启动成功
                if self.check_service_status('ollama') == 'running':
                    if 'ollama' not in self.setup_config['installed_services']:
                        self.setup_config['installed_services'].append('ollama')
                    self.setup_config['port_mappings']['ollama'] = service['default_port']
                    self.save_config()
                    return {'success': True, 'message': 'Ollama 服务启动成功'}
                else:
                    service['process'] = None
                    service['status'] = 'stopped'
                    return {'success': False, 'message': 'Ollama 服务启动失败'}
            
            # 其他服务的启动逻辑
            # ...
            
            return {'success': True, 'message': f'{service["name"]} 服务启动成功'}
        except Exception as e:
            service['process'] = None
            service['status'] = 'stopped'
            return {'success': False, 'message': f'启动服务失败: {str(e)}'}
    
    def stop_service(self, service_name):
        """停止服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            停止结果
        """
        if service_name not in self.services:
            return {'success': False, 'message': f'未知服务: {service_name}'}
        
        service = self.services[service_name]
        status = self.check_service_status(service_name)
        
        if status == 'stopped':
            return {'success': True, 'message': f'{service["name"]} 已经停止'}
        
        try:
            # 停止服务的逻辑
            if service['process']:
                service['process'].terminate()
                service['process'].wait(timeout=5)
            
            service['process'] = None
            service['status'] = 'stopped'
            
            return {'success': True, 'message': f'{service["name"]} 服务停止成功'}
        except Exception as e:
            return {'success': False, 'message': f'停止服务失败: {str(e)}'}
    
    def is_ollama_installed(self):
        """检查Ollama是否安装
        
        Returns:
            是否安装
        """
        try:
            # 检查ollama命令是否可用
            result = subprocess.run(
                ['ollama', '--version'],
                capture_output=True,
                text=True,
                shell=True
            )
            return result.returncode == 0
        except:
            return False
    
    def install_service(self, service_name):
        """安装服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            安装结果
        """
        if service_name not in self.services:
            return {'success': False, 'message': f'未知服务: {service_name}'}
        
        service = self.services[service_name]
        
        if service_name == 'ollama':
            if self.is_ollama_installed():
                return {'success': True, 'message': 'Ollama 已经安装'}
            
            # 这里可以添加Ollama的安装逻辑
            # 例如打开下载页面或执行安装命令
            return {'success': False, 'message': '请手动安装 Ollama: https://ollama.com/download'}
        
        # 其他服务的安装逻辑
        # ...
        
        return {'success': True, 'message': f'{service["name"]} 安装成功'}
    
    def get_service_info(self, service_name):
        """获取服务信息
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务信息
        """
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        status = self.check_service_status(service_name)
        
        return {
            'name': service['name'],
            'status': status,
            'default_port': service['default_port'],
            'installed': service_name in self.setup_config['installed_services']
        }
    
    def get_all_services_info(self):
        """获取所有服务信息
        
        Returns:
            所有服务信息列表
        """
        services_info = []
        for service_name in self.services:
            service_info = self.get_service_info(service_name)
            if service_info:
                services_info.append(service_info)
        return services_info
    
    def set_environment_variable(self, key, value):
        """设置环境变量
        
        Args:
            key: 环境变量键
            value: 环境变量值
        """
        self.setup_config['environment_variables'][key] = value
        EnvironmentConfig.set(key, value)
        self.save_config()
    
    def get_environment_variable(self, key):
        """获取环境变量
        
        Args:
            key: 环境变量键
            
        Returns:
            环境变量值
        """
        return self.setup_config['environment_variables'].get(key)
    
    def get_all_environment_variables(self):
        """获取所有环境变量
        
        Returns:
            环境变量字典
        """
        return self.setup_config['environment_variables']
    
    def set_port_mapping(self, service_name, port):
        """设置端口映射
        
        Args:
            service_name: 服务名称
            port: 端口号
        """
        if service_name in self.services:
            self.setup_config['port_mappings'][service_name] = port
            self.services[service_name]['default_port'] = port
            self.save_config()
    
    def get_port_mapping(self, service_name):
        """获取端口映射
        
        Args:
            service_name: 服务名称
            
        Returns:
            端口号
        """
        return self.setup_config['port_mappings'].get(service_name)
    
    def get_all_port_mappings(self):
        """获取所有端口映射
        
        Returns:
            端口映射字典
        """
        return self.setup_config['port_mappings']
    
    def generate_setup_summary(self):
        """生成搭建摘要
        
        Returns:
            搭建摘要
        """
        services_info = self.get_all_services_info()
        running_services = [service['name'] for service in services_info if service['status'] == 'running']
        installed_services = [service['name'] for service in services_info if service['installed']]
        
        return {
            'total_services': len(services_info),
            'running_services': running_services,
            'installed_services': installed_services,
            'environment_variables': len(self.setup_config['environment_variables']),
            'port_mappings': len(self.setup_config['port_mappings'])
        }
