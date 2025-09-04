import React from 'react';
import { Box, CssBaseline } from '@mui/material';
import Navbar from './Navbar';
import Footer from './Footer';

const Layout = ({ children }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
      }}
    >
      <CssBaseline />
      <Navbar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          py: 4,
        }}
      >
        {children}
      </Box>
      <Footer />
    </Box>
  );
};

export default Layout; 