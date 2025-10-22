#!/bin/bash
set -e

echo "=========================================="
echo "PHD Capital - Update Deployment"
echo "=========================================="
echo ""

APP_DIR="/var/www/phd-capital"

if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application not found at $APP_DIR"
    exit 1
fi

cd $APP_DIR

echo "📥 Step 1/4: Pulling latest changes from Git..."
git pull

echo "📦 Step 2/4: Installing/updating dependencies..."
pip install -r requirements.txt
npm install

echo "🔨 Step 3/4: Building React frontend..."
npm run build

echo "🔄 Step 4/4: Restarting application..."
systemctl restart phd-capital

echo ""
echo "✅ Update complete!"
echo ""
echo "📊 Check status: systemctl status phd-capital"
echo "📋 View logs: journalctl -u phd-capital -f"
echo ""
