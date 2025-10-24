# PHD Capital Rationale Studio

## Overview
PHD Capital Rationale Studio is a full-stack web application designed to automate the generation of professional financial rationale reports from YouTube videos. Its primary purpose is to streamline the creation of detailed financial reports by leveraging multimedia content for insightful market analysis. The project aims to improve efficiency in financial reporting and supports the business vision of transforming video content into structured financial insights.

## User Preferences
- Keep frontend design unchanged (layout, forms, fields, animations, effects, flow)
- Use Flask for backend REST API
- Use PostgreSQL for database
- JWT tokens for authentication
- Role-based access control (admin/employee)

## System Architecture
The application features a clear separation between frontend and backend, built for robust financial analysis and reporting.

### Frontend
- **Framework**: React 18 with TypeScript, built using Vite.
- **UI/UX**: Radix UI for accessibility and Tailwind CSS for a modern, consistent design.
- **State Management**: React Context API.
- **Structure**: Reusable components and page-specific structures.

### Backend
- **Framework**: Flask (Python 3.11) providing a REST API.
- **Authentication**: Flask-JWT-Extended for JWTs and bcrypt for password hashing.
- **Database**: PostgreSQL (Neon).
- **CORS**: Flask-CORS configured.
- **Core Features**:
    - **User Management**: CRUD operations with Admin/Employee roles.
    - **API Keys Management**: Secure storage for external service keys.
    - **PDF Template Management**: Configuration for standardized PDF reports.
    - **File Uploads**: Management of master CSVs, logos, and custom fonts.
    - **Channel Management**: CRUD operations for YouTube channels, including logo uploads.
    - **Media Rationale Pipeline**: A 14-step processing pipeline for YouTube videos, covering extraction, transcription, translation, analysis, and report generation, integrating various external services.
- **System Design Choices**:
    - **Modular API**: Endpoints organized by feature.
    - **Pipeline-driven Processing**: Sequential 14-step video analysis.
    - **Database Schema**: Dedicated tables for `users`, `api_keys`, `pdf_template`, `uploaded_files`, `channels`, `jobs`, `job_steps`, `saved_rationale`, and `activity_logs`.
    - **File Storage**: Secure server-side storage with UUID-based filenames.
    - **Deployment**: Optimized for VPS environments with robust deployment scripts to handle heavy background processing and large dependencies.

## External Dependencies
- **Database**: PostgreSQL (via Neon)
- **Authentication**: Flask-JWT-Extended
- **Password Hashing**: bcrypt
- **CORS Management**: Flask-CORS
- **Video Processing**: `yt-dlp` (with 2025 bot-blocking bypass)
- **Caption Fetching**: `youtube-transcript-api` (reliable auto-caption extraction)
- **Audio Processing**: `ffmpeg-python`
- **Transcription**: AssemblyAI API
- **Data Processing**: pandas, numpy
- **Translation**: Google Cloud Translation API
- **UI Icons**: Lucide React
- **AI Analysis**: OpenAI API (GPT-4o for speaker detection and analysis)
- **Financial Data**: Dhan API
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow (PIL)

## Recent Changes (October 24, 2025)
- **YOUTUBE BOT BLOCKING FIX**: Implemented comprehensive solution to bypass YouTube's 2025 bot protection that was causing HTTP 403 errors. Updated Step 1 (Audio Download) with ios/android client fallback, improved user-agent spoofing, and robust error handling. Completely replaced Step 2 (Caption Download) with youtube-transcript-api library for reliable auto-generated caption fetching (works for Hindi, English, and other languages). Both steps now have intelligent fallback mechanisms and detailed error logging. This resolves all "ERROR: unable to download video data: HTTP Error 403: Forbidden" issues.
- **LOGIN PAGE POLISH**: Finalized login page design with compact 80px logo, enabled dark mode theme, removed default credentials display box, and updated email placeholder to "Enter email address" for a clean, professional appearance.

## Recent Changes (October 23, 2025)
- **BULLETPROOF DEPLOYMENT SOLUTION CREATED**: Completely rebuilt deployment system from scratch to handle all production issues. New deployment/ folder includes: deploy.sh (fully automated one-command VPS setup with Python 3.11, all system dependencies, automatic admin user creation), update.sh (one-command updates from git), DEPLOYMENT-GUIDE.md (comprehensive Windows PowerShell SSH guide), and README.md (quick command reference). Deployment script now: installs Python 3.11 from deadsnakes PPA, installs libpq-dev and postgresql-server-dev-all for psycopg2, exports environment variables for seed script to fix database connection, automatically runs seed script to create admin user, generates secure environment keys, sets up systemd service and Nginx reverse proxy. Tested frontend build successfully (14s, 2552 modules). Ready for production deployment to Hostinger VPS (IP: 72.60.111.9, Domain: researchrationale.in, Path: /var/www/rationale-studio).
- **DEPLOYMENT FIX**: Fixed systemd error 203/EXEC by removing space from directory name. Changed from "Rationale Studio" to "rationale-studio" throughout codebase.
- **CRITICAL BUG FIXES**: Fixed SavedRationalePage.tsx sonner import, removed leaked Google Cloud credentials, fixed potential null reference in database.py line 87, cleaned up temporary files, updated .gitignore.