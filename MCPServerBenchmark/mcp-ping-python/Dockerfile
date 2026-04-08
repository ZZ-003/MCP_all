FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（ping命令需要iputils-ping包）
RUN apt-get update && apt-get install -y \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py .

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["python", "main.py"]