#!/bin/bash
# Git push with proxy fallback: try direct first (30s timeout), then gg proxy
SUB="https://f00ac030.neworld.digital/link/Qx0xmJ2KkSvWvrUUEZXiAHrpUpoIRWekOiXvjrbeDeKfMNVbOxTynd5?sub=3"

echo "--- 尝试直连 push (30s超时) ---"
if timeout 30 git push origin main 2>&1; then
    echo "--- 直连成功 ---"
    exit 0
fi

echo "--- 直连失败，切换 gg 代理重试 ---"
gg -s "$SUB" git push origin main
