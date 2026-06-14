# Nginx 与项目代理配置说明

本文说明包车排班系统在开发环境下的网络架构、各服务端口、配置文件位置，以及如何修改访问端口。

---

## 一、整体架构

系统由三个进程组成：**Nginx（对外入口）**、**Vite 前端开发服务**、**Flask 后端 API 服务**。

```
局域网用户浏览器
        │
        │  http://192.168.1.3:80  （对外访问端口，可改）
        ▼
┌───────────────────────────────────────┐
│  Nginx  (:80)                         │
│  配置文件: deploy/nginx/c_car_web.conf │
│  系统路径: /etc/nginx/sites-enabled/   │
└───────────────┬───────────────────────┘
                │
     ┌──────────┴──────────┐
     │                     │
     │ /api/*              │  /* （页面、JS、CSS、热更新 WebSocket）
     ▼                     ▼
┌─────────────┐     ┌─────────────┐
│ Flask 后端   │     │ Vite 前端    │
│ 127.0.0.1   │     │ 127.0.0.1   │
│ :5000       │     │ :5173       │
└─────────────┘     └─────────────┘
 python3 app.py      npm run dev
```

**设计要点：**

- 前端和后端只监听 `127.0.0.1`（本机），**不直接暴露**给局域网，避免绕过 Nginx。
- 局域网用户统一通过 **Nginx 的对外端口** 访问。
- 前端代码里 API 地址写死为相对路径 `/api`（见 `frontend/src/utils/api.js`），浏览器会请求「当前访问域名 + /api」，因此只要走 Nginx 入口，无需改前端代码。

---

## 二、请求是如何转发的

### 2.1 打开页面（例如访问首页）

```
浏览器 GET http://192.168.1.3/
    → Nginx location /
    → 转发到 http://127.0.0.1:5173/
    → Vite 返回 index.html 及前端资源
```

### 2.2 登录、查询任务等 API 请求

```
浏览器 POST http://192.168.1.3/api/login
    → Nginx location /api/
    → 转发到 http://127.0.0.1:5000/api/login
    → Flask 处理并返回 JSON
```

### 2.3 前端热更新（开发模式）

Vite 通过 WebSocket 推送代码变更。Nginx 在 `location /` 中配置了：

```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

这样浏览器连 `ws://192.168.1.3/...` 时，Nginx 会把 WebSocket 转发到 Vite，热更新才能正常工作。

---

## 三、各服务端口与配置文件

| 组件 | 默认端口 | 监听地址 | 项目内配置文件 | 系统部署后位置 |
|------|---------|---------|---------------|---------------|
| **Nginx（对外入口）** | **80** | `0.0.0.0`（全网卡） | `deploy/nginx/c_car_web.conf` | `/etc/nginx/sites-enabled/c_car_web` |
| Flask 后端 | 5000 | `127.0.0.1` | `backend/app.py` 最后一行 | systemd: `c-car-web-backend.service` |
| Vite 前端 | 5173 | `127.0.0.1` | `frontend/vite.config.js` | systemd: `c-car-web-frontend.service` |

### 3.1 Nginx 配置（核心）

文件：`deploy/nginx/c_car_web.conf`

```nginx
listen 80;                          # ← 对外访问端口

location /api/ {
    proxy_pass http://127.0.0.1:5000;   # ← 后端地址
}

location / {
    proxy_pass http://127.0.0.1:5173;   # ← 前端地址
}
```

### 3.2 后端端口

文件：`backend/app.py`

```python
app.run(debug=True, host='127.0.0.1', port=5000)
```

### 3.3 前端端口

文件：`frontend/vite.config.js`

```javascript
server: {
  host: '127.0.0.1',
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5000',   // 仅本地直连 Vite 时生效
      changeOrigin: true
    }
  }
}
```

> **说明：** 经 Nginx 访问时，API 由 Nginx 转发，不经过 Vite 的 `proxy`。Vite 的 proxy 只在「直接打开 `http://127.0.0.1:5173`」调试时有用。

### 3.4 systemd 服务（可选，用 install.sh 安装后生效）

| 服务名 | 启动命令 |
|--------|---------|
| `c-car-web-backend` | `python3 app.py` |
| `c-car-web-frontend` | `npm run dev -- --host 127.0.0.1 --port 5173` |

---

## 四、如何修改访问端口

下面分三种常见需求说明。**改完配置后都要重载/重启对应服务。**

---

### 4.1 修改对外访问端口（最常用）

例如：把局域网访问从 `http://192.168.1.3` 改为 `http://192.168.1.3:8080`。

**只需改 Nginx 的 `listen` 端口**，前后端内部端口（5000、5173）不用动。

**步骤：**

1. 编辑 `deploy/nginx/c_car_web.conf`：

```nginx
# 改前
listen 80;

# 改后（示例：8080）
listen 8080;
listen [::]:8080;
```

2. 同步到系统并重载 Nginx：

```bash
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t                    # 检查语法
sudo systemctl reload nginx      # 重载配置
```

3. 若启用了防火墙，放行新端口：

```bash
sudo ufw allow 8080/tcp
# 如不再使用 80 端口，可删除旧规则：sudo ufw delete allow 80/tcp
```

4. 局域网访问地址变为：

```
http://192.168.1.3:8080
```

**注意：** 1024 以下的端口（如 80）需要 root 权限，8080、8888 等高位端口普通配置即可。

---

### 4.2 修改后端内部端口（5000 → 其他）

例如改为 `5001`。需要改 **3 处**，并保持 Nginx 的 `proxy_pass` 与后端一致。

| 序号 | 文件 | 修改内容 |
|------|------|---------|
| 1 | `backend/app.py` | `port=5001` |
| 2 | `deploy/nginx/c_car_web.conf` | `proxy_pass http://127.0.0.1:5001;`（`/api/` 段） |
| 3 | `frontend/vite.config.js` | `target: 'http://127.0.0.1:5001'`（本地直连 Vite 调试用） |

若使用 systemd，还需改 `deploy/systemd/c-car-web-backend.service`（命令本身不变，端口在 app.py 里）。

**重启：**

```bash
sudo systemctl restart c-car-web-backend
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t && sudo systemctl reload nginx
```

对外访问端口（Nginx 的 80 或 8080）**不需要改**。

---

### 4.3 修改前端内部端口（5173 → 其他）

例如改为 `3000`。需要改 **3 处**：

| 序号 | 文件 | 修改内容 |
|------|------|---------|
| 1 | `frontend/vite.config.js` | `port: 3000` |
| 2 | `deploy/nginx/c_car_web.conf` | `proxy_pass http://127.0.0.1:3000;`（`location /` 段） |
| 3 | `deploy/systemd/c-car-web-frontend.service` | `--port 3000` |

**重启：**

```bash
sudo cp deploy/systemd/c-car-web-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart c-car-web-frontend
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t && sudo systemctl reload nginx
```

对外访问端口同样**不需要改**。

---

## 五、两种访问方式对比

| 访问方式 | 地址示例 | 适用场景 |
|---------|---------|---------|
| **经 Nginx（推荐，局域网用）** | `http://192.168.1.3:80` | 局域网其他电脑访问；与生产环境路径一致 |
| **直连 Vite（仅本机调试）** | `http://127.0.0.1:5173` | 本机开发；API 由 Vite proxy 转到 5000 |
| **直连 Flask（仅测 API）** | `http://127.0.0.1:5000/api/...` | 用 curl/Postman 测接口 |

---

## 六、部署与日常命令

### 首次部署（安装 Nginx + 注册 systemd 服务）

```bash
sudo bash deploy/install.sh
```

### 手动启动（不用 systemd）

```bash
bash deploy/start.sh
# 仍需单独配置 Nginx 才能局域网访问
```

### 修改 Nginx 配置后的标准流程

```bash
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t                 # 必须通过，否则不要 reload
sudo systemctl reload nginx
```

### 查看日志

```bash
# Nginx 访问/错误日志
sudo tail -f /var/log/nginx/c_car_web_access.log
sudo tail -f /var/log/nginx/c_car_web_error.log

# 后端 / 前端 systemd 日志
sudo journalctl -u c-car-web-backend -f
sudo journalctl -u c-car-web-frontend -f
```

### 检查端口占用

```bash
ss -tlnp | grep -E ':80|:5000|:5173'
```

---

## 七、常见问题

### Q1：改了 Nginx 端口，局域网还是访问不了？

1. 确认 Nginx 已重载：`sudo systemctl status nginx`
2. 确认防火墙已放行：`sudo ufw status`
3. 确认访问 URL 带上了新端口，例如 `http://192.168.1.3:8080`
4. 确认后端、前端服务在运行：`sudo systemctl status c-car-web-backend c-car-web-frontend`

### Q2：页面能打开，但登录/API 报错？

1. 检查后端是否在 5000 端口：`curl http://127.0.0.1:5000/api/init-db -X POST`
2. 检查 Nginx `/api/` 的 `proxy_pass` 是否指向正确后端端口
3. 查看 Nginx 错误日志

### Q3：本机 5173 正常，经 Nginx 访问没有热更新？

确认 `c_car_web.conf` 的 `location /` 中包含 WebSocket 相关 `Upgrade` / `Connection` 头（默认已配置）。

### Q4：云之家审批回调地址怎么填？

回调需从公网或内网可达的 **Nginx 对外地址**，例如：

```
http://192.168.1.3/api/yunzhijia/callback
```

若改了 Nginx 端口，需带上端口，例如：

```
http://192.168.1.3:8080/api/yunzhijia/callback
```

---

## 八、配置文件速查

```
c_car_web/
├── deploy/
│   ├── nginx/c_car_web.conf          # Nginx 反代规则（对外端口在这里改）
│   ├── systemd/
│   │   ├── c-car-web-backend.service # 后端 systemd
│   │   └── c-car-web-frontend.service# 前端 systemd
│   ├── install.sh                    # 一键部署脚本
│   └── start.sh                      # 手动启动脚本
├── backend/app.py                    # 后端端口 host/port
└── frontend/
    ├── vite.config.js                # 前端端口 + 本地调试 proxy
    └── src/utils/api.js              # API 基路径 /api（一般不用改）
```

---

## 九、端口修改速查表

| 想改什么 | 改哪些文件 | 局域网 URL 变化 |
|---------|-----------|----------------|
| 对外访问端口 80→8080 | 仅 `c_car_web.conf` 的 `listen` + 防火墙 | `http://IP:8080` |
| 后端 5000→5001 | `app.py` + `c_car_web.conf` + `vite.config.js` | 无变化（仍走 Nginx 对外端口） |
| 前端 5173→3000 | `vite.config.js` + `c_car_web.conf` + frontend systemd | 无变化 |

**原则：用户看到的端口 = Nginx 的 `listen`；5000 和 5173 是服务器内部端口，局域网用户通常无感知。**
