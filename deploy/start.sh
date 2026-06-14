#!/bin/bash
# 手动启动开发环境（不用 systemd）
# 用法: bash deploy/start.sh

PROJECT_DIR="/home/xxb/c_car_web"

pip3 install --user -r "$PROJECT_DIR/backend/requirements.txt" --break-system-packages 2>/dev/null \
  || pip3 install --user -r "$PROJECT_DIR/backend/requirements.txt"

cd "$PROJECT_DIR/backend"
echo "启动后端: python3 app.py (127.0.0.1:5000)"
python3 app.py &
BACKEND_PID=$!

cd "$PROJECT_DIR/frontend"
echo "启动前端: npm run dev (127.0.0.1:5173)"
npm run dev -- --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "后端 PID: $BACKEND_PID  前端 PID: $FRONTEND_PID"
echo "本地调试: http://127.0.0.1:5173"
echo "局域网访问需先配置 Nginx: sudo bash deploy/install.sh"
echo "停止服务: kill $BACKEND_PID $FRONTEND_PID"

wait
