#!/bin/bash
#
# PHD Capital Rationale Studio - Quick Update Script
# Run this after pushing changes to GitHub
# Server: 147.79.68.141
#
# Usage: bash update.sh
#

set -e

PROJECT_DIR="/var/www/rationale-studio"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PHD CAPITAL - UPDATE DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Server: 147.79.68.141"
echo "  Domain: researchrationale.in"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERROR: Please run as root"
    echo ""
    echo "Run: sudo bash update.sh"
    exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ ERROR: Project directory not found: $PROJECT_DIR"
    echo ""
    echo "Please run deploy.sh first for initial deployment"
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_DIR"

echo "📥 STEP 1/7: Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main
git pull origin main
echo "   ✅ Code updated"
echo ""

echo "📦 STEP 2/7: Updating yt-dlp to latest version..."
/usr/local/bin/yt-dlp -U 2>/dev/null || true
echo "   ✅ yt-dlp updated: $(/usr/local/bin/yt-dlp --version)"
echo ""

echo "🐍 STEP 3/7: Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet
deactivate
echo "   ✅ Python dependencies updated"
echo ""

echo "📦 STEP 4/7: Updating Node.js dependencies..."
npm install --quiet
echo "   ✅ Node dependencies updated"
echo ""

echo "⚛️  STEP 5/7: Building React frontend..."
npm run build
echo "   ✅ Frontend built"
echo ""

echo "🔧 STEP 6/7: Setting correct permissions..."
chown -R www-data:www-data "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
chmod 600 .env 2>/dev/null || true
echo "   ✅ Permissions set"
echo ""

echo "🔄 STEP 7/7: Restarting application..."
systemctl daemon-reload
systemctl restart phd-capital
systemctl restart nginx
echo "   ✅ Application restarted"
echo ""

echo "🔍 Checking application status..."
sleep 3
systemctl status phd-capital --no-pager -l | head -20
echo ""

# Check if YouTube cookies exist
if [ -f "$PROJECT_DIR/backend/youtube_cookies.txt" ]; then
    echo "✅ YouTube cookies: Configured"
else
    echo "⚠️  YouTube cookies: NOT configured"
    echo ""
    echo "   WARNING: Downloads may fail without YouTube cookies!"
    echo "   Upload cookies.txt in Admin Panel > API Keys > YouTube Authentication"
    echo "   See YOUTUBE_COOKIES_SETUP.md for instructions"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ UPDATE COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Application URLs:"
echo "   HTTP: http://researchrationale.in"
echo "   HTTP: http://147.79.68.141"
echo ""
echo "📋 Useful Commands:"
echo "   View logs:    journalctl -u phd-capital -f"
echo "   Check status: systemctl status phd-capital"
echo "   Restart app:  systemctl restart phd-capital"
echo ""
