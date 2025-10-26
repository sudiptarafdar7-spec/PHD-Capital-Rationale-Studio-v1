"""
Step 1: Download Audio from YouTube Video
Uses RapidAPI (YT Search & Download MP3) to download audio and converts to 16kHz mono WAV format
"""
import os
import re
import subprocess
import http.client
import json
import urllib.request
import urllib.parse
from backend.utils.database import get_db_cursor


def convert_to_watch_url(youtube_url):
    """
    Convert any YouTube URL format to standard watch?v= format
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/live/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - VIDEO_ID (direct)
    
    Returns:
        str: URL in format https://www.youtube.com/watch?v=VIDEO_ID
    """
    # If it's already a watch URL, return as is
    if "watch?v=" in youtube_url:
        return youtube_url
    
    # Extract video ID from various URL formats
    video_id = None
    
    # Check if it's already just a video ID (11 characters)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", youtube_url):
        video_id = youtube_url
    else:
        # Try to extract from various URL formats
        match = re.search(r"(?:v=|youtu\.be/|embed/|shorts/|live/)([a-zA-Z0-9_-]{11})", youtube_url)
        if match:
            video_id = match.group(1)
    
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {youtube_url}")
    
    # Return standard watch URL
    return f"https://www.youtube.com/watch?v={video_id}"


def download_audio(job_id, youtube_url, cookies_file=None):
    """
    Download audio from YouTube video using RapidAPI and convert to 16 kHz mono WAV
    
    Args:
        job_id: Job identifier
        youtube_url: YouTube video URL (any format)
        cookies_file: Not used anymore (kept for backward compatibility)
    
    Returns:
        dict: {
            'success': bool,
            'raw_audio': str,  # Path to raw audio file (MP3)
            'prepared_audio': str,  # Path to 16kHz mono audio file (WAV)
            'raw_size_mb': float,
            'prepared_size_mb': float,
            'error': str or None
        }
    """
    try:
        # Get RapidAPI key from database
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT key_value FROM api_keys 
                WHERE LOWER(provider) = 'rapidapi'
            """)
            api_key_row = cursor.fetchone()
            
            if not api_key_row or not api_key_row.get('key_value'):
                raise Exception(
                    "RapidAPI key not found. "
                    "Please add your RapidAPI key in the API Keys page."
                )
            
            rapidapi_key = api_key_row['key_value']
        
        # Setup paths
        audio_folder = os.path.join('backend', 'job_files', job_id, 'audio')
        os.makedirs(audio_folder, exist_ok=True)
        
        raw_audio_path = os.path.join(audio_folder, 'raw_audio.mp3')
        prepared_audio_path = os.path.join(audio_folder, 'audio_16k_mono.wav')
        
        # Convert URL to standard watch format
        print(f"🎧 Converting YouTube URL to standard format...")
        standard_url = convert_to_watch_url(youtube_url)
        print(f"✓ Standard URL: {standard_url}")
        
        # Step 1: Get download link from RapidAPI
        print(f"🎧 Requesting download link from RapidAPI...")
        
        conn = http.client.HTTPSConnection("yt-search-and-download-mp3.p.rapidapi.com")
        
        headers = {
            'x-rapidapi-key': rapidapi_key,
            'x-rapidapi-host': "yt-search-and-download-mp3.p.rapidapi.com"
        }
        
        # URL encode the YouTube URL
        encoded_url = urllib.parse.quote(standard_url, safe='')
        request_path = f"/mp3?url={encoded_url}"
        
        conn.request("GET", request_path, headers=headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()
        
        # Parse response
        response_text = data.decode("utf-8")
        print(f"✓ API Response received")
        
        # Parse JSON response
        try:
            response_json = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract download URL from text response
            # Response format: success:true title:"..." download:"..."
            download_match = re.search(r'download:"([^"]+)"', response_text)
            if download_match:
                download_url = download_match.group(1)
            else:
                raise Exception(f"Could not parse API response: {response_text[:200]}")
        else:
            # JSON response
            if not response_json.get('success'):
                raise Exception(f"API request failed: {response_json.get('message', 'Unknown error')}")
            
            download_url = response_json.get('download')
            if not download_url:
                raise Exception("No download URL in API response")
        
        print(f"✓ Download URL obtained")
        
        # Step 2: Download MP3 file
        print(f"🎧 Downloading MP3 file...")
        
        urllib.request.urlretrieve(download_url, raw_audio_path)
        
        if not os.path.exists(raw_audio_path):
            raise Exception("Failed to download MP3 file")
        
        raw_size = os.path.getsize(raw_audio_path) / (1024 * 1024)  # MB
        print(f"✓ Audio downloaded: {raw_audio_path} ({round(raw_size, 2)} MB)")
        
        # Step 3: Convert to 16 kHz mono WAV using ffmpeg
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
        
        prepared_size = os.path.getsize(prepared_audio_path) / (1024 * 1024)  # MB
        print(f"✓ Audio prepared: {prepared_audio_path} ({round(prepared_size, 2)} MB)")
        
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
