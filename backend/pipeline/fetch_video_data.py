"""
Fetch YouTube Video Metadata using yt-dlp
Extracts video metadata including title, channel, upload date/time, and duration
"""
import subprocess
import json
import os
from datetime import datetime, timezone, timedelta

# Timezone setup for IST (India Standard Time)
try:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
except ImportError:
    # Fallback for systems without zoneinfo
    IST = timezone(timedelta(hours=5, minutes=30))

def fetch_video_metadata(youtube_url):
    """
    Fetch video metadata from YouTube URL using yt-dlp command-line tool
    
    Args:
        youtube_url: YouTube video URL (full URL or video ID)
        
    Returns:
        dict: Video metadata including:
            - video_id: YouTube video ID
            - title: Video title
            - channel_name: Channel name
            - upload_date: Upload date (YYYY-MM-DD)
            - upload_time: Upload time (HH:MM:SS) - estimated as 00:00:00
            - duration: Duration in MM:SS or HH:MM:SS format
            
    Raises:
        Exception: If video cannot be fetched or parsed
    """
    # Try multiple player client configurations for better success rate
    player_clients = [
        'android,web',  # Try Android client first (usually works best)
        'web',          # Fallback to web only
        'ios,web'       # Try iOS as last resort
    ]
    
    last_error = None
    
    for player_client in player_clients:
        try:
            result = _fetch_with_client(youtube_url, player_client)
            if result:
                return result
        except Exception as e:
            last_error = str(e)
            continue
    
    # All attempts failed
    raise Exception(f"Failed to fetch video metadata after trying multiple methods. Last error: {last_error}")


def _fetch_with_client(youtube_url, player_client):
    """Helper function to fetch video with specific player client"""
    try:
        # Build yt-dlp command with enhanced YouTube bypass
        cmd = [
            'yt-dlp', 
            '-J', 
            '--no-warnings', 
            '--skip-download',
            '--no-check-certificates',
            '--geo-bypass',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--extractor-args', f'youtube:player_client={player_client}',
            '--extractor-args', 'youtube:skip=dash,hls',
            '--referer', 'https://www.youtube.com/'
        ]
        
        # Check if cookies file exists in job_files directory (writable location)
        cookies_path = os.path.join('backend', 'job_files', 'youtube_cookies.txt')
        if os.path.exists(cookies_path):
            cmd.extend(['--cookies', cookies_path])
            print(f"  ✓ Using cookies from: {cookies_path}")
        
        # Using multiple bypass options and player clients to handle YouTube restrictions
        print(f"  Trying player client: {player_client}")
        
        # Add the URL
        cmd.append(youtube_url)
        
        # Run yt-dlp as subprocess to get video info as JSON
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr
            # Provide helpful error message
            if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
                raise Exception(
                    "YouTube is blocking this request. This may be due to: "
                    "1) Age-restricted or private video, "
                    "2) Geographic restrictions, or "
                    "3) YouTube's bot detection. "
                    "Please try a different video or check if the video is publicly accessible."
                )
            raise Exception(f"yt-dlp failed: {error_msg}")
        
        # Parse JSON output
        info = json.loads(result.stdout)
        
        # Extract video ID
        video_id = info.get('id', '')
        
        # Extract title
        title = info.get('title', 'Unknown Title')
        
        # Extract channel name
        channel_name = info.get('uploader', info.get('channel', 'Unknown Channel'))
        
        # Extract upload date and time using timestamp
        # Try to get timestamp from release_timestamp or timestamp
        timestamp = info.get('release_timestamp') or info.get('timestamp')
        
        if timestamp and isinstance(timestamp, (int, float)):
            # Convert UTC timestamp to IST datetime
            utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            ist_dt = utc_dt.astimezone(IST)
            upload_date = ist_dt.strftime('%Y-%m-%d')
            upload_time = ist_dt.strftime('%H:%M:00')  # Format as HH:MM:00 (seconds set to 00)
        else:
            # Fallback to upload_date field (format: YYYYMMDD)
            upload_date_str = info.get('upload_date', '')
            if upload_date_str and len(upload_date_str) == 8:
                # Convert YYYYMMDD to YYYY-MM-DD
                upload_date = f"{upload_date_str[:4]}-{upload_date_str[4:6]}-{upload_date_str[6:8]}"
            else:
                upload_date = datetime.now(IST).strftime('%Y-%m-%d')
            
            # If timestamp not available, use 00:00:00
            upload_time = '00:00:00'
        
        # Extract duration (in seconds) and format it
        duration_seconds = info.get('duration', 0)
        if duration_seconds:
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            
            if hours > 0:
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration = f"{minutes:02d}:{seconds:02d}"
        else:
            duration = "00:00"
        
        return {
            'video_id': video_id,
            'title': title,
            'channel_name': channel_name,
            'upload_date': upload_date,
            'upload_time': upload_time,
            'duration': duration,
            'thumbnail': info.get('thumbnail', ''),
            'description': info.get('description', '')
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Request timed out while fetching video metadata")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse video metadata: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to fetch video metadata: {str(e)}")
