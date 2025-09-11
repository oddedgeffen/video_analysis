import librosa
import numpy as np
import json
from typing import Dict, List, Tuple
import re
import torch
import parselmouth

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class VoiceAnalyzer:
    """Analyzes voice features from audio segments"""
    
    def __init__(self, target_sr: int = 16000):
        """Initialize analyzer with target sample rate"""
        self.target_sr = target_sr
        
        # Feature extraction parameters
        self.frame_length = 1024
        self.hop_length = 256
        self.f0_min = 50
        self.f0_max = 500
        
        # Thresholds for derived flags
        self.thresholds = {
            'too_quiet_db': -35,
            'monotone_hz': 15,
            'too_fast_wpm': 160,
            'choppy_ratio': 0.25
        }
        
        # Silero VAD parameters
        self.vad_window_size_samples = 512  # Window size for VAD analysis
        self.vad_threshold = 0.5  # Speech detection threshold
        self.load_vad_model()

    def load_vad_model(self):
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                    model='silero_vad',
                                    force_reload=True,
                                    onnx=False)
        model = model.to(DEVICE)
        (get_speech_timestamps,
        save_audio,
        read_audio,
        VADIterator,
        collect_chunks) = utils
        self.get_speech_timestamps = get_speech_timestamps
        self.model = model
    
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load and resample audio file"""
        y, sr = librosa.load(audio_path, sr=self.target_sr, mono=True)
        return y, sr
    
    def get_segment_audio(self, y: np.ndarray, sr: int, start: float, end: float) -> np.ndarray:
        """Extract audio for a specific segment"""
        start_idx = int(start * sr)
        end_idx = int(end * sr)
        return y[start_idx:end_idx]
    
    def compute_energy_metrics(self, y: np.ndarray) -> Dict:
        """Compute RMS energy and dB metrics"""
        rms = librosa.feature.rms(y=y, frame_length=self.frame_length, hop_length=self.hop_length)[0]
        rms_mean = float(np.mean(rms))
        rms_db_mean = float(20 * np.log10(rms_mean + 1e-10))
        
        return {
            'rms_mean': rms_mean,
            'rms_db_mean': rms_db_mean,
            'rms_std': float(np.std(rms)),
            'rms_max': float(np.max(rms))
        }
    
    def compute_pitch_metrics(self, y: np.ndarray, sr: int) -> Dict:
        """Compute F0 (pitch) statistics using YIN algorithm"""
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=self.f0_min,
            fmax=self.f0_max,
            sr=sr,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )
        
        f0 = f0[~np.isnan(f0)]  # Remove NaN values
        if len(f0) == 0:
            return {
                'f0_median': 0.0,
                'f0_std': 0.0,
                'f0_range': 0.0,
                'unvoiced_ratio': 1.0
            }
        
        return {
            'f0_median': float(np.median(f0)),
            'f0_std': float(np.std(f0)),
            'f0_range': float(np.ptp(f0)),
            'unvoiced_ratio': float(1 - np.mean(voiced_flag))
        }
    

    def estimate_syllables(self, text: str) -> int:
        if not text:
            return 0
        vowels = "aeiouy"
        words = re.findall(r"[a-z]+", text.lower())
        total = 0
        for w in words:
            cnt = 0; prev_vowel = False
            for ch in w:
                v = ch in vowels
                if v and not prev_vowel:
                    cnt += 1
                prev_vowel = v
            # silent 'e' (not '-le') if >1
            if w.endswith("e") and not w.endswith("le") and cnt > 1:
                cnt -= 1
            # common suffixes if >1
            if (w.endswith("es") or w.endswith("ed")) and cnt > 1:
                cnt -= 1
            # small boost for '-ological' (empirical)
            if "ological" in w:
                cnt += 1
            total += max(1, cnt)
        return total

    
    def compute_speaking_rate(self, text: str, duration: float) -> Dict:
        """Compute speaking rate metrics"""
        words = len(text.split())
        syllables = self.estimate_syllables(text)
        
        words_per_minute = (words / duration) * 60
        syllables_per_second = syllables / duration
        
        return {
            'words_per_minute': float(words_per_minute),
            'syllables_per_second': float(syllables_per_second),
            'word_count': words,
            'syllable_count': syllables
        }
    
    def analyze_pauses(self, y: np.ndarray, sr: int) -> Dict:
        """Detect and analyze pauses using Silero VAD"""
        # Convert numpy array to torch tensor and normalize
        audio_tensor = torch.from_numpy(y).float()
        if audio_tensor.abs().max() > 1.0:
            audio_tensor /= audio_tensor.abs().max()
        
        # Move tensor to the same device as the model
        audio_tensor = audio_tensor.to(DEVICE)
        
        # Get speech timestamps using global model
        speech_timestamps = self.get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=sr,
            threshold=self.vad_threshold,
            min_speech_duration_ms=100,
            min_silence_duration_ms=100
        )
        
        # Calculate pause durations
        pauses = []
        if speech_timestamps:
            # Add initial pause if speech doesn't start immediately
            if speech_timestamps[0]['start'] > 0:
                pauses.append(speech_timestamps[0]['start'] / sr)
            
            # Add pauses between speech segments
            for i in range(len(speech_timestamps) - 1):
                pause_duration = (speech_timestamps[i + 1]['start'] - speech_timestamps[i]['end']) / sr
                if pause_duration > 0:
                    pauses.append(pause_duration)
            
            # Add final pause if speech doesn't end at the last sample
            if speech_timestamps[-1]['end'] < len(y):
                pauses.append((len(y) - speech_timestamps[-1]['end']) / sr)
        else:
            # If no speech detected, count entire segment as pause
            pauses.append(len(y) / sr)
        
        total_pause_duration = sum(pauses) if pauses else 0.0
        
        return {
            'pause_count': len(pauses),
            'total_pause_duration': float(total_pause_duration),
            'longest_pause': float(max(pauses)) if pauses else 0.0,
            'mean_pause_duration': float(np.mean(pauses)) if pauses else 0.0,
            'pause_rate': float(len(pauses) / (len(y) / sr)) if len(y) > 0 else 0.0
        }
    
    def compute_spectral_features(self, y: np.ndarray, sr: int) -> Dict:
        """Compute spectral shape features"""
        spectral_centroids = librosa.feature.spectral_centroid(
            y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length
        )[0]
        
        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length
        )[0]
        
        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length
        )[0]
        
        spectral_flatness = librosa.feature.spectral_flatness(
            y=y, n_fft=self.frame_length, hop_length=self.hop_length
        )[0]
        
        return {
            'centroid_mean': float(np.mean(spectral_centroids)),
            'bandwidth_mean': float(np.mean(spectral_bandwidth)),
            'rolloff_mean': float(np.mean(spectral_rolloff)),
            'flatness_mean': float(np.mean(spectral_flatness))
        }
    
    def compute_voice_quality(self, y: np.ndarray, sr: int) -> Dict:
        """Compute voice quality metrics"""
        zcr = librosa.feature.zero_crossing_rate(
            y, frame_length=self.frame_length, hop_length=self.hop_length
        )[0]
        
        quality = {
            'zero_crossing_rate_mean': float(np.mean(zcr)),
            'zero_crossing_rate_std': float(np.std(zcr))
        }
        # Add Parselmouth metrics if available
        try:
            # Create Praat Sound object
            sound = parselmouth.Sound(y, sr)
            
            # Calculate pitch with explicit parameters for better control
            pitch = sound.to_pitch(
                time_step=0.01,     # 10ms time step
                pitch_floor=75.0,   # Minimum F0
                pitch_ceiling=600.0 # Maximum F0
            )
            
            # Check if we have enough voiced frames
            pitch_values = pitch.selected_array['frequency']
            voiced_frames = pitch_values[pitch_values != 0]
            
            if len(voiced_frames) < 10:  # Need minimum voiced frames
                print("Warning: Too few voiced frames for reliable voice quality analysis")
                quality.update({
                    'jitter_local': 0.0,
                    'shimmer_local': 0.0,
                    'hnr_mean': 0.0,
                    'hnr_std': 0.0,
                    'f0_mean_parselmouth': 0.0,
                    'f0_std_parselmouth': 0.0,
                    'f0_median_parselmouth': 0.0,
                    'voiced_fraction': 0.0
                })
                return quality
            
            # Calculate point process for jitter/shimmer
            point_process = parselmouth.praat.call([sound, pitch], "To PointProcess (cc)")
            #################################
            # IMPROVED: Check multiple validation criteria instead of just period count
            audio_duration = len(y) / sr
            voiced_duration = len(voiced_frames) * 0.01  # 10ms per frame

            # More flexible validation
            should_calculate_jitter_shimmer = (
                audio_duration >= 0.5 and          # At least 0.5 seconds
                len(voiced_frames) >= 20 and       # At least 20 voiced frames (200ms)
                voiced_duration >= 0.3             # At least 300ms of voiced speech
            )

            if not should_calculate_jitter_shimmer:
                print(f"Warning: Insufficient data for jitter/shimmer (duration: {audio_duration:.2f}s, voiced: {voiced_duration:.2f}s)")
                quality.update({
                    'jitter_local': 0.0,
                    'shimmer_local': 0.0
                })
            else:
                # Calculate jitter (with error handling)
                try:
                    jitter_local = parselmouth.praat.call(
                        point_process, "Get jitter (local)", 
                        0, 0, 0.0001, 0.02, 1.3
                    )
                    # Validate result is reasonable (jitter should be < 10% typically)
                    if not np.isnan(jitter_local) and 0 <= jitter_local <= 0.1:
                        quality['jitter_local'] = float(jitter_local)
                    else:
                        print(f"Warning: Unrealistic jitter value: {jitter_local}")
                        quality['jitter_local'] = 0.0
                except Exception as e:
                    print(f"Warning: Jitter calculation failed - {str(e)}")
                    quality['jitter_local'] = 0.0
                ##############################################
                # Calculate shimmer (with error handling)
                try:
                    shimmer_local = parselmouth.praat.call(
                        [sound, point_process], "Get shimmer (local)", 
                        0, 0, 0.0001, 0.02, 1.3, 1.6
                    )
                    quality['shimmer_local'] = float(shimmer_local) if not np.isnan(shimmer_local) else 0.0
                except Exception as e:
                    print(f"Warning: Shimmer calculation failed - {str(e)}")
                    quality['shimmer_local'] = 0.0
            
            # Calculate harmonicity (HNR) with better handling
            try:
                harmonicity = sound.to_harmonicity(
                    time_step=0.01,
                    minimum_pitch=75.0,
                    silence_threshold=0.1,
                    periods_per_window=1.0
                )
                
                hnr_values = harmonicity.values
                # Filter out undefined values (-200) and very low values
                valid_hnr = hnr_values[(hnr_values != -200) & (hnr_values > -40)]
                
                if len(valid_hnr) > 0:
                    quality['hnr_mean'] = float(np.mean(valid_hnr))
                    quality['hnr_std'] = float(np.std(valid_hnr))
                else:
                    quality['hnr_mean'] = 0.0
                    quality['hnr_std'] = 0.0
            except Exception as e:
                print(f"Warning: HNR calculation failed - {str(e)}")
                quality['hnr_mean'] = 0.0
                quality['hnr_std'] = 0.0
            
            # Add pitch statistics from Parselmouth (more accurate than librosa)
            if len(voiced_frames) > 0:
                quality.update({
                    'f0_mean_parselmouth': float(np.mean(voiced_frames)),
                    'f0_std_parselmouth': float(np.std(voiced_frames)),
                    'f0_median_parselmouth': float(np.median(voiced_frames)),
                    'voiced_fraction': float(len(voiced_frames) / len(pitch_values))
                })
            else:
                quality.update({
                    'f0_mean_parselmouth': 0.0,
                    'f0_std_parselmouth': 0.0,
                    'f0_median_parselmouth': 0.0,
                    'voiced_fraction': 0.0
                })
            
        except Exception as e:
            print(f"Warning: Parselmouth analysis failed - {str(e)}")
            # Return zeros for all Parselmouth metrics if analysis fails
            quality.update({
                'jitter_local': 0.0,
                'shimmer_local': 0.0,
                'hnr_mean': 0.0,
                'hnr_std': 0.0,
                'f0_mean_parselmouth': 0.0,
                'f0_std_parselmouth': 0.0,
                'f0_median_parselmouth': 0.0,
                'voiced_fraction': 0.0
            })
        
        return quality
    
    def compute_derived_flags(self, features: Dict) -> Dict:
        """Compute derived boolean flags based on thresholds"""
        return {
            'too_quiet': features['energy']['rms_db_mean'] < self.thresholds['too_quiet_db'],
            'monotone': features['pitch']['f0_std'] < self.thresholds['monotone_hz'],
            'too_fast': features['rate']['words_per_minute'] > self.thresholds['too_fast_wpm'],
            'choppy': features['pauses']['total_pause_duration'] / (features['pauses']['total_pause_duration'] + len(features['audio'])/features['sr']) > self.thresholds['choppy_ratio']
        }
    
    def analyze_segment(self, y: np.ndarray, sr: int, text: str, start: float, end: float) -> Dict:
        """Analyze a single audio segment"""
        segment_audio = self.get_segment_audio(y, sr, start, end)
        duration = end - start
        
        features = {
            'audio': segment_audio,
            'sr': sr,
            'energy': self.compute_energy_metrics(segment_audio),
            'pitch': self.compute_pitch_metrics(segment_audio, sr),
            'rate': self.compute_speaking_rate(text, duration),
            'pauses': self.analyze_pauses(segment_audio, sr),
            'spectral': self.compute_spectral_features(segment_audio, sr),
            'quality': self.compute_voice_quality(segment_audio, sr)
        }
        
        features['derived_flags'] = self.compute_derived_flags(features)
        del features['audio']  # Remove audio data from output
        
        return features


def extract_audio_features(audio_path: str, segments: List[Dict]) -> Dict:
    """Extract audio features for all segments
    
    Args:
        audio_path: Path to audio file (wav/mp3)
        segments: List of segment dictionaries with start, end, and text
        
    Returns:
        Dictionary with enriched segments and global audio info
    """
    analyzer = VoiceAnalyzer()
    y, sr = analyzer.load_audio(audio_path)
    
    enriched_segments = []
    for segment in segments:
        audio_features = analyzer.analyze_segment(
            y, sr,
            segment['text'],
            segment['start'],
            segment['end']
        )
        
        enriched_segment = segment.copy()
        enriched_segment['audio_features'] = audio_features
        enriched_segments.append(enriched_segment)
    
    return {
        'segments': enriched_segments,
        'global_audio': {
            'duration_sec': float(len(y) / sr),
            'sample_rate': sr
        }
    }





def process_voice_features(images_text_transcript, audio_path):    
    # Extract voice features
    voice_features = extract_audio_features(audio_path=audio_path,
                            segments=images_text_transcript['segments'])
    
    # Add voice features to existing enriched transcript
    for segment, voice_segment in zip(images_text_transcript['segments'], voice_features['segments']):
        segment['voice_features'] = voice_segment['audio_features']
         
    # Add global audio info
    images_text_transcript['audio_metadata'] = voice_features['global_audio']
    return images_text_transcript

if __name__ == "__main__":
    import json
    # Load existing enriched transcript
    with open(r'media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\images_text_transcript.json', 'r', encoding='utf-8') as f:
        images_text_transcript = json.load(f)
    audio_path = r"C:\video_analysis\code\video_analysis_saas\media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\audio.wav"
    voice_images_text_transcript = process_voice_features(images_text_transcript, audio_path)