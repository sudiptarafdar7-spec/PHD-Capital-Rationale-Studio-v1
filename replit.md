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
    - **Media Rationale Pipeline**: A 15-step processing pipeline for YouTube videos, covering extraction, transcription, translation, analysis, and report generation, integrating various external services.
- **System Design Choices**:
    - **Modular API**: Endpoints organized by feature.
    - **Pipeline-driven Processing**: Sequential 15-step video analysis.
    - **Database Schema**: Dedicated tables for `users`, `api_keys`, `pdf_template`, `uploaded_files`, `channels`, `jobs`, `job_steps`, `saved_rationale`, and `activity_logs`.
    - **File Storage**: Secure server-side storage with UUID-based filenames.

## External Dependencies
- **Database**: PostgreSQL (via Neon)
- **Authentication**: Flask-JWT-Extended
- **Password Hashing**: bcrypt
- **CORS Management**: Flask-CORS
- **Video Processing**: `yt-dlp`
- **Audio Processing**: ffmpeg-full
- **Transcription**: AssemblyAI API
- **Data Processing**: pandas, numpy
- **Translation**: Google Cloud Translation API (v2.0.1)
- **UI Icons**: Lucide React
- **AI Analysis**: OpenAI API (GPT-4o for speaker detection and analysis)
- **Financial Data**: Dhan API
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow (PIL)

## Recent Changes (October 22, 2025)
- **VPS DEPLOYMENT SCRIPTS CREATED**: Created automated deployment scripts for Hostinger VPS due to Replit deployment timeout issues with large Nix packages (24 packages including ffmpeg, Cairo, PIL dependencies). Scripts include: vps-deploy.sh (one-command setup), update.sh (easy updates), comprehensive README, and QUICKSTART guide. VPS deployment is recommended for production.
- **DEPLOYMENT FIX: Switched to VM Deployment**: Fixed deployment timeout issues by switching from Autoscale to Reserved VM deployment. VM is better suited for heavy background processing (video analysis, PDF generation) and handles uncached Nix layers properly. Created requirements.txt with all 65 Python dependencies.
- **DEPLOYMENT FIX: Production Configuration**: Fixed deployment timeout by configuring Flask to serve built React frontend, switched from Vite preview to Gunicorn production server. Flask now serves both API endpoints (/api/*) and static frontend files from build directory on port 5000.
- **POLISH: Step 13 Chart Improvements**: Fixed chart cropping on right side by reducing padding (6→3 steps) and adjusting margins (left=0.06, right=0.94), reduced left margin whitespace, added prominent "CMP: ₹{value}" label on dotted line in middle of chart with yellow background, added CMP box with date/time in bottom-right corner showing DATE and START TIME from CSV (when CMP was fetched in Step 11), improved chart spacing with bbox_inches='tight'.
- **POLISH: Dashboard Button Enhancements**: Added "Signed" and "Unsigned" text labels to download buttons with icons, made all buttons same size, added hover effects (shadow and scale), added spinning loader when downloading PDFs, changed signed status color to purple.
- **POLISH: Saved Rationale UI Enhancements**: Fixed video date display with proper error handling (YYYY-MM-DD format from video_upload_date column), added loading spinners to all download/upload buttons, enhanced button hover effects with shadow and scale animations, redesigned "Signed PDF uploaded on [date]" badge with green color and green border on all sides, simplified button text (removed "Download" prefix - now just "Unsigned PDF" and "Signed PDF"), changed signed button to green outline style.
- **NEW FEATURE: Saved Rationale Frontend**: Built complete Saved Rationale page with backend integration. Shows all saved rationales from database with filters (Tool, Channel, Status - signed/unsigned, Date Range). Displays Video Title, Channel Name, Tool Used, Video Date, Job ID, and "Signed PDF uploaded on date" for signed rationales. Action buttons: signed (View Progress, Download Unsigned PDF, Download Signed PDF), unsigned (View Progress, Download Unsigned PDF, Upload Signed). All downloads and uploads work with backend API.
- **CRITICAL FIX: Dashboard Recent Jobs Filters & Actions**: Added all status filters (failed, running, pdf_ready, completed, signed). Changed signed status icon from loading spinner to check icon. Added status-specific action buttons: signed (View Details + Download Signed PDF), completed (View Details + Download PDF + Sign Now), pdf_ready (View Details + Download PDF). All download buttons fetch PDF paths from saved_rationale table.
- **CRITICAL FIX: Completed Status Display**: Fixed jobs with status="completed" (saved but not signed) to show unsigned PDF in iframe with Download Unsigned PDF and Sign Now buttons. The Outputs (CSV download) and Logs tabs are visible below.
- **CRITICAL FIX: PDF Paths from saved_rationale Table**: Fixed backend to fetch `unsigned_pdf_path` and `signed_pdf_path` from `saved_rationale` table (using job_id column) instead of constructing paths. Both download buttons now correctly fetch PDF paths from database and download the proper files.
- **CRITICAL FIX: Signed Status PDF Preview**: Fixed jobs with status="signed" to properly display the signed PDF in iframe with two download buttons (Download Unsigned PDF and Download Signed PDF). The CSV download and Logs tabs are also visible below. Frontend now transitions to "saved" workflow stage when job status is "signed".
- **CRITICAL FIX: CSV Download Functionality**: Fixed CSV download feature in Outputs tab. CSV path is now constructed dynamically as `backend/job_files/{job_id}/analysis/stocks_with_analysis.csv`. Backend download endpoint now supports CSV files with proper MIME type detection (text/csv for .csv files, application/pdf for .pdf files). Fixed authentication headers to use direct Bearer token instead of helper function.
- **NEW FEATURE: Outputs & Logs Tabs in PDF Preview**: Added "Outputs" and "Logs" tabs below the PDF preview when Step 14 completes. The Outputs tab shows downloadable `stocks_with_analysis.csv` file from Step 13 (dynamically retrieved from `backend/job_files/{job_id}/analysis/stocks_with_analysis.csv`). Removed mockup `final_rationale_report.pdf` entry. Fixed React hooks issue by moving download logic into a proper handler function.
- **CRITICAL FIX: Iframe PDF Authentication**: Fixed black screen issue in PDF iframe by implementing blob-based PDF loading. PDFs are now fetched with authentication headers, converted to blob URLs, and displayed in iframe. This bypasses the limitation that iframes can't send custom headers.
- **CRITICAL FIX: PDF Path Tracking for Restart Detection**: Replaced `pdfNotificationShownRef` with `lastNotifiedPdfPathRef` to track which specific PDF has been shown. This solves the issue where clicking "Restart from Step 14" wouldn't show notification or transition to PDF preview because in-flight polling requests would detect the old PDF and mark it as already shown. Now, each newly generated PDF (with different filename/timestamp) triggers notification and transition correctly.
- **CRITICAL FIX: Frontend PDF Detection (snake_case vs camelCase)**: Fixed frontend to correctly read `output_files` (snake_case) from backend instead of `outputFiles` (camelCase). This was causing pdfPath to remain undefined, preventing automatic transition to PDF preview. Now supports both formats with fallback to `job.pdf_path`.
- **REMOVED CSV EDITING STEP**: Removed CSV editor interface from frontend. Pipeline now automatically continues from Step 13 (Generate Charts) to Step 14 (Generate PDF) without stopping for CSV review. Removed CSVEditor component, handleSaveCSV/handleContinueFromCSV functions, csvData state, and 'csv-editing' workflow stage.
- **CRITICAL FIX: Frontend Real-Time PDF Preview**: Fixed frontend polling to automatically detect when Step 14 completes by adding `startPolling(currentJobId)` in `handleContinueFromCSV()`. Previously, polling stopped after Step 13 and never restarted, causing PDF preview to only appear when manually reloading the page.
- **CRITICAL FIX: Backend Status Update for New Jobs**: Fixed `run_pipeline_background()` function in media_rationale.py to set job status to 'pdf_ready' after Step 14 completes. Previously, only the restart-step endpoint had this logic, causing new jobs to never update status after PDF generation.
- **CRITICAL FIX: PDF Download Path Resolution**: Fixed absolute path construction in download endpoint to prevent double "backend/" directory issue (was causing 404 errors when downloading PDFs).
- **CRITICAL FIX: Database Constraint Updated**: Updated jobs table CHECK constraint to include 'pdf_ready' status value (was missing from live database despite being in code)
- **CRITICAL FIX: restart-step Endpoint Updated**: Added logic to set job status to 'pdf_ready' after Step 14 completes when restarting from specific step
- **FINAL FIX: Step 15 Completely Removed from Pipeline**: Deleted all Step 15 pipeline files and removed Step 15 code block from pipeline_manager.py. Step 15 is NO LONGER part of automatic pipeline execution.
- **Pipeline Now Stops at Step 14**: Pipeline runs Steps 1-14 automatically, then sets job status to 'pdf_ready' (progress=93%) and stops. No Step 15 execution happens automatically.
- **Step 15 is Now API-Only**: All PDF actions (Save/Sign/Delete) are triggered exclusively by user button clicks via API endpoints:
  - `/api/v1/saved-rationale/save` (Save button)
  - `/api/v1/saved-rationale/upload-signed` (Save & Sign button)
  - `/api/v1/media-rationale/job/{job_id}` DELETE (Delete button)
- **Frontend Updates**: Changed "15-Step Pipeline" to "14-Step Pipeline" throughout UI, removed Step 15 from pipelineSteps array in mock-data.ts
- **Frontend PDF Preview**: After Step 14 completes, frontend detects `step14.status='success' && job.status='pdf_ready'` and automatically transitions to pdf-preview stage showing PDF iframe with action buttons
- **Fixed Step 14 PDF Path Storage**: Changed pipeline_manager.py to store full relative path in job_steps.output_files instead of just filename, enabling Step 15 to access generated PDFs
- **Implemented Step 14 (Generate PDF)**: Creates professional SEBI-compliant PDF reports using ReportLab with dynamic data from database (company logo, custom fonts, channel info, video details), includes branded header/footer, stock pages with charts and analysis, disclaimer/disclosure sections
- **Fixed Step 13 BSE Exchange Support**: Added dynamic exchange_segment (NSE_EQ/BSE_EQ) based on CSV data, fixing 400 errors for BSE-listed stocks
- **Implemented Step 13 (Generate Charts)**: Fetches candlestick charts from Dhan API with MA20/50/100/200, RSI(14), volume panels, and CMP annotations in premium design
- **Implemented Step 12 (Extract Analysis)**: Uses OpenAI GPT-4o to extract detailed stock analysis from Pradip's commentary in the transcript
- **Implemented Step 11 (Fetch CMP)**: Fetches Current Market Price from Dhan API for each stock at the time it was mentioned in the video, includes rate limiting protection
- **Implemented Step 10 (Convert Timestamps)**: Converts video-relative timestamps to actual clock times using upload_time from database, adds upload_date
- **Implemented Step 9 (Map Master File)**: Maps extracted stocks to master reference file using exact and fuzzy matching to get Securities ID, Exchange (NSE/BSE), and other metadata
- **Implemented Step 8 (Extract Stock Mentions)**: Uses OpenAI GPT-4o to extract stock names, actual NSE/BSE symbols, and timestamps from Pradip's analysis
- **Implemented Step 7 (Filter Transcription)**: Filters English transcript to keep only Anchor and Pradip dialogue, removing other speakers
- **Fixed Step 6**: Corrected database column name from `api_key` to `key_value` for OpenAI API key retrieval
- **Fixed Step 4 folder structure**: Updated file paths to use consistent subdirectory organization
- **Implemented Step 6 (Detect Speakers)**: OpenAI GPT-4o integration to identify Anchor vs Pradip Halder
- **Installed reportlab** and **Pillow** for PDF generation and image processing