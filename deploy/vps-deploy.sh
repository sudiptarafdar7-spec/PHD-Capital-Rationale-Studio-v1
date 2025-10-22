#!/bin/bash
set -e

echo "=========================================="
echo "PHD Capital Rationale Studio - VPS Deploy"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use: sudo bash vps-deploy.sh)"
    exit 1
fi

# Configuration
APP_DIR="/var/www/phd-capital"
APP_USER="www-data"
DOMAIN="${1:-localhost}"

echo "📋 Configuration:"
echo "   App Directory: $APP_DIR"
echo "   Domain: $DOMAIN"
echo ""

# Step 1: Install system dependencies
echo "📦 Step 1/8: Installing system dependencies..."
apt update
apt install -y python3.11 python3-pip python3.11-venv nodejs npm postgresql nginx git ffmpeg curl

# Step 2: Install yt-dlp
echo "📦 Step 2/8: Installing yt-dlp..."
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
chmod a+rx /usr/local/bin/yt-dlp

# Step 3: Create PostgreSQL database
echo "🗄️  Step 3/8: Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE phd_capital;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER phd_user WITH PASSWORD 'ChangeMeInProduction123!';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE phd_capital TO phd_user;"
sudo -u postgres psql -c "ALTER DATABASE phd_capital OWNER TO phd_user;"

# Step 4: Clone/update application
echo "📥 Step 4/8: Setting up application..."
if [ -d "$APP_DIR" ]; then
    echo "   Directory exists, pulling latest changes..."
    cd $APP_DIR
    git pull
else
    echo "   Cloning repository..."
    mkdir -p /var/www
    # Replace with your git repository URL
    echo "   ⚠️  Please clone your repository to $APP_DIR manually:"
    echo "      git clone <your-repo-url> $APP_DIR"
    echo "      Then run this script again."
    exit 1
fi

cd $APP_DIR

# Step 5: Install Python dependencies
echo "🐍 Step 5/8: Installing Python dependencies..."
pip install -r requirements.txt
pip install gunicorn

# Step 6: Build React frontend
echo "⚛️  Step 6/8: Building React frontend..."
npm install
npm run build

# Step 7: Create environment file
echo "🔐 Step 7/8: Creating environment file..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > $APP_DIR/.env << 'ENVEOF'
# Database
DATABASE_URL=postgresql://phd_user:ChangeMeInProduction123!@localhost/phd_capital
PGHOST=localhost
PGPORT=5432
PGDATABASE=phd_capital
PGUSER=phd_user
PGPASSWORD=ChangeMeInProduction123!

# Flask
SECRET_KEY=change-this-to-random-secret-key-in-production
JWT_SECRET_KEY=change-this-to-another-random-secret-key

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your-openai-api-key-here
DHAN_API_KEY=your-dhan-api-key-here
GOOGLE_APPLICATION_CREDENTIALS_JSON=your-google-translate-credentials-json-here
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here
ENVEOF
    echo "   ⚠️  IMPORTANT: Edit $APP_DIR/.env and add your API keys!"
else
    echo "   .env file already exists, skipping..."
fi

# Step 8: Create systemd service
echo "⚙️  Step 8/8: Creating systemd service..."
cat > /etc/systemd/system/phd-capital.service << 'EOF'
[Unit]
Description=PHD Capital Rationale Studio
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/phd-capital
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/www/phd-capital/.env
ExecStart=/usr/local/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 'backend.app:create_app()'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo "🌐 Creating Nginx configuration..."
cat > /etc/nginx/sites-available/phd-capital << EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/phd-capital /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
nginx -t

# Set permissions
echo "🔒 Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Reload services
echo "🔄 Starting services..."
systemctl daemon-reload
systemctl enable phd-capital
systemctl restart phd-capital
systemctl restart nginx

# Setup firewall
echo "🔥 Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "📝 Next Steps:"
echo "   1. Edit $APP_DIR/.env and add your API keys"
echo "   2. Restart the service: systemctl restart phd-capital"
echo "   3. Check status: systemctl status phd-capital"
echo "   4. View logs: journalctl -u phd-capital -f"
echo ""
echo "🌐 Your app should be running at: http://$DOMAIN"
echo ""
echo "🔐 To add SSL certificate (recommended):"
echo "   apt install certbot python3-certbot-nginx"
echo "   certbot --nginx -d $DOMAIN"
echo ""
