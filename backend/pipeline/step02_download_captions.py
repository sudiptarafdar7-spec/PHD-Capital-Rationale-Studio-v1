"""
Step 2: Download Auto-Generated Captions from YouTube Video
Uses youtube-transcript-api for reliable caption fetching (bypasses bot blocking)
Fallback to yt-dlp if needed
"""
import os
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re


def extract_video_id(youtube_url):
    """
    Extract video ID from various YouTube URL formats
    
    Args:
        youtube_url: YouTube video URL
        
    Returns:
        str: Video ID or None if not found
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    return None


def download_captions(job_id, youtube_url, cookies_file=None):
    """
    Download auto-generated captions from YouTube video using youtube-transcript-api
    
    Args:
        job_id: Job identifier
        youtube_url: YouTube video URL
        cookies_file: Optional (not used by youtube-transcript-api, kept for compatibility)
    
    Returns:
        dict: {
            'success': bool,
            'captions_path': str,  # Path to captions.json file
            'format': str,  # 'youtube-transcript-api' or 'yt-dlp-fallback'
            'language': str,  # Language code (hi or en)
            'error': str or None
        }
    """
    try:
        # Setup paths
        captions_folder = os.path.join('backend', 'job_files', job_id, 'captions')
        os.makedirs(captions_folder, exist_ok=True)
        
        captions_json_path = os.path.join(captions_folder, 'captions.json')
        
        print(f"📝 Fetching auto-generated captions (Hindi/English)...")
        
        # Extract video ID from URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return {
                'success': False,
                'error': 'Could not extract video ID from YouTube URL'
            }
        
        print(f"✓ Video ID: {video_id}")
        
        # Try to fetch transcript using youtube-transcript-api
        try:
            # Try Hindi first, then English
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get manually created or auto-generated captions
            transcript = None
            language = None
            
            # Prefer Hindi
            try:
                transcript = transcript_list.find_transcript(['hi'])
                language = 'hi'
                print(f"✓ Found Hindi captions (auto-generated: {transcript.is_generated})")
            except NoTranscriptFound:
                # Fallback to English
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    language = 'en'
                    print(f"✓ Found English captions (auto-generated: {transcript.is_generated})")
                except NoTranscriptFound:
                    # Try any available language
                    available = list(transcript_list)
                    if available:
                        transcript = available[0]
                        language = transcript.language_code
                        print(f"✓ Found {language} captions (auto-generated: {transcript.is_generated})")
                    else:
                        raise NoTranscriptFound(video_id, [], None)
            
            # Fetch the actual transcript
            caption_data = transcript.fetch()
            
            # Convert to the expected format (same as yt-dlp json3 format)
            events = []
            for entry in caption_data:
                events.append({
                    'tStartMs': int(entry['start'] * 1000),  # Convert seconds to milliseconds
                    'dDurationMs': int(entry['duration'] * 1000),
                    'segs': [{'utf8': entry['text']}]
                })
            
            # Save in expected format
            output_data = {'events': events}
            
            with open(captions_json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            # Get file size
            file_size = os.path.getsize(captions_json_path) / 1024  # KB
            
            print(f"✅ Captions saved successfully ({len(events)} segments, {language})")
            
            return {
                'success': True,
                'captions_path': captions_json_path,
                'format': 'youtube-transcript-api',
                'language': language,
                'file_size_kb': round(file_size, 2),
                'error': None
            }
            
        except TranscriptsDisabled:
            return {
                'success': False,
                'error': 'Captions are disabled for this video'
            }
            
        except NoTranscriptFound:
            return {
                'success': False,
                'error': 'No captions found for this video (tried Hindi, English, and other languages)'
            }
            
        except Exception as e:
            # If youtube-transcript-api fails, log the error and return failure
            print(f"⚠️ youtube-transcript-api failed: {str(e)}")
            return {
                'success': False,
                'error': f'Caption fetch error: {str(e)}'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Caption download error: {str(e)}'
        }
