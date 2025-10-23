# 🚀 Complete Production Deployment Guide
## PHD Capital Rationale Studio on Hostinger VPS

---

## 📋 Server Information
- **VPS IP:** 72.60.111.9
- **Domain:** researchrationale.in
- **Repository:** https://github.com/sudiptarafdar7-spec/Rationale-Studio

---

## ✅ Pre-Deployment Checklist

Before starting deployment, ensure:

- [ ] You have SSH root access to 72.60.111.9
- [ ] VPS is running Ubuntu 20.04/22.04/24.04
- [ ] You have pushed all code to GitHub
- [ ] You have your API keys ready:
  - OpenAI API Key
  - Dhan API Key
  - AssemblyAI API Key
  - Google Cloud Translation credentials

---

## 🎯 One-Command Deployment

### Step 1: SSH into Your VPS

```bash
ssh root@72.60.111.9
```

### Step 2: Download and Run Deployment Script

```bash
# Download the script
curl -o deploy.sh https://raw.githubusercontent.com/sudiptarafdar7-spec/Rationale-Studio/main/deploy/PRODUCTION-DEPLOY.sh

# Make it executable
chmod +x deploy.sh

# Run deployment
bash deploy.sh
```

**That's it!** The script handles everything automatically:
- ✅ Installs all system dependencies
- ✅ Creates PostgreSQL database
- ✅ Clones your GitHub repository
- ✅ Sets up Python virtual environment (fixes pytz/urllib3 errors)
- ✅ Installs all 65 Python packages
- ✅ Builds React frontend
- ✅ Configures Nginx
- ✅ Creates systemd service
- ✅ Starts your application

**⏱️ Deployment time: ~5-10 minutes**

---

## 🔐 Post-Deployment: Add API Keys

After deployment completes:

### 1. Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

### 2. Edit Environment File

```bash
nano /var/www/phd-capital/.env
```

Update these values:

```env
# Paste the generated keys
SECRET_KEY=your-generated-64-char-hex-key-here
JWT_SECRET_KEY=your-generated-64-char-hex-key-here

# Add your API keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
DHAN_API_KEY=your-dhan-key
ASSEMBLYAI_API_KEY=your-assemblyai-key
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}

# Database password (change from default)
DATABASE_URL=postgresql://phd_user:YourStrongPassword@localhost/phd_capital
PGPASSWORD=YourStrongPassword
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

### 3. Change Database Password (Recommended)

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Change password
ALTER USER phd_user WITH PASSWORD 'YourNewStrongPassword123!';
\q

# Update .env file with new password
nano /var/www/phd-capital/.env
```

### 4. Restart Application

```bash
systemctl restart phd-capital
systemctl status phd-capital
```

You should see: **Active: active (running)** ✅

---

## 🌐 DNS Configuration

### Configure Your Domain Registrar

Add these DNS records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 72.60.111.9 | 3600 |
| A | www | 72.60.111.9 | 3600 |

### Verify DNS Propagation

```bash
# Check if DNS is working
nslookup researchrationale.in
dig researchrationale.in +short
ping researchrationale.in

# Should all show: 72.60.111.9
```

**⏱️ DNS propagation: 5-60 minutes**

---

## 🔒 Install SSL Certificate

### Once DNS is working:

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate (automatic Nginx configuration)
certbot --nginx -d researchrationale.in -d www.researchrationale.in
```

**Follow the prompts:**
1. Enter your email address
2. Agree to Terms of Service (Y)
3. Share email (Y or N)

Certbot will automatically:
- ✅ Get free SSL certificate
- ✅ Configure Nginx for HTTPS
- ✅ Set up HTTP → HTTPS redirect
- ✅ Enable auto-renewal

### Verify SSL is Working

Visit: **https://researchrationale.in**

You should see 🔒 in the address bar!

### Test Auto-Renewal

```bash
certbot renew --dry-run
```

Should show: **"Congratulations, all renewals succeeded"**

---

## 🎊 Access Your Application

### URLs:
- **HTTPS:** https://researchrationale.in (after SSL)
- **HTTP:** http://researchrationale.in
- **WWW:** https://www.researchrationale.in
- **IP:** http://72.60.111.9 (works immediately)

### Default Admin Login:
- **Username:** admin@phdcapital.com
- **Password:** admin123

⚠️ **CHANGE PASSWORD IMMEDIATELY!**

---

## 📊 Monitoring & Management

### Check Application Status

```bash
systemctl status phd-capital
```

**Expected output:**
```
● phd-capital.service - PHD Capital Rationale Studio
     Active: active (running)
```

### View Live Logs

```bash
# Follow logs in real-time
journalctl -u phd-capital -f

# View last 100 lines
journalctl -u phd-capital -n 100

# Filter by time
journalctl -u phd-capital --since "1 hour ago"
```

### Restart Application

```bash
systemctl restart phd-capital
```

### Check Nginx

```bash
# Check status
systemctl status nginx

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx

# View Nginx logs
tail -f /var/log/nginx/phd-capital-access.log
tail -f /var/log/nginx/phd-capital-error.log
```

---

## 🔄 Updating Your Application

When you push new code to GitHub:

### Method 1: Automatic Update Script

```bash
cd /var/www/phd-capital
bash deploy/update.sh
```

### Method 2: Manual Update

```bash
cd /var/www/phd-capital

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update Python dependencies
pip install -r requirements.txt

# Deactivate venv
deactivate

# Rebuild frontend
npm install
npm run build

# Restart application
systemctl restart phd-capital
```

---

## 🗄️ Database Management

### Connect to Database

```bash
sudo -u postgres psql -d phd_capital
```

### Common Commands

```sql
-- List all tables
\dt

-- View users
SELECT * FROM users;

-- View jobs
SELECT id, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;

-- Exit
\q
```

### Backup Database

```bash
# Create backup
sudo -u postgres pg_dump phd_capital > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql
```

### Restore Database

```bash
# Restore from backup
sudo -u postgres psql phd_capital < backup_20251023.sql
```

---

## 🐛 Troubleshooting

### Application Won't Start

```bash
# Check logs for errors
journalctl -u phd-capital -n 100

# Common issues:
# 1. Missing API keys in .env
# 2. Database connection error
# 3. Port 5000 already in use
```

**Fix:**
```bash
# Verify .env file exists and has all keys
cat /var/www/phd-capital/.env

# Test database connection
sudo -u postgres psql -d phd_capital -c "SELECT 1;"

# Check if port 5000 is free
netstat -tlnp | grep 5000
```

### Nginx 502 Bad Gateway

```bash
# Check if backend is running
systemctl status phd-capital

# View backend logs
journalctl -u phd-capital -n 50

# Restart both services
systemctl restart phd-capital
systemctl restart nginx
```

### Import Error: No module named 'xyz'

```bash
# Reinstall dependencies in venv
cd /var/www/phd-capital
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
deactivate
systemctl restart phd-capital
```

### Permission Errors

```bash
# Fix ownership
chown -R www-data:www-data /var/www/phd-capital

# Fix permissions
chmod -R 755 /var/www/phd-capital
chmod 600 /var/www/phd-capital/.env
```

### Video Processing Fails

```bash
# Check ffmpeg is installed
ffmpeg -version

# Check yt-dlp is installed
yt-dlp --version

# Reinstall if needed
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
chmod a+rx /usr/local/bin/yt-dlp
```

---

## 🔥 Firewall Configuration

### Check Firewall Status

```bash
ufw status
```

### Allow Additional Ports

```bash
# Allow custom port
ufw allow 8080/tcp

# Allow IP range
ufw allow from 192.168.1.0/24
```

---

## ⚡ Performance Optimization

### Increase Gunicorn Workers

Edit `/etc/systemd/system/phd-capital.service`:

```ini
ExecStart=/var/www/phd-capital/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 8 --timeout 300 'backend.app:create_app()'
```

Then reload:
```bash
systemctl daemon-reload
systemctl restart phd-capital
```

### Enable Nginx Caching

Add to `/etc/nginx/sites-available/phd-capital`:

```nginx
location /static/ {
    alias /var/www/phd-capital/build/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

Then restart:
```bash
nginx -t && systemctl restart nginx
```

---

## 📋 Important File Locations

| File/Directory | Purpose |
|----------------|---------|
| `/var/www/phd-capital/` | Application root |
| `/var/www/phd-capital/.env` | Environment variables & API keys |
| `/var/www/phd-capital/venv/` | Python virtual environment |
| `/var/www/phd-capital/build/` | React production build |
| `/var/www/phd-capital/backend/` | Flask backend |
| `/etc/systemd/system/phd-capital.service` | Systemd service config |
| `/etc/nginx/sites-available/phd-capital` | Nginx site config |
| `/var/log/nginx/phd-capital-*.log` | Nginx logs |
| `journalctl -u phd-capital` | Application logs |

---

## 🔐 Security Best Practices

### 1. Change Default Passwords

- ✅ Admin user password
- ✅ Database password
- ✅ SECRET_KEY and JWT_SECRET_KEY

### 2. Keep System Updated

```bash
apt update
apt upgrade -y
```

### 3. Setup Automatic Security Updates

```bash
apt install unattended-upgrades -y
dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Monitor Failed Login Attempts

```bash
# Install fail2ban
apt install fail2ban -y

# Check banned IPs
fail2ban-client status sshd
```

### 5. Backup Regularly

```bash
# Create backup script
cat > /root/backup-phd-capital.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR
sudo -u postgres pg_dump phd_capital | gzip > $BACKUP_DIR/db_$(date +%Y%m%d).sql.gz
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
EOF

chmod +x /root/backup-phd-capital.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line: 0 2 * * * /root/backup-phd-capital.sh
```

---

## 📞 Support & Resources

### Documentation
- **Full Guide:** `/var/www/phd-capital/deploy/COMPLETE-GUIDE.md`
- **Quick Start:** `/var/www/phd-capital/deploy/QUICKSTART.md`
- **Deployment Script:** `/var/www/phd-capital/deploy/PRODUCTION-DEPLOY.sh`

### Useful Commands Reference
```bash
# Application
systemctl status phd-capital
systemctl restart phd-capital
journalctl -u phd-capital -f

# Nginx
systemctl status nginx
nginx -t
systemctl restart nginx

# Database
sudo -u postgres psql -d phd_capital

# Updates
cd /var/www/phd-capital && bash deploy/update.sh

# SSL
certbot renew
certbot certificates
```

---

## ✅ Production Deployment Checklist

- [ ] VPS accessible via SSH
- [ ] Deployment script executed successfully
- [ ] API keys added to .env
- [ ] Database password changed
- [ ] Secret keys generated and configured
- [ ] DNS configured and propagated
- [ ] SSL certificate installed
- [ ] Application accessible via HTTPS
- [ ] Admin password changed from default
- [ ] Test video upload and processing
- [ ] Test PDF generation
- [ ] Logs show no errors
- [ ] Automatic backups configured
- [ ] Monitoring set up

---

**🎉 Congratulations! Your PHD Capital Rationale Studio is now live in production!**

**Production URL:** https://researchrationale.in
