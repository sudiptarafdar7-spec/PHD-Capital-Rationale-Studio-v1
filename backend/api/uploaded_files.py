from flask import request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from backend.utils.database import get_db_cursor
from backend.api import uploaded_files_bp
from datetime import datetime
import os
import uuid

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploaded_files')
ALLOWED_EXTENSIONS = {
    'masterFile': {'csv'},
    'companyLogo': {'png', 'jpg', 'jpeg'},
    'customFont': {'ttf'}
}

def get_current_user():
    user_id = get_jwt_identity()
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user

def allowed_file(filename, file_type):
    """Check if file extension is allowed for the given file type"""
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS.get(file_type, set())

def get_file_size_string(size_bytes):
    """Convert bytes to human-readable format"""
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024
    if size_mb >= 1:
        return f"{size_mb:.2f} MB"
    else:
        return f"{size_kb:.2f} KB"

def format_uploaded_file(row):
    return {
        'id': row['id'],
        'file_type': row['file_type'],
        'file_name': row['file_name'],
        'file_path': row['file_path'],
        'file_size': row['file_size'],
        'uploaded_at': row['uploaded_at'].isoformat() if row['uploaded_at'] else None,
        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
    }

@uploaded_files_bp.route('', methods=['GET'])
@jwt_required()
def get_uploaded_files():
    """Get all uploaded files"""
    try:
        current_user = get_current_user()
        if not current_user or current_user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM uploaded_files ORDER BY file_type, uploaded_at DESC")
            files = cursor.fetchall()
            
            return jsonify([format_uploaded_file(f) for f in files]), 200
                
    except Exception as e:
        print(f"Error getting uploaded files: {e}")
        return jsonify({'error': str(e)}), 500

@uploaded_files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file (multipart/form-data)"""
    try:
        current_user = get_current_user()
        if not current_user or current_user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type')
        
        if not file_type or file_type not in ALLOWED_EXTENSIONS:
            return jsonify({'error': 'Invalid file type'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, file_type):
            allowed = ', '.join(ALLOWED_EXTENSIONS[file_type])
            return jsonify({'error': f'Invalid file extension. Allowed: {allowed}'}), 400
        
        # Secure the filename
        original_filename = secure_filename(file.filename)
        
        # For masterFile and companyLogo, replace existing file
        if file_type in ['masterFile', 'companyLogo']:
            with get_db_cursor(commit=True) as cursor:
                # Check if file already exists for this type
                cursor.execute("SELECT * FROM uploaded_files WHERE file_type = %s", (file_type,))
                existing = cursor.fetchone()
                
                if existing:
                    # Delete old file from filesystem
                    old_path = existing['file_path']
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    
                    # Delete from database
                    cursor.execute("DELETE FROM uploaded_files WHERE file_type = %s", (file_type,))
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file to disk
        file.save(file_path)
        
        # Get file size
        file_size_bytes = os.path.getsize(file_path)
        file_size = get_file_size_string(file_size_bytes)
        
        # Save to database
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO uploaded_files (file_type, file_name, file_path, file_size, uploaded_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (file_type, original_filename, file_path, file_size, datetime.now(), datetime.now()))
            
            uploaded_file = cursor.fetchone()
            return jsonify(format_uploaded_file(uploaded_file)), 201
            
    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@uploaded_files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete a file"""
    try:
        current_user = get_current_user()
        if not current_user or current_user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        with get_db_cursor(commit=True) as cursor:
            # Get file info
            cursor.execute("SELECT * FROM uploaded_files WHERE id = %s", (file_id,))
            file_record = cursor.fetchone()
            
            if not file_record:
                return jsonify({'error': 'File not found'}), 404
            
            # Delete file from filesystem
            if os.path.exists(file_record['file_path']):
                os.remove(file_record['file_path'])
            
            # Delete from database
            cursor.execute("DELETE FROM uploaded_files WHERE id = %s", (file_id,))
            
            return jsonify({'message': 'File deleted successfully'}), 200
            
    except Exception as e:
        print(f"Error deleting file: {e}")
        return jsonify({'error': str(e)}), 500

@uploaded_files_bp.route('/download/<int:file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """Download a file"""
    try:
        current_user = get_current_user()
        if not current_user or current_user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM uploaded_files WHERE id = %s", (file_id,))
            file_record = cursor.fetchone()
            
            if not file_record:
                return jsonify({'error': 'File not found'}), 404
            
            if not os.path.exists(file_record['file_path']):
                return jsonify({'error': 'File not found on disk'}), 404
            
            return send_file(
                file_record['file_path'],
                as_attachment=True,
                download_name=file_record['file_name']
            )
            
    except Exception as e:
        print(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500
