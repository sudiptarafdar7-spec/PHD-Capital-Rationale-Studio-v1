# 🚀 PHD Capital Rationale Studio - Complete Deployment Guide

## Server Information
- **VPS IP:** 72.60.111.9
- **Domain:** researchrationale.in
- **OS:** Ubuntu 24.04 LTS
- **Project Folder:** Rationale Studio
- **GitHub Repository:** https://github.com/sudiptarafdar7-spec/PHD-Capital-Rationale-Studio-v1.git

---

## 📋 Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Connecting via SSH (Windows PowerShell)](#connecting-via-ssh-windows-powershell)
3. [One-Command Deployment](#one-command-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [DNS Configuration](#dns-configuration)
6. [SSL Certificate Installation](#ssl-certificate-installation)
7. [API Keys Management (Database-Based)](#api-keys-management-database-based)
8. [Monitoring & Management](#monitoring--management)
9. [Updating Your Application](#updating-your-application)
10. [Troubleshooting](#troubleshooting)

---

## ✅ Pre-Deployment Checklist

Before starting, ensure you have:

- [ ] VPS IP Address: **72.60.111.9**
- [ ] Root password for VPS
- [ ] Domain registered: **researchrationale.in**
- [ ] Code pushed to GitHub repository
- [ ] API keys ready:
  - OpenAI API Key (https://platform.openai.com/api-keys)
  - Dhan API Key (from your Dhan account)
  - AssemblyAI API Key (https://www.assemblyai.com/)
  - Google Cloud Translation JSON credentials

---

## 🔌 Connecting via SSH (Windows PowerShell)

### Step 1: Open PowerShell

Press `Windows + X`, then select **"Windows PowerShell"** or **"Terminal"**

### Step 2: Connect to Your VPS

```powershell
ssh root@72.60.111.9
```

**First time connecting?** You'll see:

```
The authenticity of host '72.60.111.9 (72.60.111.9)' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type `yes` and press Enter.

### Step 3: Enter Password

When prompted, enter your root password (you won't see characters as you type).

```
root@72.60.111.9's password: [type your password]
```

**Success!** You should see:

```
Welcome to Ubuntu 24.04 LTS
```

---

## 🚀 One-Command Deployment

### Step 1: Download Deployment Script

Once connected via SSH, run:

```bash
cd /root
curl -o deploy.sh https://raw.githubusercontent.com/sudiptarafdar7-spec/PHD-Capital-Rationale-Studio-v1/main/deployment/deploy.sh
```

### Step 2: Make Script Executable

```bash
chmod +x deploy.sh
```

### Step 3: Run Deployment

```bash
bash deploy.sh
```

**What happens next:**

The script will automatically:
1. ✅ Update system packages
2. ✅ Install Python 3, Node.js 20, PostgreSQL, Nginx, ffmpeg
3. ✅ Install yt-dlp for video downloads
4. ✅ Create PostgreSQL database: `phd_rationale_db`
5. ✅ Clone your GitHub repository
6. ✅ Create Python virtual environment
7. ✅ Install 65 Python packages (including Flask, OpenAI, pandas, etc.)
8. ✅ Install npm packages and build React frontend
9. ✅ Generate secure SECRET_KEY and JWT_SECRET_KEY
10. ✅ Create systemd service
11. ✅ Configure Nginx for researchrationale.in
12. ✅ Start application

**⏱️ Deployment time:** 5-10 minutes

### Expected Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DEPLOYMENT COMPLETE!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 Your application is running at:
   http://researchrationale.in
   http://www.researchrationale.in
   http://72.60.111.9
```

---

## 🔐 Post-Deployment Configuration

### 1. Verify Application is Running

```bash
systemctl status phd-capital
```

**Expected output:**

```
● phd-capital.service - PHD Capital Rationale Studio
   Active: active (running)
```

If you see `Active: active (running)` in **green**, your app is working! ✅

### 2. View Logs

```bash
journalctl -u phd-capital -f
```

Press `Ctrl + C` to stop viewing logs.

### 3. Test Application

Open your web browser and visit:

```
http://72.60.111.9
```

You should see the PHD Capital login page!

---

## 🌐 DNS Configuration

### Step 1: Login to Your Domain Registrar

Go to where you purchased **researchrationale.in** (e.g., GoDaddy, Namecheap, Google Domains).

### Step 2: Add DNS Records

Add these **A Records**:

| Type | Name/Host | Value/Points To | TTL |
|------|-----------|-----------------|-----|
| A | @ | 72.60.111.9 | 3600 |
| A | www | 72.60.111.9 | 3600 |

**Save changes.**

### Step 3: Wait for DNS Propagation

DNS changes take **5-60 minutes** to propagate globally.

### Step 4: Verify DNS is Working

On your **local computer**, open PowerShell and run:

```powershell
nslookup researchrationale.in
```

**Expected output:**

```
Name:    researchrationale.in
Address: 72.60.111.9
```

Once you see your IP address (72.60.111.9), DNS is working!

---

## 🔒 SSL Certificate Installation

**⚠️ Wait until DNS propagation is complete!**

### Step 1: Install Certbot

```bash
apt install certbot python3-certbot-nginx -y
```

### Step 2: Get SSL Certificate

```bash
certbot --nginx -d researchrationale.in -d www.researchrationale.in
```

### Step 3: Follow the Prompts

1. **Email address:** Enter your email for renewal notifications
2. **Terms of Service:** Type `Y` to agree
3. **Share email:** Type `Y` or `N` (your choice)

Certbot will:
- ✅ Get free SSL certificate from Let's Encrypt
- ✅ Automatically configure Nginx for HTTPS
- ✅ Set up HTTP → HTTPS redirect
- ✅ Enable auto-renewal (90 days)

### Step 4: Verify SSL

Open your browser and visit:

```
https://researchrationale.in
```

You should see a **🔒 lock icon** in the address bar!

### Step 5: Test Auto-Renewal

```bash
certbot renew --dry-run
```

**Expected output:**

```
Congratulations, all simulated renewals succeeded
```

---

## 🔑 API Keys Management (Database-Based)

**IMPORTANT:** This system uses **database-based API key management**, NOT `.env` files!

### Step 1: Login to Admin Panel

Open your browser:

```
https://researchrationale.in/login
```

**Default Admin Credentials:**
- Username: `admin@phdcapital.com`
- Password: `admin123`

### Step 2: Change Admin Password

⚠️ **IMMEDIATELY CHANGE THE DEFAULT PASSWORD!**

1. Click on your profile icon (top right)
2. Go to **Profile Settings**
3. Change password
4. Save changes

### Step 3: Navigate to API Keys Page

1. Click **API Keys** in the sidebar
2. You'll see the API Keys Management page

### Step 4: Add API Keys

Click **"Add API Key"** button for each provider:

#### OpenAI API Key

```
Provider: openai
Key Value: sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

Get your key: https://platform.openai.com/api-keys

#### Dhan API Key

```
Provider: dhan
Key Value: your-dhan-api-key-here
```

Get from your Dhan trading account.

#### AssemblyAI API Key

```
Provider: assemblyai
Key Value: your-assemblyai-key-here
```

Get your key: https://www.assemblyai.com/

#### Google Cloud Translation

```
Provider: google_cloud
Upload File: google-cloud.json
```

1. Click **Upload Google Cloud JSON**
2. Select your service account JSON file
3. Upload

### Step 5: Verify API Keys

You should see all 4 API keys listed with their providers:

- ✅ openai
- ✅ dhan
- ✅ assemblyai
- ✅ google_cloud

**Now your pipeline will work properly!**

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

Press `Ctrl + C` to stop.

### View Last 100 Log Lines

```bash
journalctl -u phd-capital -n 100
```

### View Logs from Last Hour

```bash
journalctl -u phd-capital --since "1 hour ago"
```

### Restart Application

```bash
systemctl restart phd-capital
```

### Check Nginx Status

```bash
systemctl status nginx
```

### View Nginx Logs

```bash
tail -f /var/log/nginx/phd-capital-access.log
tail -f /var/log/nginx/phd-capital-error.log
```

### Database Access

```bash
sudo -u postgres psql -d phd_rationale_db
```

Common commands:

```sql
-- List all tables
\dt

-- View users
SELECT * FROM users;

-- View jobs
SELECT id, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;

-- View API keys (ONLY provider names, NOT values)
SELECT provider, created_at FROM api_keys;

-- Exit
\q
```

---

## 🔄 Updating Your Application

When you push new code to GitHub:

### Step 1: SSH to Your Server

```powershell
ssh root@72.60.111.9
```

### Step 2: Run Update Script

```bash
cd "/var/www/Rationale Studio"
bash deployment/update.sh
```

**What it does:**

1. ✅ Pulls latest code from GitHub
2. ✅ Updates Python dependencies
3. ✅ Updates npm packages
4. ✅ Rebuilds React frontend
5. ✅ Restarts application

**⏱️ Update time:** 2-3 minutes

---

## 🐛 Troubleshooting

### Issue: Application Won't Start

**Check logs:**

```bash
journalctl -u phd-capital -n 100
```

**Common causes:**

1. Database connection error
2. Port 5000 already in use
3. Permission issues

**Fix:**

```bash
# Restart services
systemctl restart postgresql
systemctl restart phd-capital

# Check database
sudo -u postgres psql -l
```

### Issue: Nginx 502 Bad Gateway

**Cause:** Backend not running

**Fix:**

```bash
systemctl status phd-capital
systemctl restart phd-capital
systemctl restart nginx
```

### Issue: "Module not found" Error

**Cause:** Missing Python packages

**Fix:**

```bash
cd "/var/www/Rationale Studio"
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
deactivate
systemctl restart phd-capital
```

### Issue: Permission Denied Errors

**Fix:**

```bash
cd "/var/www/Rationale Studio"
chown -R www-data:www-data .
chmod -R 755 .
chmod 600 .env
systemctl restart phd-capital
```

### Issue: Video Processing Fails

**Check yt-dlp:**

```bash
yt-dlp --version
```

**Update yt-dlp:**

```bash
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
chmod a+rx /usr/local/bin/yt-dlp
```

**Check ffmpeg:**

```bash
ffmpeg -version
```

### Issue: API Keys Not Working

**Verify in database:**

```bash
sudo -u postgres psql -d phd_rationale_db
SELECT provider FROM api_keys;
\q
```

**Re-add via admin panel if missing.**

### Issue: SSL Certificate Renewal Fails

**Test renewal:**

```bash
certbot renew --dry-run
```

**Force renewal:**

```bash
certbot renew --force-renewal
```

---

## 📁 Important File Locations

| File/Directory | Location |
|----------------|----------|
| Application Root | `/var/www/Rationale Studio/` |
| Environment Config | `/var/www/Rationale Studio/.env` |
| Python Virtual Env | `/var/www/Rationale Studio/venv/` |
| React Build | `/var/www/Rationale Studio/build/` |
| Uploaded Files | `/var/www/Rationale Studio/backend/uploaded_files/` |
| Job Files | `/var/www/Rationale Studio/backend/job_files/` |
| Channel Logos | `/var/www/Rationale Studio/backend/channel_logos/` |
| Systemd Service | `/etc/systemd/system/phd-capital.service` |
| Nginx Config | `/etc/nginx/sites-available/phd-capital` |
| Nginx Logs | `/var/log/nginx/phd-capital-*.log` |
| App Logs | `journalctl -u phd-capital` |

---

## 🔧 Advanced Configuration

### Increase Gunicorn Workers (for 8-core VPS)

Edit systemd service:

```bash
nano /etc/systemd/system/phd-capital.service
```

Change line:

```
--workers 4
```

To:

```
--workers 8
```

Save (`Ctrl + X`, `Y`, Enter), then:

```bash
systemctl daemon-reload
systemctl restart phd-capital
```

### Change Database Password

```bash
sudo -u postgres psql
ALTER USER phd_user WITH PASSWORD 'YourNewSecurePassword123!';
\q

# Update .env file
nano "/var/www/Rationale Studio/.env"
# Update DATABASE_URL and PGPASSWORD

systemctl restart phd-capital
```

---

## 📞 Quick Command Reference

```bash
# Application
systemctl status phd-capital          # Check status
systemctl restart phd-capital         # Restart app
systemctl stop phd-capital            # Stop app
systemctl start phd-capital           # Start app
journalctl -u phd-capital -f          # Live logs

# Nginx
systemctl status nginx                # Check Nginx
systemctl restart nginx               # Restart Nginx
nginx -t                              # Test config

# Database
sudo -u postgres psql -d phd_rationale_db

# SSL
certbot renew                         # Renew certificate
certbot certificates                  # View certificates

# Updates
cd "/var/www/Rationale Studio"
bash deployment/update.sh

# Firewall
ufw status                            # Check firewall
ufw allow 80/tcp                      # Allow HTTP
ufw allow 443/tcp                     # Allow HTTPS
```

---

## ✅ Production Checklist

- [ ] VPS accessible via SSH
- [ ] Deployment script completed successfully
- [ ] Application running (systemctl status shows "active")
- [ ] Can access via IP: http://72.60.111.9
- [ ] DNS configured (A records added)
- [ ] DNS propagated (nslookup shows correct IP)
- [ ] Can access via domain: http://researchrationale.in
- [ ] SSL certificate installed
- [ ] HTTPS working: https://researchrationale.in
- [ ] Admin password changed from default
- [ ] All 4 API keys added via admin panel:
  - [ ] openai
  - [ ] dhan
  - [ ] assemblyai
  - [ ] google_cloud
- [ ] Test video upload works
- [ ] Test PDF generation works
- [ ] No errors in logs: `journalctl -u phd-capital -n 50`

---

## 🎊 Success!

**Your PHD Capital Rationale Studio is now live in production!**

**Production URLs:**
- https://researchrationale.in
- https://www.researchrationale.in

**Admin Panel:**
- https://researchrationale.in/login

**Default Credentials (CHANGE IMMEDIATELY):**
- Username: admin@phdcapital.com
- Password: admin123

---

## 📧 Support

If you encounter issues, check:

1. Application logs: `journalctl -u phd-capital -f`
2. Nginx logs: `tail -f /var/log/nginx/phd-capital-error.log`
3. This troubleshooting guide
4. Database connection: `sudo -u postgres psql -d phd_rationale_db -c "SELECT 1;"`

---

**🚀 Happy deploying!**
