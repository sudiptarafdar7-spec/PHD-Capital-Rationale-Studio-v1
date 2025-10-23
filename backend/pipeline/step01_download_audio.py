"""
Step 1: Download Audio from YouTube Video
Uses yt-dlp to extract audio and converts to 16kHz mono WAV format
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
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(audio_folder, 'temp_audio.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'nocheckcertificate': True,
            'no_cookies': True,  # Disable cookie saving to avoid permission errors
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        
        # Note: Cookies disabled to avoid permission issues on VPS
        # The user_agent and player_client options should be sufficient for most videos
        
        # Add options to avoid bot detection and 403 errors
        ydl_opts.update({
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'geo_bypass': True,
            'nocheckcertificate': True,
            'http_headers': {
                'Referer': 'https://www.youtube.com/',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'config'],
                }
            },
        })
        
        # Download audio
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
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
