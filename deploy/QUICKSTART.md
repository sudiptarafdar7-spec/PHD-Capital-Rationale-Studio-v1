# 🚀 Quick Start - Hostinger VPS Deployment

Deploy your PHD Capital Rationale Studio in **5 simple steps**:

---

## 1️⃣ Push Your Code to GitHub

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for production deployment"

# Add your GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/phd-capital.git

# Push
git push -u origin main
```

---

## 2️⃣ SSH into Your Hostinger VPS

```bash
ssh root@your-vps-ip-address
```

---

## 3️⃣ Clone & Deploy

```bash
# Clone your repository
cd /var/www
git clone https://github.com/YOUR_USERNAME/phd-capital.git phd-capital
cd phd-capital

# Run deployment script
chmod +x deploy/vps-deploy.sh
sudo bash deploy/vps-deploy.sh your-domain.com
```

---

## 4️⃣ Add Your API Keys

```bash
nano /var/www/phd-capital/.env
```

Update these values:
```env
# Generate secure keys (run: python3 -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET_KEY=your-generated-jwt-secret-here

# API Keys
OPENAI_API_KEY=sk-proj-xxxxx
DHAN_API_KEY=your-dhan-key
ASSEMBLYAI_API_KEY=your-assemblyai-key
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
```

Save and exit (Ctrl+X, Y, Enter)

---

## 5️⃣ Restart & Go Live

```bash
systemctl restart phd-capital
```

**🎉 Your app is now live at: http://your-domain.com**

---

## 🔐 Add SSL (Optional but Recommended)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

Now accessible at: **https://your-domain.com** ✅

---

## 📊 Useful Commands

```bash
# Check if app is running
systemctl status phd-capital

# View live logs
journalctl -u phd-capital -f

# Restart app
systemctl restart phd-capital

# Update app after code changes
cd /var/www/phd-capital && bash deploy/update.sh
```

---

## 🆘 Troubleshooting

**App won't start?**
```bash
journalctl -u phd-capital -n 50
```

**Database error?**
```bash
sudo -u postgres psql -d phd_capital -c "SELECT 1;"
```

**Nginx 502 error?**
```bash
systemctl restart phd-capital
systemctl restart nginx
```

---

## ✅ Production Checklist

- [ ] Domain DNS pointing to VPS IP
- [ ] SSL certificate installed (HTTPS)
- [ ] All API keys added to .env
- [ ] Admin password changed from default
- [ ] Database backups configured
- [ ] Firewall enabled (UFW)

---

**Need help?** Check the full guide: `deploy/README.md`
