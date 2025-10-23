#!/bin/bash
#
# PHD Capital - Quick Update Script
# Updates application after git push
#

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

echo "📥 Step 1/5: Pulling latest changes from Git..."
git fetch origin
git reset --hard origin/main
git pull origin main

echo "📦 Step 2/5: Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet
deactivate

echo "📦 Step 3/5: Updating Node dependencies..."
npm install --quiet

echo "🔨 Step 4/5: Building React frontend..."
npm run build

echo "🔄 Step 5/5: Restarting application..."
systemctl restart phd-capital

# Wait for service to start
sleep 3

echo ""
echo "✅ Update complete!"
echo ""
echo "📊 Service status:"
systemctl status phd-capital --no-pager -l
echo ""
echo "📋 View live logs: journalctl -u phd-capital -f"
echo ""
