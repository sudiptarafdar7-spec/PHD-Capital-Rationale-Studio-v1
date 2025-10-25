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
- **Video Metadata**: YouTube Data API v3 (for fetching video metadata)
- **Video Processing**: `yt-dlp` (for downloading audio and captions)
- **Audio Processing**: `ffmpeg-python`
- **Transcription**: AssemblyAI API
- **Data Processing**: pandas, numpy, isodate (for ISO 8601 duration parsing)
- **Translation**: Google Cloud Translation API
- **UI Icons**: Lucide React
- **AI Analysis**: OpenAI API (GPT-4o for speaker detection and analysis)
- **Financial Data**: Dhan API
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow (PIL)
- **HTTP Requests**: requests library

## Recent Changes

### October 25, 2025
- **BULLETPROOF AUDIO DOWNLOAD SYSTEM**: Completely rewrote `step01_download_audio.py` for maximum reliability across all servers including VPS:
  - Smart caching: Checks if audio already exists before downloading to save bandwidth and time
  - Retry logic: 3 automatic attempts with exponential backoff (2s, 4s, 8s)
  - Multiple user agents: Rotates through 5 different user agents (Windows, Mac, Linux, Firefox, Android) to reduce bot detection
  - Robust error handling: 30s socket timeout, 5min ffmpeg timeout, detailed error messages
  - Enhanced yt-dlp config: Multiple player clients (android, web, ios), fragment retries
  - VPS-optimized: Lightweight implementation, no Playwright or heavy dependencies
  - Production-ready: Maintains backward compatibility with existing pipeline

- **YOUTUBE DATA API v3 MIGRATION**: Migrated video metadata fetching from yt-dlp to YouTube Data API v3 for improved reliability and performance. Changes include:
  - Added YouTube Data API v3 field to API Keys page (frontend)
  - Updated `fetch_video_data.py` to use YouTube Data API v3 instead of yt-dlp for metadata extraction
  - Support for all YouTube URL formats: watch, live, shorts, embed, and short URLs
  - Installed `isodate` Python package for parsing ISO 8601 duration format
  - API key is securely stored in the database and retrieved during video metadata fetching
  - All metadata fields preserved (video_id, title, channel_name, upload_date, upload_time, duration, thumbnail, description)
  - Timezone conversion from UTC to IST maintained
  - Proper error handling for missing API keys, invalid URLs, and API failures
  - Note: yt-dlp is still used for downloading audio and captions with improved reliability

### October 23, 2025
- **BULLETPROOF DEPLOYMENT SOLUTION CREATED**: Completely rebuilt deployment system from scratch to handle all production issues. New deployment/ folder includes: deploy.sh (fully automated one-command VPS setup with Python 3.11, all system dependencies, automatic admin user creation), update.sh (one-command updates from git), DEPLOYMENT-GUIDE.md (comprehensive Windows PowerShell SSH guide), and README.md (quick command reference). Deployment script now: installs Python 3.11 from deadsnakes PPA, installs libpq-dev and postgresql-server-dev-all for psycopg2, exports environment variables for seed script to fix database connection, automatically runs seed script to create admin user, generates secure environment keys, sets up systemd service and Nginx reverse proxy. Tested frontend build successfully (14s, 2552 modules). Ready for production deployment to Hostinger VPS (IP: 72.60.111.9, Domain: researchrationale.in, Path: /var/www/rationale-studio).
- **DEPLOYMENT FIX**: Fixed systemd error 203/EXEC by removing space from directory name. Changed from "Rationale Studio" to "rationale-studio" throughout codebase.
- **CRITICAL BUG FIXES**: Fixed SavedRationalePage.tsx sonner import, removed leaked Google Cloud credentials, fixed potential null reference in database.py line 87, cleaned up temporary files, updated .gitignore.