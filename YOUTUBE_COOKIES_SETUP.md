# YouTube Cookies Setup Guide

## Why Do I Need This?

YouTube uses bot detection to block video downloads from VPS and cloud servers. This is why you see errors like:

```
ERROR: [youtube] Sign in to confirm you're not a bot
```

**Solution:** Upload your browser cookies so the system can download videos as if you're signed in to YouTube, bypassing the bot detection.

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Browser Extension

Choose one of these browser extensions to export your YouTube cookies:

#### **Chrome, Edge, Brave:**
- Extension: **"Get cookies.txt LOCALLY"**
- Link: https://chrome.google.com/webstore/detail/cclelndahbckbenkjhflpdbgdldlbecc
- ✅ Recommended - works perfectly with YouTube

#### **Firefox:**
- Extension: **"cookies.txt"**
- Link: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
- ✅ Firefox-specific version

### Step 2: Sign In to YouTube

1. Open your browser (Chrome/Firefox/Edge)
2. Go to **https://www.youtube.com**
3. **Sign in** to your YouTube/Google account
4. Make sure you're fully signed in (see your profile picture in the top-right)

### Step 3: Export Cookies

1. While on **youtube.com**, click the extension icon in your browser toolbar
2. Click **"Export"** or **"Download cookies.txt"**
3. Save the file as **`cookies.txt`** (default name)
4. The file will be downloaded to your Downloads folder

### Step 4: Upload to Rationale Studio

1. Log in to your **Rationale Studio** admin panel
2. Go to **Settings → API Keys**
3. Scroll down to the **"YouTube Authentication"** section
4. Click **"Choose File"** and select your `cookies.txt` file
5. Click **"Upload"**
6. ✅ You'll see "Configured" badge when successful

---

## 🎯 Verification

After uploading cookies, test the pipeline:

1. Go to **Media Rationale** page
2. Start a new analysis with any YouTube video
3. Watch **Step 1 (Download Audio)** - it should complete successfully
4. No more bot detection errors! 🎉

---

## 🔄 When to Re-Upload Cookies

YouTube cookies expire after some time (usually 30-90 days). You'll need to re-upload if:

- ❌ Downloads start failing with "Sign in to confirm you're not a bot" error
- ❌ You sign out of YouTube in your browser
- ❌ You clear your browser cookies

**Solution:** Simply export and upload fresh cookies following the same steps above.

---

## 🛡️ Security & Privacy

### Is this safe?

✅ **YES** - The cookies file is:
- Stored securely on your VPS server only
- Only accessible to admin users
- Never transmitted to third parties
- Used only for downloading YouTube videos

### What data is in cookies.txt?

The file contains:
- Your YouTube session tokens
- Authentication cookies
- No passwords (passwords are never stored in cookies)

### Can I use a different Google account?

Yes! You can:
- Sign in to YouTube with any Google account
- Export cookies from that account
- Upload to Rationale Studio
- The system will download videos as that user

---

## 📋 Troubleshooting

### Problem: "Invalid file type" error

**Solution:** Make sure you're uploading a `.txt` file, not `.json` or other format. The file must be in Netscape cookie format.

### Problem: Downloads still failing after upload

**Solutions:**
1. Make sure you were **signed in** to YouTube when exporting cookies
2. Try exporting fresh cookies (sign out and sign in again)
3. Check that the cookies file is not empty (should be 10-50 KB)
4. Try a different browser extension

### Problem: "Cookies file not found" in logs

**Solution:** Re-upload the cookies file through the API Keys page.

### Problem: Extension not working

**Alternative Method - Manual Export:**
1. Open YouTube in your browser while signed in
2. Press **F12** to open Developer Tools
3. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Click **Cookies** → **https://www.youtube.com**
5. Right-click in the cookies table → **Export all** (if available)
6. Or use a different extension like "EditThisCookie"

---

## 🔧 Technical Details (Advanced)

### Cookie File Format

The cookies.txt file uses Netscape cookie format:
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	CONSENT	YES+...
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	...
```

### How It Works

1. System checks for `backend/youtube_cookies.txt` file
2. If exists, passes file to `yt-dlp` with `--cookies` parameter
3. yt-dlp uses cookies to authenticate with YouTube
4. Downloads proceed as if user is signed in
5. Bot detection bypassed ✅

### Server Path

The cookies file is stored at:
```
/var/www/rationale-studio/backend/youtube_cookies.txt
```

Only root and the application user can read this file.

---

## 💡 Tips

1. **Keep cookies fresh**: Export new cookies every month
2. **Use a dedicated account**: Consider using a separate YouTube account for the system
3. **Test regularly**: Run test downloads to ensure cookies are still valid
4. **Backup**: Keep a copy of your cookies file locally

---

## 📞 Need Help?

If you're still experiencing issues:
1. Check the error message in the pipeline step
2. Verify you uploaded cookies while signed in to YouTube
3. Try exporting fresh cookies
4. Contact support with the error message

---

**Last Updated:** October 25, 2025  
**Compatible With:** Chrome, Firefox, Edge, Brave browsers
