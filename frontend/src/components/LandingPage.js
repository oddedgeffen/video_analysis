import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Box, Typography, Button, Container } from '@mui/material';

function LandingPage() {
  const navigate = useNavigate();
  const { code } = useParams(); // Get trial code from URL

  const handleGetStarted = () => {
    // Navigate to the trial record page with the trial code
    navigate(`/trial/${code}/record`);
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