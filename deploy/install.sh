#!/bin/bash
# 安装 Nginx 并配置开发环境（系统 Python + Vite，无虚拟环境）
# 用法: sudo bash deploy/install.sh

set -e

PROJECT_DIR="/home/xxb/c_car_web"
NGINX_SITE="c_car_web"
USER_NAME="xxb"

if [ "$(id -u)" -ne 0 ]; then
  echo "请使用 root 权限运行: sudo bash deploy/install.sh"
  exit 1
fi

echo "==> 1. 安装 Nginx..."
apt-get update -qq
apt-get install -y nginx

echo "==> 2. 安装 Python 依赖（系统环境）..."
sudo -u "$USER_NAME" pip3 install --user -r "$PROJECT_DIR/backend/requirements.txt" --break-system-packages 2>/dev/null \
  || sudo -u "$USER_NAME" pip3 install --user -r "$PROJECT_DIR/backend/requirements.txt"

echo "==> 3. 安装前端依赖..."
cd "$PROJECT_DIR/frontend"
if [ ! -d node_modules ]; then
  sudo -u "$USER_NAME" npm install
fi

echo "==> 4. 配置 Nginx..."
cp "$PROJECT_DIR/deploy/nginx/c_car_web.conf" "/etc/nginx/sites-available/$NGINX_SITE"
ln -sf "/etc/nginx/sites-available/$NGINX_SITE" "/etc/nginx/sites-enabled/$NGINX_SITE"
rm -f /etc/nginx/sites-enabled/default
nginx -t

echo "==> 5. 配置 systemd 服务..."
# 清理旧服务名（如有）
systemctl stop c-car-web c-car-web-dev c-car-web-frontend-dev 2>/dev/null || true
systemctl disable c-car-web c-car-web-dev c-car-web-frontend-dev 2>/dev/null || true
rm -f /etc/systemd/system/c-car-web.service /etc/systemd/system/c-car-web-dev.service /etc/systemd/system/c-car-web-frontend-dev.service

cp "$PROJECT_DIR/deploy/systemd/c-car-web-backend.service" /etc/systemd/system/
cp "$PROJECT_DIR/deploy/systemd/c-car-web-frontend.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable c-car-web-backend c-car-web-frontend
systemctl restart c-car-web-backend c-car-web-frontend

echo "==> 6. 初始化数据库..."
sleep 3
curl -sf -X POST http://127.0.0.1:5000/api/init-db || echo "（数据库可能已初始化，跳过）"

echo "==> 7. 启动 Nginx..."
systemctl enable nginx
systemctl restart nginx

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow 80/tcp
  echo "已放行防火墙 80 端口"
fi

echo ""
echo "=========================================="
echo "  部署完成！"
echo "  局域网访问: http://192.168.1.3"
echo "  默认账号: admin / admin123"
echo "=========================================="
echo ""
echo "服务说明："
echo "  后端: python3 app.py  → 127.0.0.1:5000"
echo "  前端: npm run dev     → 127.0.0.1:5173"
echo "  入口: Nginx           → :80"
echo ""
echo "常用命令:"
echo "  查看后端: sudo systemctl status c-car-web-backend"
echo "  查看前端: sudo systemctl status c-car-web-frontend"
echo "  后端日志: sudo journalctl -u c-car-web-backend -f"
echo "  前端日志: sudo journalctl -u c-car-web-frontend -f"
echo "  重启全部: sudo systemctl restart c-car-web-backend c-car-web-frontend nginx"
