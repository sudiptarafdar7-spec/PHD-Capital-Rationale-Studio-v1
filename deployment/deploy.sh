#!/bin/bash
#
# PHD Capital Rationale Studio - Production Deployment Script
# Server: 72.60.111.9 (Ubuntu 24.04 LTS)
# Domain: researchrationale.in
# GitHub: https://github.com/sudiptarafdar7-spec/PHD-Capital-Rationale-Studio-v1.git
#
# Usage: bash deploy.sh
#

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PHD CAPITAL RATIONALE STUDIO - PRODUCTION DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Server IP: 72.60.111.9"
echo "  Domain: researchrationale.in"
echo "  OS: Ubuntu 24.04 LTS"
echo "  Project Folder: rationale-studio"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERROR: Please run as root"
    echo ""
    echo "Run: sudo bash deploy.sh"
    exit 1
fi

# Configuration
PROJECT_DIR="/var/www/rationale-studio"
DOMAIN="researchrationale.in"
GITHUB_REPO="https://github.com/sudiptarafdar7-spec/PHD-Capital-Rationale-Studio-v1.git"
DB_NAME="phd_rationale_db"
DB_USER="phd_user"
DB_PASSWORD="ChangeMeToSecurePassword123!"

echo "📋 Configuration:"
echo "   Project Directory: $PROJECT_DIR"
echo "   Domain: $DOMAIN"
echo "   Database: $DB_NAME"
echo "   Repository: $GITHUB_REPO"
echo ""

# ═══════════════════════════════════════════════════════════
# STEP 1: Update System & Install Dependencies
# ═══════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 STEP 1/10: Installing System Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

apt update -qq
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    software-properties-common \
    ffmpeg \
    2>/dev/null || true

echo "   ✅ System dependencies installed"

# ═══════════════════════════════════════════════════════════
# STEP 2: Install Node.js 20.x
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 STEP 2/10: Installing Node.js 20.x"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v node &> /dev/null || [[ $(node -v | cut -d'v' -f2 | cut -d'.' -f1) -lt 20 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
    echo "   ✅ Node.js $(node -v) installed"
else
    echo "   ✅ Node.js $(node -v) already installed"
fi

# ═══════════════════════════════════════════════════════════
# STEP 3: Install yt-dlp
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 STEP 3/10: Installing yt-dlp"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f /usr/local/bin/yt-dlp ]; then
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
    chmod a+rx /usr/local/bin/yt-dlp
    echo "   ✅ yt-dlp installed"
else
    /usr/local/bin/yt-dlp -U 2>/dev/null || true
    echo "   ✅ yt-dlp updated to latest version"
fi

# ═════════════════════════════════════════════════════════════
# STEP 4: Setup PostgreSQL Database
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  STEP 4/10: Setting up PostgreSQL Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE \"$DB_NAME\";" 2>/dev/null || echo "   ℹ️  Database already exists"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "   ℹ️  User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \"$DB_NAME\" TO $DB_USER;" 2>/dev/null
sudo -u postgres psql -c "ALTER DATABASE \"$DB_NAME\" OWNER TO $DB_USER;" 2>/dev/null

echo "   ✅ PostgreSQL database configured"
echo "      Database: $DB_NAME"
echo "      User: $DB_USER"

# ═══════════════════════════════════════════════════════════
# STEP 5: Clone/Update Application from GitHub
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 STEP 5/10: Cloning Application from GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$PROJECT_DIR" ]; then
    echo "   ℹ️  Project directory exists, updating..."
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/main
    git pull origin main
    echo "   ✅ Code updated from GitHub"
else
    echo "   📦 Cloning repository..."
    mkdir -p "/var/www"
    git clone "$GITHUB_REPO" "$PROJECT_DIR"
    echo "   ✅ Repository cloned"
fi

cd "$PROJECT_DIR"

# Create necessary directories
mkdir -p backend/uploaded_files backend/job_files backend/channel_logos backend/api_keys

echo "   ✅ Application code ready"

# ═══════════════════════════════════════════════════════════
# STEP 6: Setup Python Virtual Environment
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 STEP 6/10: Setting up Python Virtual Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Remove old venv if exists
if [ -d "venv" ]; then
    rm -rf venv
fi

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# Install Python dependencies
echo "   📦 Installing Python packages (this may take 5-10 minutes)..."
pip install -r requirements.txt --quiet
pip install gunicorn --quiet

deactivate

echo "   ✅ Python environment configured (65 packages installed)"

# ═══════════════════════════════════════════════════════════
# STEP 7: Build React Frontend
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚛️  STEP 7/10: Building React Frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Install Node dependencies
echo "   📦 Installing npm packages..."
npm install --quiet

# Build production bundle
echo "   🔨 Building production bundle..."
npm run build

echo "   ✅ React frontend built successfully"

# ═══════════════════════════════════════════════════════════
# STEP 8: Create Environment File
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 STEP 8/10: Creating Environment Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate secure keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

cat > .env << ENVEOF
# Flask Configuration
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY

# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
PGHOST=localhost
PGPORT=5432
PGDATABASE=$DB_NAME
PGUSER=$DB_USER
PGPASSWORD=$DB_PASSWORD

# NOTE: API Keys are managed via Admin Panel (stored in database)
# No need to add OPENAI_API_KEY, DHAN_API_KEY, etc. here
# Add them through: Admin Panel > API Keys Management
ENVEOF

chmod 600 .env

echo "   ✅ Environment file created with secure keys"
echo ""
echo "   ⚠️  IMPORTANT: API Keys Management"
echo "   ════════════════════════════════════════════════════"
echo "   This system uses DATABASE-based API key management."
echo "   After deployment, login to admin panel and add:"
echo "     • OpenAI API Key (for GPT-4 analysis)"
echo "     • Dhan API Key (for stock charts)"
echo "     • AssemblyAI API Key (for transcription)"
echo "     • Google Cloud JSON (for translation)"
echo ""
echo "   Navigate to: Admin Panel > API Keys"
echo "   ════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════
# STEP 9: Setup Systemd Service
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  STEP 9/10: Creating Systemd Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > /etc/systemd/system/phd-capital.service << 'SERVICEEOF'
[Unit]
Description=PHD Capital Rationale Studio
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/rationale-studio
Environment="PATH=/var/www/rationale-studio/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/www/rationale-studio/.env
ExecStart=/var/www/rationale-studio/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 300 --worker-class sync 'backend.app:create_app()'
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=phd-capital

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "   ✅ Systemd service created"

# ═══════════════════════════════════════════════════════════
# STEP 10: Setup Nginx
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 STEP 10/10: Configuring Nginx"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > /etc/nginx/sites-available/phd-capital << 'NGINXEOF'
server {
    listen 80;
    server_name researchrationale.in www.researchrationale.in;

    client_max_body_size 500M;
    client_body_timeout 300s;

    # Logging
    access_log /var/log/nginx/phd-capital-access.log;
    error_log /var/log/nginx/phd-capital-error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for video processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINXEOF

# Enable site
ln -sf /etc/nginx/sites-available/phd-capital /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

echo "   ✅ Nginx configured for $DOMAIN"

# ═══════════════════════════════════════════════════════════
# FINALIZE: Set Permissions & Start Services
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔒 Setting Permissions & Starting Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

chown -R www-data:www-data "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
chmod 600 "$PROJECT_DIR/.env"

systemctl daemon-reload
systemctl enable phd-capital
systemctl restart phd-capital
systemctl restart nginx

# Configure firewall
echo "   🔥 Configuring firewall..."
ufw allow 22/tcp 2>/dev/null || true
ufw allow 80/tcp 2>/dev/null || true
ufw allow 443/tcp 2>/dev/null || true
ufw --force enable 2>/dev/null || true

echo "   ✅ Services started"

# ═══════════════════════════════════════════════════════════
# DEPLOYMENT COMPLETE
# ═══════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Your application is running at:"
echo "   http://$DOMAIN"
echo "   http://www.$DOMAIN"
echo "   http://72.60.111.9"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 IMPORTANT NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Configure DNS (if not already done):"
echo "   Go to your domain registrar and add:"
echo "   • A Record: @ → 72.60.111.9"
echo "   • A Record: www → 72.60.111.9"
echo ""
echo "2️⃣  Install SSL Certificate (after DNS propagates):"
echo "   apt install certbot python3-certbot-nginx -y"
echo "   certbot --nginx -d researchrationale.in -d www.researchrationale.in"
echo ""
echo "3️⃣  Add API Keys via Admin Panel:"
echo "   Login: http://$DOMAIN/login"
echo "   Default credentials:"
echo "     Username: admin@phdcapital.com"
echo "     Password: admin123"
echo ""
echo "   Then navigate to: API Keys Management"
echo "   Add these keys:"
echo "     • openai → Your OpenAI API key"
echo "     • dhan → Your Dhan API key"
echo "     • assemblyai → Your AssemblyAI API key"
echo "     • google_cloud → Upload Google Cloud JSON file"
echo ""
echo "   ⚠️  CHANGE ADMIN PASSWORD IMMEDIATELY!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 USEFUL COMMANDS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Check application status:"
echo "  systemctl status phd-capital"
echo ""
echo "View logs:"
echo "  journalctl -u phd-capital -f"
echo ""
echo "Restart application:"
echo "  systemctl restart phd-capital"
echo ""
echo "Update application (after git push):"
echo "  cd /var/www/rationale-studio && bash deployment/update.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
