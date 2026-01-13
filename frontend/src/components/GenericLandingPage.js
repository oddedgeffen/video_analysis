import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';

function GenericLandingPage() {
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
                        AI-Powered Presentation Feedback
                    </Typography>

                    <Typography
                        variant="h5"
                        component="h2"
                        sx={{
                            fontWeight: 400,
                            fontSize: { xs: '1.2rem', sm: '1.5rem' },
                            maxWidth: '600px',
                            mb: 4,
                            lineHeight: 1.4,
                            color: 'text.secondary'
                        }}
                    >
                        Please use a valid trial link to access the service, or sign in as admin
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
                        <Button
                            variant="outlined"
                            size="large"
                            onClick={() => window.location.href = '/admin/login'}
                            sx={{
                                fontSize: '1.1rem',
                                padding: '12px 24px'
                            }}
                        >
                            Admin Login
                        </Button>
                        <Button
                            variant="text"
                            size="large"
                            onClick={() => window.location.href = 'mailto:support@example.com'}
                            sx={{
                                fontSize: '1.1rem',
                                padding: '12px 24px'
                            }}
                        >
                            Contact Support
                        </Button>
                    </Box>
                </Box>
            </Container>
        </Box>
    );
}

export default GenericLandingPage;
