#!/bin/bash

# --- LOGIC STREAM: OCI ARM DEPLOYMENT AUTOMATION ---
# Targeted for Ubuntu 22.04 on ARM/Ampere A1 (24GB RAM)

set -e

echo "🚀 [Logic Stream] Initializing Oracle Cloud Node Setup..."

# 1. System Cleanup & Core Updates
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git curl libpq-dev

# 2. Virtual Environment Lifecycle
if [ ! -d "venv" ]; then
    echo "📦 [Logic Stream] Provisioning Virtual Environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip

# 3. Dependency Restoration (Full BERT/Torch Stack)
echo "🧠 [Logic Stream] Installing Neural Infrastructure (BERT/Torch)..."
pip install -r requirements.txt

# 4. Django Operational Prep
echo "🛠 [Logic Stream] Executing Operational Telemetry Setup..."
python manage.py collectstatic --noinput
python manage.py migrate

# 5. Nginx Node Configuration
echo "🌐 [Logic Stream] Configuring Nginx Reverse Proxy..."
sudo tee /etc/nginx/sites-available/logic_stream <<EOF
server {
    listen 80;
    server_name _;

    location /static/ {
        alias $(pwd)/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$(pwd)/logic_stream.sock;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/logic_stream /etc/nginx/sites-enabled
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# 6. Service Definition (Systemd)
echo "⚙️ [Logic Stream] Registering Command Center Service..."
sudo tee /etc/systemd/system/logic_stream.service <<EOF
[Unit]
Description=Logic Stream Command Center
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
Environment="GOOGLE_API_KEY=$GOOGLE_API_KEY"
ExecStart=$(pwd)/venv/bin/gunicorn --config gunicorn_config.py devsupport_nexus.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable logic_stream
sudo systemctl start logic_stream

echo "✅ [Logic Stream] Deployment Complete! Your Node is now active."
echo "🔗 Access your site at your Oracle Cloud Public IP."
