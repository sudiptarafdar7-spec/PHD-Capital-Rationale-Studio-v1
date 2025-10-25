# YouTube OAuth Setup Guide (VPS)

## Why OAuth Instead of Cookies?

OAuth authentication is **more reliable and long-lasting** than cookies for VPS servers:
- ✅ **Tokens last longer** (months vs weeks)
- ✅ **No browser extension needed** (CLI-based setup)
- ✅ **More reliable** on VPS/cloud servers
- ✅ **One-time setup** (automatic renewal)

---

## 🚀 Quick Setup (5 Minutes on VPS)

### Step 1: SSH into Your VPS

```bash
ssh root@72.60.111.9
cd /var/www/rationale-studio
```

### Step 2: Authenticate with OAuth (One-Time)

Run this command to start the OAuth flow:

```bash
mkdir -p backend/.yt-dlp-oauth
yt-dlp --username oauth --cache-dir backend/.yt-dlp-oauth https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**What happens:**
1. yt-dlp will display a URL like: `https://www.google.com/device`
2. Open that URL **on your local computer** (not VPS)
3. Sign in to your Google/YouTube account
4. Enter the code shown in the terminal
5. Click "Allow" to authorize yt-dlp
6. yt-dlp will download the test video and save the OAuth token

**Output you should see:**
```
To give yt-dlp access to your account, go to https://www.google.com/device and enter code: ABC-DEF-GHI
Waiting for authorization...
[youtube] Extracting URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[youtube] dQw4w9WgXcQ: Downloading webpage
[download] Destination: ...
✓ OAuth token saved successfully
```

### Step 3: Verify OAuth Token Exists

```bash
ls -la backend/.yt-dlp-oauth/
```

You should see cache files. This means OAuth is configured! ✅

### Step 4: Test Download

Try downloading another video to confirm:

```bash
yt-dlp --username oauth --cache-dir backend/.yt-dlp-oauth https://www.youtube.com/watch?v=3LH29rJJ4xo
```

If it downloads successfully without asking for authorization again, OAuth is working! 🎉

### Step 5: Restart Backend Service

```bash
systemctl restart rationale-studio
```

Now your pipeline will automatically use OAuth for all downloads!

---

## 🎯 How It Works in the Pipeline

The pipeline automatically detects OAuth configuration:

1. **Checks** if `backend/.yt-dlp-oauth/` directory exists
2. **If yes**: Uses OAuth authentication (most reliable)
3. **If no**: Falls back to cookies file (if uploaded)
4. **If neither**: Downloads without authentication (may fail on VPS)

**Priority:**
```
OAuth (best) → Cookies (good) → No auth (fails on VPS)
```

---

## 🔄 Token Renewal

OAuth tokens automatically renew! You don't need to re-authenticate unless:
- You manually delete the `.yt-dlp-oauth` folder
- YouTube revokes the token (rare)
- Token expires (usually after 6+ months)

If downloads start failing, just re-run Step 2.

---

## 📋 Troubleshooting

### Problem: "Could not find a registered application"

**Solution:** Make sure you're using the latest yt-dlp version:
```bash
pip install --upgrade yt-dlp
```

### Problem: "Invalid grant" or "Token expired"

**Solution:** Delete old tokens and re-authenticate:
```bash
rm -rf backend/.yt-dlp-oauth
# Then run Step 2 again
```

### Problem: Downloads still failing with 403

**Solutions:**
1. Verify OAuth directory exists: `ls -la backend/.yt-dlp-oauth/`
2. Re-run authentication (Step 2)
3. Check VPS IP isn't blocked by YouTube (rare)

### Problem: Can't access the authorization URL

**Solution:** Copy the URL from the terminal and paste it into your local browser. You don't need to be on the VPS to authorize.

---

## 🔒 Security & Privacy

### Is OAuth safe?

✅ **YES** - OAuth is the industry standard for secure authentication:
- No passwords are stored anywhere
- Tokens are stored locally on your VPS only
- Google can revoke access anytime from your account settings
- Never transmitted to third parties

### What access does yt-dlp get?

yt-dlp gets **read-only access** to:
- Your YouTube account information
- Ability to download videos as if you're signed in

It **cannot**:
- Upload videos
- Delete videos
- Modify your account
- Access other Google services

### Where are tokens stored?

```
/var/www/rationale-studio/backend/.yt-dlp-oauth/
```

Only root and the application user can read these files.

### Can I revoke access?

Yes! Go to your Google Account settings:
1. Visit: https://myaccount.google.com/permissions
2. Find "yt-dlp"
3. Click "Remove access"

---

## 🆚 OAuth vs Cookies Comparison

| Feature | OAuth | Cookies |
|---------|-------|---------|
| **Setup** | CLI command | Browser extension |
| **Duration** | 6+ months | 30-90 days |
| **VPS Reliability** | ✅ Excellent | ⚠️ Good |
| **Renewal** | Automatic | Manual re-upload |
| **Security** | ✅ Industry standard | ⚠️ Session-based |
| **Ease of Use** | Medium | Easy |

**Recommendation:** Use OAuth for production VPS deployments.

---

## 💡 Alternative: Keep Using Cookies

If you prefer cookies over OAuth, you can continue using the cookies.txt upload method:
1. Go to **Settings → API Keys**
2. Upload fresh cookies.txt file
3. Pipeline will use cookies if OAuth is not configured

Both methods work! OAuth is just more reliable long-term.

---

## 🔧 Advanced: Custom OAuth Cache Directory

If you want to use a different cache directory:

1. Edit `backend/pipeline/step01_download_audio.py`
2. Change line:
   ```python
   oauth_cache_dir = os.path.join('backend', '.yt-dlp-oauth')
   ```
3. Restart backend service

---

## 📞 Need Help?

If OAuth setup isn't working:
1. Check yt-dlp version: `yt-dlp --version` (should be latest)
2. Verify directory exists: `ls -la backend/.yt-dlp-oauth/`
3. Check logs: `journalctl -u rationale-studio -n 100`
4. Try re-authentication (delete folder and run Step 2 again)

---

**Last Updated:** October 25, 2025  
**Tested On:** Ubuntu 22.04 LTS, Hostinger VPS  
**yt-dlp Version:** 2024.10.22 or later
