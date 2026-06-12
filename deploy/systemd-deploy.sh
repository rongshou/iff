#!/bin/bash
# systemd 部署方式
set -e

echo "天权 · systemd 部署"

# 创建数据链接
mkdir -p /home/admin/tianquan/backend/data
ln -sf /home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/advisor.db /home/admin/tianquan/backend/data/advisor.db
ln -sf /home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/real_case_probability.json /home/admin/tianquan/backend/data/real_case_probability.json

# 安装 systemd 服务
sudo cp /home/admin/tianquan/deploy/tianquan-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tianquan-backend
sudo systemctl restart tianquan-backend

echo "✅ Backend 已启动 (systemd)"
echo "  状态: sudo systemctl status tianquan-backend"
echo "  日志: sudo journalctl -u tianquan-backend -f"
