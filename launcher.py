import os
import sys
import threading
import time
import subprocess
import json
from datetime import datetime

class ServerLauncher:
    """服务器启动器，负责管理所有服务器的启动和停止"""
    
    def __init__(self):
        """初始化服务器启动器"""
        self.servers = {
            'main': {
                'name': '主服务器',
                'module': 'servers.main_server',
                'class': 'MainServer',
                'port': 48911,
                'status': 'stopped',
                'process': None
            },
            'memory': {
                'name': '记忆服务器',
                'module': 'servers.memory_server',
                'class': 'MemoryServer',
                'port': 48912,
                'status': 'stopped',
                'process': None
            },
            'monitor': {
                'name': '监控服务器',
                'module': 'servers.monitor_server',
                'class': 'MonitorServer',
                'port': 48913,
                'status': 'stopped',
                'process': None
            },
            'agent': {
                'name': '智能体服务器',
                'module': 'servers.agent_server',
                'class': 'AgentServer',
                'port': 48915,
                'status': 'stopped',
                'process': None
            }
        }
        self.log_file = 'launcher.log'
        self.config_file = 'launcher_config.json'
        self.config = {
            'auto_start': False,
            'start_delay': 2,
            'stop_timeout': 5
        }
        
        # 加载配置
        self.load_config()
        # 初始化日志
        self.init_log()
    
    def init_log(self):
        """初始化日志文件"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"服务器启动器初始化 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n")
        except Exception as e:
            print(f"初始化日志文件失败: {str(e)}")
    
    def log(self, message):
        """记录日志
        
        Args:
            message: 日志消息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except Exception as e:
            print(f"写入日志失败: {str(e)}")
        
        print(log_message, end='')
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.log(f"已加载配置: {self.config}")
        except Exception as e:
            self.log(f"加载配置文件失败: {str(e)}")
            self.config = {
                'auto_start': False,
                'start_delay': 2,
                'stop_timeout': 5
            }
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.log(f"已保存配置: {self.config}")
        except Exception as e:
            self.log(f"保存配置文件失败: {str(e)}")
    
    def start_server(self, server_name):
        """启动单个服务器
        
        Args:
            server_name: 服务器名称
            
        Returns:
            启动结果
        """
        if server_name not in self.servers:
            message = f'未知服务器: {server_name}'
            self.log(message)
            return {'success': False, 'message': message}
        
        server = self.servers[server_name]
        
        if server['status'] == 'running':
            message = f'{server["name"]} 已经在运行'
            self.log(message)
            return {'success': True, 'message': message}
        
        try:
            # 构建启动命令
            script_content = f"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并启动服务器
from {server['module']} import {server['class']}

server = {server['class']}()
server.start()

# 保持运行
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

server.stop()
"""
            
            # 写入临时脚本
            temp_script = f'start_{server_name}_server.py'
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 启动服务器进程
            process = subprocess.Popen(
                [sys.executable, temp_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            
            server['process'] = process
            server['status'] = 'starting'
            
            # 等待服务器启动
            time.sleep(self.config['start_delay'])
            
            # 检查服务器是否启动成功
            # 这里可以添加更详细的检查逻辑
            server['status'] = 'running'
            
            message = f'{server["name"]} 启动成功，端口: {server["port"]}'
            self.log(message)
            return {'success': True, 'message': message}
        except Exception as e:
            server['process'] = None
            server['status'] = 'stopped'
            message = f'启动 {server["name"]} 失败: {str(e)}'
            self.log(message)
            return {'success': False, 'message': message}
    
    def stop_server(self, server_name):
        """停止单个服务器
        
        Args:
            server_name: 服务器名称
            
        Returns:
            停止结果
        """
        if server_name not in self.servers:
            message = f'未知服务器: {server_name}'
            self.log(message)
            return {'success': False, 'message': message}
        
        server = self.servers[server_name]
        
        if server['status'] == 'stopped':
            message = f'{server["name"]} 已经停止'
            self.log(message)
            return {'success': True, 'message': message}
        
        try:
            if server['process']:
                server['process'].terminate()
                server['process'].wait(timeout=self.config['stop_timeout'])
            
            server['process'] = None
            server['status'] = 'stopped'
            
            # 清理临时脚本
            temp_script = f'start_{server_name}_server.py'
            if os.path.exists(temp_script):
                os.remove(temp_script)
            
            message = f'{server["name"]} 停止成功'
            self.log(message)
            return {'success': True, 'message': message}
        except Exception as e:
            server['process'] = None
            server['status'] = 'stopped'
            message = f'停止 {server["name"]} 失败: {str(e)}'
            self.log(message)
            return {'success': False, 'message': message}
    
    def start_all_servers(self):
        """启动所有服务器
        
        Returns:
            启动结果
        """
        results = []
        
        # 按照依赖顺序启动服务器
        start_order = ['memory', 'agent', 'monitor', 'main']
        
        for server_name in start_order:
            result = self.start_server(server_name)
            results.append(result)
            
            # 如果启动失败，停止之前启动的服务器
            if not result['success']:
                for started_server in start_order[:start_order.index(server_name)]:
                    self.stop_server(started_server)
                break
        
        # 检查是否所有服务器都启动成功
        all_success = all(result['success'] for result in results)
        if all_success:
            message = '所有服务器启动成功'
            self.log(message)
            return {'success': True, 'message': message}
        else:
            message = '部分服务器启动失败'
            self.log(message)
            return {'success': False, 'message': message}
    
    def stop_all_servers(self):
        """停止所有服务器
        
        Returns:
            停止结果
        """
        results = []
        
        # 按照相反的顺序停止服务器
        stop_order = ['main', 'monitor', 'agent', 'memory']
        
        for server_name in stop_order:
            result = self.stop_server(server_name)
            results.append(result)
        
        # 检查是否所有服务器都停止成功
        all_success = all(result['success'] for result in results)
        if all_success:
            message = '所有服务器停止成功'
            self.log(message)
            return {'success': True, 'message': message}
        else:
            message = '部分服务器停止失败'
            self.log(message)
            return {'success': False, 'message': message}
    
    def get_server_status(self, server_name):
        """获取服务器状态
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器状态
        """
        if server_name not in self.servers:
            return None
        
        server = self.servers[server_name]
        return {
            'name': server['name'],
            'status': server['status'],
            'port': server['port'],
            'process_id': server['process'].pid if server['process'] else None
        }
    
    def get_all_servers_status(self):
        """获取所有服务器状态
        
        Returns:
            所有服务器状态列表
        """
        status_list = []
        for server_name in self.servers:
            status = self.get_server_status(server_name)
            if status:
                status_list.append(status)
        return status_list
    
    def print_status(self):
        """打印所有服务器状态"""
        self.log('\n服务器状态:')
        self.log('-' * 80)
        
        for server_name, server in self.servers.items():
            status = server['status']
            port = server['port']
            process_id = server['process'].pid if server['process'] else 'N/A'
            
            self.log(f'{server["name"]}: {status} (端口: {port}, PID: {process_id})')
        
        self.log('-' * 80)
    
    def run(self):
        """运行启动器"""
        import time
        
        self.log('服务器启动器运行中...')
        self.log('命令: start_all, stop_all, start <server>, stop <server>, status, exit')
        
        try:
            while True:
                command = input('> ').strip().lower()
                
                if command == 'start_all':
                    result = self.start_all_servers()
                    self.log(f'结果: {result["message"]}')
                elif command == 'stop_all':
                    result = self.stop_all_servers()
                    self.log(f'结果: {result["message"]}')
                elif command.startswith('start '):
                    server_name = command.split(' ')[1]
                    result = self.start_server(server_name)
                    self.log(f'结果: {result["message"]}')
                elif command.startswith('stop '):
                    server_name = command.split(' ')[1]
                    result = self.stop_server(server_name)
                    self.log(f'结果: {result["message"]}')
                elif command == 'status':
                    self.print_status()
                elif command == 'exit':
                    self.log('退出启动器...')
                    self.stop_all_servers()
                    break
                else:
                    self.log('未知命令，请重新输入')
        except KeyboardInterrupt:
            self.log('收到中断信号，退出启动器...')
            self.stop_all_servers()

if __name__ == '__main__':
    launcher = ServerLauncher()
    
    # 如果设置了自动启动
    if launcher.config.get('auto_start', False):
        launcher.log('自动启动所有服务器...')
        launcher.start_all_servers()
        launcher.print_status()
    
    # 运行交互式命令行
    launcher.run()
