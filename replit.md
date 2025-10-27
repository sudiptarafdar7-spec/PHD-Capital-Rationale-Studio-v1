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
- **Video Processing**: `yt-dlp`
- **Audio Processing**: `ffmpeg-python`
- **Transcription**: AssemblyAI API
- **Data Processing**: pandas, numpy
- **Translation**: Google Cloud Translation API
- **UI Icons**: Lucide React
- **AI Analysis**: OpenAI API (GPT-4o for speaker detection and analysis)
- **Financial Data**: Dhan API
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow (PIL)

## Recent Changes (October 27, 2025)
- **DATABASE CONNECTION FIX**: Fixed database connection to use `DATABASE_URL` directly with `sslmode='require'` for secure Neon connections. Updated `backend/utils/database.py` to handle new database credentials properly.
- **DATABASE RECREATION**: Created fresh PostgreSQL database after user deletion. Successfully seeded with all 9 tables and created admin user (admin@phdcapital.in / admin123) and employee user (rajesh@phdcapital.in / employee123).
- **LOGIN PAGE POLISH**: Reduced logo size from 192px to 80px, enabled dark mode theme, removed default credentials display, updated email placeholder to "Enter email address" for cleaner professional appearance.
- **BULLETPROOF DEPLOYMENT SOLUTION**: Deployment system ready with deploy.sh (fully automated VPS setup with Python 3.11, all system dependencies, automatic admin user creation), update.sh (one-command updates from git), DEPLOYMENT-GUIDE.md (comprehensive Windows PowerShell SSH guide). Ready for production deployment to Hostinger VPS (IP: 72.60.111.9, Domain: researchrationale.in, Path: /var/www/rationale-studio).
- **DEPLOYMENT FIX**: Fixed systemd error 203/EXEC by removing space from directory name. Changed from "Rationale Studio" to "rationale-studio" throughout codebase.