from pathlib import Path
from django.conf import settings
import json
import os
import multiprocessing
import logging
import psutil

# Only lightweight imports at module level — no torch, mediapipe, librosa, etc.
try:
    from .utils_processor import save_debug_transcript, debug_print_text_analysis, print_voice_features, decimal_limit_transcript
except ImportError:
    from video_analyzer.utils_processor import save_debug_transcript, debug_print_text_analysis, print_voice_features, decimal_limit_transcript

# Import RunPod processing functions (lightweight — just HTTP calls)
import sys
from pathlib import Path as PathLib
runpod_path = str(PathLib(__file__).parent.parent / 'runpod')
if runpod_path not in sys.path:
    sys.path.insert(0, runpod_path)

process_frames_remote = None
try:
    from enpoint import process_frames_remote  # type: ignore
except ImportError:
    pass

import numpy as np

logger = logging.getLogger(__name__)


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types from ML processing steps."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

DEBUG = False

try:
    USE_RUNPOD = getattr(settings, 'USE_RUNPOD', False)
    SAMPLE_TIME_INTERVAL = getattr(settings, 'SAMPLE_TIME_INTERVAL', 1)
except Exception:
    USE_RUNPOD = False
    SAMPLE_TIME_INTERVAL = 1


def _log_ram(label):
    mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    print(f"RAM [{label}]: {mb:.0f} MB")
    logger.info(f"RAM [{label}]: {mb:.0f} MB")


# ---------------------------------------------------------------------------
#  Subprocess workers — each one runs in a child process.
#  When the child exits, the OS reclaims ALL memory (Python + C++ backends).
#  These must be module-level functions so multiprocessing can pickle them.
# ---------------------------------------------------------------------------

def _text_worker(video_path, audio_path, model_size, language, result_path):
    """Child process: Whisper transcription."""
    try:
        from video_analyzer.process_text import analyze_text
    except ImportError:
        from process_text import analyze_text
    try:
        _log_ram("Text/Whisper child: before processing")
        result = analyze_text(
            video_path=video_path, dst_audio_path=audio_path,
            model_size=model_size, language=language, cleanup=True
        )
        _log_ram("Text/Whisper child: after processing")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, cls=_NumpyEncoder)
    except Exception as e:
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump({'__error__': str(e)}, f)


def _frames_worker(input_path, video_path, frame_interval, use_mp, result_path):
    """Child process: MediaPipe frame analysis."""
    try:
        from video_analyzer.process_frames import process_video_segments
    except ImportError:
        from process_frames import process_video_segments
    try:
        _log_ram("Frames/MediaPipe child: before processing")
        with open(input_path, 'r', encoding='utf-8') as f:
            text_transcript = json.load(f)
        result = process_video_segments(
            text_transcript, video_path,
            frame_interval=frame_interval, use_multiprocessing=use_mp
        )
        _log_ram("Frames/MediaPipe child: after processing")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, cls=_NumpyEncoder)
    except Exception as e:
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump({'__error__': str(e)}, f)


def _voice_worker(input_path, audio_path, result_path):
    """Child process: Silero VAD voice analysis."""
    try:
        from video_analyzer.process_voice import process_voice_features
    except ImportError:
        from process_voice import process_voice_features
    try:
        _log_ram("Voice/Silero child: before processing")
        with open(input_path, 'r', encoding='utf-8') as f:
            images_text_transcript = json.load(f)
        result = process_voice_features(images_text_transcript, audio_path)
        _log_ram("Voice/Silero child: after processing")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, cls=_NumpyEncoder)
    except Exception as e:
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump({'__error__': str(e)}, f)


def _run_step(worker_func, step_name, *args):
    """Spawn worker in a child process, wait for it to finish."""
    logger.info(f"Starting {step_name} in subprocess...")
    ctx = multiprocessing.get_context('spawn')
    p = ctx.Process(target=worker_func, args=args)
    p.start()
    p.join()
    if p.exitcode != 0:
        raise RuntimeError(
            f"{step_name} subprocess crashed (exit code {p.exitcode}). "
            f"Likely out of memory."
        )
    logger.info(f"{step_name} subprocess finished (exit code 0)")


def _read_result(path, step_name):
    """Read JSON result from subprocess, raise if it contains an error."""
    with open(path, 'r', encoding='utf-8') as f:
        result = json.load(f)
    if isinstance(result, dict) and '__error__' in result:
        raise RuntimeError(f"{step_name} failed: {result['__error__']}")
    return result


# ---------------------------------------------------------------------------
#  Main orchestrator
# ---------------------------------------------------------------------------

def process_video_file(paths, video_id=None, use_runpod=None, use_multiprocessing=False):
    """
    Main function to process a video file. a
    Each ML step runs in a separate subprocess so memory is fully reclaimed
    between steps (C++ backends don't release memory via Python's gc).
    """
    if use_runpod is None:
        use_runpod = USE_RUNPOD

    logger.info(f"Processing video file: {paths['original_video']}")
    logger.info(f"Processing mode: {'RunPod (Remote)' if use_runpod else 'Local'}")
    _log_ram("Baseline before processing")

    # Temp files for passing data between subprocesses
    tmp_dir = paths['base_dir']
    tmp_dir.mkdir(parents=True, exist_ok=True)
    text_result_path    = str(tmp_dir / '_step_text.json')
    frames_input_path   = str(tmp_dir / '_step_frames_in.json')
    frames_result_path  = str(tmp_dir / '_step_frames.json')
    voice_input_path    = str(tmp_dir / '_step_voice_in.json')
    voice_result_path   = str(tmp_dir / '_step_voice.json')

    tmp_files = [text_result_path, frames_input_path, frames_result_path,
                 voice_input_path, voice_result_path]

    try:
        # ---- Step 1: Text / Whisper ----
        _run_step(
            _text_worker, "Text/Whisper",
            str(paths['original_video']), str(paths['audio_file']),
            "base", "en", text_result_path
        )
        text_transcript = _read_result(text_result_path, "Text/Whisper")
        _log_ram("After Text/Whisper subprocess exited")

        # ---- Step 2: Frames / MediaPipe ----
        fps = text_transcript['video_metadata']['fps']
        frame_interval = int(fps * SAMPLE_TIME_INTERVAL)

        if use_runpod:
            if process_frames_remote is None:
                raise ImportError("RunPod module not available. Install runpod requirements.")
            logger.info("Using RunPod for frame processing (remote)")
            images_text_transcript = process_frames_remote(
                text_transcript=text_transcript,
                video_url=paths['file_url'],
                frame_interval=frame_interval,
                use_multiprocessing=use_multiprocessing
            )
            logger.info("RunPod processing completed successfully")
        else:
            with open(frames_input_path, 'w', encoding='utf-8') as f:
                json.dump(text_transcript, f, ensure_ascii=False, cls=_NumpyEncoder)
            _run_step(
                _frames_worker, "Frames/MediaPipe",
                frames_input_path, str(paths['original_video']),
                frame_interval, use_multiprocessing, frames_result_path
            )
            images_text_transcript = _read_result(frames_result_path, "Frames/MediaPipe")

        _log_ram("After Frames/MediaPipe subprocess exited")

        # ---- Step 3: Voice / Silero VAD ----
        with open(voice_input_path, 'w', encoding='utf-8') as f:
            json.dump(images_text_transcript, f, ensure_ascii=False, cls=_NumpyEncoder)
        _run_step(
            _voice_worker, "Voice/Silero",
            voice_input_path, str(paths['audio_file']), voice_result_path
        )
        final_transcript = _read_result(voice_result_path, "Voice/Silero")
        _log_ram("After Voice/Silero subprocess exited")

        # ---- Post-processing (lightweight, in main process) ----
        final_transcript = decimal_limit_transcript(final_transcript, 3)
        save_debug_transcript(final_transcript, 'final_transcript', paths, dbg_local=DEBUG)

        return final_transcript

    finally:
        for tmp in tmp_files:
            try:
                os.unlink(tmp)
            except OSError:
                pass


if __name__ == "__main__":
    from pathlib import Path
    base_dir = Path(r'C:\video_analysis\code\video_analysis_saas\media\uploads')
    paths = {
        'original_video': base_dir / 'original.webm',
        'audio_file': base_dir / 'audio.wav',
        'base_dir': base_dir
    }
    res = process_video_file(paths)
