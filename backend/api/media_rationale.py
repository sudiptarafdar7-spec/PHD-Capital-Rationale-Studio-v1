from flask import request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.utils.database import get_db_cursor
from backend.api import media_rationale_bp
from backend.models.user import User
from backend.pipeline.fetch_video_data import fetch_video_metadata
from backend.pipeline.pipeline_manager import create_job_directory, PIPELINE_STEPS, run_pipeline_step
from datetime import datetime
import os
import secrets
import threading
import csv
import io
import shutil

def is_admin(user_id):
    user = User.find_by_id(user_id)
    return user and user.get('role') == 'admin'

def check_job_access(job_id, current_user_id):
    """Verify user owns this job or is admin"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT user_id FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            return False, "Job not found"
        
        if job['user_id'] != current_user_id and not is_admin(current_user_id):
            return False, "Access denied"
        
        return True, None

@media_rationale_bp.route('/fetch-video', methods=['POST'])
@jwt_required()
def fetch_video():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        youtube_url = data.get('youtubeUrl', '').strip()
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        # Fetch video metadata using yt-dlp
        video_data = fetch_video_metadata(youtube_url)
        
        # Match channel logo from database using exact channel name
        channel_logo_url = ''
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, channel_logo_path 
                FROM channels 
                WHERE LOWER(channel_name) = LOWER(%s)
            """, (video_data['channel_name'],))
            
            channel = cursor.fetchone()
            if channel and channel.get('channel_logo_path'):
                # Construct the URL to access the channel logo
                channel_logo_url = f"/api/v1/channels/{channel['id']}/logo"
        
        return jsonify({
            'success': True,
            'message': 'Video metadata fetched successfully',
            'data': {
                'videoId': video_data['video_id'],
                'title': video_data['title'],
                'channelName': video_data['channel_name'],
                'channelLogo': channel_logo_url,
                'uploadDate': video_data['upload_date'],
                'uploadTime': video_data['upload_time'],
                'duration': video_data['duration']
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching video: {str(e)}")
        return jsonify({'error': f'Failed to fetch video metadata: {str(e)}'}), 500

@media_rationale_bp.route('/start-analysis', methods=['POST'])
@jwt_required()
def start_analysis():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Extract required data
        tool_used = data.get('toolUsed', 'Media Rationale')
        video_title = data.get('videoTitle', '')
        video_id = data.get('videoId', '')
        channel_name = data.get('channelName', '')
        upload_date = data.get('uploadDate', '')
        upload_time = data.get('uploadTime', '00:00:00')
        duration = data.get('duration', '')
        youtube_url = data.get('youtubeUrl', '')
        
        if not youtube_url or not video_title:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Generate unique job ID
        job_id = f"job-{secrets.token_hex(4)}"
        
        # Get channel_id from database (if exists)
        channel_id = None
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM channels 
                WHERE LOWER(channel_name) = LOWER(%s)
            """, (channel_name,))
            
            channel = cursor.fetchone()
            if channel:
                channel_id = channel['id']
        
        # Create job directory structure
        create_job_directory(job_id)
        
        # Create job record in database
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO jobs (
                    id, user_id, channel_id, tool_used, video_title, video_id,
                    upload_date, upload_time, youtube_url, duration, status, 
                    current_step, progress, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                job_id, current_user_id, channel_id, tool_used, video_title, video_id,
                upload_date, upload_time, youtube_url, duration, 'pending', 
                0, 0, datetime.now(), datetime.now()
            ))
            
            # Initialize all 14 pipeline steps (Step 15 is API-only)
            for step in PIPELINE_STEPS:
                cursor.execute("""
                    INSERT INTO job_steps (
                        job_id, step_number, step_name, 
                        status, message, output_files
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    job_id, step['number'], step['name'],
                    'pending', None, []
                ))
        
        # Start pipeline execution in background thread
        def run_pipeline_background():
            try:
                # Update job status to processing
                with get_db_cursor(commit=True) as cursor:
                    cursor.execute("""
                        UPDATE jobs 
                        SET status = 'processing', updated_at = %s
                        WHERE id = %s
                    """, (datetime.now(), job_id))
                
                # Run all pipeline steps (1-14)
                # Step 15 is handled via API endpoints (Save/Sign/Delete), not automatic pipeline
                all_success = True
                for step_num in range(1, 15):
                    success = run_pipeline_step(job_id, step_num)
                    if not success:
                        all_success = False
                        break
                
                # After Step 14 completes successfully, set status to 'pdf_ready'
                if all_success:
                    with get_db_cursor(commit=True) as cursor:
                        cursor.execute("""
                            UPDATE jobs 
                            SET status = 'pdf_ready', progress = 93, updated_at = %s
                            WHERE id = %s
                        """, (datetime.now(), job_id))
                
            except Exception as e:
                print(f"Pipeline error for job {job_id}: {str(e)}")
                with get_db_cursor(commit=True) as cursor:
                    cursor.execute("""
                        UPDATE jobs 
                        SET status = 'failed', updated_at = %s
                        WHERE id = %s
                    """, (datetime.now(), job_id))
        
        # Start background thread
        thread = threading.Thread(target=run_pipeline_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Analysis started successfully',
            'jobId': job_id
        }), 200
        
    except Exception as e:
        print(f"Error starting analysis: {str(e)}")
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>', methods=['GET'])
@jwt_required()
def get_job(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        # Get job details from database
        with get_db_cursor() as cursor:
            # Fetch job record
            cursor.execute("""
                SELECT 
                    j.id,
                    j.user_id,
                    j.channel_id,
                    j.tool_used,
                    j.video_title,
                    j.video_id,
                    j.upload_date,
                    j.upload_time,
                    j.youtube_url,
                    j.duration,
                    j.status,
                    j.current_step,
                    j.progress,
                    j.created_at,
                    j.updated_at,
                    c.id as db_channel_id,
                    c.channel_name,
                    c.channel_logo_path
                FROM jobs j
                LEFT JOIN channels c ON j.channel_id = c.id
                WHERE j.id = %s
            """, (job_id,))
            
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            # Construct channel logo URL if channel exists
            channel_logo_url = ''
            if job.get('db_channel_id') and job.get('channel_logo_path'):
                channel_logo_url = f"/api/v1/channels/{job['db_channel_id']}/logo"
            
            # Fetch all job steps
            cursor.execute("""
                SELECT 
                    step_number,
                    step_name,
                    status,
                    message,
                    output_files,
                    started_at,
                    ended_at
                FROM job_steps
                WHERE job_id = %s
                ORDER BY step_number ASC
            """, (job_id,))
            
            steps = cursor.fetchall()
            
            # Get step descriptions from PIPELINE_STEPS
            step_descriptions = {step['number']: step['description'] for step in PIPELINE_STEPS}
            
            # Format steps for frontend
            formatted_steps = []
            for step in steps:
                formatted_steps.append({
                    'step_number': step['step_number'],
                    'name': step['step_name'],
                    'description': step_descriptions.get(step['step_number'], ''),
                    'status': step['status'],
                    'message': step.get('message'),
                    'outputFiles': step.get('output_files', []),
                    'startedAt': step['started_at'].isoformat() if step.get('started_at') else None,
                    'endedAt': step['ended_at'].isoformat() if step.get('ended_at') else None
                })
            
            # Fetch unsigned and signed PDF paths from saved_rationale table
            unsigned_pdf_path = None
            signed_pdf_path = None
            if job['status'] in ('signed', 'completed'):
                cursor.execute("""
                    SELECT unsigned_pdf_path, signed_pdf_path
                    FROM saved_rationale
                    WHERE job_id = %s
                """, (job_id,))
                rationale = cursor.fetchone()
                if rationale:
                    unsigned_pdf_path = rationale.get('unsigned_pdf_path')
                    signed_pdf_path = rationale.get('signed_pdf_path')
            
            # Format job response
            job_data = {
                'id': job['id'],
                'userId': job['user_id'],
                'toolUsed': job['tool_used'],
                'videoTitle': job['video_title'],
                'videoId': job['video_id'],
                'videoUploadDate': job['upload_date'].isoformat() if job.get('upload_date') else '',
                'youtubeUrl': job['youtube_url'],
                'duration': job['duration'],
                'channelName': job.get('channel_name'),
                'channelLogo': channel_logo_url,
                'status': job['status'],
                'currentStep': job['current_step'],
                'progress': job['progress'],
                'steps': formatted_steps,
                'unsignedPdfPath': unsigned_pdf_path,  # Include unsigned PDF path from saved_rationale
                'signedPdfPath': signed_pdf_path,  # Include signed PDF path from saved_rationale
                'createdAt': job['created_at'].isoformat() if job.get('created_at') else None,
                'updatedAt': job['updated_at'].isoformat() if job.get('updated_at') else None
            }
            
            return jsonify({
                'success': True,
                'job': job_data
            }), 200
        
    except Exception as e:
        print(f"Error getting job: {str(e)}")
        return jsonify({'error': f'Failed to get job: {str(e)}'}), 500

@media_rationale_bp.route('/restart-step/<job_id>/<int:step_number>', methods=['POST'])
@jwt_required()
def restart_step(job_id, step_number):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        # Validate step number (Pipeline has 14 steps, Step 15 is API-only)
        if step_number < 1 or step_number > 14:
            return jsonify({'error': 'Invalid step number. Must be between 1 and 14'}), 400
        
        # Check if job exists
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, status FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
        
        # Reset the specified step and all subsequent steps to 'pending'
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE job_steps
                SET status = 'pending', message = NULL, output_files = ARRAY[]::text[], 
                    started_at = NULL, ended_at = NULL
                WHERE job_id = %s AND step_number >= %s
            """, (job_id, step_number))
            
            # Update job status to processing and reset progress
            # Pipeline has 14 steps (Step 15 is API-only)
            progress = int(((step_number - 1) / 14) * 100)
            cursor.execute("""
                UPDATE jobs
                SET status = 'processing', current_step = %s, progress = %s, updated_at = %s
                WHERE id = %s
            """, (step_number - 1, progress, datetime.now(), job_id))
        
        # Restart pipeline execution from the specified step in background thread
        def run_pipeline_from_step():
            try:
                # Run pipeline steps from step_number to 14 (Step 15 is API-only)
                all_success = True
                for step_num in range(step_number, 15):
                    success = run_pipeline_step(job_id, step_num)
                    if not success:
                        all_success = False
                        break
                
                # After Step 14 completes successfully, set status to 'pdf_ready'
                if all_success:
                    with get_db_cursor(commit=True) as cursor:
                        cursor.execute("""
                            UPDATE jobs 
                            SET status = 'pdf_ready', progress = 93, updated_at = %s
                            WHERE id = %s
                        """, (datetime.now(), job_id))
                    print(f"✅ Pipeline completed! Job {job_id} status set to 'pdf_ready' (awaiting user action)")
                        
            except Exception as e:
                print(f"Pipeline restart error for job {job_id}: {str(e)}")
                with get_db_cursor(commit=True) as cursor:
                    cursor.execute("""
                        UPDATE jobs 
                        SET status = 'failed', updated_at = %s
                        WHERE id = %s
                    """, (datetime.now(), job_id))
        
        # Start background thread
        thread = threading.Thread(target=run_pipeline_from_step)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Pipeline restarted from step {step_number}'
        }), 200
        
    except Exception as e:
        print(f"Error restarting step: {str(e)}")
        return jsonify({'error': f'Failed to restart step: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>/csv', methods=['GET'])
@jwt_required()
def get_csv(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        # Check if job exists
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
        
        # Path to stocks_with_chart.csv
        csv_path = os.path.join('backend', 'job_files', job_id, 'analysis', 'stocks_with_chart.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({'error': 'CSV file not found. Please complete pipeline steps up to step 13.'}), 404
        
        # Read CSV file and return as JSON
        csv_data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_data.append(row)
        
        return jsonify({
            'success': True,
            'data': csv_data
        }), 200
        
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return jsonify({'error': f'Failed to read CSV: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>/csv', methods=['PUT'])
@jwt_required()
def update_csv(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        data = request.get_json()
        
        csv_data = data.get('data', [])
        
        if not csv_data:
            return jsonify({'error': 'CSV data is required'}), 400
        
        # Check if job exists
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
        
        # Path to stocks_with_chart.csv
        csv_path = os.path.join('backend', 'job_files', job_id, 'analysis', 'stocks_with_chart.csv')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # Write CSV data back to file
        if csv_data:
            fieldnames = csv_data[0].keys()
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
        
        return jsonify({
            'success': True,
            'message': 'CSV updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error updating CSV: {str(e)}")
        return jsonify({'error': f'Failed to update CSV: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>/generate-pdf', methods=['POST'])
@jwt_required()
def generate_pdf(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        # Check if job exists
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, status FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
        
        # Run step 14 (Generate PDF) in background thread
        def run_pdf_generation():
            try:
                run_pipeline_step(job_id, 14)
            except Exception as e:
                print(f"PDF generation error for job {job_id}: {str(e)}")
        
        thread = threading.Thread(target=run_pdf_generation)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'PDF generation started'
        }), 200
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>/save', methods=['POST'])
@jwt_required()
def save_rationale(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        # Get job details
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, channel_id, tool_used, video_title, 
                       upload_date, youtube_url
                FROM jobs WHERE id = %s
            """, (job_id,))
            
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
        
        # Path to unsigned PDF
        pdf_path = os.path.join('backend', 'job_files', job_id, 'output', 'final_rationale_report.pdf')
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF not found. Please generate PDF first.'}), 404
        
        # Save to saved_rationale table
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO saved_rationale (
                    job_id, channel_id, tool_used, video_title, 
                    video_upload_date, youtube_url, unsigned_pdf_path, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                job_id, job['channel_id'], job['tool_used'], job['video_title'],
                job['upload_date'], job['youtube_url'], pdf_path, datetime.now()
            ))
            
            result = cursor.fetchone()
            rationale_id = result['id'] if result else None
        
        # Create activity log
        from backend.api.activity_logs import create_activity_log
        create_activity_log(
            current_user_id, 
            'save_rationale',
            f'Saved rationale for "{job["video_title"]}"',
            job_id,
            job['tool_used']
        )
        
        return jsonify({
            'success': True,
            'message': 'Rationale saved successfully',
            'rationaleId': rationale_id
        }), 200
        
    except Exception as e:
        print(f"Error saving rationale: {str(e)}")
        return jsonify({'error': f'Failed to save rationale: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>/upload-signed', methods=['POST'])
@jwt_required()
def upload_signed_pdf(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if rationale exists for this job
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM saved_rationale WHERE job_id = %s
            """, (job_id,))
            
            rationale = cursor.fetchone()
            
            if not rationale:
                return jsonify({'error': 'Please save rationale first before uploading signed PDF'}), 400
        
        # Save signed PDF file
        signed_pdf_dir = os.path.join('backend', 'job_files', job_id, 'output')
        os.makedirs(signed_pdf_dir, exist_ok=True)
        
        signed_pdf_path = os.path.join(signed_pdf_dir, 'signed_rationale_report.pdf')
        file.save(signed_pdf_path)
        
        # Update saved_rationale with signed PDF path
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE saved_rationale
                SET signed_pdf_path = %s, signed_uploaded_at = %s
                WHERE job_id = %s
            """, (signed_pdf_path, datetime.now(), job_id))
        
        # Create activity log
        from backend.api.activity_logs import create_activity_log
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT video_title, tool_used FROM jobs WHERE id = %s
            """, (job_id,))
            job = cursor.fetchone()
        
        if job:
            create_activity_log(
                current_user_id,
                'upload_signed',
                f'Uploaded signed PDF for "{job["video_title"]}"',
                job_id,
                job['tool_used']
            )
        
        return jsonify({
            'success': True,
            'message': 'Signed PDF uploaded successfully'
        }), 200
        
    except Exception as e:
        print(f"Error uploading signed PDF: {str(e)}")
        return jsonify({'error': f'Failed to upload signed PDF: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>/pdf/unsigned', methods=['GET'])
@jwt_required()
def download_unsigned_pdf(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        pdf_path = os.path.join('backend', 'job_files', job_id, 'output', 'final_rationale_report.pdf')
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF not found'}), 404
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'rationale_{job_id}_unsigned.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error downloading PDF: {str(e)}")
        return jsonify({'error': f'Failed to download PDF: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>/pdf/signed', methods=['GET'])
@jwt_required()
def download_signed_pdf(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        pdf_path = os.path.join('backend', 'job_files', job_id, 'output', 'signed_rationale_report.pdf')
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'Signed PDF not found'}), 404
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'rationale_{job_id}_signed.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error downloading signed PDF: {str(e)}")
        return jsonify({'error': f'Failed to download signed PDF: {str(e)}'}), 500

@media_rationale_bp.route('/job/<job_id>', methods=['DELETE'])
@jwt_required()
def delete_job(job_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check authorization
        has_access, error_msg = check_job_access(job_id, current_user_id)
        if not has_access:
            return jsonify({'error': error_msg}), 403
        
        # Check if job exists
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
        
        # Delete job from database (will cascade delete job_steps)
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        
        # Delete job directory and all files
        job_dir = os.path.join('backend', 'job_files', job_id)
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir)
        
        return jsonify({
            'success': True,
            'message': 'Job deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting job: {str(e)}")
        return jsonify({'error': f'Failed to delete job: {str(e)}'}), 500
