# 🚀 Deployment Summary

## PHD Capital Rationale Studio - Production Deployment

---

## 📊 System Overview

### Server Details
- **VPS IP:** 72.60.111.9
- **Domain:** researchrationale.in
- **Repository:** https://github.com/sudiptarafdar7-spec/Rationale-Studio
- **Server OS:** Ubuntu 24.04 LTS

### Technology Stack
- **Backend:** Flask (Python 3.11) + Gunicorn
- **Frontend:** React 18 + TypeScript + Vite
- **Database:** PostgreSQL (Neon)
- **Web Server:** Nginx
- **Process Manager:** systemd

---

## ✅ Fixes Applied

### Critical Bugs Fixed
1. **Frontend Build Error** - Fixed incorrect import in `src/pages/SavedRationalePage.tsx`:
   - Changed: `import { toast } from 'sonner@2.0.3'`
   - To: `import { toast } from 'sonner'`

2. **Security Vulnerability** - Removed exposed Google Cloud credentials:
   - Deleted: `backend/api_keys/google-cloud.json`
   - Updated `.gitignore` to prevent future commits

3. **Deployment Script** - Fixed Python package installation issues:
   - Uses virtual environment properly
   - Fixes `pytz` and `urllib3` module errors
   - Handles Ubuntu 24.04 system-managed packages correctly

4. **Repository Cleanup**:
   - Removed `attached_assets/` folder (temporary upload files)
   - Updated `.gitignore` to exclude temporary files

---

## 📁 Deployment Files

| File | Purpose |
|------|---------|
| **PRODUCTION-DEPLOY.sh** | Main deployment script (one-command setup) |
| **COMPLETE-GUIDE.md** | Comprehensive deployment documentation |
| **update.sh** | Quick update script for code changes |
| **DEPLOYMENT-SUMMARY.md** | This file (overview and checklist) |

---

## 🎯 Deployment Process

### One-Command Deployment

```bash
# SSH to VPS
ssh root@72.60.111.9

# Download and run deployment
curl -o deploy.sh https://raw.githubusercontent.com/sudiptarafdar7-spec/Rationale-Studio/main/deploy/PRODUCTION-DEPLOY.sh
chmod +x deploy.sh
bash deploy.sh
```

**What the script does:**
1. ✅ Installs: Python, Node.js, PostgreSQL, Nginx, ffmpeg, yt-dlp
2. ✅ Creates PostgreSQL database and user
3. ✅ Clones GitHub repository
4. ✅ Creates Python virtual environment
5. ✅ Installs all 65 Python dependencies
6. ✅ Builds React frontend (production build)
7. ✅ Configures Nginx reverse proxy
8. ✅ Creates systemd service
9. ✅ Starts application

**Deployment time:** ~5-10 minutes

---

## 🔐 Post-Deployment Steps

### 1. Add API Keys

```bash
nano /var/www/phd-capital/.env
```

Required keys:
- `SECRET_KEY` (generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- `JWT_SECRET_KEY` (generate same way)
- `OPENAI_API_KEY`
- `DHAN_API_KEY`
- `ASSEMBLYAI_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`

### 2. Restart Application

```bash
systemctl restart phd-capital
systemctl status phd-capital
```

### 3. Configure DNS

Add A records at your domain registrar:
- `@` → 72.60.111.9
- `www` → 72.60.111.9

Wait 5-60 minutes for DNS propagation.

### 4. Install SSL Certificate

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d researchrationale.in -d www.researchrationale.in
```

---

## 🌐 Access URLs

- **Production:** https://researchrationale.in (after SSL)
- **WWW:** https://www.researchrationale.in
- **Direct IP:** http://72.60.111.9 (works immediately)

**Default Login:**
- Username: `admin@phdcapital.com`
- Password: `admin123`
- ⚠️ **Change password after first login!**

---

## 📊 Monitoring Commands

### Application Status
```bash
systemctl status phd-capital
journalctl -u phd-capital -f
```

### Nginx Status
```bash
systemctl status nginx
nginx -t
tail -f /var/log/nginx/phd-capital-access.log
```

### Database Access
```bash
sudo -u postgres psql -d phd_capital
```

---

## 🔄 Updating After Code Changes

```bash
cd /var/www/phd-capital
bash deploy/update.sh
```

This will:
1. Pull latest code from GitHub
2. Update Python dependencies (in venv)
3. Update Node dependencies
4. Rebuild React frontend
5. Restart application

---

## 🐛 Common Issues & Solutions

### Issue: Application won't start
**Solution:**
```bash
journalctl -u phd-capital -n 100  # Check logs
cat /var/www/phd-capital/.env     # Verify API keys
```

### Issue: Nginx 502 Bad Gateway
**Solution:**
```bash
systemctl restart phd-capital
systemctl restart nginx
```

### Issue: Module not found (pytz, urllib3, etc.)
**Solution:**
```bash
cd /var/www/phd-capital
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
deactivate
systemctl restart phd-capital
```

### Issue: Permission denied
**Solution:**
```bash
chown -R www-data:www-data /var/www/phd-capital
chmod -R 755 /var/www/phd-capital
chmod 600 /var/www/phd-capital/.env
```

---

## ✅ Production Checklist

### Pre-Deployment
- [x] Code pushed to GitHub
- [x] All bugs fixed
- [x] Sensitive files removed
- [x] .gitignore updated

### Deployment
- [ ] SSH access to VPS confirmed
- [ ] Deployment script executed
- [ ] No errors during installation
- [ ] Application running (systemctl status)

### Configuration
- [ ] API keys added to .env
- [ ] Secret keys generated
- [ ] Database password changed
- [ ] Admin password changed

### DNS & SSL
- [ ] DNS A records configured
- [ ] DNS propagation verified
- [ ] SSL certificate installed
- [ ] HTTPS working with lock icon

### Testing
- [ ] Can access application via HTTPS
- [ ] Can login as admin
- [ ] Can upload video
- [ ] Pipeline runs successfully
- [ ] PDF generation works
- [ ] No errors in logs

### Security
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] Default passwords changed
- [ ] Google Cloud credentials revoked (old leaked key)
- [ ] New credentials configured
- [ ] Database backups configured

---

## 📈 Performance Notes

- **Gunicorn workers:** 4 (configured for 4-core VPS)
- **Worker timeout:** 120s (for video processing)
- **Nginx timeout:** 300s (5 minutes)
- **Max upload size:** 500MB

To increase workers (for 8-core VPS):
```bash
# Edit: /etc/systemd/system/phd-capital.service
# Change: --workers 4 to --workers 8
systemctl daemon-reload
systemctl restart phd-capital
```

---

## 🔒 Security Features

- ✅ HTTPS with Let's Encrypt SSL
- ✅ Firewall (UFW) configured
- ✅ API keys in environment variables
- ✅ Database credentials secured
- ✅ Application runs as www-data user
- ✅ Automatic SSL renewal (90 days)

---

## 📚 Documentation

- **Complete Guide:** `deploy/COMPLETE-GUIDE.md`
- **Deployment Script:** `deploy/PRODUCTION-DEPLOY.sh`
- **Update Script:** `deploy/update.sh`
- **This Summary:** `deploy/DEPLOYMENT-SUMMARY.md`

---

## 🆘 Support

If you encounter issues:

1. Check logs: `journalctl -u phd-capital -f`
2. Verify .env file has all required keys
3. Test database connection: `sudo -u postgres psql -d phd_capital -c "SELECT 1;"`
4. Check service status: `systemctl status phd-capital nginx`
5. Review complete guide: `deploy/COMPLETE-GUIDE.md`

---

## 🎊 Success Criteria

Your deployment is successful when:

- ✅ Application accessible via https://researchrationale.in
- ✅ SSL certificate shows lock icon in browser
- ✅ Can login with admin credentials
- ✅ Can upload YouTube video and process
- ✅ PDF report generates successfully
- ✅ No errors in logs: `journalctl -u phd-capital -n 50`

---

**🚀 Your PHD Capital Rationale Studio is now production-ready!**

**Production URL:** https://researchrationale.in  
**Admin Panel:** https://researchrationale.in/login
