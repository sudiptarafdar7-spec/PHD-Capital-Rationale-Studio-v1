#!/bin/bash
#
# PHD Capital - Quick Update Script
# Run this after pushing new code to GitHub
#

set -e

PROJECT_DIR="/var/www/Rationale Studio"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PHD CAPITAL - UPDATE DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project not found at $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "📥 Step 1/5: Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main
git pull origin main

echo ""
echo "🐍 Step 2/5: Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet
deactivate

echo ""
echo "📦 Step 3/5: Updating Node dependencies..."
npm install --quiet

echo ""
echo "🔨 Step 4/5: Building React frontend..."
npm run build

echo ""
echo "🔄 Step 5/5: Restarting application..."
systemctl restart phd-capital

sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ UPDATE COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Service Status:"
systemctl status phd-capital --no-pager -l | head -20
echo ""
echo "📋 View live logs: journalctl -u phd-capital -f"
echo ""
