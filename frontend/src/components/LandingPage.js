import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Button, Container, Grid, Paper } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import ImageSearchIcon from '@mui/icons-material/ImageSearch';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import DownloadIcon from '@mui/icons-material/Download';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useTheme, useMediaQuery } from '@mui/material';

function LandingPage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const steps = [
    {
      icon: <UploadFileIcon sx={{ fontSize: 40 }} />,
      text: "Upload your document"
    },
    {
      icon: <ImageSearchIcon sx={{ fontSize: 40 }} />,
      text: "Select old logo"
    },
    {
      icon: <AddPhotoAlternateIcon sx={{ fontSize: 40 }} />,
      text: "Add new logo"
    },
    {
      icon: <DownloadIcon sx={{ fontSize: 40 }} />,
      text: "Get updated file"
    }
  ];

  const Arrow = () => (
    <Grid 
      item 
      xs={12} 
      sm="auto"
      sx={{ 
        display: 'flex', 
        alignItems: 'center',
        justifyContent: 'center',
        py: { xs: 1, sm: 0 }
      }}
    >
      <ArrowForwardIcon 
        sx={{ 
          color: 'primary.main',
          transform: { xs: 'rotate(90deg)', sm: 'none' },
          fontSize: 30
        }} 
      />
    </Grid>
  );

  const handleGetStarted = () => {
    navigate('/upload');
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
            Replace logos in your documents. In seconds.
          </Typography>

          <Grid container alignItems="center" justifyContent="center" sx={{ maxWidth: 1200 }}>
            {steps.map((step, index) => (
              <React.Fragment key={index}>
                <Grid item xs={12} sm="auto">
                  <Paper 
                    elevation={0}
                    sx={{
                      p: 3,
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 2,
                      backgroundColor: 'transparent',
                      minWidth: { sm: '200px' }
                    }}
                  >
                    <Box sx={{ 
                      color: 'primary.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 1
                    }}>
                      {step.icon}
                    </Box>
                    <Typography variant="h6" component="h3" sx={{ fontWeight: 'medium' }}>
                      {step.text}
                    </Typography>
                  </Paper>
                </Grid>
                {index < steps.length - 1 && <Arrow />}
              </React.Fragment>
            ))}
          </Grid>

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

      <Box 
        sx={{ 
          bgcolor: 'grey.50',
          py: 8,
          px: 2
        }}
      >
        <Container maxWidth="md" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', pl: { xs: 2, sm: '15%', md: '20%' } }}>
          <Typography 
            variant="h2" 
            component="h2" 
            sx={{ 
              fontSize: { xs: '1.75rem', sm: '2.25rem' },
              mb: 4,
              fontWeight: 700
            }}
          >
            🧩 What It Works With
          </Typography>
          <Box 
            sx={{ 
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              pl: 4
            }}
          >
            <Typography variant="h6" sx={{ fontSize: '1.25rem', whiteSpace: 'nowrap' }}>✅ PDF (.pdf)</Typography>
            <Typography variant="h6" sx={{ fontSize: '1.25rem', whiteSpace: 'nowrap' }}>✅ Word (.docx)</Typography>
            <Typography variant="h6" sx={{ fontSize: '1.25rem', whiteSpace: 'nowrap' }}>✅ PowerPoint (.pptx)</Typography>
          </Box>
        </Container>
      </Box>

      <Box 
        sx={{ 
          py: 8,
          px: 2
        }}
      >
        <Container maxWidth="md" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', pl: { xs: 2, sm: '15%', md: '20%' } }}>
          <Typography 
            variant="h2" 
            component="h2" 
            sx={{ 
              fontSize: { xs: '1.75rem', sm: '2.25rem' },
              mb: 4,
              fontWeight: 700
            }}
          >
            🎯 Who It's For
          </Typography>
          <Box 
            sx={{ 
              display: 'flex',
              flexDirection: 'column',
              gap: 3,
              pl: 4
            }}
          >
            <Typography 
              variant="h6" 
              sx={{ 
                fontSize: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                whiteSpace: 'nowrap'
              }}
            >
              • Startups that just rebranded
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                fontSize: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                whiteSpace: 'nowrap'
              }}
            >
              • Marketing or ops teams handling branded docs
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                fontSize: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                whiteSpace: 'nowrap'
              }}
            >
              • Agencies working with multiple clients
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                fontSize: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                whiteSpace: 'nowrap'
              }}
            >
              • Anyone tired of clicking "Replace Image" 400 times
            </Typography>
          </Box>
        </Container>
      </Box>

      <Box 
        sx={{ 
          bgcolor: 'grey.50',
          py: 8,
          px: 2
        }}
      >
        <Container maxWidth="md" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', pl: { xs: 2, sm: '15%', md: '20%' } }}>
          <Typography 
            variant="h2" 
            component="h2" 
            sx={{ 
              fontSize: { xs: '1.75rem', sm: '2.25rem' },
              mb: 4,
              fontWeight: 700
            }}
          >
            ⚙️ How It Works
          </Typography>
          <Box 
            sx={{ 
              display: 'flex',
              flexDirection: 'column',
              gap: 3,
              pl: 4
            }}
          >
            {[
              "Upload your document",
              "We show all images inside it",
              "You select the old logo",
              "Upload the new logo",
              "We replace and auto-download the new file"
            ].map((step, index) => (
              <Typography 
                key={index}
                variant="h6" 
                sx={{ 
                  fontSize: '1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  whiteSpace: 'nowrap'
                }}
              >
                {index + 1}. {step}
              </Typography>
            ))}
          </Box>
        </Container>
      </Box>

      <Box 
        sx={{ 
          py: 8,
          px: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          bgcolor: 'white'
        }}
      >
        <a 
          href="https://www.producthunt.com/products/replogo?embed=true&utm_source=badge-featured&utm_medium=badge&utm_source=badge-replogo" 
          target="_blank"
          rel="noopener noreferrer"
        >
          <img 
            src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=994343&theme=light&t=1753128268952" 
            alt="RepLogo - Replace logos in your PDFs, Word, and PowerPoint files | Product Hunt" 
            style={{ width: '250px', height: '54px' }} 
            width="250" 
            height="54" 
          />
        </a>
      </Box>
    </Box>
  );
}

export default LandingPage;