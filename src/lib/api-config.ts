const API_BASE_URL = '';

export const API_ENDPOINTS = {
  auth: {
    login: `${API_BASE_URL}/api/v1/auth/login`,
    logout: `${API_BASE_URL}/api/v1/auth/logout`,
    me: `${API_BASE_URL}/api/v1/auth/me`,
  },
  users: {
    getAll: `${API_BASE_URL}/api/v1/users`,
    getOne: (id: string) => `${API_BASE_URL}/api/v1/users/${id}`,
    create: `${API_BASE_URL}/api/v1/users`,
    update: (id: string) => `${API_BASE_URL}/api/v1/users/${id}`,
    delete: (id: string) => `${API_BASE_URL}/api/v1/users/${id}`,
    changePassword: (id: string) => `${API_BASE_URL}/api/v1/users/${id}/password`,
  },
  apiKeys: {
    base: `${API_BASE_URL}/api/v1/api-keys`,
    get: `${API_BASE_URL}/api/v1/api-keys`,
    update: `${API_BASE_URL}/api/v1/api-keys`,
    delete: (provider: string) => `${API_BASE_URL}/api/v1/api-keys/${provider}`,
  },
  pdfTemplate: {
    get: `${API_BASE_URL}/api/v1/pdf-template`,
    update: `${API_BASE_URL}/api/v1/pdf-template`,
  },
  uploadedFiles: {
    getAll: `${API_BASE_URL}/api/v1/uploaded-files`,
    upload: `${API_BASE_URL}/api/v1/uploaded-files/upload`,
    delete: (id: number) => `${API_BASE_URL}/api/v1/uploaded-files/${id}`,
    download: (id: number) => `${API_BASE_URL}/api/v1/uploaded-files/download/${id}`,
  },
  channels: {
    getAll: `${API_BASE_URL}/api/v1/channels`,
    create: `${API_BASE_URL}/api/v1/channels`,
    update: (id: number) => `${API_BASE_URL}/api/v1/channels/${id}`,
    delete: (id: number) => `${API_BASE_URL}/api/v1/channels/${id}`,
  },
  mediaRationale: {
    fetchVideo: `${API_BASE_URL}/api/v1/media-rationale/fetch-video`,
    startAnalysis: `${API_BASE_URL}/api/v1/media-rationale/start-analysis`,
    getJob: (jobId: string) => `${API_BASE_URL}/api/v1/media-rationale/job/${jobId}`,
    restartStep: (jobId: string, stepNumber: number) => `${API_BASE_URL}/api/v1/media-rationale/restart-step/${jobId}/${stepNumber}`,
    getCsv: (jobId: string) => `${API_BASE_URL}/api/v1/media-rationale/job/${jobId}/csv`,
    updateCsv: (jobId: string) => `${API_BASE_URL}/api/v1/media-rationale/job/${jobId}/csv`,
    generatePdf: (jobId: string) => `${API_BASE_URL}/api/v1/media-rationale/job/${jobId}/generate-pdf`,
    save: (jobId: string) => `${API_BASE_URL}/api/v1/saved-rationale/save`,
    uploadSigned: (jobId: string) => `${API_BASE_URL}/api/v1/saved-rationale/upload-signed`,
    downloadPdf: (filePath: string) => `${API_BASE_URL}/api/v1/saved-rationale/download/${encodeURIComponent(filePath)}`,
    deleteJob: (jobId: string) => `${API_BASE_URL}/api/v1/media-rationale/job/${jobId}`,
  },
  savedRationale: {
    getAll: `${API_BASE_URL}/api/v1/saved-rationale`,
    getOne: (id: number) => `${API_BASE_URL}/api/v1/saved-rationale/${id}`,
    save: `${API_BASE_URL}/api/v1/saved-rationale/save`,
    uploadSigned: `${API_BASE_URL}/api/v1/saved-rationale/upload-signed`,
    downloadPdf: (filePath: string) => `${API_BASE_URL}/api/v1/saved-rationale/download/${encodeURIComponent(filePath)}`,
  },
  activityLogs: {
    getAll: `${API_BASE_URL}/api/v1/activity-logs`,
    create: `${API_BASE_URL}/api/v1/activity-logs`,
  },
};

export const getAuthHeaders = (token?: string) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};
