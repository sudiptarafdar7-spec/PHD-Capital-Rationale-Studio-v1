# 🚀 Your VPS Deployment Guide

## Server Details
- **VPS IP:** 72.60.111.9
- **Domain:** researchrationale.in
- **Repository:** https://github.com/sudiptarafdar7-spec/Rationale-Studio

---

## 📋 Prerequisites Checklist

Before starting, ensure:
- [ ] Domain DNS A record points to: **72.60.111.9**
- [ ] You have SSH root access to the VPS
- [ ] VPS is running Ubuntu 20.04/22.04 or Debian 11/12

---

## 🎯 Step-by-Step Deployment

### **Step 1: Connect to Your VPS**

```bash
ssh root@72.60.111.9
```

If you have a different SSH key or user:
```bash
ssh -i ~/.ssh/your-key.pem user@72.60.111.9
```

---

### **Step 2: Clone Repository**

```bash
cd /var/www
git clone https://github.com/sudiptarafdar7-spec/Rationale-Studio.git phd-capital
cd phd-capital
```

---

### **Step 3: Run Deployment Script**

```bash
chmod +x deploy/vps-deploy.sh
sudo bash deploy/vps-deploy.sh researchrationale.in
```

**⏱️ This will take 5-10 minutes.** The script will:
- Install Python, Node.js, PostgreSQL, Nginx, ffmpeg
- Create database
- Build your React app
- Configure everything automatically

---

### **Step 4: Configure API Keys**

```bash
nano /var/www/phd-capital/.env
```

**Generate secure keys:**
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

**Update these in .env:**
```env
# Use the generated keys from above
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET_KEY=your-generated-jwt-secret-here

# Add your API keys
OPENAI_API_KEY=sk-proj-xxxxx
DHAN_API_KEY=your-dhan-api-key
ASSEMBLYAI_API_KEY=your-assemblyai-key
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}

# Database (already configured by script)
DATABASE_URL=postgresql://phd_user:ChangeMeInProduction123!@localhost/phd_capital
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

---

### **Step 5: Restart Application**

```bash
systemctl restart phd-capital
systemctl status phd-capital
```

You should see: **Active: active (running)**

---

### **Step 6: Configure DNS (If Not Done)**

Go to your domain registrar (GoDaddy/Namecheap/etc) and add:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 72.60.111.9 | 3600 |
| A | www | 72.60.111.9 | 3600 |

**⏱️ DNS propagation takes 5-60 minutes**

---

### **Step 7: Add SSL Certificate (Recommended)**

Once DNS is working:

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d researchrationale.in -d www.researchrationale.in
```

Enter your email when prompted, agree to terms.

**✅ Your app will now be at: https://researchrationale.in**

---

## 🎊 **Your App is Live!**

### Access Your Application:
- **HTTP:** http://researchrationale.in
- **HTTPS (after SSL):** https://researchrationale.in

### Default Admin Login:
- **Username:** admin@phdcapital.com
- **Password:** admin123

⚠️ **Change this password immediately after first login!**

---

## 📊 **Useful Commands**

### Check if app is running:
```bash
systemctl status phd-capital
```

### View live logs:
```bash
journalctl -u phd-capital -f
```

### Restart app:
```bash
systemctl restart phd-capital
```

### Check Nginx:
```bash
systemctl status nginx
nginx -t
```

### Connect to database:
```bash
sudo -u postgres psql -d phd_capital
```

---

## 🔄 **Update Your App Later**

When you push new code to GitHub:

```bash
cd /var/www/phd-capital
bash deploy/update.sh
```

---

## 🐛 **Troubleshooting**

### App won't start?
```bash
journalctl -u phd-capital -n 100
```

### Nginx 502 error?
```bash
systemctl restart phd-capital
systemctl restart nginx
```

### DNS not working?
```bash
# Check DNS propagation
nslookup researchrationale.in
ping researchrationale.in
```

### Permission issues?
```bash
chown -R www-data:www-data /var/www/phd-capital
chmod -R 755 /var/www/phd-capital
```

---

## ✅ **Post-Deployment Checklist**

- [ ] App running: `systemctl status phd-capital`
- [ ] Nginx running: `systemctl status nginx`
- [ ] DNS resolving to 72.60.111.9
- [ ] SSL certificate installed
- [ ] Admin password changed
- [ ] All API keys configured
- [ ] Test video upload and processing
- [ ] Test PDF generation

---

## 🔐 **Security Recommendations**

1. **Change database password:**
```bash
sudo -u postgres psql
ALTER USER phd_user WITH PASSWORD 'YourStrongPasswordHere';
```

2. **Update .env with new password:**
```bash
nano /var/www/phd-capital/.env
# Update: DATABASE_URL=postgresql://phd_user:YourStrongPasswordHere@localhost/phd_capital
systemctl restart phd-capital
```

3. **Configure firewall:**
```bash
ufw status
# Should show: 22/tcp, 80/tcp, 443/tcp ALLOW
```

---

## 📞 **Need Help?**

- **Logs:** `journalctl -u phd-capital -f`
- **Nginx Logs:** `tail -f /var/log/nginx/error.log`
- **Database:** `sudo -u postgres psql -d phd_capital`

---

**🎉 Congratulations! Your PHD Capital Rationale Studio is now live at researchrationale.in!**
