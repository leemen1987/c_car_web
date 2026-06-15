# AGENTS.md

## Architecture

Charter bus scheduling system (包车排班系统). Two-tier monolith:

- **Backend**: Flask + SQLAlchemy + MySQL — single `backend/app.py` (1879 lines, all routes). Models in `backend/models.py`. Config in `backend/config.py`.
- **Frontend**: Vue 3 + Element Plus + Vite — `frontend/src/`. Views map 1:1 to routes in `frontend/src/router/index.js`.
- **No monorepo tooling** — backend and frontend are independent, no shared build.

## Commands

There is **no test suite, no linter, no typechecker, no formatter** configured. Do not guess commands that don't exist.

```bash
# Frontend dev server (port 5174 per vite.config.js)
cd frontend && npm run dev

# Frontend production build
cd frontend && npm run build

# Backend dev server (port 5000)
cd backend && python3 app.py

# Full deploy (requires root)
sudo bash deploy/install.sh

# Manual dev start (both servers)
bash deploy/start.sh

# DB init / migrate (runs ALTER TABLE for new columns)
curl -s -X POST http://127.0.0.1:5000/api/init-db
```

## Port

- Frontend dev server: **5174** (set in `frontend/vite.config.js`, referenced by `deploy/nginx/c_car_web.conf`)
- Backend: **5000** (hardcoded in `backend/app.py:1879`)
- Nginx: **80** → proxies `/api/` to `:5000`, `/` to `:5174`

Note: vite.config.js is the single source of truth for frontend port. Do not add `--port` overrides in systemd or start.sh — they will desync from Nginx.

## Database

- MySQL at `config.py:5` — credentials are hardcoded (not env vars). Connection pool has `pool_recycle=300` and `pool_pre_ping=True` to handle idle disconnects.
- **Schema migrations** are done via raw ALTER TABLE in the `/api/init-db` endpoint (`app.py:1763`). New columns must be added there. There is no migration framework (no Alembic).
- Default admin: `admin / admin123` (created by init-db).

## Auth & Permissions

- Flask session-based auth (`session['user_id']`). Two decorators: `@login_required`, `@admin_required`.
- Frontend stores user in `localStorage.getItem('user')`. Router guard redirects to `/login` if missing.
- Per-page permissions stored as JSON array on User model. Permission keys: `task`, `client`, `report`, `permission`, `driver`, `vehicle`, `labor_rate`.

## External Integrations

- **云之家 (Yunzhijia)**: Approval workflow. Template IDs in `_APPROVAL_TEMPLATE_MAP` keyed by vehicle company (`国顺司`, `国开司`, `外单位`). Callback at `/api/yunzhijia/callback` with AES-ECB decryption.
- **企业微信 (WeChat Work)**: Schedule confirmation messaging. `backend/utils/wx_work.py` wraps the API. External contacts (wx_userid starting with `wm`) require manual link sharing — no direct message API support.

## Key Patterns

- All API responses follow `{code: 200, data: ..., msg: ...}`. Frontend axios interceptor (`frontend/src/utils/api.js`) rejects non-200 codes.
- Task lifecycle: `pending` → `scheduled` (assigned vehicle+driver) → `completed` (actual fees recorded).
- Task change tracking: `Task.add_changes()` stores JSON change_log with snapshots.
- Confirmation flow: push confirm link via WeChat Work → customer opens `/confirm/:token` (public, no login) → confirms/rejects.
- Approval flow groups tasks by vehicle company, one approval instance per company group.

## Deploy (systemd + Nginx)

- Backend: `c-car-web-backend.service` → `python3 app.py` on `:5000`
- Frontend: `c-car-web-frontend.service` → `npm run dev` on `:5174`
- Nginx: `:80` → proxies `/api/` to `:5000`, `/` to `:5174` with WebSocket upgrade for HMR
- Logs: `journalctl -u c-car-web-backend -f` / `journalctl -u c-car-web-frontend -f`
