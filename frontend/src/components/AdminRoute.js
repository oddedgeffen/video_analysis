import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert
} from '@mui/material';
import AdminDashboard from './AdminDashboard';

const AdminRoute = () => {
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    // For MVP, we'll use a simple password check
    // In production, you should use proper authentication
    if (password === 'admin123') {
      setIsAuthenticated(true);
      setError(null);
    } else {
      setError('Invalid password');
    }
  };

  if (isAuthenticated) {
    return <AdminDashboard />;
  }

  return (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      bgcolor: 'grey.100'
    }}>
      <Paper sx={{ 
        p: 4, 
        maxWidth: 400,
        width: '100%',
        mx: 2
      }}>
        <Typography variant="h5" gutterBottom align="center">
          Admin Access
        </Typography>
        
        <form onSubmit={handleSubmit}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            fullWidth
            type="password"
            label="Admin Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
          />
          
          <Button
            fullWidth
            type="submit"
            variant="contained"
            sx={{ mt: 2 }}
          >
            Access Dashboard
          </Button>
        </form>
      </Paper>
    </Box>
  );
};

export default AdminRoute; 