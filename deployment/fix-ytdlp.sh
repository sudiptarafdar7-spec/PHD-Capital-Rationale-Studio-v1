#!/bin/bash
#
# Fix YT-DLP on VPS - Update to latest version and test
#
# Usage: bash fix-ytdlp.sh
#

set -e

PROJECT_DIR="/var/www/rationale-studio"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  YT-DLP FIX FOR VPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERROR: Please run as root"
    echo ""
    echo "Run: sudo bash fix-ytdlp.sh"
    exit 1
fi

echo "📥 STEP 1/4: Updating yt-dlp to latest version..."
cd "$PROJECT_DIR"
source venv/bin/activate
pip install --upgrade yt-dlp
YT_DLP_VERSION=$(yt-dlp --version)
echo "   ✅ yt-dlp updated to version: $YT_DLP_VERSION"
deactivate
echo ""

echo "🧪 STEP 2/4: Testing yt-dlp with public video..."
cd "$PROJECT_DIR"
source venv/bin/activate
TEST_OUTPUT=$(yt-dlp -J --no-warnings --skip-download --no-cookies \
    --user-agent 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
    --extractor-args 'youtube:player_client=android,web' \
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 2>&1)

if echo "$TEST_OUTPUT" | grep -q '"id"'; then
    echo "   ✅ yt-dlp test SUCCESSFUL"
else
    echo "   ❌ yt-dlp test FAILED"
    echo ""
    echo "Error output:"
    echo "$TEST_OUTPUT" | head -20
    echo ""
    echo "This may be due to:"
    echo "  - VPS IP blocked by YouTube"
    echo "  - Network connectivity issues"
    echo "  - YouTube API changes"
    echo ""
fi
deactivate
echo ""

echo "🔄 STEP 3/4: Restarting application..."
systemctl restart phd-capital
sleep 2
echo "   ✅ Application restarted"
echo ""

echo "🔍 STEP 4/4: Checking application status..."
if systemctl is-active --quiet phd-capital; then
    echo "   ✅ Application is RUNNING"
else
    echo "   ❌ Application is NOT running"
    echo ""
    echo "Check logs: journalctl -u phd-capital -n 50"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ FIX COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Application URL: http://researchrationale.in"
echo ""
echo "📋 View logs: journalctl -u phd-capital -f"
echo ""
echo "⚠️  If videos still fail, YouTube may be blocking your VPS IP."
echo "    Try using videos from channels that allow embedding."
echo ""
