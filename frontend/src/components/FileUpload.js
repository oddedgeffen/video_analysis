import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Divider,
  ImageList,
  ImageListItem,
  Checkbox,
  LinearProgress,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import UploadIcon from '@mui/icons-material/Upload';
import CloseIcon from '@mui/icons-material/Close';
import axios from 'axios';
import FeedbackDialog from './FeedbackDialog';
import { API_BASE_URL } from '../utils/api';
import logo from '../logo.svg';

// Set axios defaults for CSRF protection with Django
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

// Poll interval in milliseconds
const POLL_INTERVAL = 3000;

// Maximum file size (25MB in bytes)
const MAX_FILE_SIZE = 25 * 1024 * 1024;  // 25MB

// Helper function to format file size
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Helper function to validate file size
const validateFileSize = (file) => {
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(`File size (${formatFileSize(file.size)}) exceeds the maximum limit of ${formatFileSize(MAX_FILE_SIZE)}`);
  }
};

const FileUpload = () => {
  const theme = useTheme();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [processedDocumentUrl, setProcessedDocumentUrl] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [documentId, setDocumentId] = useState(null);
  const [documentStatus, setDocumentStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(new Set());
  const [extractedImages, setExtractedImages] = useState([]);
  const [selectedImages, setSelectedImages] = useState(new Set());
  const [selectedOldLogo, setSelectedOldLogo] = useState(null);
  const [showNewLogoUpload, setShowNewLogoUpload] = useState(false);
  const [newLogo, setNewLogo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [activeStep, setActiveStep] = useState(0);
  const steps = ['Uploading', 'Processing', 'Downloading'];

  // Calculate progress based on status
  useEffect(() => {
    if (documentStatus === 'pending') {
      setProcessingProgress(20);
    } else if (documentStatus === 'processing') {
      setProcessingProgress(60);
    } else if (documentStatus === 'completed') {
      setProcessingProgress(100);
    } else if (documentStatus === 'failed') {
      setProcessingProgress(0);
    }
  }, [documentStatus]);

  // Restore feedback state from localStorage
  useEffect(() => {
    if (documentId) {
      const hasPendingFeedback = localStorage.getItem(`feedback_pending_${documentId}`);
      if (hasPendingFeedback === 'true') {
        setShowFeedback(true);
        setFeedbackGiven(prev => new Set([...prev, documentId]));
      }
    }
  }, [documentId]);

  // Update steps based on status
  useEffect(() => {
    if (uploading && documentStatus === 'pending') {
      setActiveStep(0);
    } else if (documentStatus === 'processing') {
      setActiveStep(1);
    } else if (documentStatus === 'completed') {
      setActiveStep(2);
    }
  }, [documentStatus, uploading]);

  // Update isProcessing based on documentStatus
  useEffect(() => {
    if (documentStatus === 'completed' || documentStatus === 'failed') {
      setIsProcessing(false);
    }
  }, [documentStatus]);

  const handleFeedbackClose = () => {
    if (documentId) {
      localStorage.removeItem(`feedback_pending_${documentId}`);
    }
    setShowFeedback(false);
  };

  // Handle file selection
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      try {
        validateFileSize(selectedFile);
        setFile(selectedFile);
        setError(null);
        handleUpload(selectedFile);
      } catch (err) {
        setError(err.message);
        e.target.value = '';
      }
    }
  };

  // Handle drag events
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      try {
        validateFileSize(droppedFile);
        setFile(droppedFile);
        setError(null);
        handleUpload(droppedFile);
      } catch (err) {
        setError(err.message);
      }
    }
  };

  // Remove the selected file
  const removeFile = () => {
    setFile(null);
    if (processedDocumentUrl) {
      setProcessedDocumentUrl(null);
      setSuccess(false);
    }
  };

  // Poll for document status
  const pollDocumentStatus = async (id) => {
    if (!id) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/documents/${id}/`);
      const { status, processed_document, error_message } = response.data;
      
      setDocumentStatus(status);
      
      if (status === 'completed') {
        setSuccess(true);
        setIsPolling(false);
        setUploading(false);
        await handleDownload();
      } else if (status === 'failed') {
        setError(error_message || 'Processing failed');
        setIsPolling(false);
        setUploading(false);
      } else if (status === 'processing' || status === 'pending') {
        setTimeout(() => pollDocumentStatus(id), POLL_INTERVAL);
      }
    } catch (err) {
      console.error("Error polling for status:", err);
      setError("Failed to get document status");
      setIsPolling(false);
      setUploading(false);
    }
  };

  // Start polling when document ID is set
  useEffect(() => {
    if (documentId && isPolling) {
      pollDocumentStatus(documentId);
    }
  }, [documentId, isPolling]);

  // Handle initial document upload
  const handleUpload = async (uploadFile) => {
    setUploading(true);
    setError(null);
    setSuccess(false);
    setProcessedDocumentUrl(null);
    setDocumentStatus('pending');
    setFeedbackGiven(new Set());
    setExtractedImages([]);
    setSelectedImages(new Set());
    setSelectedOldLogo(null);
    setShowNewLogoUpload(false);
    setNewLogo(null);

    const formData = new FormData();
    formData.append('document', uploadFile);

    try {
      const response = await axios.post(`${API_BASE_URL}/extract-images/`, formData);
      
      if (response.data.images) {
        setExtractedImages(response.data.images);
        setSuccess(true);
      } else {
        setError("No images found in the document");
      }
    } catch (err) {
      console.error("Upload error:", err);
      setError(err.response?.data?.error || "An error occurred during upload");
    } finally {
      setUploading(false);
    }
  };

  // Handle old logo selection
  const handleImageSelect = (imageIndex, imageData) => {
    setSelectedImages(new Set([imageIndex]));
    setSelectedOldLogo(imageData);
    setShowNewLogoUpload(true);
  };

  // Handle new logo upload and automatically process
  const handleNewLogoChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      try {
        validateFileSize(e.target.files[0]);
        setNewLogo(e.target.files[0]);
        setError(null);

        // Start processing
        setIsProcessing(true);
        setUploading(true);
        
        // Convert base64 to blob for old logo
        const base64Data = selectedOldLogo.split(',')[1];
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const oldLogoBlob = new Blob([byteArray], { type: 'image/png' });
        
        // Create form data
        const formData = new FormData();
        formData.append('original_document', file);
        formData.append('old_logo', oldLogoBlob, 'selected_logo.png');
        formData.append('new_logo', e.target.files[0]);
        
        // Send to processing endpoint
        const response = await axios.post(`${API_BASE_URL}/documents/`, formData);
        
        if (response.data) {
          setDocumentId(response.data.id);
          setDocumentStatus('processing');
          setIsPolling(true);
        }
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Error processing document');
        setIsProcessing(false);
        e.target.value = '';
      } finally {
        setUploading(false);
      }
    }
  };

  // Handle document download
  const handleDownload = async () => {
    if (!documentId) return;
    
    try {
      const checkResponse = await axios.get(`${API_BASE_URL}/documents/${documentId}/download/`);
      
      if (checkResponse.data.download_url) {
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        iframe.src = checkResponse.data.download_url;
        
        if (!feedbackGiven.has(documentId)) {
          localStorage.setItem(`feedback_pending_${documentId}`, 'true');
          setShowFeedback(true);
          setFeedbackGiven(prev => new Set([...prev, documentId]));
        }
        
        setTimeout(() => {
          document.body.removeChild(iframe);
        }, 5000);
      } else {
        const fileResponse = await axios.get(`${API_BASE_URL}/documents/${documentId}/download/`, {
          responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(fileResponse.data);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        if (!feedbackGiven.has(documentId)) {
          localStorage.setItem(`feedback_pending_${documentId}`, 'true');
          setShowFeedback(true);
          setFeedbackGiven(prev => new Set([...prev, documentId]));
        }
      }
    } catch (err) {
      console.error("Download error:", err);
      setError(err.response?.data?.detail || "An error occurred during download");
    }
  };

  return (
    <Box>
      <Box sx={{ 
        mb: 4, 
        textAlign: 'center',
        background: 'linear-gradient(45deg, #1565C0 30%, #1976D2 90%)',
        borderRadius: '8px',
        padding: '2rem',
        boxShadow: '0 3px 5px 2px rgba(25, 118, 210, 0.3)'
      }}>
        <Typography 
          variant="h4" 
          component="h1" 
          gutterBottom 
          sx={{ 
            fontWeight: 'bold',
            color: 'white',
            mb: 2,
            textShadow: '0 2px 4px rgba(0,0,0,0.15)'
          }}
        >
          Swap your logo, fast
        </Typography>
        <Typography 
          variant="subtitle1" 
          sx={{ 
            mb: 1,
            color: 'rgba(255, 255, 255, 0.85)',
            maxWidth: '600px',
            margin: '0 auto',
            lineHeight: 1.6,
            fontSize: '1.1rem'
          }}
        >
          Upload a document to get started
        </Typography>
      </Box>

      <Box sx={{
        mb: 3,
        p: 2,
        border: '2px dashed',
        borderColor: dragOver ? theme.palette.primary.main : file ? theme.palette.success.light : theme.palette.grey[300],
        borderRadius: 1,
        backgroundColor: dragOver ? 'rgba(37, 99, 235, 0.05)' : file ? 'rgba(5, 150, 105, 0.05)' : theme.palette.background.paper,
        transition: 'all 0.2s ease',
        '&:hover': {
          borderColor: file ? theme.palette.success.main : theme.palette.primary.main,
          backgroundColor: file ? 'rgba(5, 150, 105, 0.1)' : theme.palette.grey[100],
        },
        cursor: uploading ? 'not-allowed' : 'pointer',
        opacity: uploading ? 0.7 : 1,
        pointerEvents: uploading ? 'none' : 'auto'
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !uploading && document.getElementById('file-input').click()}
      >
        {file ? (
          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center', 
            width: '100%',
            py: 1,
            px: 2,
            bgcolor: 'rgba(5, 150, 105, 0.1)',
            borderRadius: 1,
          }}>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              width: '100%',
              mb: 0.5
            }}>
              <Typography variant="body2" sx={{ flex: 1, fontWeight: 500 }}>
                {file.name}
              </Typography>
              <IconButton 
                size="small" 
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile();
                }}
                sx={{ 
                  color: theme.palette.error.main,
                  '&:hover': {
                    bgcolor: theme.palette.error.light,
                  }
                }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
            <Typography variant="caption" color="text.secondary">
              Size: {formatFileSize(file.size)}
            </Typography>
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {dragOver ? 'Start by uploading a document' : 'Start by uploading a document'}
            </Typography>
            <Button
              variant="outlined"
              component="span"
              startIcon={<UploadIcon />}
              size="small"
              sx={{ mt: 1 }}
            >
              Browse Files
            </Button>
            <input
              id="file-input"
              type="file"
              hidden
              accept=".pdf,.docx,.pptx"
              onChange={handleFileChange}
            />
          </Box>
        )}
      </Box>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2, borderRadius: 1 }}
          variant="filled"
        >
          {error}
        </Alert>
      )}

      {documentStatus === 'failed' && (
        <Alert 
          severity="error" 
          sx={{ mb: 2, borderRadius: 1 }}
          variant="filled"
        >
          Processing failed. Please try again.
        </Alert>
      )}

      {/* Image Grid - Only show if no logo is selected yet */}
      {extractedImages.length > 0 && !showNewLogoUpload && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Step 1: Select the logo to replace
          </Typography>
          <ImageList sx={{ 
            width: '100%', 
            height: 'auto',
            opacity: uploading ? 0.7 : 1,
            pointerEvents: uploading ? 'none' : 'auto'
          }} cols={3} rowHeight={200}>
            {extractedImages.map((image, index) => (
              <ImageListItem 
                key={index}
                sx={{ 
                  cursor: 'pointer',
                  position: 'relative',
                  '&:hover': {
                    '& .MuiCheckbox-root': {
                      opacity: 1
                    },
                    '& img': {
                      filter: 'brightness(1.1)',
                      boxShadow: '0 0 15px rgba(25, 118, 210, 0.3)',
                      transform: 'scale(1.02)',
                    }
                  }
                }}
                onClick={() => handleImageSelect(index, image)}
              >
                <img
                  src={image}
                  alt={`Extracted image ${index + 1}`}
                  loading="lazy"
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    border: selectedImages.has(index) ? `2px solid ${theme.palette.primary.main}` : 'none',
                    borderRadius: '4px',
                    padding: '8px',
                    backgroundColor: 'white',
                    transition: 'all 0.3s ease',
                    boxShadow: selectedImages.has(index) ? '0 0 10px rgba(25, 118, 210, 0.2)' : 'none'
                  }}
                />
                <Checkbox
                  checked={selectedImages.has(index)}
                  sx={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    opacity: selectedImages.has(index) ? 1 : 0,
                    transition: 'opacity 0.2s',
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    margin: '4px',
                    '&:hover': {
                      opacity: 1
                    }
                  }}
                />
              </ImageListItem>
            ))}
          </ImageList>
        </Box>
      )}

      {/* New Logo Upload Step */}
      {showNewLogoUpload && (
        <Box sx={{ mt: 4 }}>
          {/* Selected Old Logo Preview */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mr: 2 }}>
              Selected logo to replace:
            </Typography>
            <Box
              sx={{
                width: '100px',
                height: '100px',
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 1,
                p: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'white',
              }}
            >
              <img
                src={selectedOldLogo}
                alt="Selected logo"
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: 'contain',
                }}
              />
            </Box>
            <Button
              variant="outlined"
              color="primary"
              onClick={() => {
                setShowNewLogoUpload(false);
                setSelectedOldLogo(null);
                setSelectedImages(new Set());
                setNewLogo(null);
                setProcessingProgress(0);
                setDocumentStatus(null);
              }}
              sx={{ 
                ml: 2,
                borderRadius: 2,
                px: 2,
                py: 1,
                textTransform: 'none',
                fontSize: '0.9rem',
                fontWeight: 500,
                border: '2px solid',
                borderColor: theme.palette.primary.main,
                '&:hover': {
                  border: '2px solid',
                  borderColor: theme.palette.primary.dark,
                  backgroundColor: 'rgba(25, 118, 210, 0.04)',
                },
                '&:disabled': {
                  borderColor: theme.palette.grey[300],
                  color: theme.palette.grey[500],
                },
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
              disabled={uploading || isProcessing}
              startIcon={<CloseIcon />}
            >
              Change Old Logo
            </Button>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Step 2: Upload the new logo
            </Typography>
          </Box>

          <Box
            sx={{
              border: '2px dashed',
              borderColor: (uploading || isProcessing) ? theme.palette.grey[400] : theme.palette.grey[300],
              borderRadius: 1,
              p: 3,
              textAlign: 'center',
              backgroundColor: (uploading || isProcessing) ? theme.palette.grey[100] : theme.palette.background.paper,
              cursor: (uploading || isProcessing) ? 'not-allowed' : 'pointer',
              opacity: (uploading || isProcessing) ? 0.7 : 1,
              pointerEvents: (uploading || isProcessing) ? 'none' : 'auto'
            }}
            onClick={() => !(uploading || isProcessing) && document.getElementById('new-logo-input').click()}
          >
            {(uploading || isProcessing) ? (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                gap: 3,
                mt: 2,
                position: 'relative'
              }}>
                <Box sx={{ position: 'relative' }}>
                  <CircularProgress
                    size={100}
                    thickness={3}
                    sx={{
                      color: theme.palette.primary.main,
                    }}
                  />
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      bottom: 0,
                      right: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography
                      variant="body2"
                      component="div"
                      color="text.secondary"
                      sx={{ 
                        fontWeight: 500,
                        textAlign: 'center',
                        maxWidth: '80px',
                        lineHeight: 1.2
                      }}
                    >
                      {documentStatus === 'pending' && 'Uploading...'}
                      {documentStatus === 'processing' && 'Processing...'}
                      {documentStatus === 'completed' && 'Downloading...'}
                    </Typography>
                  </Box>
                </Box>
                
                <Typography 
                  variant="body2" 
                  color="text.secondary"
                  sx={{ 
                    textAlign: 'center',
                    maxWidth: '300px',
                    lineHeight: 1.5
                  }}
                >
                  {documentStatus === 'pending' && 'Preparing your files for processing'}
                  {documentStatus === 'processing' && 'Processing your document...'}
                  {documentStatus === 'completed' && 'Preparing your document for download'}
                </Typography>
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Click to upload new logo
                </Typography>
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<UploadIcon />}
                  size="small"
                  disabled={uploading || isProcessing}
                >
                  Browse Files
                </Button>
              </Box>
            )}
            <input
              id="new-logo-input"
              type="file"
              hidden
              accept="image/*"
              onChange={handleNewLogoChange}
              disabled={uploading || isProcessing}
            />
          </Box>

          {error && (
            <Alert 
              severity="error" 
              sx={{ mt: 2, borderRadius: 1 }}
              variant="filled"
            >
              {error}
            </Alert>
          )}

          {documentStatus === 'completed' && (
            <Alert 
              severity="success" 
              sx={{ mt: 2, borderRadius: 1 }} 
              variant="filled"
            >
              Document processed successfully! Downloading...
            </Alert>
          )}
        </Box>
      )}

      {uploading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <CircularProgress />
        </Box>
      )}

      <FeedbackDialog 
        open={showFeedback} 
        onClose={handleFeedbackClose}
      />
    </Box>
  );
};

export default FileUpload; 