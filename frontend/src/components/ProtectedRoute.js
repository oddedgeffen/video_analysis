import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Box, Typography, Paper, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
    const { isAdmin, loading, checked } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();

    // Show loading while checking auth status
    if (loading || !checked) {
        return (
            <Box sx={{
                height: '100vh',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                backgroundColor: '#f5f5f5'
            }}>
                <Typography>Loading...</Typography>
            </Box>
        );
    }

    // Check if user is admin
    if (isAdmin) {
        return children; // Admin has access
    }

    // Check if user is on a trial route
    const isTrialRoute = location.pathname.startsWith('/trial/');
    if (isTrialRoute) {
        return children; // Trial routes are handled by their own components
    }

    // Check if user is on admin routes
    const isAdminRoute = location.pathname.startsWith('/admin');
    if (isAdminRoute) {
        return children; // Admin routes are handled by their own components
    }

    // Check if user is on chat route
    const isChatRoute = location.pathname.startsWith('/chat/');
    if (isChatRoute) {
        return children; // Chat routes are handled by their own components
    }

    // Check if user is on admin record route
    if (location.pathname === '/record') {
        // Only admins can access /record
        return (
            <Box sx={{
                height: '100vh',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                backgroundColor: '#f5f5f5',
                padding: 3
            }}>
                <Paper sx={{
                    padding: 4,
                    textAlign: 'center',
                    maxWidth: 500,
                    boxShadow: 3
                }}>
                    <Typography variant="h4" gutterBottom color="error">
                        Admin Access Required
                    </Typography>
                    <Typography variant="body1" paragraph>
                        This recording page is only accessible to administrators.
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
                        <Button
                            variant="outlined"
                            onClick={() => window.location.href = '/admin/login'}
                        >
                            Admin Login
                        </Button>
                    </Box>
                </Paper>
            </Box>
        );
    }

    // For root path and upload path, show access denied
    if (location.pathname === '/' || location.pathname === '/upload') {
        return (
            <Box sx={{
                height: '100vh',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                backgroundColor: '#f5f5f5',
                padding: 3
            }}>
                <Paper sx={{
                    padding: 4,
                    textAlign: 'center',
                    maxWidth: 500,
                    boxShadow: 3
                }}>
                    <Typography variant="h4" gutterBottom color="primary">
                        Access Restricted
                    </Typography>
                    <Typography variant="body1" paragraph>
                        This video analysis service requires either:
                    </Typography>
                    <Box sx={{ textAlign: 'left', mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            • A valid trial link
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            • Admin authentication
                        </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                        Please use a trial link or contact an administrator for access.
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
                        <Button
                            variant="outlined"
                            onClick={() => navigate('/admin/login')}
                        >
                            Admin Login
                        </Button>
                        <Button
                            variant="text"
                            onClick={() => window.location.href = 'mailto:support@example.com'}
                        >
                            Contact Support
                        </Button>
                    </Box>
                </Paper>
            </Box>
        );
    }

    // Default case - allow access
    return children;
};

export default ProtectedRoute;
