import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert
} from '@mui/material';
import axios from 'axios';
import { API_BASE_URL } from '../utils/api';

const ChatPage = () => {
  const { videoId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/video-analysis/${videoId}/`);
        setAnalysisResults(response.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch analysis results');
        console.error('Analysis fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [videoId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Video Analysis Results
      </Typography>
      
      {/* Display analysis results here */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="body1">
          Analysis results for video ID: {videoId}
        </Typography>
        {/* Add more UI components to display the analysis results */}
      </Paper>
    </Box>
  );
};

export default ChatPage;
