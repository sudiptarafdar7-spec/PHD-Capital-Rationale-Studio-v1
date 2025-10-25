import React, { useState, useEffect } from 'react';
import { Key, Upload, Check, X, Eye, EyeOff, Loader2, Cookie, Info, Trash2 } from 'lucide-react';
import { API_ENDPOINTS, getAuthHeaders } from '../lib/api-config';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';

export default function ApiKeysPage() {
  const [loading, setLoading] = useState(true);
  const [savingStates, setSavingStates] = useState<Record<string, boolean>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [keys, setKeys] = useState<Record<string, string>>({
    openai: '',
    assemblyai: '',
    dhan: '',
    youtube_data: '',
  });
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [cookiesFile, setCookiesFile] = useState<File | null>(null);
  const [cookiesStatus, setCookiesStatus] = useState<{
    exists: boolean;
    file_size_kb: number;
    modified_at: string | null;
    absolute_path?: string;
    current_working_dir?: string;
    is_readable?: boolean;
    diagnostic?: {
      relative_path: string;
      resolved_path: string;
      exists: boolean;
      readable: boolean;
    };
  } | null>(null);
  const [configuredProviders, setConfiguredProviders] = useState<Record<string, boolean>>({
    openai: false,
    assemblyai: false,
    google_cloud: false,
    dhan: false,
    youtube_data: false,
  });

  useEffect(() => {
    loadApiKeys();
    loadCookiesStatus();
  }, []);

  const loadApiKeys = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(API_ENDPOINTS.apiKeys.get, {
        headers: getAuthHeaders(token || ''),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Data is now an array of { id, provider, value, created_at, updated_at }
        const keyMap: Record<string, string> = {};
        const configMap: Record<string, boolean> = {
          openai: false,
          assemblyai: false,
          google_cloud: false,
          dhan: false,
          youtube_data: false,
        };
        
        data.forEach((item: any) => {
          if (item.provider === 'google_cloud') {
            configMap.google_cloud = !!item.value;
            if (item.value) {
              const mockFile = new File([''], 'google-cloud.json', { type: 'application/json' });
              setUploadedFile(mockFile);
            }
          } else {
            keyMap[item.provider] = item.value || '';
            configMap[item.provider] = !!item.value;
          }
        });
        
        setKeys(keyMap);
        setConfiguredProviders(configMap);
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to load API keys');
      }
    } catch (error) {
      console.error('Error loading API keys:', error);
      toast.error('Error loading API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveKey = async (providerId: string, providerName: string) => {
    if (!keys[providerId] || keys[providerId].trim() === '') {
      toast.error('API key required', {
        description: 'Please enter an API key before saving.',
      });
      return;
    }

    setSavingStates(prev => ({ ...prev, [providerId]: true }));

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(API_ENDPOINTS.apiKeys.update, {
        method: 'PUT',
        headers: getAuthHeaders(token || ''),
        body: JSON.stringify({
          provider: providerId,
          value: keys[providerId],
        }),
      });

      if (response.ok) {
        setConfiguredProviders(prev => ({ ...prev, [providerId]: true }));
        toast.success(`${providerName} API key saved`, {
          description: 'The key has been stored securely.',
        });
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to save API key');
      }
    } catch (error) {
      console.error('Error saving API key:', error);
      toast.error('Error saving API key');
    } finally {
      setSavingStates(prev => ({ ...prev, [providerId]: false }));
    }
  };

  const handleFileSelect = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json,application/json';
    input.onchange = (e: Event) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        // Check if it's a JSON file
        if (!file.name.endsWith('.json')) {
          toast.error('Invalid file type', {
            description: 'Please upload a JSON file.',
          });
          return;
        }

        // Check file size (max 1MB)
        if (file.size > 1024 * 1024) {
          toast.error('File too large', {
            description: 'Please upload a file smaller than 1MB.',
          });
          return;
        }

        setUploadedFile(file);
        toast.success('File selected', {
          description: file.name,
        });
      }
    };
    input.click();
  };

  const handleFileUpload = async (providerId: string, providerName: string) => {
    if (!uploadedFile) {
      toast.error('No file selected', {
        description: 'Please select a JSON file first.',
      });
      return;
    }

    setSavingStates(prev => ({ ...prev, [providerId]: true }));

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', uploadedFile);
      
      const response = await fetch(`${API_ENDPOINTS.apiKeys.base}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        setConfiguredProviders(prev => ({ ...prev, [providerId]: true }));
        toast.success(`${providerName} JSON file uploaded`, {
          description: `${uploadedFile.name} has been saved securely.`,
        });
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to upload file');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error('Error uploading file');
    } finally {
      setSavingStates(prev => ({ ...prev, [providerId]: false }));
    }
  };

  const toggleShowKey = (provider: string) => {
    setShowKeys(prev => ({ ...prev, [provider]: !prev[provider] }));
  };

  const loadCookiesStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_ENDPOINTS.apiKeys.base}/cookies-status`, {
        headers: getAuthHeaders(token || ''),
      });

      if (response.ok) {
        const data = await response.json();
        setCookiesStatus(data);
      }
    } catch (error) {
      console.error('Error loading cookies status:', error);
    }
  };

  const handleCookiesFileSelect = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt,text/plain';
    input.onchange = (e: Event) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        if (!file.name.endsWith('.txt')) {
          toast.error('Invalid file type', {
            description: 'Please upload a .txt file (cookies.txt format).',
          });
          return;
        }

        if (file.size > 1024 * 1024) {
          toast.error('File too large', {
            description: 'Please upload a file smaller than 1MB.',
          });
          return;
        }

        setCookiesFile(file);
        toast.success('File selected', {
          description: file.name,
        });
      }
    };
    input.click();
  };

  const handleCookiesUpload = async () => {
    if (!cookiesFile) {
      toast.error('No file selected', {
        description: 'Please select a cookies.txt file first.',
      });
      return;
    }

    setSavingStates(prev => ({ ...prev, youtube_cookies: true }));

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', cookiesFile);
      
      const response = await fetch(`${API_ENDPOINTS.apiKeys.base}/upload-cookies`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('YouTube cookies uploaded', {
          description: data.message,
        });
        loadCookiesStatus();
        setCookiesFile(null);
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to upload cookies');
      }
    } catch (error) {
      console.error('Error uploading cookies:', error);
      toast.error('Error uploading cookies');
    } finally {
      setSavingStates(prev => ({ ...prev, youtube_cookies: false }));
    }
  };

  const handleDeleteCookies = async () => {
    if (!confirm('Are you sure you want to delete the YouTube cookies file?')) {
      return;
    }

    setSavingStates(prev => ({ ...prev, youtube_cookies: true }));

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_ENDPOINTS.apiKeys.base}/delete-cookies`, {
        method: 'DELETE',
        headers: getAuthHeaders(token || ''),
      });

      if (response.ok) {
        toast.success('Cookies deleted', {
          description: 'YouTube cookies file has been removed.',
        });
        loadCookiesStatus();
        setCookiesFile(null);
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to delete cookies');
      }
    } catch (error) {
      console.error('Error deleting cookies:', error);
      toast.error('Error deleting cookies');
    } finally {
      setSavingStates(prev => ({ ...prev, youtube_cookies: false }));
    }
  };

  const apiProviders = [
    {
      id: 'openai',
      name: 'OpenAI',
      description: 'Required for GPT-4 based analysis and extraction',
      type: 'key',
      placeholder: 'sk-...',
    },
    {
      id: 'assemblyai',
      name: 'AssemblyAI',
      description: 'Required for audio transcription with speaker labels',
      type: 'key',
      placeholder: 'xxxxxxxxxxxxxxxxxxxx',
    },
    {
      id: 'google_cloud',
      name: 'Google Cloud',
      description: 'Required for translation services',
      type: 'file',
      placeholder: 'Upload service account JSON',
    },
    {
      id: 'dhan',
      name: 'Dhan API',
      description: 'Required for fetching stock prices and charts',
      type: 'key',
      placeholder: 'eyJhbGciOiJIUzI1NiIsInR5cCI6...',
    },
    {
      id: 'youtube_data',
      name: 'YouTube Data API v3',
      description: 'Required for fetching video metadata (title, channel, upload date, duration)',
      type: 'key',
      placeholder: 'AIzaSy...',
    },
  ];

  const getProviderStatus = (providerId: string) => {
    return configuredProviders[providerId] || false;
  };

  return (
    <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl sm:text-2xl text-foreground mb-1">API Keys</h1>
        <p className="text-sm sm:text-base text-muted-foreground">Configure external service API keys for the rationale generation pipeline</p>
      </div>

      {/* Warning Banner */}
      <Card className="bg-yellow-500/10 border-yellow-500/30 p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-yellow-500/20 rounded-lg flex-shrink-0">
            <Key className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
          </div>
          <div>
            <h3 className="text-yellow-700 dark:text-yellow-400 mb-1">Security Notice</h3>
            <p className="text-sm text-yellow-700/80 dark:text-yellow-300/80">
              All API keys are stored securely in the database and only accessible to administrators. 
              Keys are used during job execution to connect to external services. Never share your API keys with unauthorized users.
            </p>
          </div>
        </div>
      </Card>

      {/* API Keys Configuration */}
      <div className="grid grid-cols-1 gap-6">
        {apiProviders.map((provider) => {
          const isConfigured = getProviderStatus(provider.id);
          const isSaving = savingStates[provider.id] || false;
          
          return (
            <Card key={provider.id} className="premium-card">
              <div className="p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row items-start justify-between mb-4 gap-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="p-2.5 sm:p-3 icon-bg-primary rounded-xl shrink-0">
                    <Key className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-base sm:text-lg text-foreground">{provider.name}</h3>
                    <p className="text-xs sm:text-sm text-muted-foreground">{provider.description}</p>
                  </div>
                </div>
                <Badge className={
                  isConfigured
                    ? 'bg-green-500/20 text-green-600 dark:text-green-500 border-green-500/30 shrink-0'
                    : 'bg-muted text-muted-foreground border-border shrink-0'
                }>
                  {isConfigured ? (
                    <><Check className="w-3 h-3 mr-1" /> Configured</>
                  ) : (
                    <><X className="w-3 h-3 mr-1" /> Not Configured</>
                  )}
                </Badge>
              </div>

              {provider.type === 'key' ? (
                <div className="space-y-3">
                  <Label htmlFor={provider.id} className="text-foreground text-sm">
                    API Key
                  </Label>
                  <div className="relative">
                    <Input
                      id={provider.id}
                      type={showKeys[provider.id] ? 'text' : 'password'}
                      placeholder={provider.placeholder}
                      value={keys[provider.id] || ''}
                      onChange={(e) => setKeys(prev => ({ ...prev, [provider.id]: e.target.value }))}
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => toggleShowKey(provider.id)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showKeys[provider.id] ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <Button
                      onClick={() => handleSaveKey(provider.id, provider.name)}
                      disabled={isSaving}
                      className="bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700"
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        'Save Key'
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    The key will be stored securely and only accessible to administrators
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <Label htmlFor={`${provider.id}-file`} className="text-foreground text-sm">
                    Service Account JSON
                  </Label>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      onClick={handleFileSelect}
                      className="flex-1"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      {uploadedFile ? uploadedFile.name : 'Choose File'}
                    </Button>
                    {uploadedFile && (
                      <Button
                        onClick={() => handleFileUpload(provider.id, provider.name)}
                        disabled={isSaving}
                        className="bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700"
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Uploading...
                          </>
                        ) : (
                          'Upload'
                        )}
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Upload your Google Cloud service account JSON file. The file will be stored securely on the server.
                  </p>
                </div>
              )}
            </div>
            </Card>
          );
        })}
      </div>

      {/* YouTube Cookies Section */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg sm:text-xl text-foreground mb-1">YouTube Authentication</h2>
          <p className="text-sm text-muted-foreground">Required for VPS servers to bypass YouTube bot detection</p>
        </div>

        <Card className="premium-card border-orange-500/30">
          <div className="p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row items-start justify-between mb-4 gap-3">
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <div className="p-2.5 sm:p-3 bg-orange-500/10 rounded-xl shrink-0">
                  <Cookie className="w-5 h-5 sm:w-6 sm:h-6 text-orange-500" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-base sm:text-lg text-foreground">YouTube Cookies</h3>
                  <p className="text-xs sm:text-sm text-muted-foreground">
                    Upload cookies.txt to authenticate video downloads on VPS servers
                  </p>
                </div>
              </div>
              <Badge className={
                cookiesStatus?.exists
                  ? 'bg-green-500/20 text-green-600 dark:text-green-500 border-green-500/30 shrink-0'
                  : 'bg-muted text-muted-foreground border-border shrink-0'
              }>
                {cookiesStatus?.exists ? (
                  <><Check className="w-3 h-3 mr-1" /> Configured</>
                ) : (
                  <><X className="w-3 h-3 mr-1" /> Not Configured</>
                )}
              </Badge>
            </div>

            {/* Info Banner */}
            <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                <div className="text-xs text-blue-600 dark:text-blue-400">
                  <p className="mb-1"><strong>Why is this needed?</strong></p>
                  <p className="text-blue-600/80 dark:text-blue-400/80">
                    YouTube blocks anonymous downloads from VPS/cloud servers. Uploading your browser cookies 
                    allows the system to download videos as if you're signed in, bypassing bot detection.
                  </p>
                </div>
              </div>
            </div>

            {/* Current Status */}
            {cookiesStatus?.exists && (
              <div className="mb-4 space-y-2">
                <div className="p-3 bg-muted/50 rounded-lg space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">File Size:</span>
                    <span className="text-foreground font-medium">{cookiesStatus.file_size_kb} KB</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Last Updated:</span>
                    <span className="text-foreground font-medium">
                      {cookiesStatus.modified_at ? new Date(cookiesStatus.modified_at).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  {cookiesStatus.is_readable !== undefined && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Readable:</span>
                      <span className={`font-medium ${cookiesStatus.is_readable ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {cookiesStatus.is_readable ? '✓ Yes' : '✗ No (Permission Issue!)'}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Diagnostic Info */}
                {cookiesStatus.diagnostic && (
                  <details className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-xs">
                    <summary className="cursor-pointer font-medium text-blue-600 dark:text-blue-400 flex items-center gap-2">
                      <Info className="w-4 h-4" />
                      Diagnostic Information (for troubleshooting)
                    </summary>
                    <div className="mt-2 space-y-1 text-blue-600/80 dark:text-blue-400/80 font-mono">
                      <div><strong>Working Dir:</strong> {cookiesStatus.current_working_dir}</div>
                      <div><strong>Relative Path:</strong> {cookiesStatus.diagnostic.relative_path}</div>
                      <div><strong>Absolute Path:</strong> {cookiesStatus.diagnostic.resolved_path}</div>
                      <div><strong>File Exists:</strong> {cookiesStatus.diagnostic.exists ? '✓ Yes' : '✗ No'}</div>
                      <div><strong>File Readable:</strong> {cookiesStatus.diagnostic.readable ? '✓ Yes' : '✗ No'}</div>
                    </div>
                    {!cookiesStatus.diagnostic.readable && cookiesStatus.diagnostic.exists && (
                      <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-red-600 dark:text-red-400">
                        <strong>⚠️ Permission Issue:</strong> File exists but cannot be read. On VPS, run:
                        <code className="block mt-1 p-1 bg-black/20 rounded">
                          sudo chmod 644 {cookiesStatus.diagnostic.resolved_path}
                        </code>
                      </div>
                    )}
                  </details>
                )}
              </div>
            )}

            {/* Upload Section */}
            <div className="space-y-3">
              <Label htmlFor="cookies-file" className="text-foreground text-sm">
                Cookies File (cookies.txt)
              </Label>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  onClick={handleCookiesFileSelect}
                  className="flex-1"
                  disabled={savingStates.youtube_cookies}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {cookiesFile ? cookiesFile.name : 'Choose File'}
                </Button>
                {cookiesFile && (
                  <Button
                    onClick={handleCookiesUpload}
                    disabled={savingStates.youtube_cookies}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700"
                  >
                    {savingStates.youtube_cookies ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      'Upload'
                    )}
                  </Button>
                )}
                {cookiesStatus?.exists && (
                  <Button
                    variant="destructive"
                    size="icon"
                    onClick={handleDeleteCookies}
                    disabled={savingStates.youtube_cookies}
                    title="Delete cookies file"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Export cookies from your browser in Netscape format and upload the .txt file here.
              </p>
            </div>

            {/* Instructions */}
            <div className="mt-4 p-3 bg-muted/30 rounded-lg">
              <p className="text-xs font-medium text-foreground mb-2">How to export cookies:</p>
              <ol className="text-xs text-muted-foreground space-y-1 list-decimal list-inside">
                <li>Install a browser extension like "Get cookies.txt LOCALLY" (Chrome/Firefox)</li>
                <li>Sign in to YouTube in your browser</li>
                <li>Go to youtube.com and click the extension icon</li>
                <li>Export cookies and save the cookies.txt file</li>
                <li>Upload the file here</li>
              </ol>
              <p className="text-xs text-orange-600 dark:text-orange-400 mt-2">
                ⚠️ Note: Cookies expire after some time. Re-upload if downloads start failing.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
