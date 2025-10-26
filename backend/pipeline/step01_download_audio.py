"""
Step 1: Download Audio from YouTube Video
Uses Apify YouTube Video Downloader API to get video URL, then ffmpeg to download and extract audio
"""
import os
import subprocess
from apify_client import ApifyClient
from backend.utils.database import get_db_cursor


def download_audio(job_id, youtube_url, cookies_file=None):
    """
    Download audio from YouTube video using Apify and convert to 16 kHz mono WAV
    
    Args:
        job_id: Job identifier
        youtube_url: YouTube video URL
        cookies_file: Not used (kept for backward compatibility)
    
    Returns:
        dict: {
            'success': bool,
            'raw_audio': str,  # Path to raw audio file (WAV format)
            'prepared_audio': str,  # Path to 16kHz mono audio file
            'raw_size_mb': float,
            'prepared_size_mb': float,
            'error': str or None
        }
    """
    try:
        # Get Apify API key from database
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT key_value FROM api_keys 
                WHERE LOWER(provider) = 'apify'
            """)
            api_key_row = cursor.fetchone()
            
            if not api_key_row or not api_key_row['key_value']:
                return {
                    'success': False,
                    'error': 'Apify API key not configured. Please add your Apify API key in the API Keys page.'
                }
            
            apify_api_key = api_key_row['key_value']

        # Setup paths
        audio_folder = os.path.join('backend', 'job_files', job_id, 'audio')
        os.makedirs(audio_folder, exist_ok=True)
        
        raw_audio_path = os.path.join(audio_folder, 'raw_audio.wav')
        prepared_audio_path = os.path.join(audio_folder, 'audio_16k_mono.wav')
        
        # Step 1: Get video download URL from Apify
        print(f"🎧 Fetching video URL from Apify: {youtube_url}")
        
        try:
            # Initialize Apify client
            client = ApifyClient(apify_api_key)
            
            # Prepare the Actor input
            run_input = {
                "videos": [{
                    "url": youtube_url
                }]
            }
            
            # Run the Actor and wait for it to finish
            print("⏳ Starting Apify YouTube Video Downloader...")
            run = client.actor("streamers/youtube-video-downloader").call(run_input=run_input)
            
            # Get the dataset ID
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                return {
                    'success': False,
                    'error': 'Apify actor did not return a dataset ID. Please check your Apify API key.'
                }
            
            print(f"✓ Apify job completed. Dataset ID: {dataset_id}")
            
        except Exception as e:
            error_msg = str(e)
            if "Invalid token" in error_msg or "Unauthorized" in error_msg:
                return {
                    'success': False,
                    'error': 'Invalid Apify API key. Please check your API key in the API Keys page.'
                }
            return {
                'success': False,
                'error': f'Apify actor execution failed: {error_msg}'
            }
        
        # Step 2: Fetch results from dataset
        try:
            items = list(client.dataset(dataset_id).iterate_items())
            
            if not items or len(items) == 0:
                return {
                    'success': False,
                    'error': 'No video data returned from Apify. The video may be unavailable, private, or age-restricted.'
                }
            
            # Get the first video result
            video_data = items[0]
            
            # Find the download URL - try different possible fields
            download_url = None
            for url_field in ['videoUrl', 'url', 'downloadUrl', 'fileUrl', 'videoLink']:
                if url_field in video_data and video_data[url_field]:
                    download_url = video_data[url_field]
                    break
            
            if not download_url:
                return {
                    'success': False,
                    'error': f'No download URL found in Apify response. Available fields: {", ".join(video_data.keys())}'
                }
            
            print(f"📥 Video URL obtained from Apify")
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to fetch Apify dataset: {str(e)}'
            }
        
        # Step 3: Download and extract audio to WAV using ffmpeg
        # This mimics the original yt-dlp behavior: extract audio and convert to WAV
        print(f"🎵 Downloading and extracting audio to WAV...")
        
        try:
            # Download and extract audio directly to WAV format
            # ffmpeg handles HLS/M3U8 URLs natively
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', download_url,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM WAV codec
                '-ar', '44100',  # 44.1kHz sample rate
                '-ac', '2',  # Stereo
                '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '-y',  # Overwrite
                raw_audio_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                stderr_preview = result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
                return {
                    'success': False,
                    'error': f'Audio download/extraction failed. The URL may have expired or be inaccessible. Error: {stderr_preview}'
                }
            
            if not os.path.exists(raw_audio_path):
                return {
                    'success': False,
                    'error': 'Raw audio file was not created. The download may have failed.'
                }
            
            print(f"✓ Raw audio extracted: {raw_audio_path}")
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Audio download timed out after 5 minutes. The video may be too large or the connection is slow.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Audio extraction failed: {str(e)}'
            }
        
        # Step 4: Convert to 16 kHz mono WAV for transcription
        print(f"🔊 Converting to 16 kHz mono WAV for transcription...")
        
        try:
            convert_cmd = [
                'ffmpeg',
                '-i', raw_audio_path,
                '-ar', '16000',  # 16 kHz sample rate (required for AssemblyAI)
                '-ac', '1',       # mono (1 channel)
                '-y',             # overwrite
                prepared_audio_path
            ]
            
            result = subprocess.run(
                convert_cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes timeout
            )
            
            if result.returncode != 0:
                stderr_preview = result.stderr[-300:] if len(result.stderr) > 300 else result.stderr
                # Clean up raw audio on failure
                if os.path.exists(raw_audio_path):
                    os.remove(raw_audio_path)
                return {
                    'success': False,
                    'error': f'Audio conversion to 16kHz mono failed: {stderr_preview}'
                }
            
            if not os.path.exists(prepared_audio_path):
                # Clean up raw audio on failure
                if os.path.exists(raw_audio_path):
                    os.remove(raw_audio_path)
                return {
                    'success': False,
                    'error': 'Prepared audio file was not created'
                }
            
            print(f"✓ Audio prepared: {prepared_audio_path}")
            
        except subprocess.TimeoutExpired:
            # Clean up raw audio on failure
            if os.path.exists(raw_audio_path):
                os.remove(raw_audio_path)
            return {
                'success': False,
                'error': 'Audio conversion timed out after 3 minutes. The audio file may be too large.'
            }
        except Exception as e:
            # Clean up raw audio on failure
            if os.path.exists(raw_audio_path):
                os.remove(raw_audio_path)
            return {
                'success': False,
                'error': f'Audio conversion failed: {str(e)}'
            }
        
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
            'error': f'Unexpected error in audio download: {str(e)}'
        }
