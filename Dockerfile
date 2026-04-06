# 论文小助手 Docker 配置
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 创建数据目录
RUN mkdir -p /app/data/uploads /app/data/vectors /app/data/charts

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV DB_PATH=/app/data/papers.db
ENV VECTOR_INDEX_PATH=/app/data/vectors/faiss.index
ENV UPLOAD_DIR=/app/data/uploads
ENV CHART_DIR=/app/data/charts

# 暴露端口
EXPOSE 8000

# 启动命令
WORKDIR /app/backend
CMD ["python", "run.py"]
