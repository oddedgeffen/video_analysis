import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  TextField,
  IconButton,
  useTheme
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import axios from 'axios';
import { API_BASE_URL } from '../utils/api';

const Message = ({ role, content }) => {
  const theme = useTheme();
  const isAssistant = role === 'assistant';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isAssistant ? 'flex-start' : 'flex-end',
        mb: 2
      }}
    >
      <Paper
        sx={{
          p: 2,
          maxWidth: '70%',
          bgcolor: isAssistant ? '#1e1e1e' : theme.palette.primary.main,
          color: 'white',
          borderRadius: 2,
          boxShadow: 3
        }}
      >
        <Typography
          variant="body1"
          sx={{ whiteSpace: 'pre-wrap' }}
          dangerouslySetInnerHTML={{ __html: content }}
        />
      </Paper>
    </Box>
  );
};

const ChatPage = () => {
  const theme = useTheme();
  const { videoId } = useParams();
  const messagesEndRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [questionsRemaining, setQuestionsRemaining] = useState(10);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const checkVideoStatus = async () => {
      try {
        const statusResponse = await axios.get(`${API_BASE_URL}/video-status/${videoId}/`);
        // Debug log
        console.log('ChatPage status poll', statusResponse.data);

        if (statusResponse.data.status === 'completed') {
          // Video is ready, start the chat
          const chatResponse = await axios.post(`${API_BASE_URL}/chat/start/${videoId}/`);
          console.log('Chat start response', chatResponse.data);
          const { conversation_id, messages: initialMessages, questions_remaining } = chatResponse.data;

          setConversationId(conversation_id);
          setMessages(initialMessages);
          setQuestionsRemaining(questions_remaining);
          setError(null);
          setLoading(false);
        } else if (statusResponse.data.status === 'processing') {
          // Keep polling
          setTimeout(checkVideoStatus, 2000);
        } else if (statusResponse.data.status === 'failed') {
          throw new Error(statusResponse.data.error || 'Video processing failed');
        }
      } catch (err) {
        console.error('ChatPage init error', err);
        // If backend directory isn't ready yet, keep polling instead of erroring
        if (err?.response?.status === 404) {
          setTimeout(checkVideoStatus, 2000);
          return;
        }
        setError(err.response?.data?.error || 'Failed to start chat');
        setLoading(false);
      }
    };

    checkVideoStatus();
  }, [videoId]);

  if (loading) {
    return (
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h4" gutterBottom>
            Video Analysis Chat
          </Typography>
        </Box>

        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 3,
            p: 3
          }}
        >
          <CircularProgress size={60} />
          <Typography variant="h6" align="center" sx={{ fontWeight: 600 }}>
            🎬 Your Video is Being Analyzed!
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" sx={{ maxWidth: 500 }}>
            Our AI is processing your <strong>facial expressions</strong>, <strong>voice patterns</strong>, and <strong>speech content</strong> to provide personalized feedback.
            <br />
            <br />
            This typically takes 30-60 seconds.
          </Typography>
          <Typography
            variant="body2"
            align="center"
            sx={{
              mt: 1,
              p: 2,
              bgcolor: 'primary.lighter',
              borderRadius: 1,
              maxWidth: 450
            }}
          >
            💡 <strong>Pro Tip:</strong> Once ready, ask the AI specific questions like "What should I improve?" or "How confident did I appear?"
          </Typography>
        </Box>
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

  const handleQuestionSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || asking || questionsRemaining <= 0) return;

    setAsking(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/chat/question/${conversationId}/`, {
        question: question.trim()
      });

      const { answer, questions_remaining } = response.data;

      setMessages([
        ...messages,
        { role: 'user', content: question },
        { role: 'assistant', content: answer }
      ]);
      setQuestionsRemaining(questions_remaining);
      setQuestion('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send question');
      console.error('Question error:', err);
    } finally {
      setAsking(false);
    }
  };

  return (
    <Box sx={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      bgcolor: '#121212',
      color: 'white'
    }}>
      <Box sx={{
        p: 3,
        borderBottom: 1,
        borderColor: 'rgba(255,255,255,0.1)',
        bgcolor: '#1e1e1e'
      }}>
        <Typography variant="h4" gutterBottom sx={{ color: 'white' }}>
          Video Analysis Chat
        </Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
          Questions remaining: {questionsRemaining}
        </Typography>
      </Box>

      <Box sx={{
        flex: 1,
        p: 3,
        overflow: 'auto',
        bgcolor: '#121212'
      }}>
        {messages.map((message, index) => (
          <Message key={index} role={message.role} content={message.content} />
        ))}
        <div ref={messagesEndRef} />
      </Box>

      <Box
        component="form"
        onSubmit={handleQuestionSubmit}
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'rgba(255,255,255,0.1)',
          bgcolor: '#1e1e1e'
        }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            variant="outlined"
            placeholder={asking ? "Processing your question..." : "Ask a question about the video..."}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={asking || questionsRemaining <= 0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (question.trim() && !asking && questionsRemaining > 0) {
                  handleQuestionSubmit(e);
                }
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: '#1e1e1e',
                opacity: asking ? 0.7 : 1,
                transition: 'opacity 0.2s',
                '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                '&:hover fieldset': { borderColor: theme.palette.primary.main },
                '& .MuiInputBase-input': {
                  color: 'white'
                },
                '& textarea::placeholder': {
                  color: 'rgba(255,255,255,0.7)',
                  opacity: 1
                }
              }
            }}
          />
          <IconButton
            type="submit"
            color="primary"
            disabled={!question.trim() || asking || questionsRemaining <= 0}
            sx={{
              opacity: asking ? 0.5 : 1,
              transition: 'opacity 0.2s',
              '&.Mui-disabled': {
                opacity: 0.3
              }
            }}
          >
            {asking ? <CircularProgress size={24} /> : <SendIcon />}
          </IconButton>
        </Box>
        {questionsRemaining <= 0 && (
          <Typography variant="body2" color="error" sx={{ mt: 1 }}>
            You have reached the maximum number of questions for this video.
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default ChatPage;
