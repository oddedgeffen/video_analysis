import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import { AuthProvider } from './contexts/AuthContext';
import RecordVideo from './components/RecordVideo';
import AdminRoute from './components/AdminRoute';
import AdminLogin from './components/AdminLogin';
import LandingPage from './components/LandingPage';
import GenericLandingPage from './components/GenericLandingPage';
import ChatPage from './components/ChatPage';
import ProtectedRoute from './components/ProtectedRoute';

const theme = createTheme({
  palette: {
    background: {
      default: '#f5f5f5',
    },
  },
  shape: {
    borderRadius: 10
  }
});

function App() {
  // Set the correct basename based on environment and host
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const basename = isLocalhost ? '/' : '';  // Use root path in production, / in localhost

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router basename={basename}>
          <Routes>
            <Route path="/" element={
              <ProtectedRoute>
                <RecordVideo />
              </ProtectedRoute>
            } />
            <Route path="/upload" element={
              <ProtectedRoute>
                <RecordVideo />
              </ProtectedRoute>
            } />
            <Route path="/trial/:code" element={<LandingPage />} />
            <Route path="/trial/:code/record" element={<RecordVideo />} />
            <Route path="/admin" element={<AdminRoute />} />
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/chat/:videoId" element={<ChatPage />} />
            {/* Catch-all route for invalid URLs - redirect to generic landing page */}
            <Route path="*" element={<GenericLandingPage />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
