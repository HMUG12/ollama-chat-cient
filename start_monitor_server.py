
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并启动服务器
from servers.monitor_server import MonitorServer

server = MonitorServer()
server.start()

# 保持运行
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

server.stop()
