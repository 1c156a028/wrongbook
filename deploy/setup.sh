#!/usr/bin/env bash
# ============================================================
# 错题本 一键部署脚本
# 适用：全新的 Ubuntu 22.04 / 24.04 云服务器，以 root 身份运行
#
# 用法（在服务器上以 root 执行，用 git clone 而不是 curl raw，
# 因为国内服务器常常访问不了 raw.githubusercontent.com）：
#   git clone https://github.com/1c156a028/wrongbook.git /tmp/wb
#   bash /tmp/wb/deploy/setup.sh
#
# 它做了 6 件事：
#   1. 装系统依赖（python3 / venv / pip / git）
#   2. 把代码拉到 /opt/wrongbook
#   3. 建虚拟环境、装 requirements.txt
#   4. 生成 .env（随机 SECRET_KEY、关掉 debug）
#   5. 初始化数据库，写入演示数据
#   6. 注册成 systemd 服务，开机自启、崩溃自动重启
# ============================================================
set -euo pipefail

APP_DIR=/opt/wrongbook
REPO=https://github.com/1c156a028/wrongbook.git
PORT=80

echo "==> 1/6 安装系统依赖"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl

echo "==> 2/6 拉取代码到 $APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git pull
else
  git clone "$REPO" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "==> 3/6 创建虚拟环境并安装依赖"
python3 -m venv .venv
# 用清华镜像加速：国内服务器直连 pypi.org 经常只有几十 KB/s
PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
.venv/bin/pip install --upgrade pip -q -i "$PIP_MIRROR"
.venv/bin/pip install -r requirements.txt -i "$PIP_MIRROR"

echo "==> 4/6 生成 .env（只在第一次生成）"
if [ ! -f .env ]; then
  SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  {
    echo "SECRET_KEY=$SECRET"
    echo "DATABASE_PATH=wrongbook.db"
    echo "FLASK_DEBUG=0"
    echo "PORT=$PORT"
  } > .env
  echo "    已生成 .env（SECRET_KEY 是随机值，别人伪造不了你的登录）"
else
  echo "    .env 已存在，保留原样"
fi

echo "==> 5/6 初始化数据库"
if [ ! -f wrongbook.db ]; then
  .venv/bin/python seed.py
  echo "    已建库并写入演示数据（demo / 123456）"
else
  echo "    wrongbook.db 已存在，跳过（不会覆盖你的数据）"
fi

echo "==> 6/6 注册 systemd 服务"
cat > /etc/systemd/system/wrongbook.service <<EOF
[Unit]
Description=WrongBook Flask app
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/gunicorn -w 2 -b 0.0.0.0:$PORT app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wrongbook >/dev/null 2>&1
systemctl restart wrongbook

sleep 2
if systemctl is-active --quiet wrongbook; then
  IP=$(curl -s --max-time 5 ifconfig.me || echo "你的公网IP")
  echo ""
  echo "=================================================="
  echo " 部署成功！打开浏览器访问：  http://$IP/"
  echo ""
  echo " 常用命令："
  echo "   systemctl status wrongbook     # 看运行状态"
  echo "   systemctl restart wrongbook    # 改完代码后重启"
  echo "   journalctl -u wrongbook -f     # 实时看日志"
  echo "=================================================="
else
  echo "启动失败，查看日志： journalctl -u wrongbook -n 50 --no-pager"
  exit 1
fi
