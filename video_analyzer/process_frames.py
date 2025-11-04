import json
import cv2
import numpy as np
import mediapipe as mp
from tqdm import tqdm
import torch
from typing import Dict, List, Union, Tuple


# Constants for feature calculations
# GAZE_ANGLE_THRESH = 12   # Degrees threshold for eye contact (skipped for now)
BROW_RAISE_THRESH = 0.15 # Threshold for significant brow raise
HEAD_MOTION_THRESH = 0.1 # Threshold for head motion detection

# MediaPipe Face Mesh landmark indices (0-467 available, 468-477 for iris with refine_landmarks=True)
FACE_LANDMARKS = {
    "eyes": {
        "left": {
            "center": [33, 133],  # Left eye center points
            "iris": [468, 469, 470, 471],  # Left iris landmarks
            "top": 159,           # Upper eyelid
            "bottom": 145,        # Lower eyelid
            "outer": 33,          # Outer corner
            "inner": 133,         # Inner corner
            "contour": [33, 133, 159, 145, 163]  # Eye contour points
        },
        "right": {
            "center": [362, 263], # Right eye center points
            "iris": [473, 474, 475, 476],  # Right iris landmarks
            "top": 386,           # Upper eyelid
            "bottom": 374,        # Lower eyelid
            "outer": 362,         # Outer corner
            "inner": 263,         # Inner corner
            "contour": [362, 263, 386, 374, 398]  # Eye contour points
        }
    },
    "eyebrows": {
        "left": {
            "outer": 282,         # Outer end
            "inner": 293,         # Inner end
            "top": 282,           # Upper point
            "bottom": 293,        # Lower point
            "contour": [282, 283, 284, 293, 295]  # Eyebrow contour
        },
        "right": {
            "outer": 52,          # Outer end
            "inner": 53,          # Inner end
            "top": 52,            # Upper point
            "bottom": 53,         # Lower point
            "contour": [52, 53, 54, 63, 66]  # Eyebrow contour
        }
    },
    "nose": {
        "tip": 1,                # Nose tip
        "bridge": 168,           # Bridge of nose
        "left_nostril": 331,     # Left nostril
        "right_nostril": 101,    # Right nostril
        "top": 168,              # Top of nose
        "bottom": 1,             # Bottom of nose
        "contour": [168, 1, 331, 101, 197, 419]  # Nose contour
    },
    "mouth": {
        "upper_lip": 13,         # Upper lip center
        "lower_lip": 14,         # Lower lip center
        "left_corner": 61,       # Left corner
        "right_corner": 291,     # Right corner
        "top": 0,                # Top of upper lip
        "bottom": 17,            # Bottom of lower lip
        "contour_outer": [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291],  # Outer lip
        "contour_inner": [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]   # Inner lip
    },
    "face": {
        "chin": 152,             # Chin center
        "forehead": 10,          # Forehead center
        "left_cheek": 234,       # Left cheek
        "right_cheek": 454,      # Right cheek
        "jaw_left": 234,         # Left jaw
        "jaw_right": 454,        # Right jaw
        "contour": [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152],  # Face outline
        "silhouette": list(range(0, 17))  # Standard face silhouette
    }
}


def initialize_face_mesh():
    # Initialize MediaPipe Face Mesh
    mp_face_mesh = mp.solutions.face_mesh

    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        refine_landmarks=True  # Enable iris landmarks
    )
    return face_mesh

class FaceMetrics:
    """Helper class for calculating facial metrics and tracking motion"""
    
    def __init__(self, frame_width, frame_height, fps):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.prev_landmarks = None
        self.motion_history = {
            'head_yaw': [],
            'head_pitch': [],
            'head_roll': [],
            'gaze_shifts': [],
            'mouth_motion': []
        }
    

    def calculate_gaze_direction(self, iris_center, eye_center):
        """Calculate gaze direction in degrees using iris position"""
        dx = iris_center[0] - eye_center[0]
        dy = iris_center[1] - eye_center[1]
        yaw = np.degrees(np.arctan2(dx, 1))
        pitch = np.degrees(np.arctan2(dy, 1))
        return yaw, pitch
    
    def calculate_mouth_ar(self, top, bottom, left, right):
        """Calculate Mouth Aspect Ratio"""
        height = abs(top.y - bottom.y)
        width = abs(left.x - right.x)
        return height / width if width > 0 else 0
    
    def calculate_motion_metrics(self, current_landmarks):
        """Calculate motion-based metrics"""
        if self.prev_landmarks is None:
            self.prev_landmarks = current_landmarks
            return {}
        
        # Calculate angular velocities
        yaw_vel = abs(current_landmarks['head']['rotation']['yaw'] - self.prev_landmarks['head']['rotation']['yaw']) * self.fps
        pitch_vel = abs(current_landmarks['head']['rotation']['pitch'] - self.prev_landmarks['head']['rotation']['pitch']) * self.fps
        roll_vel = abs(current_landmarks['head']['rotation']['roll'] - self.prev_landmarks['head']['rotation']['roll']) * self.fps
        
        # Update motion history
        self.motion_history['head_yaw'].append(yaw_vel)
        self.motion_history['head_pitch'].append(pitch_vel)
        self.motion_history['head_roll'].append(roll_vel)
        
        # Calculate rates (over last second)
        window = int(min(self.fps, len(self.motion_history['head_yaw'])))
        metrics = {
            'head_motion': {
                'yaw_rate': np.mean(self.motion_history['head_yaw'][-window:]),
                'pitch_rate': np.mean(self.motion_history['head_pitch'][-window:]),
                'roll_rate': np.mean(self.motion_history['head_roll'][-window:]),
                'stability_rms': np.sqrt(np.mean(np.array([
                    self.motion_history['head_yaw'][-window:],
                    self.motion_history['head_pitch'][-window:],
                    self.motion_history['head_roll'][-window:]
                ])**2))
            }
        }
        
        self.prev_landmarks = current_landmarks
        return metrics

def extract_face_features(image: np.ndarray, metrics: FaceMetrics = None) -> Dict:
    """
    Extract comprehensive face features using MediaPipe Face Mesh.
    
    Args:
        image: RGB image as numpy array
        metrics: FaceMetrics instance for temporal measurements
        
    Returns:
        Dictionary with extensive facial features and measurements
    """
    face_mesh = initialize_face_mesh()

    h, w = image.shape[:2]
    results = face_mesh.process(image)
    
    features = {
        "face_detected": False,
        "eyes": {
            "left": {
                "width_height_ratio": 0.0,
                "iris_position": {"x": 0.0, "y": 0.0},
                "gaze": {"yaw": 0.0, "pitch": 0.0}
            },
            "right": {
                "width_height_ratio": 0.0,
                "iris_position": {"x": 0.0, "y": 0.0},
                "gaze": {"yaw": 0.0, "pitch": 0.0}
            },
            "saccade_rate": 0.0
        },
        "eyebrows": {
            "left": {
                "raise": 0.0,
                "furrow": 0.0
            },
            "right": {
                "raise": 0.0,
                "furrow": 0.0
            },
            "asymmetry": 0.0
        },
        "mouth": {
            "mar": 0.0,  # Mouth Aspect Ratio
            "width_height_ratio": 0.0,
            "asymmetry": 0.0,
            "smile_intensity": 0.0,
            "lip_press": 0.0,
            "motion_energy": 0.0
        },
        "head": {
            "rotation": {
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0
            },
            "motion": {
                "nod_rate": 0.0,
                "shake_rate": 0.0,
                "stability_rms": 0.0
            }
        },
        "face": {
            "width_height_ratio": 0.0,
            "symmetry": 0.0,
            "scale": 0.0,  # % of frame
            "center_offset": {"x": 0.0, "y": 0.0}  # from frame center
        }
    }
    
    if not results.multi_face_landmarks:
        return features
        
    features["face_detected"] = True
    landmarks = results.multi_face_landmarks[0].landmark
    
    # Process eyes
    for side in ["left", "right"]:
        eye_points = FACE_LANDMARKS["eyes"][side]
        
        # Calculate EAR
        eye_top = landmarks[eye_points["top"]]
        eye_bottom = landmarks[eye_points["bottom"]]
        eye_outer = landmarks[eye_points["outer"]]
        eye_inner = landmarks[eye_points["inner"]]
        
        # Calculate width/height ratio
        width = abs(eye_outer.x - eye_inner.x)
        height = abs(eye_top.y - eye_bottom.y)
        width_height_ratio = width / height if height > 0 else 0
        
        # Calculate eye center (mean of the two corner landmarks)
        eye_center = np.mean([[landmarks[i].x, landmarks[i].y] for i in eye_points["center"]], axis=0)
        
        # Calculate iris center (mean of the 4 iris landmarks)
        iris_center = np.mean([[landmarks[i].x, landmarks[i].y] for i in eye_points["iris"]], axis=0)
        
        # Calculate gaze direction using iris position relative to eye center
        gaze_yaw, gaze_pitch = metrics.calculate_gaze_direction(iris_center, eye_center)
        
        # Update eye features
        features["eyes"][side].update({
            "width_height_ratio": float(width_height_ratio),
            "iris_position": {
                "x": float(iris_center[0] - eye_center[0]),
                "y": float(iris_center[1] - eye_center[1])
            },
            "gaze": {
                "yaw": float(gaze_yaw),
                "pitch": float(gaze_pitch)
            }
            # eye_contact feature skipped for now
        })
    
    # Process eyebrows
    for side in ["left", "right"]:
        brow_points = FACE_LANDMARKS["eyebrows"][side]
        eye_points = FACE_LANDMARKS["eyes"][side]
        
        # Calculate brow raise
        brow_height = abs(landmarks[brow_points["top"]].y - landmarks[eye_points["top"]].y)
        features["eyebrows"][side]["raise"] = float(brow_height)
        
        # Calculate brow furrow
        if side == "left":
            furrow = abs(landmarks[brow_points["inner"]].x - landmarks[FACE_LANDMARKS["eyebrows"]["right"]["inner"]].x)
            features["eyebrows"]["furrow"] = float(furrow)
    
    # Calculate eyebrow asymmetry
    features["eyebrows"]["asymmetry"] = float(abs(
        features["eyebrows"]["left"]["raise"] - features["eyebrows"]["right"]["raise"]
    ))
    
    # Process mouth
    mouth_points = FACE_LANDMARKS["mouth"]
    mar = metrics.calculate_mouth_ar(
        landmarks[mouth_points["top"]],
        landmarks[mouth_points["bottom"]],
        landmarks[mouth_points["left_corner"]],
        landmarks[mouth_points["right_corner"]]
    )
    
    # Calculate mouth metrics
    mouth_width = abs(landmarks[mouth_points["left_corner"]].x - landmarks[mouth_points["right_corner"]].x)
    mouth_height = abs(landmarks[mouth_points["top"]].y - landmarks[mouth_points["bottom"]].y)
    
    features["mouth"].update({
        "mar": float(mar),
        "width_height_ratio": float(mouth_width / mouth_height if mouth_height > 0 else 0),
        "asymmetry": float(abs(
            landmarks[mouth_points["left_corner"]].y - landmarks[mouth_points["right_corner"]].y
        )),
        "smile_intensity": float(mouth_width * 2),  # Normalized smile score
        "lip_press": float(1.0 - mar)  # Inverse of mouth opening
    })
    
    # Head pose
    face_points = FACE_LANDMARKS["face"]
    features["head"]["rotation"].update({
        "yaw": float(abs(landmarks[face_points["left_cheek"]].z - landmarks[face_points["right_cheek"]].z)),
        "pitch": float(abs(landmarks[FACE_LANDMARKS["nose"]["tip"]].y - landmarks[FACE_LANDMARKS["nose"]["bridge"]].y)),
        "roll": float(np.degrees(np.arctan2(
            landmarks[face_points["right_cheek"]].y - landmarks[face_points["left_cheek"]].y,
            landmarks[face_points["right_cheek"]].x - landmarks[face_points["left_cheek"]].x
        )))
    })
    
    # Face geometry
    face_width = abs(landmarks[face_points["jaw_left"]].x - landmarks[face_points["jaw_right"]].x)
    face_height = abs(landmarks[face_points["forehead"]].y - landmarks[face_points["chin"]].y)
    face_center_x = (landmarks[face_points["jaw_left"]].x + landmarks[face_points["jaw_right"]].x) / 2
    face_center_y = (landmarks[face_points["forehead"]].y + landmarks[face_points["chin"]].y) / 2
    
    features["face"].update({
        "width_height_ratio": float(face_width / face_height if face_height > 0 else 0),
        "scale": float(face_width * face_height * 100),  # % of frame area
        "center_offset": {
            "x": float((face_center_x - 0.5) * 2),  # -1 to 1, where 0 is center
            "y": float((face_center_y - 0.5) * 2)
        }
    })
    
    # Calculate symmetry
    left_points = np.array([[landmarks[i].x, landmarks[i].y] for i in range(0, 468//2)])
    right_points = np.array([[1-landmarks[i].x, landmarks[i].y] for i in range(468//2, 468)])
    features["face"]["symmetry"] = float(np.mean(np.linalg.norm(left_points - right_points, axis=1)))
    
    # Add motion metrics if available
    if metrics is not None:
        motion_features = metrics.calculate_motion_metrics(features)
        if motion_features:
            features["head"]["motion"].update(motion_features.get("head_motion", {}))
    
    return features


def sample_frames(
    video_path: str, 
    start: float, 
    end: float, 
    frame_interval: int = 30  # Sample every Nth frame
) -> List[Tuple[float, np.ndarray]]:
    """
    Sample frames from video between start and end times.
    
    Args:
        video_path: Path to video file
        start: Start time in seconds
        end: End time in seconds
        frame_interval: Sample every Nth frame
        
    Returns:
        List of tuples (timestamp, frame)
    """
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    
    # Calculate start and end frame numbers
    start_frame = int(start * video_fps)
    end_frame = int(end * video_fps)
    
    # Sample frames at regular intervals
    for frame_idx in range(start_frame, end_frame, frame_interval):
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        
        ret, frame = cap.read()
        if ret:
            # Calculate time for this frame
            time = frame_idx / video_fps
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append((time, frame_rgb))
    
    cap.release()
    return frames

def convert_numpy_in_dict(obj):
    if isinstance(obj, dict):
        return {key: convert_numpy_in_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_in_dict(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert arrays to lists
    else:
        return obj



def process_video_segments(text_transcript: dict, video_path: str, frame_interval: int = 30) -> Dict:
    """
    Process video segments and extract visual information.
    
    Args:
        json_path: Path to input JSON file
        video_path: Path to video file
        frame_interval: Sample every Nth frame
        
    Returns:
        Updated JSON text_transcript with visual information
    """
    
    # Initialize video capture to get properties
    video_fps = text_transcript['video_metadata']['fps']
    frame_width = text_transcript['video_metadata']['frame_width']
    frame_height = text_transcript['video_metadata']['frame_height']
    
    # Initialize metrics calculator
    metrics = FaceMetrics(frame_width, frame_height, video_fps)
    processed_segments = []
    
    # Process each segment
    for segment in tqdm(text_transcript['segments'], desc="Processing segments"):
        processed_segment = {
            'start': float(segment['start']),
            'end': float(segment['end']),
            'text': segment['text'],
            'duration': float(segment['end'] - segment['start'])
        }
        
        visual_info = []
        frames = sample_frames(video_path, segment['start'], segment['end'], frame_interval)
        
        if frames:   
            # Process all frames for face features
            for frame_time, frame in frames:
                face_features = extract_face_features(frame, metrics)
                frame_info = {
                    "frame_time": float(frame_time),
                    "face_features": face_features
                }
                visual_info.append(frame_info)
        
        processed_segment['visual_info'] = visual_info
        processed_segments.append(processed_segment)
    
    final_dict =  {
        'segments': processed_segments,
        'metadata': {
            'total_segments': len(processed_segments),
            'frame_interval': frame_interval,
            'video_properties': {
                'width': frame_width,
                'height': frame_height,
                'fps': float(video_fps)
            }
        }
    }
    final_dict = convert_numpy_in_dict(final_dict)
    return final_dict

if __name__ == "__main__":
    
    input_json = r'C:\video_analysis\code\video_analysis_saas\media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\text_transcript.json'
    video_path = r"C:\video_analysis\code\video_analysis_saas\media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\original.webm"
    with open(input_json, 'r', encoding='utf-8') as f:
        text_transcript = json.load(f)
    images_text_transcript = process_video_segments(text_transcript, video_path)
    import json
    output_json = "enriched_transcript.json"

    def convert(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_)):
            return bool(o)
        return str(o)  # fallback for unsupported types

    with open(r'media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\images_text_transcript.json', 'w', encoding='utf-8') as f:
        json.dump(images_text_transcript, f, indent=2, ensure_ascii=False, default=convert)
