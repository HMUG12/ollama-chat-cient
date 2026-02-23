# NOKE架构适配改进方案

## 1. 项目结构改进

### 1.1 目录结构
```
PythonProject5/
├── main.py              # 主入口文件
├── servers/             # 服务器模块
│   ├── __init__.py
│   ├── main_server.py   # 主服务器
│   ├── memory_server.py # 记忆服务器
│   ├── agent_server.py  # 智能体服务器
│   └── monitor_server.py # 监控服务器
├── communication/       # 通信模块
│   ├── __init__.py
│   ├── websocket_client.py # WebSocket客户端
│   └── websocket_server.py # WebSocket服务器
├── local_setup/         # 本地搭建模块
│   ├── __init__.py
│   ├── setup_wizard.py  # 搭建向导
│   └── service_manager.py # 服务管理器
├── config/              # 配置模块
│   ├── __init__.py
│   ├── environment.py   # 环境变量配置
│   └── ports.py         # 端口配置
├── utils/               # 工具模块
│   ├── __init__.py
│   └── helpers.py       # 辅助函数
├── assets/              # 资源文件
│   └── icon.ico
├── requirements.txt     # 依赖文件
└── start.py             # 启动脚本
```

### 1.2 核心功能模块

#### 1.2.1 主服务器 (Main Server)
- 负责处理客户端请求
- 管理与其他服务器的通信
- 提供WebSocket接口

#### 1.2.2 记忆服务器 (Memory Server)
- 存储和管理对话历史
- 提供记忆检索功能
- 端口: 48912

#### 1.2.3 智能体服务器 (Agent Server)
- 处理AI模型调用
- 提供智能体功能
- 与外部API交互

#### 1.2.4 监控服务器 (Monitor Server)
- 监控系统状态
- 提供多端同步功能
- 端口: 48913

## 2. 通信机制改进

### 2.1 WebSocket支持
- 实现双向实时通信
- 支持多服务器间的通信
- 提供HTTP fallback机制

### 2.2 通信协议
- 采用JSON格式传输数据
- 实现消息类型和错误处理
- 支持心跳机制

## 3. 本地搭建功能

### 3.1 搭建向导
- 自动检测系统环境
- 配置必要的依赖
- 启动所需服务

### 3.2 服务管理
- 服务状态监控
- 自动重启失败服务
- 服务配置管理

## 4. 环境变量和端口配置

### 4.1 环境变量
- NEKO_MAIN_SERVER_PORT: 48911
- NEKO_MEMORY_SERVER_PORT: 48912
- NEKO_MONITOR_SERVER_PORT: 48913
- NEKO_TOOL_SERVER_PORT: 48915

### 4.2 端口管理
- 自动检测端口可用性
- 支持端口冲突处理
- 提供端口配置界面

## 5. 实现步骤

1. **基础架构搭建**
   - 创建目录结构
   - 实现核心模块

2. **通信层实现**
   - 实现WebSocket通信
   - 测试多服务器通信

3. **本地搭建功能**
   - 实现搭建向导
   - 测试服务管理功能

4. **配置和优化**
   - 配置环境变量
   - 优化性能和稳定性

5. **测试和验证**
   - 功能测试
   - 性能测试
   - 兼容性测试

## 6. 技术栈

- **后端**: Python 3.13+
- **通信**: WebSocket, FastAPI
- **GUI**: CustomTkinter
- **依赖管理**: pip
- **服务管理**: 多进程/多线程

## 7. 兼容性考虑

- 支持Windows、Linux、macOS
- 支持不同版本的Python
- 支持不同配置的硬件环境

## 8. 未来扩展

- 支持更多AI模型
- 提供插件系统
- 实现更复杂的智能体功能
- 支持云服务集成
