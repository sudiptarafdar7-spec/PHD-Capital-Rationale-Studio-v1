import React, { useState, useEffect, useRef } from 'react';
import { Play, RotateCcw, Download, FileText, PlayCircle, Clock, Calendar, Youtube, Trash2, FileSignature, Save } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import StepProgressTracker from '../components/StepProgressTracker';
import SignedFileUpload from '../components/SignedFileUpload';
import { pipelineSteps } from '../lib/mock-data';
import { extractVideoId } from '../lib/youtube-utils';
import { playCompletionBell, playSuccessBell } from '../lib/sound-utils';
import { toast } from 'sonner';
import { API_ENDPOINTS, getAuthHeaders } from '../lib/api-config';
import { useAuth } from '../lib/auth-context';

interface MediaRationalePageProps {
  onNavigate: (page: string, jobId?: string) => void;
  selectedJobId?: string;
}

interface VideoMetadata {
  title: string;
  uploadDate: string;
  uploadTime: string;
  duration: string;
  videoId: string;
  channelName: string;
  channelLogo: string;
}

type WorkflowStage = 'input' | 'processing' | 'pdf-generation' | 'pdf-preview' | 'saved' | 'upload-signed' | 'completed';
type SaveType = 'save' | 'save-and-sign' | null;

export default function MediaRationalePage({ onNavigate, selectedJobId }: MediaRationalePageProps) {
  const { token } = useAuth();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastNotifiedPdfPathRef = useRef<string | null>(null);
  
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [isFetchingMetadata, setIsFetchingMetadata] = useState(false);
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(selectedJobId || null);
  const [jobSteps, setJobSteps] = useState<any[]>([]);
  const [progress, setProgress] = useState(0);
  const [workflowStage, setWorkflowStage] = useState<WorkflowStage>('input');
  const [currentStepNumber, setCurrentStepNumber] = useState(0);
  const [saveType, setSaveType] = useState<SaveType>(null);
  const [uploadedSignedFile, setUploadedSignedFile] = useState<{
    fileName: string;
    uploadedAt: string;
  } | null>(null);
  const [pdfPath, setPdfPath] = useState<string | null>(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);

  // Mock channel data
  const mockChannels = [
    {
      id: 'ch-1',
      name: 'PHD Capital Main',
      logoPath: 'https://api.dicebear.com/7.x/shapes/svg?seed=PHD',
    },
    {
      id: 'ch-2',
      name: 'Market Analysis Daily',
      logoPath: 'https://api.dicebear.com/7.x/shapes/svg?seed=Market',
    },
  ];

  const getChannelLogo = (channelName: string): string => {
    const channel = mockChannels.find(ch => ch.name.toLowerCase() === channelName.toLowerCase());
    return channel?.logoPath || 'https://api.dicebear.com/7.x/shapes/svg?seed=default';
  };

  // Poll job status
  const fetchJobStatus = async (jobId: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.mediaRationale.getJob(jobId), {
        headers: getAuthHeaders(token),
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }
      
      const data = await response.json();
      if (data.success && data.job) {
        setProgress(data.job.progress);
        setCurrentStepNumber(data.job.currentStep);
        setJobSteps(data.job.steps);
        
        // Update video metadata if not already set
        if (!videoMetadata && data.job.videoTitle) {
          setVideoMetadata({
            title: data.job.videoTitle,
            uploadDate: data.job.videoUploadDate,
            uploadTime: '00:00:00',
            duration: data.job.duration,
            videoId: data.job.videoId,
            channelName: data.job.channelName || '',
            channelLogo: data.job.channelLogo || '',
          });
          setYoutubeUrl(data.job.youtubeUrl || '');
        }
        
        // Skip CSV editing step - continue polling until Step 14 completes
        // Step 13 completes automatically and pipeline continues to Step 14
        
        // Check if Step 14 completed (PDF generated and ready)
        const step14 = data.job.steps.find((s: any) => s.step_number === 14);
        console.log('[DEBUG] Step 14 status:', step14?.status, 'Job status:', data.job.status);
        console.log('[DEBUG] Step 14 data:', step14);
        
        // Handle pdf_ready, signed, and completed statuses
        if (step14?.status === 'success' && (data.job.status === 'pdf_ready' || data.job.status === 'signed' || data.job.status === 'completed')) {
          // Get PDF path based on job status
          let pdfFile = null;
          
          // For signed/completed jobs, use paths from saved_rationale table EXCLUSIVELY
          if (data.job.status === 'signed' || data.job.status === 'completed') {
            // Use signed PDF path if available, otherwise use unsigned PDF path from saved_rationale
            pdfFile = data.job.signedPdfPath || data.job.unsignedPdfPath || null;
            console.log('[DEBUG] Using saved_rationale paths - Signed:', data.job.signedPdfPath, 'Unsigned:', data.job.unsignedPdfPath);
            console.log('[DEBUG] Selected PDF path:', pdfFile);
          } else {
            // For pdf_ready status, use Step 14 output files
            const outputFiles = step14.output_files || step14.outputFiles || [];
            const jobPdfPath = data.job.pdf_path;
            
            if (outputFiles.length > 0) {
              pdfFile = outputFiles.find((f: string) => f.endsWith('.pdf'));
            } else if (jobPdfPath) {
              pdfFile = jobPdfPath;
            }
            console.log('[DEBUG] Using Step 14 output PDF path:', pdfFile);
          }
          
          console.log('[DEBUG] Job status:', data.job.status);
          console.log('[DEBUG] Final PDF path:', pdfFile);
          console.log('[DEBUG] lastNotifiedPdfPath:', lastNotifiedPdfPathRef.current);
          
          if (pdfFile) {
            setPdfPath(pdfFile);
            
            // Transition to appropriate stage based on job status
            const targetStage = data.job.status === 'signed' ? 'saved' : 
                               data.job.status === 'completed' ? 'completed' : 
                               'pdf-preview';
            
            // Only show notification if this is a NEW PDF (path changed) or transitioning to a new stage
            if (pdfFile !== lastNotifiedPdfPathRef.current || workflowStage !== targetStage) {
              console.log(`[DEBUG] Transitioning to ${targetStage} - PDF detected!`);
              lastNotifiedPdfPathRef.current = pdfFile;
              stopPolling();
              setWorkflowStage(targetStage);
              
              if (data.job.status === 'pdf_ready') {
                playCompletionBell();
                toast.success('PDF Generated Successfully!', {
                  description: 'Your rationale report is ready for preview',
                });
              }
            } else {
              console.log('[DEBUG] Skipping transition - same PDF and stage');
            }
          } else {
            console.log('[DEBUG] No PDF file found - saved_rationale paths may be missing');
          }
        }
        
        // Check if job failed
        if (data.job.status === 'failed') {
          stopPolling();
        }
      }
    } catch (error) {
      console.error('Error fetching job status:', error);
    }
  };
  
  const startPolling = (jobId: string) => {
    stopPolling();
    pollingIntervalRef.current = setInterval(() => {
      fetchJobStatus(jobId);
    }, 2000);
  };
  
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };
  
  // Cleanup polling on unmount
  useEffect(() => {
    return () => stopPolling();
  }, []);
  
  // Load existing job if selectedJobId is provided
  useEffect(() => {
    if (selectedJobId) {
      setCurrentJobId(selectedJobId);
      setWorkflowStage('processing'); // Will be updated by fetchJobStatus
      fetchJobStatus(selectedJobId);
      
      toast.info('Loading job...', {
        description: `Job ID: ${selectedJobId}`,
      });
    }
  }, [selectedJobId]);

  // Fetch PDF as blob and create object URL for iframe (to support authenticated requests)
  useEffect(() => {
    if (!pdfPath || !token) {
      setPdfBlobUrl(null);
      return;
    }

    let blobUrl: string | null = null;

    const fetchPdfBlob = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.mediaRationale.downloadPdf(pdfPath), {
          headers: getAuthHeaders(token),
        });

        if (!response.ok) {
          console.error('Failed to fetch PDF:', response.status);
          return;
        }

        const blob = await response.blob();
        blobUrl = URL.createObjectURL(blob);
        setPdfBlobUrl(blobUrl);
      } catch (error) {
        console.error('Error fetching PDF:', error);
      }
    };

    fetchPdfBlob();

    // Cleanup: revoke blob URL when component unmounts or pdfPath changes
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [pdfPath, token]);

  const handleFetchVideo = async () => {
    if (!youtubeUrl.trim()) {
      toast.error('Please enter a YouTube URL');
      return;
    }

    if (!youtubeUrl.includes('youtube.com') && !youtubeUrl.includes('youtu.be')) {
      toast.error('Please enter a valid YouTube URL');
      return;
    }

    setIsFetchingMetadata(true);

    toast.info('Fetching video metadata...', {
      description: 'Retrieving YouTube video information',
    });

    try {
      const response = await fetch(API_ENDPOINTS.mediaRationale.fetchVideo, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ youtubeUrl }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to fetch video metadata');
      }

      const metadata: VideoMetadata = {
        title: data.data.title,
        uploadDate: data.data.uploadDate,
        uploadTime: data.data.uploadTime,
        duration: data.data.duration,
        videoId: data.data.videoId,
        channelName: data.data.channelName,
        channelLogo: data.data.channelLogo || '',
      };

      setVideoMetadata(metadata);
      setIsFetchingMetadata(false);

      toast.success('Video metadata fetched successfully!', {
        description: 'Ready to start analysis',
      });
    } catch (error: any) {
      console.error('Error fetching video:', error);
      toast.error('Failed to fetch video metadata', {
        description: error.message || 'Please try again',
      });
      setIsFetchingMetadata(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!videoMetadata) {
      toast.error('Please fetch video metadata first');
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.mediaRationale.startAnalysis, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          youtubeUrl,
          toolUsed: 'Media Rationale',
          videoTitle: videoMetadata.title,
          videoId: videoMetadata.videoId,
          channelName: videoMetadata.channelName,
          uploadDate: videoMetadata.uploadDate,
          uploadTime: videoMetadata.uploadTime,
          duration: videoMetadata.duration,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to start analysis');
      }

      const jobId = data.jobId;
      setCurrentJobId(jobId);
      setProgress(0);
      setWorkflowStage('processing');
      
      // Reset last notified PDF path for new job
      lastNotifiedPdfPathRef.current = null;

      toast.success('Analysis started!', {
        description: `Job ID: ${jobId}`,
      });

      // Start polling for job status
      startPolling(jobId);
    } catch (error: any) {
      console.error('Error starting analysis:', error);
      toast.error('Failed to start analysis', {
        description: error.message || 'Please try again',
      });
    }
  };

  const handleRestartFromStep = async (stepNumber: number) => {
    if (!currentJobId) return;

    try {
      const response = await fetch(API_ENDPOINTS.mediaRationale.restartStep(currentJobId, stepNumber), {
        method: 'POST',
        headers: getAuthHeaders(token),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to restart step');
      }

      toast.info(`Restarting from Step ${stepNumber}`, {
        description: 'All subsequent steps will be re-executed',
      });

      // Reset last notified PDF path for new execution
      lastNotifiedPdfPathRef.current = null;
      setWorkflowStage('processing');

      // Start polling for job status
      startPolling(currentJobId);
    } catch (error: any) {
      console.error('Error restarting step:', error);
      toast.error('Failed to restart step', {
        description: error.message || 'Please try again',
      });
    }
  };

  const handleDeleteJob = async () => {
    if (!currentJobId) return;

    try {
      const response = await fetch(API_ENDPOINTS.mediaRationale.deleteJob(currentJobId), {
        method: 'DELETE',
        headers: getAuthHeaders(token),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to delete job');
      }

      toast.success('Job deleted successfully', {
        description: 'Starting a new analysis',
      });
      handleRestart();
    } catch (error: any) {
      console.error('Error deleting job:', error);
      toast.error('Failed to delete job', {
        description: error.message || 'Please try again',
      });
    }
  };

  const handleRestart = () => {
    stopPolling();
    lastNotifiedPdfPathRef.current = null;
    setYoutubeUrl('');
    setIsFetchingMetadata(false);
    setVideoMetadata(null);
    setCurrentJobId(null);
    setJobSteps([]);
    setProgress(0);
    setWorkflowStage('input');
    setCurrentStepNumber(0);
  };

  const handleDownloadPDF = async (signed: boolean = false) => {
    if (!pdfPath) {
      toast.error('PDF not available', {
        description: 'Please wait for PDF generation to complete',
      });
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.mediaRationale.downloadPdf(pdfPath), {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to download PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // Extract filename from path
      const filename = pdfPath.split('/').pop() || 'rationale_report.pdf';
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('Downloading PDF', {
        description: filename,
      });
    } catch (error: any) {
      console.error('Error downloading PDF:', error);
      toast.error('Failed to download PDF', {
        description: error.message || 'Please try again',
      });
    }
  };

  const handleSave = async () => {
    if (!currentJobId) return;

    setSaveType('save');

    try {
      toast.info('Saving rationale...', {
        description: 'Saving PDF and job data',
      });

      const response = await fetch(API_ENDPOINTS.mediaRationale.save(currentJobId), {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ jobId: currentJobId }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to save rationale');
      }

      setProgress(100);

      toast.success('Rationale saved successfully!', {
        description: 'Job saved and logged. View in Saved Rationale.',
      });

      setWorkflowStage('saved');
    } catch (error: any) {
      console.error('Error saving rationale:', error);
      toast.error('Failed to save rationale', {
        description: error.message || 'Please try again',
      });
    }
  };

  const handleSaveAndSign = async () => {
    if (!currentJobId) return;

    setSaveType('save-and-sign');

    try {
      toast.info('Saving unsigned PDF and job data', {
        description: 'Preparing for signed file upload',
      });

      const response = await fetch(API_ENDPOINTS.mediaRationale.save(currentJobId), {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ jobId: currentJobId }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to save rationale');
      }

      toast.success('Unsigned PDF saved successfully', {
        description: 'Job and rationale log created. Please upload signed PDF.',
      });

      setWorkflowStage('upload-signed');
    } catch (error: any) {
      console.error('Error saving rationale:', error);
      toast.error('Failed to save rationale', {
        description: error.message || 'Please try again',
      });
    }
  };

  const handleSignedFileUpload = async (file: File) => {
    if (!currentJobId) return;

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('jobId', currentJobId);

      // Don't set Content-Type header - let browser set it automatically for FormData
      const response = await fetch(API_ENDPOINTS.mediaRationale.uploadSigned(currentJobId), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to upload signed PDF');
      }

      // Store the uploaded file info
      setUploadedSignedFile({
        fileName: file.name,
        uploadedAt: new Date().toISOString(),
      });

      setProgress(100);
      setWorkflowStage('completed');

      // Play success bell for signed file upload
      playSuccessBell();

      toast.success('Workflow completed! 🎉', {
        description: 'All steps finished successfully with signed PDF',
      });
    } catch (error: any) {
      console.error('Error uploading signed PDF:', error);
      toast.error('Failed to upload signed PDF', {
        description: error.message || 'Please try again',
      });
    }
  };

  const renderRightPanel = () => {
    if (workflowStage === 'pdf-generation') {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg text-foreground">Generating PDF Report</h3>
          </div>
          <div className="bg-background border border-border rounded-lg p-12 text-center">
            <Loader2 className="w-16 h-16 mx-auto mb-4 text-blue-500 animate-spin" />
            <p className="text-foreground">Generating PDF from CSV data...</p>
            <p className="text-sm text-muted-foreground mt-2">Step 14 in progress</p>
          </div>
        </div>
      );
    }

    if (workflowStage === 'pdf-preview') {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg text-foreground">Generated PDF Report</h3>
          </div>

          {/* PDF Viewer */}
          <div className="bg-background border border-border rounded-lg overflow-hidden">
            {pdfBlobUrl ? (
              <iframe
                src={pdfBlobUrl}
                className="w-full h-[500px]"
                title="PDF Report Preview"
              />
            ) : (
              <div className="w-full h-[500px] flex items-center justify-center bg-muted">
                <p className="text-muted-foreground">Loading PDF...</p>
              </div>
            )}
          </div>

          {/* Action Buttons - 4 buttons */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={handleDownloadPDF}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
            <Button
              onClick={handleSave}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              <Save className="w-4 h-4 mr-2" />
              Save
            </Button>
            <Button
              onClick={handleSaveAndSign}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              <FileSignature className="w-4 h-4 mr-2" />
              Save & Sign
            </Button>
            <Button
              onClick={handleDeleteJob}
              variant="outline"
              className="border-red-500/50 text-red-500 hover:bg-red-600 hover:text-white hover:border-red-600"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      );
    }

    if (workflowStage === 'saved') {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg text-foreground">Signed PDF Preview</h3>
          </div>

          {/* PDF Viewer - Shows Signed PDF */}
          <div className="bg-background border border-border rounded-lg overflow-hidden">
            {pdfBlobUrl ? (
              <iframe
                src={pdfBlobUrl}
                className="w-full h-[500px]"
                title="Signed PDF Report Preview"
              />
            ) : (
              <div className="w-full h-[500px] flex items-center justify-center bg-muted">
                <p className="text-muted-foreground">Loading Signed PDF...</p>
              </div>
            )}
          </div>

          {/* Download Unsigned and Signed PDF Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={async () => {
                // Download unsigned PDF from saved_rationale table
                try {
                  const jobResponse = await fetch(API_ENDPOINTS.mediaRationale.getJob(currentJobId), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  });
                  
                  if (!jobResponse.ok) {
                    toast.error('Failed to fetch job data');
                    return;
                  }
                  
                  const jobData = await jobResponse.json();
                  const unsignedPdfPath = jobData.job?.unsignedPdfPath;
                  
                  if (!unsignedPdfPath) {
                    toast.error('Unsigned PDF not found');
                    return;
                  }
                  
                  const response = await fetch(API_ENDPOINTS.mediaRationale.downloadPdf(unsignedPdfPath), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  });
                  
                  if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'unsigned_rationale_report.pdf';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    toast.success('Unsigned PDF downloaded successfully!');
                  } else {
                    toast.error('Failed to download unsigned PDF');
                  }
                } catch (error) {
                  console.error('Error downloading unsigned PDF:', error);
                  toast.error('Failed to download unsigned PDF');
                }
              }}
              variant="outline"
              className="border-blue-500/50 text-blue-500 hover:bg-blue-600 hover:text-white hover:border-blue-600"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Unsigned PDF
            </Button>
            <Button
              onClick={async () => {
                // Download signed PDF from saved_rationale table
                try {
                  const jobResponse = await fetch(API_ENDPOINTS.mediaRationale.getJob(currentJobId), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  });
                  
                  if (!jobResponse.ok) {
                    toast.error('Failed to fetch job data');
                    return;
                  }
                  
                  const jobData = await jobResponse.json();
                  const signedPdfPath = jobData.job?.signedPdfPath;
                  
                  if (!signedPdfPath) {
                    toast.error('Signed PDF not found');
                    return;
                  }
                  
                  const response = await fetch(API_ENDPOINTS.mediaRationale.downloadPdf(signedPdfPath), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  });
                  
                  if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'signed_rationale_report.pdf';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    toast.success('Signed PDF downloaded successfully!');
                  } else {
                    toast.error('Failed to download signed PDF');
                  }
                } catch (error) {
                  console.error('Error downloading signed PDF:', error);
                  toast.error('Failed to download signed PDF');
                }
              }}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Signed PDF
            </Button>
          </div>
        </div>
      );
    }

    if (workflowStage === 'completed') {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg text-foreground">Unsigned PDF Preview</h3>
          </div>

          {/* PDF Viewer - Shows Unsigned PDF */}
          <div className="bg-background border border-border rounded-lg overflow-hidden">
            {pdfBlobUrl ? (
              <iframe
                src={pdfBlobUrl}
                className="w-full h-[500px]"
                title="Unsigned PDF Report Preview"
              />
            ) : (
              <div className="w-full h-[500px] flex items-center justify-center bg-muted">
                <p className="text-muted-foreground">Loading Unsigned PDF...</p>
              </div>
            )}
          </div>

          {/* Download Unsigned PDF and Sign Now Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={async () => {
                // Download unsigned PDF from saved_rationale table
                try {
                  const jobResponse = await fetch(API_ENDPOINTS.mediaRationale.getJob(currentJobId), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  });
                  
                  if (!jobResponse.ok) {
                    toast.error('Failed to fetch job data');
                    return;
                  }
                  
                  const jobData = await jobResponse.json();
                  const unsignedPdfPath = jobData.job?.unsignedPdfPath;
                  
                  if (!unsignedPdfPath) {
                    toast.error('Unsigned PDF not found');
                    return;
                  }
                  
                  const response = await fetch(API_ENDPOINTS.mediaRationale.downloadPdf(unsignedPdfPath), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  });
                  
                  if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'unsigned_rationale_report.pdf';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    toast.success('Unsigned PDF downloaded successfully!');
                  } else {
                    toast.error('Failed to download unsigned PDF');
                  }
                } catch (error) {
                  console.error('Error downloading unsigned PDF:', error);
                  toast.error('Failed to download unsigned PDF');
                }
              }}
              variant="outline"
              className="border-blue-500/50 text-blue-500 hover:bg-blue-600 hover:text-white hover:border-blue-600"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Unsigned PDF
            </Button>
            <Button
              onClick={() => {
                setSaveType('save-and-sign');
                setWorkflowStage('upload-signed');
                toast.info('Upload signed PDF', {
                  description: 'Please upload the signed version of your PDF',
                });
              }}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              <FileSignature className="w-4 h-4 mr-2" />
              Sign Now
            </Button>
          </div>
        </div>
      );
    }

    if (workflowStage === 'upload-signed') {
      return (
        <SignedFileUpload
          jobId={currentJobId || ''}
          uploadedFile={uploadedSignedFile}
          onUploadComplete={handleSignedFileUpload}
        />
      );
    }

    // Default state - show placeholder or outputs
    if (currentJobId && jobSteps.length > 0) {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg text-foreground">Generated Report</h3>
          </div>

          <div className="bg-background border border-border rounded-lg p-12 text-center">
            <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">Processing...</p>
            <p className="text-sm text-muted-foreground mt-2">Step {currentStepNumber} of 14</p>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl text-foreground mb-1">Media Rationale</h1>
        <p className="text-muted-foreground">
          Transform YouTube market analysis videos into comprehensive SEBI compliant PDF reports with AI-powered Tool.
        </p>
      </div>

      {/* Input Section */}
      <Card className="bg-card border-border p-6 shadow-sm">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: URL Input */}
          <div className="flex flex-col">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 bg-blue-500/20 rounded-lg">
                <PlayCircle className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <h2 className="text-foreground">Provide Youtube URL</h2>
                <p className="text-xs text-muted-foreground">Enter a YouTube URL to fetch video data</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="youtube-url" className="text-foreground text-sm mb-1.5 block">
                  YouTube Video URL
                </Label>
                <Input
                  id="youtube-url"
                  type="url"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  disabled={workflowStage !== 'input' || isFetchingMetadata}
                  className="bg-background border-input text-foreground placeholder:text-muted-foreground"
                />
              </div>

              <Button
                onClick={handleFetchVideo}
                disabled={isFetchingMetadata || workflowStage !== 'input' || !youtubeUrl.trim() || !!videoMetadata}
                className="gradient-primary w-full h-11"
                size="default"
              >
                {isFetchingMetadata ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <Youtube className="w-4 h-4 mr-2" />
                    Fetch Video
                  </>
                )}
              </Button>

              {currentJobId && workflowStage !== 'input' && (
                <Button
                  variant="outline"
                  onClick={handleRestart}
                  className="border-blue-500/50 text-blue-500 hover:bg-blue-600 hover:text-white hover:border-blue-600 w-full h-10"
                  size="default"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  New Analysis
                </Button>
              )}
            </div>
          </div>

          {/* Right Column: Video Metadata */}
          <div className="flex flex-col">
            {videoMetadata ? (
              <>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2.5 bg-green-500/20 rounded-lg">
                    <Youtube className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <h2 className="text-foreground">Video Information</h2>
                  </div>
                </div>

                <div className="bg-background border border-border rounded-lg overflow-hidden">
                  {/* YouTube Video Embed */}
                  <iframe
                    src={`https://www.youtube.com/embed/${videoMetadata.videoId}`}
                    title={videoMetadata.title}
                    className="w-full h-48"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                  
                  <div className="p-3 space-y-2.5">
                    <h3 className="text-foreground text-sm line-clamp-2 leading-snug">
                      {videoMetadata.title}
                    </h3>
                    
                    {/* Channel Name and Logo */}
                    <div className="flex items-center gap-2 pb-2.5 border-b border-border">
                      <img 
                        src={videoMetadata.channelLogo} 
                        alt={videoMetadata.channelName}
                        className="w-6 h-6 rounded-full"
                      />
                      <div>
                        <p className="text-xs text-muted-foreground">Channel</p>
                        <p className="text-xs text-foreground">{videoMetadata.channelName}</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="flex items-start gap-2">
                        <Calendar className="w-3.5 h-3.5 text-muted-foreground mt-0.5" />
                        <div>
                          <p className="text-xs text-muted-foreground">Upload Date</p>
                          <p className="text-xs text-foreground">{videoMetadata.uploadDate}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-2">
                        <Clock className="w-3.5 h-3.5 text-muted-foreground mt-0.5" />
                        <div>
                          <p className="text-xs text-muted-foreground">Upload Time</p>
                          <p className="text-xs text-foreground">{videoMetadata.uploadTime}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-2 col-span-2">
                        <PlayCircle className="w-3.5 h-3.5 text-muted-foreground mt-0.5" />
                        <div>
                          <p className="text-xs text-muted-foreground">Duration</p>
                          <p className="text-xs text-foreground">{videoMetadata.duration}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center bg-background border border-dashed border-border rounded-lg h-full">
                <div className="text-center py-12">
                  <Youtube className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-30" />
                  <p className="text-sm text-muted-foreground">Video information will appear here</p>
                  <p className="text-xs text-muted-foreground mt-1">After fetching metadata</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Start Analysis Button */}
        {videoMetadata && !currentJobId && workflowStage === 'input' && (
          <div className="mt-6 pt-6 border-t border-border">
            <Button
              onClick={handleStartAnalysis}
              className="bg-green-600 hover:bg-green-700 text-white w-full h-11"
              size="default"
            >
              <Play className="w-4 h-4 mr-2" />
              Start Analysis
            </Button>
          </div>
        )}
      </Card>

      {/* Results Section */}
      {currentJobId && jobSteps.length > 0 && (
        <Card className="bg-card border-border shadow-sm">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
            {/* Left Column: 14-Step Pipeline */}
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg text-foreground">14-Step Pipeline</h3>
                  <p className="text-sm text-muted-foreground">Job ID: {currentJobId}</p>
                </div>
              </div>

              <StepProgressTracker 
                steps={jobSteps} 
                onRestartFromStep={handleRestartFromStep}
              />
            </div>

            {/* Right Column: Dynamic Content Based on Workflow Stage */}
            <div className="space-y-4">
              {renderRightPanel()}

              {/* Tabs for Additional Data - Show after PDF is ready */}
              {(workflowStage === 'pdf-preview' || workflowStage === 'saved' || workflowStage === 'completed') && (
                <Tabs defaultValue="outputs" className="w-full mt-6">
                  <div className="border-b border-border">
                    <TabsList className="bg-muted border border-border">
                      <TabsTrigger value="outputs" className="data-[state=active]:bg-blue-600/80 data-[state=active]:text-white text-foreground">
                        Outputs
                      </TabsTrigger>
                      <TabsTrigger value="logs" className="data-[state=active]:bg-blue-600/80 data-[state=active]:text-white text-foreground">
                        Logs
                      </TabsTrigger>
                    </TabsList>
                  </div>

                  <TabsContent value="outputs" className="pt-4">
                    <div className="space-y-4">
                      <h3 className="text-foreground mb-3">Generated Files</h3>
                      
                      <div className="space-y-3">
                        {/* CSV File from Step 13 - Fixed path format */}
                        {(() => {
                          const step13 = jobSteps.find((s: any) => s.step_number === 13);
                          if (!step13 || step13.status !== 'success') return null;
                          
                          const handleDownloadCSV = async () => {
                            try {
                              if (!token) {
                                toast.error('Authentication required');
                                return;
                              }
                              
                              // Construct fixed CSV path
                              const csvPath = `backend/job_files/${currentJobId}/analysis/stocks_with_analysis.csv`;
                              const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
                              const downloadUrl = `${apiBaseUrl}/api/v1/saved-rationale/download/${encodeURIComponent(csvPath)}`;
                              
                              console.log('[CSV Download] Downloading CSV from:', downloadUrl);
                              
                              const response = await fetch(downloadUrl, {
                                method: 'GET',
                                headers: {
                                  'Authorization': `Bearer ${token}`,
                                },
                              });
                              
                              console.log('[CSV Download] Response status:', response.status);
                              
                              if (!response.ok) {
                                const errorText = await response.text();
                                console.error('[CSV Download] Error:', errorText);
                                toast.error(`Failed to download CSV: ${response.status}`);
                                return;
                              }
                              
                              const blob = await response.blob();
                              const url = window.URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = 'stocks_with_analysis.csv';
                              document.body.appendChild(a);
                              a.click();
                              window.URL.revokeObjectURL(url);
                              document.body.removeChild(a);
                              toast.success('CSV downloaded successfully!');
                            } catch (error: any) {
                              console.error('[CSV Download] Exception:', error);
                              console.error('[CSV Download] Error message:', error?.message || 'Unknown error');
                              toast.error(`Failed to download CSV: ${error?.message || 'Unknown error'}`);
                            }
                          };
                          
                          return (
                            <Card className="bg-card border-border p-4 shadow-sm">
                              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                                <div className="flex items-center gap-3 min-w-0 flex-1">
                                  <div className="p-2 bg-green-500/20 rounded-lg shrink-0">
                                    <FileText className="w-5 h-5 text-green-500" />
                                  </div>
                                  <div className="min-w-0">
                                    <p className="text-foreground truncate">stocks_with_analysis.csv</p>
                                    <p className="text-xs text-muted-foreground">Stock Data CSV with Analysis</p>
                                  </div>
                                </div>
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  className="border-blue-500/50 text-blue-500 hover:bg-blue-600 hover:text-white hover:border-blue-600 w-full sm:w-auto shrink-0"
                                  onClick={handleDownloadCSV}
                                >
                                  <Download className="w-4 h-4 mr-2" />
                                  Download
                                </Button>
                              </div>
                            </Card>
                          );
                        })()}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="logs" className="pt-4">
                    <div className="space-y-4">
                      <h3 className="text-foreground mb-3">Execution Logs</h3>
                      
                      <Card className="bg-card border-border p-4 font-mono text-xs shadow-sm">
                        <div className="space-y-1 text-muted-foreground max-h-[300px] overflow-y-auto">
                          {jobSteps
                            .filter(s => s.status !== 'pending')
                            .map(step => (
                              <div key={step.id}>
                                <span className="text-muted-foreground">[{new Date().toLocaleTimeString()}]</span>{' '}
                                <span className={
                                  step.status === 'success' ? 'text-green-500' :
                                  step.status === 'failed' ? 'text-red-500' :
                                  'text-blue-500'
                                }>
                                  {step.status.toUpperCase()}
                                </span>{' '}
                                Step {step.step_number}: {step.name} - {step.message}
                              </div>
                            ))}
                        </div>
                      </Card>
                    </div>
                  </TabsContent>
                </Tabs>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function Loader2({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
