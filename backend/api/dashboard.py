from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.utils.database import get_db_cursor
from backend.api import dashboard_bp

@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """Get dashboard statistics and recent jobs"""
    try:
        user_id = get_jwt_identity()
        
        with get_db_cursor() as cursor:
            # Get stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as running_jobs,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_jobs
                FROM jobs
                WHERE user_id = %s
            """, (user_id,))
            
            stats_row = cursor.fetchone()
            
            stats = {
                'total_jobs': stats_row['total_jobs'] or 0,
                'completed_jobs': stats_row['completed_jobs'] or 0,
                'failed_jobs': stats_row['failed_jobs'] or 0,
                'running_jobs': stats_row['running_jobs'] or 0,
                'pending_jobs': stats_row['pending_jobs'] or 0,
                'total_change': '+ 0% from last month',  # TODO: Calculate real change
                'completed_change': '+ 0% from last month',
                'failed_change': '+ 0% from last month'
            }
            
            # Get recent jobs with filters
            search_query = request.args.get('search', '')
            tool_filter = request.args.get('tool', 'all')
            status_filter = request.args.get('status', 'all')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            limit = int(request.args.get('limit', 20))
            offset = int(request.args.get('offset', 0))
            
            # Build query
            where_conditions = ['j.user_id = %s']
            query_params = [user_id]
            
            # Search filter
            if search_query:
                where_conditions.append("""
                    (LOWER(j.video_title) LIKE %s OR 
                     LOWER(j.youtube_url) LIKE %s OR 
                     LOWER(j.id) LIKE %s)
                """)
                search_pattern = f'%{search_query.lower()}%'
                query_params.extend([search_pattern, search_pattern, search_pattern])
            
            # Status filter
            if status_filter != 'all':
                # Map 'running' to 'processing' for database compatibility
                db_status = 'processing' if status_filter == 'running' else status_filter
                where_conditions.append('j.status = %s')
                query_params.append(db_status)
            
            # Date range filter
            if date_from:
                where_conditions.append('j.created_at >= %s')
                query_params.append(date_from)
            
            if date_to:
                where_conditions.append('j.created_at <= %s')
                query_params.append(f'{date_to} 23:59:59')
            
            where_clause = ' AND '.join(where_conditions)
            
            # Get jobs
            cursor.execute(f"""
                SELECT 
                    j.id,
                    j.youtube_url,
                    j.status,
                    j.video_title as title,
                    c.channel_name,
                    j.created_at,
                    j.updated_at
                FROM jobs j
                LEFT JOIN channels c ON j.channel_id = c.id
                WHERE {where_clause}
                ORDER BY j.created_at DESC
                LIMIT %s OFFSET %s
            """, (*query_params, limit, offset))
            
            jobs = cursor.fetchall()
            
            # Calculate progress for each job
            jobs_with_progress = []
            for job in jobs:
                # Get job steps to calculate progress
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_steps,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as completed_steps
                    FROM job_steps
                    WHERE job_id = %s
                """, (job['id'],))
                
                steps_row = cursor.fetchone()
                total_steps = steps_row['total_steps'] or 15  # Default to 15 steps
                completed_steps = steps_row['completed_steps'] or 0
                
                # Calculate progress percentage
                progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
                
                # Map 'processing' status to 'running' for frontend compatibility
                display_status = 'running' if job['status'] == 'processing' else job['status']
                
                jobs_with_progress.append({
                    'id': job['id'],
                    'youtube_url': job['youtube_url'],
                    'status': display_status,
                    'title': job['title'],
                    'channel_name': job['channel_name'],
                    'created_at': job['created_at'].isoformat() if job['created_at'] else None,
                    'updated_at': job['updated_at'].isoformat() if job['updated_at'] else None,
                    'progress': progress
                })
            
            # Get total count for pagination
            cursor.execute(f"""
                SELECT COUNT(*) as total
                FROM jobs j
                LEFT JOIN channels c ON j.channel_id = c.id
                WHERE {where_clause}
            """, query_params)
            
            total_count = cursor.fetchone()['total']
            
            return jsonify({
                'stats': stats,
                'jobs': jobs_with_progress,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }), 200
            
    except Exception as e:
        print(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics only"""
    try:
        user_id = get_jwt_identity()
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as running_jobs,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_jobs
                FROM jobs
                WHERE user_id = %s
            """, (user_id,))
            
            stats_row = cursor.fetchone()
            
            stats = {
                'total_jobs': stats_row['total_jobs'] or 0,
                'completed_jobs': stats_row['completed_jobs'] or 0,
                'failed_jobs': stats_row['failed_jobs'] or 0,
                'running_jobs': stats_row['running_jobs'] or 0,
                'pending_jobs': stats_row['pending_jobs'] or 0,
                'total_change': '+ 0% from last month',
                'completed_change': '+ 0% from last month',
                'failed_change': '+ 0% from last month'
            }
            
            return jsonify(stats), 200
            
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'error': str(e)}), 500
