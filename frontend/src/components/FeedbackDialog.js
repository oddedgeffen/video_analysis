import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  Rating,
  IconButton
} from '@mui/material';
import axios from 'axios';
import CloseIcon from '@mui/icons-material/Close';
import { API_BASE_URL } from '../utils/api';

// Helper function to save feedback
const saveFeedback = (rating, feedback) => {
  const reviews = JSON.parse(localStorage.getItem('reviews') || '[]');
  reviews.push({
    rating,
    feedback,
    timestamp: new Date().toISOString()
  });
  localStorage.setItem('reviews', JSON.stringify(reviews));
};

// Helper function to get all feedback
export const getAllFeedback = () => {
  return JSON.parse(localStorage.getItem('reviews') || '[]');
};

const FeedbackDialog = ({ open, onClose }) => {
  const [feedback, setFeedback] = useState('');
  const [rating, setRating] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Custom handler to prevent closing when clicking outside
  const handleDialogClose = (event, reason) => {
    // Only allow closing via the Skip or Submit buttons
    if (reason === 'backdropClick' || reason === 'escapeKeyDown') {
      return;
    }
    onClose();
  };

  const handleSubmit = async () => {
    // Only submit if there's feedback text
    if (!feedback.trim()) {
      setError('Please provide feedback');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/feedback/`, {
        rating: rating || null,
        feedback_text: feedback.trim()
      });
      
      onClose();
      // Reset state for next time
      setFeedback('');
      setRating(0);
    } catch (err) {
      console.error('Feedback submission error:', err);
      const errorMessage = err.response?.data?.detail || 
                         err.response?.data?.error || 
                         'Failed to submit feedback. Please try again.';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSkip = () => {
    onClose();
    // Reset state for next time
    setFeedback('');
    setRating(0);
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleDialogClose}  // Use custom handler to prevent closing
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>✅ Your document is ready!</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, my: 1 }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <Box display="flex" flexDirection="column">
            <Typography>⭐ How did the logo replacement go?</Typography>
            <Typography sx={{ ml: 3 }}>
              (Your feedback helps us improve)
            </Typography>
          </Box>
          <Rating
            name="feedback-rating"
            value={rating}
            onChange={(_, newValue) => {
              setRating(newValue);
              setError(null);
            }}
            size="large"
          />
          <TextField
            multiline
            rows={3}
            variant="outlined"
            placeholder="Share your thoughts and suggestions"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            fullWidth
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleSkip} color="inherit">Skip</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          color="primary"
          disabled={submitting}
        >
          {submitting ? 'Submitting...' : 'Submit Feedback'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FeedbackDialog; 