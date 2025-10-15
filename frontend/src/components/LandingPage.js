import React from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Box, Typography, Button, Container, Chip } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

function LandingPage() {
  const navigate = useNavigate();
  const { code } = useParams(); // Get trial code from URL
  const location = useLocation();
  const { isAdmin } = useAuth();

  // Check if this is the admin dashboard
  const isAdminDashboard = location.pathname === '/admin/dashboard';

  const handleGetStarted = () => {
    if (isAdminDashboard) {
      // Navigate to admin recording page
      navigate('/record');
    } else {
      // Navigate to the trial record page with the trial code
      navigate(`/trial/${code}/record`);
    }
  };

  return (
    <Box>
      <Container maxWidth="lg">
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            textAlign: 'center',
            gap: 6,
            py: 4
          }}
        >
          {/* Admin badge */}
          {isAdminDashboard && (
            <Chip
              label="Admin Access - Unlimited"
              color="primary"
              variant="filled"
              sx={{
                fontSize: '1rem',
                fontWeight: 600,
                padding: '8px 16px',
                mb: 2
              }}
            />
          )}

          <Typography
            variant="h1"
            component="h1"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '2rem', sm: '2.75rem', md: '3.5rem' },
              maxWidth: '800px',
              mb: 2,
              lineHeight: 1.2
            }}
          >
            This is video analysis landing page
          </Typography>

          <Button
            variant="contained"
            size="large"
            onClick={handleGetStarted}
            sx={{
              fontSize: '1.2rem',
              padding: '12px 32px',
              mt: 4
            }}
          >
            Get Started
          </Button>
        </Box>
      </Container>
    </Box>
  );
}

export default LandingPage;