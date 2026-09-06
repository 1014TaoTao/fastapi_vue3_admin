# 使用 python:3.12-slim 镜像作为基础镜像
FROM python:3.12-slim

# 使用 LABEL 替代 MAINTAINER
LABEL maintainer="948080782@qq.com"

# 设置时区
ENV TZ Asia/Shanghai

# 设置容器内工作目录
WORKDIR /home

# 先复制依赖清单并安装（利用 layer 缓存：代码变更时不重装依赖）
COPY ./backend/requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码（backend/.venv、logs、缓存等由根 .dockerignore 排除）
COPY ./backend/ .

# 暴露端口
EXPOSE 8001

# 运行应用
CMD ["python", "main.py", "run", "--env=prod"]
