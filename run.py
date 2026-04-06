"""
启动脚本
"""
import sys
import os

# 将当前目录添加到Python路径，确保能找到app模块
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn
from app.config import config

if __name__ == "__main__":
    print("""
    =========================================
    
         AI论文小助手 启动中...
    
    =========================================
    """)
    
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
