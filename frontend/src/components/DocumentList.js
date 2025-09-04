import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
  Grid,
  CircularProgress
} from '@mui/material';
import {
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../utils/api';

const DocumentList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents/`);
      setDocuments(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch documents');
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = async (documentId, fileName) => {
    try {
      // First check if we get a pre-signed URL
      const checkResponse = await axios.get(`${API_BASE_URL}/documents/${documentId}/download/`);
      
      if (checkResponse.data.download_url) {
        // S3 pre-signed URL case
        window.location.href = checkResponse.data.download_url;
      } else {
        // Local file case - make a new request with blob response type
        const fileResponse = await axios.get(`${API_BASE_URL}/documents/${documentId}/download/`, {
          responseType: 'blob'
        });
        
        // Create a download link
        const url = window.URL.createObjectURL(new Blob([fileResponse.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Error downloading document:', err);
    }
  };

  const handleDelete = async (documentId) => {
    try {
      await axios.delete(`${API_BASE_URL}/documents/${documentId}/`);
      fetchDocuments(); // Refresh the list
    } catch (err) {
      console.error('Error deleting document:', err);
    }
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'processing':
        return <Chip icon={<PendingIcon />} label="Processing" color="warning" />;
      case 'completed':
        return <Chip icon={<CheckCircleIcon />} label="Completed" color="success" />;
      case 'error':
        return <Chip icon={<ErrorIcon />} label="Error" color="error" />;
      default:
        return <Chip label={status} />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2, color: 'error.main' }}>
        <Typography>{error}</Typography>
      </Box>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Uploaded Documents
      </Typography>
      
      {documents.length === 0 ? (
        <Typography color="textSecondary" align="center" sx={{ py: 4 }}>
          No documents uploaded yet
        </Typography>
      ) : (
        <List>
          {documents.map((doc) => (
            <ListItem
              key={doc.id}
              sx={{
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                mb: 2,
                flexDirection: { xs: 'column', sm: 'row' }
              }}
            >
              <ListItemText
                primary={doc.original_document_name}
                secondary={
                  <Grid container spacing={2} alignItems="center">
                    <Grid item>
                      {getStatusChip(doc.status)}
                    </Grid>
                    <Grid item>
                      <Typography variant="caption">
                        Uploaded: {new Date(doc.created_at).toLocaleString()}
                      </Typography>
                    </Grid>
                  </Grid>
                }
              />
              <Box sx={{ display: 'flex', gap: 1, mt: { xs: 1, sm: 0 } }}>
                {doc.status === 'completed' && (
                  <IconButton
                    color="primary"
                    onClick={() => handleDownload(doc.id, doc.processed_document_name)}
                    title="Download processed document"
                  >
                    <DownloadIcon />
                  </IconButton>
                )}
                <IconButton
                  color="error"
                  onClick={() => handleDelete(doc.id)}
                  title="Delete document"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default DocumentList; 