# PHD Capital Rationale Studio - VPS Deployment Guide

## 🚀 Quick Deployment to Hostinger VPS

This guide will help you deploy your application to a Hostinger VPS server in under 10 minutes.

---

## 📋 Prerequisites

- Hostinger VPS with Ubuntu 20.04/22.04 or Debian 11/12
- Root/sudo access to the server
- Domain name pointed to your VPS IP (optional but recommended)
- SSH access configured

---

## 🎯 One-Command Deployment

### Step 1: Connect to Your VPS

```bash
ssh root@your-vps-ip-address
```

### Step 2: Clone Your Repository

```bash
cd /var/www
git clone <your-github-repo-url> phd-capital
cd phd-capital
```

### Step 3: Run the Deployment Script

```bash
chmod +x deploy/vps-deploy.sh
sudo bash deploy/vps-deploy.sh your-domain.com
```

**Note:** Replace `your-domain.com` with your actual domain, or use `localhost` if you don't have a domain.

### Step 4: Configure Environment Variables

Edit the `.env` file with your API keys:

```bash
nano /var/www/phd-capital/.env
```

**Required API Keys:**
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `DHAN_API_KEY` - Get from your Dhan trading account
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Google Cloud Translation API credentials
- `ASSEMBLYAI_API_KEY` - Get from https://www.assemblyai.com/

**Security Keys (generate random strings):**
```bash
# Generate secure random keys
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Restart the Application

```bash
systemctl restart phd-capital
systemctl status phd-capital
```

---

## 🎉 Your App is Live!

Visit your domain: `http://your-domain.com`

**Default Admin Credentials:**
- Username: `admin@phdcapital.com`
- Password: `admin123`

⚠️ **IMPORTANT:** Change the admin password immediately after first login!

---

## 🔐 Add SSL Certificate (Recommended)

Secure your app with free SSL from Let's Encrypt:

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

Your app will now be accessible at: `https://your-domain.com`

---

## 📊 Monitoring & Management

### Check Application Status

```bash
systemctl status phd-capital
```

### View Live Logs

```bash
journalctl -u phd-capital -f
```

### Restart Application

```bash
systemctl restart phd-capital
```

### Restart Nginx

```bash
systemctl restart nginx
```

### Check Nginx Configuration

```bash
nginx -t
```

---

## 🔄 Updating Your Application

When you push new code to GitHub:

```bash
cd /var/www/phd-capital
git pull
npm run build
systemctl restart phd-capital
```

---

## 🗄️ Database Management

### Connect to PostgreSQL

```bash
sudo -u postgres psql -d phd_capital
```

### Create Database Backup

```bash
sudo -u postgres pg_dump phd_capital > backup_$(date +%Y%m%d).sql
```

### Restore Database Backup

```bash
sudo -u postgres psql phd_capital < backup_20251022.sql
```

---

## 📁 Important File Locations

- **Application:** `/var/www/phd-capital`
- **Environment:** `/var/www/phd-capital/.env`
- **Systemd Service:** `/etc/systemd/system/phd-capital.service`
- **Nginx Config:** `/etc/nginx/sites-available/phd-capital`
- **Logs:** `journalctl -u phd-capital`
- **Uploaded Files:** `/var/www/phd-capital/backend/uploaded_files/`
- **Job Files:** `/var/www/phd-capital/backend/job_files/`

---

## 🐛 Troubleshooting

### App Won't Start

```bash
# Check logs
journalctl -u phd-capital -n 50

# Check if port 5000 is in use
netstat -tlnp | grep 5000

# Verify environment file
cat /var/www/phd-capital/.env
```

### Database Connection Error

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test database connection
sudo -u postgres psql -d phd_capital -c "SELECT 1;"
```

### Nginx 502 Bad Gateway

```bash
# Check if Gunicorn is running
systemctl status phd-capital

# Check Nginx error logs
tail -f /var/log/nginx/error.log
```

### Permission Issues

```bash
# Fix permissions
chown -R www-data:www-data /var/www/phd-capital
chmod -R 755 /var/www/phd-capital
```

---

## 🔥 Firewall Configuration

The deployment script automatically configures UFW firewall:

```bash
# Check firewall status
ufw status

# Allow additional ports if needed
ufw allow 8080/tcp
```

---

## 📊 Performance Optimization

### Increase Gunicorn Workers

Edit `/etc/systemd/system/phd-capital.service`:

```ini
ExecStart=/usr/local/bin/gunicorn --bind 127.0.0.1:5000 --workers 8 --timeout 120 'backend.app:create_app()'
```

Then reload:
```bash
systemctl daemon-reload
systemctl restart phd-capital
```

### Enable Nginx Caching

Add to your Nginx config:

```nginx
location /static/ {
    alias /var/www/phd-capital/build/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 🆘 Support

If you encounter issues:

1. **Check Logs:** `journalctl -u phd-capital -f`
2. **Verify Environment:** Ensure all API keys are set in `.env`
3. **Test Database:** Connect to PostgreSQL and verify tables exist
4. **Check Permissions:** Ensure www-data owns application files

---

## 📝 What the Script Does

The automated deployment script:

1. ✅ Installs Python 3.11, Node.js, PostgreSQL, Nginx, ffmpeg
2. ✅ Creates PostgreSQL database and user
3. ✅ Installs all Python dependencies from requirements.txt
4. ✅ Builds React frontend (npm run build)
5. ✅ Creates systemd service for automatic startup
6. ✅ Configures Nginx reverse proxy
7. ✅ Sets up firewall rules
8. ✅ Starts the application

**Total Deployment Time:** ~5-10 minutes

---

## 🎯 Production Checklist

Before going live:

- [ ] Changed default admin password
- [ ] Set secure SECRET_KEY and JWT_SECRET_KEY
- [ ] Added all required API keys to .env
- [ ] Configured SSL certificate (HTTPS)
- [ ] Set up database backups
- [ ] Configured domain DNS
- [ ] Tested all features (video upload, PDF generation)
- [ ] Enabled firewall
- [ ] Set up monitoring/alerting

---

## 💰 Estimated VPS Requirements

**Minimum:**
- 2 CPU cores
- 4 GB RAM
- 50 GB SSD storage
- Ubuntu 22.04 LTS

**Recommended:**
- 4 CPU cores
- 8 GB RAM
- 100 GB SSD storage
- Ubuntu 22.04 LTS

---

**🎉 Congratulations! Your PHD Capital Rationale Studio is now deployed on Hostinger VPS!**
