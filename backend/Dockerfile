# 基础镜像：使用预编译了 libvmaf 的 FFmpeg
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖和 FFmpeg（包含 libvmaf）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libvmaf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 下载 VMAF 模型文件
RUN mkdir -p /usr/share/model && \
    curl -L -o /usr/share/model/vmaf_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_v0.6.1.json && \
    curl -L -o /usr/share/model/vmaf_4k_v0.6.1.json \
    https://raw.githubusercontent.com/Netflix/vmaf/master/model/vmaf_4k_v0.6.1.json

# 设置工作目录
WORKDIR /app

# 安装 Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml ./

# 安装 Python 依赖
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p uploads reports

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
