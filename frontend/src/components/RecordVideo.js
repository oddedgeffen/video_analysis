import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import VideocamIcon from '@mui/icons-material/Videocam';
import StopIcon from '@mui/icons-material/Stop';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';
import { API_BASE_URL } from '../utils/api';

const RecordVideo = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  
  const [isRecording, setIsRecording] = useState(false);
  const [recordedVideo, setRecordedVideo] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
      const [stream, setStream] = useState(null);
    const [processingStatus, setProcessingStatus] = useState(null);
    const [devices, setDevices] = useState({ video: [], audio: [] });
      const [selectedCamera, setSelectedCamera] = useState('');
  const [selectedMic, setSelectedMic] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const audioAnalyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Request permissions and get available devices
  const getDevices = async () => {
    try {
      // First request permissions by trying to access the devices
      const initialStream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      });
      
      // Once we have permissions, enumerate devices
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      const audioDevices = devices.filter(device => device.kind === 'audioinput');
      
      setDevices({
        video: videoDevices,
        audio: audioDevices
      });

      // Set default devices if none are selected
      if (!selectedCamera && videoDevices.length > 0) {
        setSelectedCamera(videoDevices[0].deviceId);
      }
      if (!selectedMic && audioDevices.length > 0) {
        setSelectedMic(audioDevices[0].deviceId);
      }

      // Stop the initial stream since we'll create a new one with selected devices
      initialStream.getTracks().forEach(track => track.stop());
    } catch (err) {
      console.error('Error getting devices:', err);
      if (err.name === 'NotAllowedError') {
        setError('Please allow access to your camera and microphone to use this feature. Click the camera icon in your browser\'s address bar to grant permission.');
      } else {
        setError('Failed to access cameras and microphones. Please make sure your devices are connected and try again.');
      }
    }
  };

  // Initialize devices when component mounts
  useEffect(() => {
    getDevices();
    return () => {
      // Cleanup: stop all tracks and audio analysis when component unmounts
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioAnalyserRef.current) {
        audioAnalyserRef.current.disconnect();
      }
    };
  }, []);

  // Initialize camera when devices are selected
  useEffect(() => {
    if (selectedCamera && selectedMic) {
      initializeCamera();
    }
  }, [selectedCamera, selectedMic]);

  // Function to analyze audio levels
  const analyzeAudio = (audioContext, stream) => {
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(stream);
    microphone.connect(analyser);
    analyser.fftSize = 256;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const updateAudioLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      // Calculate average volume level
      const average = dataArray.reduce((acc, val) => acc + val, 0) / bufferLength;
      // Normalize to 0-100 range
      const normalizedLevel = (average / 256) * 100;
      setAudioLevel(normalizedLevel);
      
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    };
    
    audioAnalyserRef.current = analyser;
    updateAudioLevel();
  };

  const initializeCamera = async () => {
    try {
      // Stop existing stream and audio analysis
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: selectedCamera ? { exact: selectedCamera } : undefined
        },
        audio: {
          deviceId: selectedMic ? { exact: selectedMic } : undefined
        }
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      
      // Initialize audio analysis
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyzeAudio(audioContext, mediaStream);
      
      setError(null);
    } catch (err) {
      setError("Failed to access camera and microphone. Please ensure you have granted the necessary permissions.");
      console.error("Camera access error:", err);
    }
  };

  const startRecording = () => {
    if (!stream) {
      setError("Camera not initialized");
      return;
    }

    try {
      chunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks (camera and microphone)
        stream.getTracks().forEach(track => track.stop());
        
        // Stop audio analysis
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        if (audioAnalyserRef.current) {
          audioAnalyserRef.current.disconnect();
        }
        
        // Clear the video preview source
        if (videoRef.current) {
          videoRef.current.srcObject = null;
        }

        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        const videoUrl = URL.createObjectURL(blob);
        
        // Set recorded video for preview
        setRecordedVideo({ blob, url: videoUrl });
        setStream(null); // Clear the stream reference
        
        // Automatically download the video
        downloadVideo(blob);
        
        // Automatically upload and navigate to chat
        await uploadVideoAndNavigate(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setError(null);
      setProcessingStatus(null);
    } catch (err) {
      setError("Failed to start recording");
      console.error("Recording error:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const downloadVideo = (blob) => {
    try {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `video-${Date.now()}.webm`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download error:", err);
      setError("Failed to download video");
    }
  };

  const uploadVideoAndNavigate = async (blob) => {
    setUploading(true);
    setProcessingStatus('uploading');
    
    try {
      const formData = new FormData();
      formData.append('video', blob, `video-${Date.now()}.webm`);
      
      const response = await axios.post(`${API_BASE_URL}/upload-video/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data.videoId) {
        setProcessingStatus('processing');
        // Navigate to chat page with the video ID
        navigate(`/chat/${response.data.videoId}`);
      } else {
        throw new Error('No video ID received from server');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload video');
      setProcessingStatus('error');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const retakeVideo = async () => {
    // Clean up the object URL
    if (recordedVideo?.url) {
      URL.revokeObjectURL(recordedVideo.url);
    }

    setRecordedVideo(null);
    setError(null);
    setProcessingStatus(null);

    // Reinitialize camera
    try {
      await initializeCamera();
    } catch (err) {
      setError("Failed to restart camera. Please refresh the page and try again.");
      console.error("Camera restart error:", err);
    }
  };

  const handleManualUpload = async () => {
    if (!recordedVideo) {
      setError("No video recorded");
      return;
    }
    await uploadVideoAndNavigate(recordedVideo.blob);
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography
        variant="h4"
        component="h1"
        gutterBottom
        sx={{ textAlign: 'center', mb: 4 }}
      >
        Record Your Video
      </Typography>

      <Paper
        elevation={3}
        sx={{
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 3
        }}
      >
        {/* Device Selection */}
        <Box sx={{ width: '100%' }}>
          <Stack 
            direction="row" 
            spacing={2} 
            alignItems="center"
            sx={{ mb: 2 }}
          >
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Select Devices
            </Typography>
            <Button
              startIcon={<RefreshIcon />}
              onClick={getDevices}
              disabled={isRecording}
              size="small"
            >
              Refresh Devices
            </Button>
          </Stack>

          <Stack 
            direction={{ xs: 'column', sm: 'row' }} 
            spacing={2} 
            sx={{ width: '100%' }}
          >
            <FormControl fullWidth disabled={isRecording}>
              <InputLabel>Camera</InputLabel>
              <Select
                value={selectedCamera}
                label="Camera"
                onChange={(e) => setSelectedCamera(e.target.value)}
              >
                {devices.video.length === 0 ? (
                  <MenuItem disabled value="">
                    No cameras found
                  </MenuItem>
                ) : (
                  devices.video.map((device) => (
                    <MenuItem key={device.deviceId} value={device.deviceId}>
                      {device.label || `Camera ${devices.video.indexOf(device) + 1}`}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>

            <FormControl fullWidth disabled={isRecording}>
              <InputLabel>Microphone</InputLabel>
              <Select
                value={selectedMic}
                label="Microphone"
                onChange={(e) => setSelectedMic(e.target.value)}
              >
                {devices.audio.length === 0 ? (
                  <MenuItem disabled value="">
                    No microphones found
                  </MenuItem>
                ) : (
                  devices.audio.map((device) => (
                    <MenuItem key={device.deviceId} value={device.deviceId}>
                      {device.label || `Microphone ${devices.audio.indexOf(device) + 1}`}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Stack>

          {/* Audio Level Meter */}
          {selectedMic && !isRecording && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Microphone Test
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ 
                  flex: 1,
                  height: 20,
                  bgcolor: 'grey.300',
                  borderRadius: 1,
                  overflow: 'hidden'
                }}>
                  <Box
                    sx={{
                      height: '100%',
                      width: `${audioLevel}%`,
                      bgcolor: audioLevel > 75 ? 'error.main' : audioLevel > 30 ? 'success.main' : 'primary.main',
                      transition: 'width 0.1s ease-out, background-color 0.3s ease'
                    }}
                  />
                </Box>
                <Typography variant="body2" sx={{ minWidth: 40 }}>
                  {Math.round(audioLevel)}%
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                Speak to test your microphone. The bar should move when you talk.
              </Typography>
            </Box>
          )}

          {(devices.video.length === 0 || devices.audio.length === 0) && (
            <Alert 
              severity="warning" 
              sx={{ mt: 2 }}
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={getDevices}
                >
                  Try Again
                </Button>
              }
            >
              {devices.video.length === 0 && devices.audio.length === 0 ? (
                "No camera or microphone found. Please connect your devices and click 'Try Again'."
              ) : devices.video.length === 0 ? (
                "No camera found. Please connect a camera and click 'Try Again'."
              ) : (
                "No microphone found. Please connect a microphone and click 'Try Again'."
              )}
            </Alert>
          )}
        </Box>

        {/* Video Preview */}
        <Box
          sx={{
            width: '100%',
            aspectRatio: '16/9',
            backgroundColor: '#000',
            borderRadius: 1,
            overflow: 'hidden'
          }}
        >
          {recordedVideo ? (
            <video
              src={recordedVideo.url}
              controls
              style={{ width: '100%', height: '100%' }}
            />
          ) : (
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              style={{ width: '100%', height: '100%' }}
            />
          )}
        </Box>

        {/* Recording Status */}
        {isRecording && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: 'red',
                animation: 'blink 1s infinite'
              }}
            />
            <Typography variant="body2" color="error">
              Recording...
            </Typography>
          </Box>
        )}

        {/* Controls */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          {!recordedVideo ? (
            <Button
              variant="contained"
              color={isRecording ? "error" : "primary"}
              startIcon={isRecording ? <StopIcon /> : <VideocamIcon />}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={!stream || uploading}
              size="large"
            >
              {isRecording ? "Stop Recording" : "Start Recording"}
            </Button>
          ) : (
            <>
              <Button
                variant="outlined"
                onClick={retakeVideo}
                disabled={uploading}
              >
                Record Again
              </Button>
              {!uploading && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleManualUpload}
                >
                  Upload & Analyze
                </Button>
              )}
            </>
          )}
        </Box>

        {/* Upload Progress */}
        {uploading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="body2">
              {processingStatus === 'uploading' ? 'Uploading video...' : 'Processing...'}
            </Typography>
          </Box>
        )}

        {/* Error Messages */}
        {error && (
          <Alert
            severity="error"
            sx={{ width: '100%' }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        {/* Status Messages */}
        {processingStatus === 'uploading' && (
          <Alert
            severity="info"
            sx={{ width: '100%' }}
          >
            Uploading your video...
          </Alert>
        )}

        {processingStatus === 'processing' && (
          <Alert
            severity="info"
            sx={{ width: '100%' }}
          >
            Video uploaded successfully! Redirecting to analysis...
          </Alert>
        )}

        {/* Instructions */}
        <Paper
          sx={{
            p: 2,
            backgroundColor: theme.palette.grey[50],
            width: '100%'
          }}
        >
          <Typography variant="body2" color="textSecondary">
            <strong>Instructions:</strong>
            <br />
            1. Click "Start Recording" to begin
            <br />
            2. Speak clearly and look at the camera
            <br />
            3. Click "Stop Recording" when finished
            <br />
            4. Your video will automatically download and be processed for analysis
          </Typography>
        </Paper>
      </Paper>

      {/* CSS for blinking animation */}
      <style>
        {`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
        `}
      </style>
    </Box>
  );
};

export default RecordVideo;