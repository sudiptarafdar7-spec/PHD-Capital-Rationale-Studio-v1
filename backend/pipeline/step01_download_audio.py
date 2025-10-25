"""
Step 1: Download Audio from YouTube Video
Uses yt-dlp with cookies authentication for VPS bot detection bypass
"""
import os
import subprocess
import time
import random
from yt_dlp import YoutubeDL


# Multiple user agents to rotate through for better reliability
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
]


def download_audio(job_id, youtube_url, cookies_file=None):
    """
    Bulletproof audio download with cookies authentication support.
    Download audio from YouTube video and convert to 16 kHz mono WAV.
    
    Args:
        job_id: Job identifier
        youtube_url: YouTube video URL
        cookies_file: Optional path to cookies.txt file for authentication
    
    Returns:
        dict: {
            'success': bool,
            'raw_audio': str,  # Path to raw audio file
            'prepared_audio': str,  # Path to 16kHz mono audio file
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
        temp_audio = os.path.join(audio_folder, 'temp_audio.wav')
        
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
        
        # ===== STEP 1: Download audio using yt-dlp with retry logic =====
        print(f"🎧 Downloading audio from YouTube: {youtube_url}")
        
        max_retries = 3
        retry_delay = 2  # seconds
        download_success = False
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  Attempt {attempt}/{max_retries}...")
                
                # Randomize user agent for each attempt
                user_agent = random.choice(USER_AGENTS)
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(audio_folder, 'temp_audio.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'socket_timeout': 30,
                    'retries': 3,
                    'fragment_retries': 3,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                        'preferredquality': '192',
                    }],
                    'user_agent': user_agent,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web', 'ios'],
                            'player_skip': ['webpage', 'config'],
                        }
                    },
                }
                
                # Use cookies file for authentication (recommended method for VPS)
                if cookies_file and os.path.exists(cookies_file):
                    ydl_opts['cookiefile'] = cookies_file
                    if attempt == 1:
                        print(f"  ✓ Using cookies file for authentication")
                else:
                    if attempt == 1:
                        print(f"  ⚠️ No cookies configured")
                        print(f"  ⚠️ Downloads may fail on VPS servers due to bot detection")
                
                # Attempt download
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
                
                # Check if download succeeded
                if os.path.exists(temp_audio):
                    download_success = True
                    print(f"  ✓ Download successful on attempt {attempt}")
                    break
                else:
                    last_error = f"Temp audio file not created (attempt {attempt})"
                    print(f"  ⚠️ {last_error}")
                
            except Exception as e:
                last_error = str(e)
                print(f"  ⚠️ Attempt {attempt} failed: {last_error}")
                
                # Wait before retrying (exponential backoff)
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** (attempt - 1))  # 2s, 4s, 8s
                    print(f"  ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # If all retries failed
        if not download_success:
            error_msg = f'Failed to download audio after {max_retries} attempts. Last error: {last_error}'
            
            # Provide helpful error message if authentication is missing
            if 'Sign in to confirm' in str(last_error) or '403' in str(last_error):
                error_msg += '\n\n💡 TIP: This error usually means YouTube bot detection. Please upload cookies.txt file in Settings → API Keys. See YOUTUBE_COOKIES_SETUP.md for instructions.'
            
            return {
                'success': False,
                'error': error_msg,
                'raw_audio': '',
                'prepared_audio': '',
                'raw_size_mb': 0,
                'prepared_size_mb': 0
            }
        
        # Rename to raw_audio.wav
        if os.path.exists(raw_audio_path):
            os.remove(raw_audio_path)
        os.rename(temp_audio, raw_audio_path)
        print(f"✓ Audio downloaded: {raw_audio_path}")
        
        # ===== STEP 2: Convert to 16 kHz mono using ffmpeg =====
        print(f"🔊 Converting to 16 kHz mono WAV for transcription...")
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', raw_audio_path,
            '-ar', '16000',  # 16 kHz sample rate (required for AssemblyAI)
            '-ac', '1',       # mono (1 channel)
            '-y',             # overwrite output file if exists
            '-loglevel', 'error',  # Only show errors
            prepared_audio_path
        ]
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for ffmpeg
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
        raw_size = os.path.getsize(raw_audio_path) / (1024 * 1024)  # MB
        prepared_size = os.path.getsize(prepared_audio_path) / (1024 * 1024)  # MB
        
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
