"""
Step 1: Download Audio from YouTube Video
Uses yt-dlp to extract audio and converts to 16kHz mono WAV format
Updated with 2025 bot-blocking bypass techniques
"""
import os
import subprocess
from yt_dlp import YoutubeDL


def download_audio(job_id, youtube_url, cookies_file=None):
    """
    Download audio from YouTube video and convert to 16 kHz mono WAV
    
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
        
        # Step 1: Download audio using yt-dlp
        print(f"🎧 Downloading audio from YouTube: {youtube_url}")
        
        # Updated yt-dlp options to bypass 2025 bot blocking
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(audio_folder, 'temp_audio.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            # 2025 Bot Blocking Bypass - Updated User Agent
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            # Use the best available client
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web'],
                    'player_skip': ['webpage'],
                }
            },
            # Additional anti-bot measures
            'nocheckcertificate': True,
            'geo_bypass': True,
            # Use age_limit to avoid restrictions
            'age_limit': None,
        }
        
        # Add cookies file if explicitly provided
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            print(f"✓ Using provided cookies file: {cookies_file}")
        
        # Download audio with fallback
        download_successful = False
        error_msg = None
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            download_successful = True
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ Primary download method failed: {error_msg}")
            
            # Fallback: Try with different client settings
            print(f"🔄 Trying fallback method with android client...")
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['android'],
                }
            }
            
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
                download_successful = True
                print("✓ Fallback method succeeded!")
            except Exception as e2:
                error_msg = f"Both methods failed. Primary: {error_msg}, Fallback: {str(e2)}"
        
        if not download_successful:
            return {
                'success': False,
                'error': f'Audio download error: {error_msg}'
            }
        
        # Check if download succeeded
        if not os.path.exists(temp_audio):
            return {
                'success': False,
                'error': 'Failed to download audio file from YouTube'
            }
        
        # Rename to raw_audio.wav
        os.rename(temp_audio, raw_audio_path)
        print(f"✓ Audio downloaded: {raw_audio_path}")
        
        # Step 2: Convert to 16 kHz mono using ffmpeg
        print(f"🔊 Converting to 16 kHz mono WAV for transcription...")
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', raw_audio_path,
            '-ar', '16000',  # 16 kHz sample rate (required for AssemblyAI)
            '-ac', '1',       # mono (1 channel)
            '-y',             # overwrite output file if exists
            prepared_audio_path
        ]
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {
                'success': False,
                'error': f'FFmpeg conversion failed: {result.stderr}'
            }
        
        if not os.path.exists(prepared_audio_path):
            return {
                'success': False,
                'error': 'Prepared audio file was not created'
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
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Audio download error: {str(e)}'
        }
