import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from backend.config import Config

def get_db_connection():
    conn = psycopg2.connect(
        host=Config.PGHOST,
        port=Config.PGPORT,
        database=Config.PGDATABASE,
        user=Config.PGUSER,
        password=Config.PGPASSWORD
    )
    return conn

@contextmanager
def get_db_cursor(commit=False):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def init_database():
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(50) PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                mobile VARCHAR(20),
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'employee')),
                password_hash VARCHAR(255) NOT NULL,
                avatar_path TEXT,
                job_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        """)
        
        # API Keys table (multi-row: one row per provider)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                provider VARCHAR(50) UNIQUE NOT NULL,
                key_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_provider ON api_keys(provider);
        """)
        
        # PDF Template table (single row for company information)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_template (
                id SERIAL PRIMARY KEY,
                company_name TEXT,
                registration_details TEXT,
                disclaimer_text TEXT,
                disclosure_text TEXT,
                company_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert default row if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM pdf_template")
        result = cursor.fetchone()
        count = result['count'] if result else 0
        if count == 0:
            cursor.execute("""
                INSERT INTO pdf_template (company_name, registration_details, disclaimer_text, disclosure_text, company_data, updated_at)
                VALUES ('', '', '', '', '', CURRENT_TIMESTAMP)
            """)
        
        # Uploaded Files table (multi-row: masterFile, companyLogo, customFonts)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id SERIAL PRIMARY KEY,
                file_type VARCHAR(50) NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                file_path TEXT NOT NULL,
                file_size VARCHAR(20) NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_uploaded_files_type ON uploaded_files(file_type);
        """)
        
        # Channels table (multi-row: one row per YouTube channel)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id SERIAL PRIMARY KEY,
                channel_name VARCHAR(255) NOT NULL,
                channel_logo_path TEXT,
                channel_url TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(channel_name);
        """)
        
        # Jobs table (stores each Media/Premium/Manual Rationale job)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id VARCHAR(50) PRIMARY KEY,
                youtube_url TEXT,
                video_id VARCHAR(50),
                video_title TEXT,
                channel_id INTEGER REFERENCES channels(id),
                upload_date DATE,
                upload_time TIME,
                duration VARCHAR(20),
                user_id VARCHAR(50) REFERENCES users(id),
                tool_used VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'pdf_ready', 'completed', 'failed', 'signed')),
                progress INTEGER DEFAULT 0,
                current_step INTEGER DEFAULT 0,
                folder_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_tool_used ON jobs(tool_used);
        """)
        
        # Job Steps table (tracks each step in pipeline for each job)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_steps (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(50) REFERENCES jobs(id) ON DELETE CASCADE,
                step_number INTEGER NOT NULL,
                step_name VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed')),
                message TEXT,
                input_files TEXT[],
                output_files TEXT[],
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_steps_job_id ON job_steps(job_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_steps_status ON job_steps(status);
        """)
        
        # Saved Rationale table (final saved rationales)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_rationale (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(50) UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
                tool_used VARCHAR(50) NOT NULL,
                channel_id INTEGER REFERENCES channels(id),
                video_title TEXT,
                video_upload_date DATE,
                youtube_url TEXT,
                unsigned_pdf_path TEXT,
                signed_pdf_path TEXT,
                sign_status VARCHAR(20) DEFAULT 'Unsigned' CHECK (sign_status IN ('Unsigned', 'Signed')),
                signed_uploaded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_saved_rationale_tool_used ON saved_rationale(tool_used);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_saved_rationale_channel_id ON saved_rationale(channel_id);
        """)
        
        # Activity Logs table (audit trail for all system activities)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) REFERENCES users(id),
                job_id VARCHAR(50) REFERENCES jobs(id) ON DELETE SET NULL,
                action VARCHAR(50) NOT NULL CHECK (action IN ('job_started', 'job_completed', 'job_failed', 'login', 'logout', 'user_created', 'user_updated', 'user_deleted')),
                tool_used VARCHAR(50),
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
        """)
        
        print("✓ Database tables created successfully")
