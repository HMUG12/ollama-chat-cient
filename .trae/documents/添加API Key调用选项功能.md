# 添加API Key调用选项功能

## 功能分析

当前项目是一个基于Ollama的本地聊天客户端，只连接到本地Ollama服务。用户希望添加API Key调用选项，以便能够使用外部API服务。

## 实现计划

### 1. UI界面修改

- 在侧边栏添加API设置区域
  - 添加API模式切换开关（本地Ollama/外部API）
  - 添加API Key输入框（带密码显示/隐藏功能）
  - 添加API基础URL输入框
  - 添加保存设置按钮

### 2. 数据结构修改

- 在`OllamaChatGUI`类中添加以下属性：
  - `use_api_key`：布尔值，标记是否使用API Key
  - `api_key`：字符串，存储API Key
  - `api_base_url`：字符串，存储外部API基础URL

### 3. 核心功能修改

- 修改`get_ai_response`方法：
  - 根据模式选择使用不同的API端点
  - 当使用API Key时，在请求头中添加认证信息
  - 调整请求格式以适应不同API的要求

- 修改`test_connection`方法：
  - 根据当前模式测试不同的连接

- 修改`get_available_models`方法：
  - 当使用外部API时，提供适当的模型列表

### 4. 配置管理

- 添加配置保存和加载功能：
  - 使用JSON文件存储API设置
  - 启动时加载保存的配置
  - 修改设置时自动保存

### 5. 错误处理和用户反馈

- 添加API Key验证逻辑
- 提供清晰的错误信息
- 确保在不同模式下的用户体验一致性

## 技术实现要点

- 使用CTkinter的内置组件创建UI元素
- 使用requests库处理API调用，添加Authorization头
- 使用JSON文件进行配置持久化
- 保持代码结构清晰，确保向后兼容性

## 预期效果

用户将能够：
1. 在本地Ollama模式和外部API模式之间切换
2. 输入和管理API Key
3. 配置外部API的基础URL
4. 使用API Key进行AI模型调用
5. 享受与本地模式相同的用户体验