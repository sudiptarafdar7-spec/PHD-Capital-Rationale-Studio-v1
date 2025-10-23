#!/bin/bash
#
# Setup YouTube Cookies for YT-DLP
#
# This script helps you set up cookies for yt-dlp to bypass YouTube bot detection
#
# Usage: bash setup-cookies.sh
#

set -e

PROJECT_DIR="/var/www/rationale-studio"
COOKIES_FILE="$PROJECT_DIR/backend/job_files/youtube_cookies.txt"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  YOUTUBE COOKIES SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERROR: Please run as root"
    echo ""
    echo "Run: sudo bash setup-cookies.sh"
    exit 1
fi

echo "📋 STEP 1/3: Creating cookies directory..."
mkdir -p "$PROJECT_DIR/backend/job_files"
echo "   ✅ Directory created"
echo ""

echo "📝 STEP 2/3: How to export cookies from your browser"
echo ""
echo "   1. Open YouTube.com in your browser (Chrome/Firefox)"
echo "   2. Log in to your YouTube account"
echo "   3. Install 'Get cookies.txt LOCALLY' browser extension:"
echo "      Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
echo "      Firefox: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/"
echo "   4. Click the extension icon while on youtube.com"
echo "   5. Click 'Export' to download youtube.com_cookies.txt"
echo "   6. Upload the file to your VPS at: $COOKIES_FILE"
echo ""
echo "   To upload from your computer, run:"
echo "   scp youtube.com_cookies.txt root@72.60.111.9:$COOKIES_FILE"
echo ""

read -p "   Have you uploaded the cookies file? (y/n): " uploaded

if [ "$uploaded" != "y" ]; then
    echo ""
    echo "❌ Please upload the cookies file first, then run this script again."
    exit 1
fi

echo ""
echo "🔐 STEP 3/3: Setting proper permissions..."

if [ ! -f "$COOKIES_FILE" ]; then
    echo "   ❌ ERROR: Cookies file not found at $COOKIES_FILE"
    echo ""
    echo "   Please upload the file and try again."
    exit 1
fi

# Set proper ownership and permissions
chown www-data:www-data "$COOKIES_FILE"
chmod 644 "$COOKIES_FILE"

echo "   ✅ Permissions set (readable by application)"
echo ""

echo "🔄 Restarting application..."
systemctl restart phd-capital
sleep 2
echo "   ✅ Application restarted"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ COOKIES SETUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Cookies file location: $COOKIES_FILE"
echo "🌐 Application URL: http://researchrationale.in"
echo ""
echo "⚠️  IMPORTANT: Cookies expire after ~6 months."
echo "   If videos start failing, re-export and upload new cookies."
echo ""
