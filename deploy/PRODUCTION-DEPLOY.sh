#!/bin/bash
#
# PHD Capital Rationale Studio - Production Deployment Script
# Customized for: researchrationale.in (72.60.111.9)
#
# This script includes all fixes for issues encountered during initial deployment:
# - Uses Python virtual environment (fixes pytz and urllib3 errors)
# - Handles Ubuntu 24.04 system-managed packages
# - Auto-clones GitHub repository
# - Builds React frontend
# - Configures Nginx with proper domain
# - Sets up systemd service with venv
#

set -e

echo "================================================================"
echo "  PHD Capital Rationale Studio - Production Deployment"
echo "  Domain: researchrationale.in"
echo "  VPS IP: 72.60.111.9"
echo "================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo bash deploy/PRODUCTION-DEPLOY.sh"
    exit 1
fi

# Configuration
APP_DIR="/var/www/phd-capital"
DOMAIN="researchrationale.in"
REPO_URL="https://github.com/sudiptarafdar7-spec/Rationale-Studio.git"

echo "📋 Configuration:"
echo "   App Directory: $APP_DIR"
echo "   Domain: $DOMAIN"
echo "   Repository: $REPO_URL"
echo ""

# ============================================================
# STEP 1: Install System Dependencies
# ============================================================
echo "📦 Step 1/9: Installing system dependencies..."
apt update -qq
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    nodejs \
    npm \
    postgresql \
    nginx \
    git \
    ffmpeg \
    curl \
    build-essential \
    software-properties-common \
    2>/dev/null

echo "   ✅ System dependencies installed"

# ============================================================
# STEP 2: Install yt-dlp
# ============================================================
echo "📦 Step 2/9: Installing yt-dlp..."
if [ ! -f /usr/local/bin/yt-dlp ]; then
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
    chmod a+rx /usr/local/bin/yt-dlp
    echo "   ✅ yt-dlp installed"
else
    echo "   ✅ yt-dlp already installed"
fi

# ============================================================
# STEP 3: Setup PostgreSQL Database
# ============================================================
echo "🗄️  Step 3/9: Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE phd_capital;" 2>/dev/null || echo "   Database already exists"
sudo -u postgres psql -c "CREATE USER phd_user WITH PASSWORD 'ChangeMeInProduction123!';" 2>/dev/null || echo "   User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE phd_capital TO phd_user;" 2>/dev/null
sudo -u postgres psql -c "ALTER DATABASE phd_capital OWNER TO phd_user;" 2>/dev/null
echo "   ✅ Database configured"

# ============================================================
# STEP 4: Clone/Update Application
# ============================================================
echo "📥 Step 4/9: Setting up application code..."
if [ -d "$APP_DIR" ]; then
    echo "   Directory exists, pulling latest changes..."
    cd $APP_DIR
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    echo "   Cloning repository..."
    mkdir -p /var/www
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# Create necessary directories
mkdir -p backend/uploaded_files backend/job_files backend/channel_logos backend/api_keys
echo "   ✅ Application code ready"

# ============================================================
# STEP 5: Setup Python Virtual Environment
# ============================================================
echo "🐍 Step 5/9: Setting up Python virtual environment..."
cd $APP_DIR

# Remove old venv if exists
if [ -d "venv" ]; then
    echo "   Removing old virtual environment..."
    rm -rf venv
fi

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip inside venv
pip install --upgrade pip --quiet

# Install Python dependencies inside venv
echo "   Installing Python packages (this may take a few minutes)..."
pip install -r requirements.txt --quiet
pip install gunicorn --quiet

deactivate
echo "   ✅ Python environment configured with all dependencies"

# ============================================================
# STEP 6: Build React Frontend
# ============================================================
echo "⚛️  Step 6/9: Building React frontend..."
cd $APP_DIR

# Install Node dependencies
npm install --quiet

# Build production bundle
npm run build

echo "   ✅ React frontend built successfully"

# ============================================================
# STEP 7: Create Environment File
# ============================================================
echo "🔐 Step 7/9: Creating environment file..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > $APP_DIR/.env << 'ENVEOF'
# Database Configuration
DATABASE_URL=postgresql://phd_user:ChangeMeInProduction123!@localhost/phd_capital
PGHOST=localhost
PGPORT=5432
PGDATABASE=phd_capital
PGUSER=phd_user
PGPASSWORD=ChangeMeInProduction123!

# Flask Configuration
SECRET_KEY=CHANGE-THIS-TO-RANDOM-SECRET-KEY
JWT_SECRET_KEY=CHANGE-THIS-TO-ANOTHER-RANDOM-KEY

# API Keys (REQUIRED - Add your actual keys)
OPENAI_API_KEY=your-openai-api-key-here
DHAN_API_KEY=your-dhan-api-key-here
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here
GOOGLE_APPLICATION_CREDENTIALS_JSON={}
ENVEOF
    echo "   ⚠️  IMPORTANT: Edit $APP_DIR/.env and add your API keys!"
    echo ""
    echo "   Generate secure keys with:"
    echo "   python3 -c \"import secrets; print(secrets.token_hex(32))\""
    echo ""
else
    echo "   ✅ .env file already exists"
fi

# ============================================================
# STEP 8: Setup Systemd Service
# ============================================================
echo "⚙️  Step 8/9: Creating systemd service..."
cat > /etc/systemd/system/phd-capital.service << 'EOF'
[Unit]
Description=PHD Capital Rationale Studio
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/phd-capital
Environment="PATH=/var/www/phd-capital/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/www/phd-capital/.env
ExecStart=/var/www/phd-capital/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 --worker-class sync 'backend.app:create_app()'
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=phd-capital

[Install]
WantedBy=multi-user.target
EOF

echo "   ✅ Systemd service created"

# ============================================================
# STEP 9: Setup Nginx
# ============================================================
echo "🌐 Step 9/9: Configuring Nginx..."
cat > /etc/nginx/sites-available/phd-capital << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    client_max_body_size 500M;
    client_body_timeout 300s;

    # Logging
    access_log /var/log/nginx/phd-capital-access.log;
    error_log /var/log/nginx/phd-capital-error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/phd-capital /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
if nginx -t 2>/dev/null; then
    echo "   ✅ Nginx configured successfully"
else
    echo "   ❌ Nginx configuration error"
    nginx -t
    exit 1
fi

# ============================================================
# FINALIZE: Set Permissions & Start Services
# ============================================================
echo ""
echo "🔒 Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod 600 $APP_DIR/.env

echo "🔄 Starting services..."
systemctl daemon-reload
systemctl enable phd-capital
systemctl restart phd-capital
systemctl restart nginx

# Setup firewall
echo "🔥 Configuring firewall..."
ufw allow 22/tcp 2>/dev/null || true
ufw allow 80/tcp 2>/dev/null || true
ufw allow 443/tcp 2>/dev/null || true
ufw --force enable 2>/dev/null || true

# ============================================================
# DEPLOYMENT COMPLETE
# ============================================================
echo ""
echo "================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================================"
echo ""
echo "🌐 Your application is running at:"
echo "   http://$DOMAIN"
echo "   http://www.$DOMAIN"
echo "   http://72.60.111.9"
echo ""
echo "📝 IMPORTANT NEXT STEPS:"
echo ""
echo "1️⃣  Configure DNS (if not done):"
echo "   Add A records pointing to: 72.60.111.9"
echo "   - @ → 72.60.111.9"
echo "   - www → 72.60.111.9"
echo ""
echo "2️⃣  Add API Keys:"
echo "   nano $APP_DIR/.env"
echo ""
echo "   Generate secure keys:"
echo "   python3 -c \"import secrets; print('SECRET_KEY=' + secrets.token_hex(32))\""
echo "   python3 -c \"import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))\""
echo ""
echo "   Required API keys:"
echo "   - OPENAI_API_KEY (https://platform.openai.com/api-keys)"
echo "   - DHAN_API_KEY (from your Dhan account)"
echo "   - ASSEMBLYAI_API_KEY (https://www.assemblyai.com/)"
echo "   - GOOGLE_APPLICATION_CREDENTIALS_JSON (Google Cloud Translation)"
echo ""
echo "3️⃣  Restart after adding keys:"
echo "   systemctl restart phd-capital"
echo ""
echo "4️⃣  Install SSL certificate (after DNS works):"
echo "   apt install certbot python3-certbot-nginx -y"
echo "   certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""
echo "================================================================"
echo "📊 USEFUL COMMANDS:"
echo "================================================================"
echo ""
echo "Check service status:"
echo "  systemctl status phd-capital"
echo ""
echo "View logs:"
echo "  journalctl -u phd-capital -f"
echo ""
echo "Restart application:"
echo "  systemctl restart phd-capital"
echo ""
echo "Update application (after git push):"
echo "  cd /var/www/phd-capital && bash deploy/update.sh"
echo ""
echo "================================================================"
echo "🎊 Default Admin Login:"
echo "================================================================"
echo "  Username: admin@phdcapital.com"
echo "  Password: admin123"
echo ""
echo "  ⚠️  CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN!"
echo "================================================================"
