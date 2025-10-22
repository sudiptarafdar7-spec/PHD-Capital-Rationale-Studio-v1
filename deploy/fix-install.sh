#!/bin/bash
# Quick fix for Ubuntu 24.04 system-managed Python packages

echo "🔧 Installing Python packages with system override..."

cd /var/www/phd-capital

# Install using virtual environment (best practice)
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
deactivate

echo "✅ Packages installed in virtual environment!"
echo ""
echo "Now updating systemd service to use venv..."

# Update systemd service to use venv
cat > /etc/systemd/system/phd-capital.service << 'EOF'
[Unit]
Description=PHD Capital Rationale Studio
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/phd-capital
Environment="PATH=/var/www/phd-capital/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/www/phd-capital/.env
ExecStart=/var/www/phd-capital/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 'backend.app:create_app()'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R www-data:www-data /var/www/phd-capital

# Reload and restart
systemctl daemon-reload
systemctl restart phd-capital

echo ""
echo "✅ Service updated and restarted!"
echo ""
echo "Check status: systemctl status phd-capital"
