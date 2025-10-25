"""
Fetch YouTube Video Metadata using YouTube Data API v3
Extracts video metadata including title, channel, upload date/time, and duration
"""
import re
import requests
import isodate
from datetime import datetime, timezone, timedelta
from backend.utils.database import get_db_cursor

# Timezone setup for IST (India Standard Time)
try:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
except ImportError:
    # Fallback for systems without zoneinfo
    IST = timezone(timedelta(hours=5, minutes=30))


def extract_video_id(youtube_url):
    """
    Extracts the YouTube video ID from a URL or returns it directly if already an ID.
    """
    if re.match(r"^[a-zA-Z0-9_-]{11}$", youtube_url):
        return youtube_url
    match = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})", youtube_url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL or Video ID")


def fetch_video_metadata(youtube_url):
    """
    Fetch video metadata from YouTube Data API v3

    Args:
        youtube_url: YouTube video URL or ID

    Returns:
        dict: Video metadata including:
            - video_id
            - title
            - channel_name
            - upload_date
            - upload_time
            - duration
            - thumbnail
            - description

    Raises:
        Exception: If video cannot be fetched or parsed
    """
    try:
        # Get YouTube API key from database
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT key_value FROM api_keys 
                WHERE LOWER(provider) = 'youtube_data'
            """)
            api_key_row = cursor.fetchone()
            
            if not api_key_row or not api_key_row['key_value']:
                raise Exception(
                    "YouTube Data API v3 key not found. "
                    "Please add your YouTube Data API v3 key in the API Keys page."
                )
            
            api_key = api_key_row['key_value']

        video_id = extract_video_id(youtube_url)

        # Build API URL
        api_url = (
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=snippet,contentDetails&id={video_id}&key={api_key}"
        )

        # Send request
        response = requests.get(api_url, timeout=15)
        if response.status_code != 200:
            raise Exception(f"YouTube API request failed: {response.text}")

        data = response.json()
        items = data.get("items", [])
        if not items:
            raise Exception(f"No video found for ID: {video_id}")

        info = items[0]
        snippet = info.get("snippet", {})
        content = info.get("contentDetails", {})

        # Title and channel
        title = snippet.get("title", "Unknown Title")
        channel_name = snippet.get("channelTitle", "Unknown Channel")

        # Upload datetime (convert UTC → IST)
        published_at = snippet.get("publishedAt")
        if published_at:
            utc_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            ist_dt = utc_dt.astimezone(IST)
            upload_date = ist_dt.strftime("%Y-%m-%d")
            upload_time = ist_dt.strftime("%H:%M:%S")
        else:
            upload_date = datetime.now(IST).strftime("%Y-%m-%d")
            upload_time = "00:00:00"

        # Duration (ISO 8601 → HH:MM:SS)
        iso_duration = content.get("duration", "PT0S")
        duration_td = isodate.parse_duration(iso_duration)
        total_seconds = int(duration_td.total_seconds())
        if total_seconds >= 3600:
            duration = f"{total_seconds//3600:02d}:{(total_seconds%3600)//60:02d}:{total_seconds%60:02d}"
        else:
            duration = f"{(total_seconds%3600)//60:02d}:{total_seconds%60:02d}"

        # Thumbnail & description
        thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
        description = snippet.get("description", "")

        return {
            "video_id": video_id,
            "title": title,
            "channel_name": channel_name,
            "upload_date": upload_date,
            "upload_time": upload_time,
            "duration": duration,
            "thumbnail": thumbnail,
            "description": description,
        }

    except requests.Timeout:
        raise Exception("Request timed out while fetching video metadata")
    except Exception as e:
        raise Exception(f"Failed to fetch video metadata: {str(e)}")
