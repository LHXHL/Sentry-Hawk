FROM python:3.10

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app


# 移除原有的 debian.sources 文件
RUN rm -f /etc/apt/sources.list.d/debian.sources

# 创建新的 debian.sources 文件并写入清华镜像源配置
RUN echo 'Types: deb\nURIs: https://mirrors.tuna.tsinghua.edu.cn/debian\nSuites: bookworm bookworm-updates\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\nTypes: deb\nURIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security\nSuites: bookworm-security\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg' > /etc/apt/sources.list.d/debian.sources

# 更新 APT 缓存
RUN apt-get update && \
    apt-get install -y nmap 


# 复制并安装依赖
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY . /app/


# 为 plugin 目录添加 777 权限
RUN chmod -R 777 /app/plugin

# 暴露端口
EXPOSE 8000


# 启动命令
CMD ["sh", "-c", "python ./manage.py makemigrations --no-input && python ./manage.py migrate --fake-initial && python -u ./manage.py runserver 0.0.0.0:8000"]
