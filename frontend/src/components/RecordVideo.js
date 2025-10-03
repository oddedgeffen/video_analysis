import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useNavigate, useParams } from 'react-router-dom';
import VideocamIcon from '@mui/icons-material/Videocam';
import StopIcon from '@mui/icons-material/Stop';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';
import { API_BASE_URL } from '../utils/api';

const RecordVideo = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { code } = useParams(); // Get trial code from URL
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioAnalyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const currentStreamRef = useRef(null);
  const initializingRef = useRef(false);

  const [isRecording, setIsRecording] = useState(false);
  const [recordedVideo, setRecordedVideo] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [devices, setDevices] = useState({ video: [], audio: [] });
  const [selectedCamera, setSelectedCamera] = useState('');
  const [selectedMic, setSelectedMic] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [cameraInitialized, setCameraInitialized] = useState(false);
  const [trialValid, setTrialValid] = useState(null);
  const [trialInfo, setTrialInfo] = useState(null);
  const [trialError, setTrialError] = useState(null);

  // Trial code validation
  const validateTrialCode = useCallback(async (trialCode) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/trial/check/${trialCode}/`);
      setTrialInfo(response.data);
      setTrialValid(response.data.valid);
      setTrialError(null);
      return response.data.valid;
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to validate trial code';
      setTrialError(errorMessage);
      setTrialValid(false);
      setTrialInfo(null);
      return false;
    }
  }, []);

  // Get effective trial code based on environment and URL
  const getEffectiveTrialCode = useCallback(() => {
    if (code) {
      // Code provided in URL - use it regardless of environment
      return code;
    }

    // Check if we're on the regular /upload route (no trial code expected)
    if (window.location.pathname === '/upload') {
      if (process.env.NODE_ENV === 'development') {
        // Development mode on /upload - bypass trial validation
        return null; // This will trigger the bypass logic below
      } else {
        // Production mode on /upload - this shouldn't happen, but handle gracefully
        return null;
      }
    }

    if (process.env.NODE_ENV === 'development') {
      // Development mode without code - use test code or bypass
      return 'dev-test-code'; // You can change this to a real test code or null to bypass
    }

    // Production without code - invalid
    return null;
  }, [code]);

  // Check trial code validity on mount
  useEffect(() => {
    const effectiveCode = getEffectiveTrialCode();

    if (!effectiveCode) {
      // Check if we're on the regular /upload route
      if (window.location.pathname === '/upload') {
        // Regular upload route - bypass trial validation entirely
        setTrialValid(true);
        setTrialInfo({ valid: true, videos_remaining: 999, max_videos: 999 });
        setTrialError(null);
      } else if (process.env.NODE_ENV === 'development') {
        // Development mode - bypass trial validation
        setTrialValid(true);
        setTrialInfo({ valid: true, videos_remaining: 999, max_videos: 999 });
        setTrialError(null);
      } else {
        // Production mode without trial code - show error
        setTrialError('Invalid trial link');
        setTrialValid(false);
        setTrialInfo(null);
      }
    } else if (effectiveCode === 'dev-test-code') {
      // Development test code - bypass validation
      setTrialValid(true);
      setTrialInfo({ valid: true, videos_remaining: 999, max_videos: 999 });
      setTrialError(null);
    } else {
      // Validate the real trial code
      validateTrialCode(effectiveCode);
    }
  }, [getEffectiveTrialCode, validateTrialCode]);

  // Cleanup function that doesn't depend on state
  const cleanup = useCallback(() => {
    if (currentStreamRef.current) {
      currentStreamRef.current.getTracks().forEach(track => track.stop());
      currentStreamRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioAnalyserRef.current) {
      try {
        audioAnalyserRef.current.disconnect();
      } catch (e) {
        // Ignore disconnect errors
      }
      audioAnalyserRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
        audioContextRef.current = null;
      } catch (e) {
        // Ignore close errors
      }
    }
  }, []);

  // Audio analysis function
  const startAudioAnalysis = useCallback((stream) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }

      const audioContext = audioContextRef.current;

      if (audioContext.state === 'suspended') {
        audioContext.resume();
      }

      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      microphone.connect(analyser);
      analyser.fftSize = 256;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateAudioLevel = () => {
        if (!audioAnalyserRef.current) return;

        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((acc, val) => acc + val, 0) / bufferLength;
        const normalizedLevel = (average / 256) * 100;
        setAudioLevel(normalizedLevel);

        animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
      };

      audioAnalyserRef.current = analyser;
      updateAudioLevel();
    } catch (err) {
      console.error('Audio analysis error:', err);
    }
  }, []);

  // Initialize camera function - stable version
  const initializeCamera = useCallback(async (cameraId, micId) => {
    if (!cameraId || initializingRef.current) return;

    initializingRef.current = true;

    try {
      // Clean up previous stream
      cleanup();

      const constraints = {
        video: {
          deviceId: { exact: cameraId }
        },
        ...(micId && {
          audio: {
            deviceId: { exact: micId }
          }
        })
      };

      console.log('Initializing with constraints:', constraints);
      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);

      // Store stream reference
      currentStreamRef.current = mediaStream;

      // Set the stream to the video element
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;

        // Simple play without complex event handling
        try {
          await videoRef.current.play();
        } catch (playError) {
          console.warn('Video play error:', playError);
        }
      }

      setCameraInitialized(true);

      // Initialize audio analysis if we have audio track
      if (micId && mediaStream.getAudioTracks().length > 0) {
        startAudioAnalysis(mediaStream);
      }

      setError(null);
    } catch (err) {
      setError("Failed to access camera and microphone. Please ensure you have granted the necessary permissions.");
      console.error("Camera access error:", err);
      setCameraInitialized(false);
    } finally {
      initializingRef.current = false;
    }
  }, [cleanup, startAudioAnalysis]);

  // Get devices function
  const getDevices = useCallback(async () => {
    try {
      // First request permissions
      const initialStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });

      // Stop it immediately
      initialStream.getTracks().forEach(track => track.stop());

      // Now enumerate devices
      const deviceList = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = deviceList.filter(device => device.kind === 'videoinput');
      const audioDevices = deviceList.filter(device => device.kind === 'audioinput');

      setDevices({
        video: videoDevices,
        audio: audioDevices
      });

      // Set default devices if none are selected and devices are available
      if (!selectedCamera && videoDevices.length > 0) {
        setSelectedCamera(videoDevices[0].deviceId);
      }
      if (!selectedMic && audioDevices.length > 0) {
        setSelectedMic(audioDevices[0].deviceId);
      }

    } catch (err) {
      console.error('Error getting devices:', err);
      if (err.name === 'NotAllowedError') {
        setError('Please allow access to your camera and microphone to use this feature.');
      } else {
        setError('Failed to access cameras and microphones. Please make sure your devices are connected and try again.');
      }
    }
  }, [selectedCamera, selectedMic]);

  // Initialize devices on mount
  useEffect(() => {
    getDevices();

    return () => {
      cleanup();
    };
  }, [getDevices, cleanup]);

  // Initialize camera when devices are selected
  useEffect(() => {
    if (selectedCamera && !isRecording && !recordedVideo) {
      // Debounce camera initialization
      const timeoutId = setTimeout(() => {
        initializeCamera(selectedCamera, selectedMic);
      }, 500);

      return () => clearTimeout(timeoutId);
    }
  }, [selectedCamera, selectedMic, isRecording, recordedVideo, initializeCamera]);

  const startRecording = () => {
    if (!currentStreamRef.current) {
      setError("Camera not initialized");
      return;
    }

    try {
      chunksRef.current = [];
      const mediaRecorder = new MediaRecorder(currentStreamRef.current);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        // Stop the stream and clean up
        cleanup();
        setCameraInitialized(false);

        // Clear the video preview
        if (videoRef.current) {
          videoRef.current.srcObject = null;
        }

        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        const videoUrl = URL.createObjectURL(blob);

        setRecordedVideo({ blob, url: videoUrl });
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
      console.log('Debug: Starting video upload, blob size:', blob.size);
      const formData = new FormData();
      const filename = `video-${Date.now()}.webm`;
      formData.append('video', blob, filename);

      // Add trial code to form data
      const effectiveCode = getEffectiveTrialCode();
      if (window.location.pathname === '/upload') {
        // Regular upload route - skip trial code entirely
        console.log('Debug: Regular upload route - no trial code needed');
      } else if (effectiveCode && effectiveCode !== 'dev-test-code') {
        formData.append('trial_code', effectiveCode);
        console.log('Debug: Added trial code to form data:', effectiveCode);
      } else if (process.env.NODE_ENV === 'development') {
        // In development, you might want to use a real test trial code
        // For now, we'll skip adding trial_code in development
        console.log('Debug: Development mode - skipping trial code');
      }

      console.log('Debug: Created FormData with filename:', filename);

      // Removed stray debugger that could pause the app in dev tools

      // Upload video and start processing
      console.log('Debug: Sending POST request to:', `${API_BASE_URL}/process-video/`);
      const response = await axios.post(`${API_BASE_URL}/process-video/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000,
      });

      if (response.data.videoId) {
        // Immediately navigate to chat; ChatPage handles polling and UI
        navigate(`/chat/${response.data.videoId}`);
      } else {
        throw new Error('No video ID received from server');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload video');
      setProcessingStatus('error');
      console.error('Upload error:', err);
    }
  };

  const retakeVideo = () => {
    if (recordedVideo?.url) {
      URL.revokeObjectURL(recordedVideo.url);
    }

    setRecordedVideo(null);
    setError(null);
    setProcessingStatus(null);
    setCameraInitialized(false);

    // The useEffect will handle re-initializing the camera
  };

  const handleAnalyzeVideo = async () => {
    if (!recordedVideo) {
      setError("No video recorded");
      return;
    }

    try {
      downloadVideo(recordedVideo.blob);
      await uploadVideoAndNavigate(recordedVideo.blob);
    } catch (err) {
      setError("Failed to process video. Please try again.");
      console.error("Video processing error:", err);
    }
  };

  // Device change handlers
  const handleCameraChange = (e) => {
    const newCameraId = e.target.value;
    if (newCameraId !== selectedCamera) {
      setSelectedCamera(newCameraId);
      setCameraInitialized(false);
    }
  };

  const handleMicChange = (e) => {
    const newMicId = e.target.value;
    if (newMicId !== selectedMic) {
      setSelectedMic(newMicId);
      if (cameraInitialized) {
        setCameraInitialized(false);
      }
    }
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
        {/* Trial Status */}
        {trialValid === false && trialError && (
          <Alert severity="error" sx={{ width: '100%' }}>
            {trialError}
            {process.env.NODE_ENV === 'production' && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Please use a valid trial link to access this service.
              </Typography>
            )}
          </Alert>
        )}

        {trialValid === true && trialInfo && (
          <Alert severity="success" sx={{ width: '100%' }}>
            <Typography variant="body2">
              Trial valid! You have {trialInfo.videos_remaining} of {trialInfo.max_videos} videos remaining.
              {trialInfo.expires_at && (
                <span> Expires: {new Date(trialInfo.expires_at).toLocaleDateString()}</span>
              )}
            </Typography>
          </Alert>
        )}

        {trialValid === null && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
            <CircularProgress size={20} />
            <Typography variant="body2">Validating trial code...</Typography>
          </Box>
        )}

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
                onChange={handleCameraChange}
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
                onChange={handleMicChange}
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
          {selectedMic && cameraInitialized && !isRecording && (
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
            overflow: 'hidden',
            position: 'relative'
          }}
        >
          {recordedVideo ? (
            <video
              src={recordedVideo.url}
              controls
              style={{ width: '100%', height: '100%' }}
            />
          ) : selectedCamera ? (
            <>
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  display: cameraInitialized ? 'block' : 'none'
                }}
              />
              {!cameraInitialized && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column',
                    gap: 2,
                    color: 'white',
                    backgroundColor: 'rgba(0,0,0,0.8)'
                  }}
                >
                  <CircularProgress color="primary" size={40} />
                  <Typography>
                    Initializing camera...
                  </Typography>
                </Box>
              )}
            </>
          ) : (
            <Box
              sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 2,
                color: 'white'
              }}
            >
              <VideocamIcon sx={{ fontSize: 48 }} />
              <Typography>
                Select a camera to start preview
              </Typography>
            </Box>
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
              disabled={!cameraInitialized || uploading || trialValid !== true}
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
                  onClick={handleAnalyzeVideo}
                  disabled={trialValid !== true}
                >
                  Analyze My Video
                </Button>
              )}
            </>
          )}
        </Box>

        {/* Upload & Processing Progress */}
        {(uploading || processingStatus === 'processing') && (
          <Box sx={{ mt: 2, width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <CircularProgress size={24} />
              <Typography variant="body2">
                {processingStatus === 'uploading' && 'Uploading video...'}
                {processingStatus === 'processing' && 'Analyzing video...'}
              </Typography>
            </Box>
            <Alert severity="info">
              {processingStatus === 'uploading' &&
                'Uploading your video to the server...'
              }
              {processingStatus === 'processing' &&
                'Your video is being analyzed. This may take a few minutes depending on the video length. Please don\'t close this window.'
              }
            </Alert>
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
            1. Select your camera and microphone from the dropdowns above
            <br />
            2. Wait for the camera preview to appear
            <br />
            3. Click "Start Recording" to begin
            <br />
            4. Speak clearly and look at the camera
            <br />
            5. Click "Stop Recording" when finished
            <br />
            6. Your video will automatically download and be processed for analysis
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