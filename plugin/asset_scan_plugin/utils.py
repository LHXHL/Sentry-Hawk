import re

# 去除端口
def remove_port(url):
    return re.sub(r":\d+", "", url)


# 使用正则去掉 http:// 或 https://
def clean_url(url):
    # 移除协议前缀
    url_pattern = re.compile(r'https?://')
    url = re.sub(url_pattern, '', url)
    
    # 移除端口号
    url = remove_port(url)
    
    # 移除路径部分
    url = url.split('/')[0]
    
    return url


# 判断是不是ipv4
def is_ipv4(url):
    ipv4_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
    if ipv4_pattern.match(url):
        return True
    return False

