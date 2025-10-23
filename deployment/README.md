# 🚀 Quick Deployment Reference

## Server Details
- **IP:** 72.60.111.9
- **Domain:** researchrationale.in
- **Project:** rationale-studio
- **OS:** Ubuntu 24.04 LTS

---

## 🎯 One-Command Deployment

### Windows PowerShell

```powershell
# Connect to server
ssh root@72.60.111.9

# Download and run deployment
cd /root
curl -o deploy.sh https://raw.githubusercontent.com/sudiptarafdar7-spec/PHD-Capital-Rationale-Studio-v1/main/deployment/deploy.sh
chmod +x deploy.sh
bash deploy.sh
```

**Time:** 5-10 minutes

---

## 📝 After Deployment

### 1. Configure DNS

Add A records at your domain registrar:
- `@` → 72.60.111.9
- `www` → 72.60.111.9

### 2. Install SSL (after DNS propagates)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d researchrationale.in -d www.researchrationale.in
```

### 3. Add API Keys

1. Visit: https://researchrationale.in/login
2. Login: `admin@phdcapital.com` / `admin123`
3. **Change password immediately!**
4. Go to: API Keys Management
5. Add all 4 keys:
   - openai
   - dhan
   - assemblyai
   - google_cloud (upload JSON file)

---

## 📚 Documentation

- **Complete Guide:** [DEPLOYMENT-GUIDE.md](./DEPLOYMENT-GUIDE.md)
- **Deployment Script:** [deploy.sh](./deploy.sh)
- **Update Script:** [update.sh](./update.sh)

---

## 🔄 Quick Commands

```bash
# Check status
systemctl status phd-capital

# View logs
journalctl -u phd-capital -f

# Restart
systemctl restart phd-capital

# Update after git push
cd /var/www/rationale-studio
bash deployment/update.sh
```

---

## ✅ Success Criteria

Application is ready when:
- ✅ https://researchrationale.in loads
- ✅ SSL certificate shows lock icon
- ✅ Can login as admin
- ✅ All 4 API keys configured
- ✅ Can process YouTube video
- ✅ PDF generates successfully

---

**📖 Full Documentation:** See [DEPLOYMENT-GUIDE.md](./DEPLOYMENT-GUIDE.md)
