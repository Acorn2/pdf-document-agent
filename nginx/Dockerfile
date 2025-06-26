FROM nginx:alpine

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 创建日志目录
RUN mkdir -p /var/log/nginx

# 暴露端口
EXPOSE 80 443

# 启动nginx
CMD ["nginx", "-g", "daemon off;"] 