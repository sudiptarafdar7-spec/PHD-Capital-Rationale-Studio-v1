"""
Step 1: Download Audio from YouTube Video
Bulletproof implementation with yt-dlp primary + Playwright fallback
"""
import os
import subprocess
import shutil
import random
import re
import json
import requests
from yt_dlp import YoutubeDL

# Random user agents to avoid bot detection
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]


def download_audio(job_id, youtube_url, cookies_file=None):
    """
    Bulletproof YouTube audio download:
    - Primary: yt-dlp with cookies and retry logic
    - Fallback: Playwright browser automation
    - Converts to 16kHz mono WAV
    
    Args:
        job_id: Job identifier
        youtube_url: YouTube video URL
        cookies_file: Optional path to cookies.txt file
    
    Returns:
        dict: {
            'success': bool,
            'raw_audio': str,
            'prepared_audio': str,
            'raw_size_mb': float,
            'prepared_size_mb': float,
            'error': str or None
        }
    """
    try:
        # Setup paths
        audio_folder = os.path.join('backend', 'job_files', job_id, 'audio')
        os.makedirs(audio_folder, exist_ok=True)
        
        raw_audio_path = os.path.join(audio_folder, 'raw_audio.wav')
        prepared_audio_path = os.path.join(audio_folder, 'audio_16k_mono.wav')
        temp_audio_path = os.path.join(audio_folder, 'temp_audio.wav')
        
        # ===== CACHING: Check if audio already exists =====
        if os.path.exists(prepared_audio_path) and os.path.exists(raw_audio_path):
            print(f"✓ Audio already exists in cache, skipping download")
            raw_size = os.path.getsize(raw_audio_path) / (1024 * 1024)
            prepared_size = os.path.getsize(prepared_audio_path) / (1024 * 1024)
            
            return {
                'success': True,
                'raw_audio': raw_audio_path,
                'prepared_audio': prepared_audio_path,
                'raw_size_mb': round(raw_size, 2),
                'prepared_size_mb': round(prepared_size, 2),
                'error': None
            }
        
        # ===== STEP 1: Try yt-dlp first =====
        print(f"🎧 Attempting yt-dlp download for {youtube_url}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_audio_path.replace('.wav', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'ios'],
                    'player_skip': ['webpage', 'config'],
                }
            },
        }
        
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            print(f"  ✓ Using cookies file for authentication")
        
        ydl_success = False
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(youtube_url, download=True)
            
            if os.path.exists(temp_audio_path):
                ydl_success = True
                print(f"  ✓ yt-dlp download successful")
        except Exception as e:
            print(f"  ⚠️ yt-dlp failed: {str(e)}")
        
        # ===== STEP 2: Fallback to Playwright if yt-dlp failed =====
        if not ydl_success:
            print("⚡ Falling back to Playwright browser automation")
            
            try:
                from playwright.sync_api import sync_playwright
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent=random.choice(USER_AGENTS)
                    )
                    page = context.new_page()
                    
                    page.goto(youtube_url, wait_until="networkidle", timeout=60000)
                    
                    html = page.content()
                    
                    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
                    if match:
                        data = json.loads(match.group(1))
                        formats = data.get("streamingData", {}).get("adaptiveFormats", [])
                        
                        audio_url = None
                        for fmt in formats:
                            mime_type = fmt.get("mimeType", "")
                            if "audio" in mime_type:
                                audio_url = fmt.get("url")
                                if audio_url:
                                    break
                        
                        if audio_url:
                            print(f"  ✓ Found audio stream URL")
                            response = requests.get(audio_url, stream=True, timeout=120)
                            response.raise_for_status()
                            
                            with open(temp_audio_path, 'wb') as f:
                                shutil.copyfileobj(response.raw, f)
                            
                            print(f"  ✓ Playwright download successful")
                        else:
                            raise Exception("No audio stream found in video data")
                    else:
                        raise Exception("Could not extract video data from page")
                    
                    browser.close()
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Both yt-dlp and Playwright failed. Last error: {str(e)}',
                    'raw_audio': '',
                    'prepared_audio': '',
                    'raw_size_mb': 0,
                    'prepared_size_mb': 0
                }
        
        # Check if download succeeded
        if not os.path.exists(temp_audio_path):
            return {
                'success': False,
                'error': 'Download failed: audio file not created',
                'raw_audio': '',
                'prepared_audio': '',
                'raw_size_mb': 0,
                'prepared_size_mb': 0
            }
        
        # Rename to raw_audio.wav
        if os.path.exists(raw_audio_path):
            os.remove(raw_audio_path)
        os.rename(temp_audio_path, raw_audio_path)
        print(f"✓ Audio downloaded: {raw_audio_path}")
        
        # ===== STEP 3: Convert to 16 kHz mono using ffmpeg =====
        print(f"🔊 Converting to 16 kHz mono WAV for transcription...")
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', raw_audio_path,
            '-ar', '16000',
            '-ac', '1',
            '-y',
            '-loglevel', 'error',
            prepared_audio_path
        ]
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            return {
                'success': False,
                'error': f'FFmpeg conversion failed: {result.stderr}',
                'raw_audio': raw_audio_path,
                'prepared_audio': '',
                'raw_size_mb': 0,
                'prepared_size_mb': 0
            }
        
        if not os.path.exists(prepared_audio_path):
            return {
                'success': False,
                'error': 'Prepared audio file was not created by FFmpeg',
                'raw_audio': raw_audio_path,
                'prepared_audio': '',
                'raw_size_mb': 0,
                'prepared_size_mb': 0
            }
        
        print(f"✓ Audio prepared: {prepared_audio_path}")
        
        # Get file sizes for logging
        raw_size = os.path.getsize(raw_audio_path) / (1024 * 1024)
        prepared_size = os.path.getsize(prepared_audio_path) / (1024 * 1024)
        
        return {
            'success': True,
            'raw_audio': raw_audio_path,
            'prepared_audio': prepared_audio_path,
            'raw_size_mb': round(raw_size, 2),
            'prepared_size_mb': round(prepared_size, 2),
            'error': None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'FFmpeg conversion timeout (exceeded 5 minutes)',
            'raw_audio': '',
            'prepared_audio': '',
            'raw_size_mb': 0,
            'prepared_size_mb': 0
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Audio download error: {str(e)}',
            'raw_audio': '',
            'prepared_audio': '',
            'raw_size_mb': 0,
            'prepared_size_mb': 0
        }
