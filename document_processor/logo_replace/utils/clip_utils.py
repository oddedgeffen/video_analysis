import torch
import clip
from PIL import Image
import io
import cv2
import numpy as np
from functools import lru_cache
import gc

@lru_cache(maxsize=1)
def get_clip_model():
    """
    Load and return the CLIP model and preprocessing function.
    Returns:
        tuple: (model, preprocess) - CLIP model and preprocessing function
    """
    print("Loading CLIP model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Disable JIT on CPU to reduce memory usage
    use_jit = True if device == "cuda" else False
    model, preprocess = clip.load("ViT-B/32", device=device, jit=use_jit)
    model.eval()  # Set to evaluation mode
    print(f"CLIP model loaded on {device}")
    return model, preprocess

def get_image_embedding(image_path_or_object, model=None, preprocess=None):
    """
    Get CLIP embedding for an image.
    
    Args:
        image_path_or_object: Path to image or PIL Image object
        model: CLIP model (if None, will load a new model)
        preprocess: CLIP preprocessing function (if None, will load with model)
        device: Device to run the model on
    Returns:
        torch.Tensor: Image embedding
    """
    if model is None or preprocess is None:
        model, preprocess = get_clip_model()
    
    # Handle different input types
    image = None
    try:
        if isinstance(image_path_or_object, str):
            # Load image from path
            image = Image.open(image_path_or_object)
        elif isinstance(image_path_or_object, bytes):
            # Load image from bytes
            image = Image.open(io.BytesIO(image_path_or_object))
        elif isinstance(image_path_or_object, Image.Image):
            # Use provided PIL Image
            image = image_path_or_object
        else:
            raise ValueError("Unsupported image type")
        
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Preprocess and get embedding
        # Determine the device (same logic as model loading)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            # Detach and clone to ensure we can free the input tensor
            image_features = image_features.detach().clone()
        
        # Free memory
        del image_input
        
        return image_features
    
    finally:
        # Free memory from loaded images
        if image and isinstance(image, Image.Image):
            image.close()
        # Run garbage collection to free memory
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

def is_similar_to_target(image_path_or_object, target_embedding, model=None, preprocess=None, threshold=0.93):
    """
    Compare an image to a target embedding and determine if they're similar.
    
    Args:
        image_path_or_object: Path to image or PIL Image object
        target_embedding: CLIP embedding of target image
        model: CLIP model (if None, will load a new model)
        preprocess: CLIP preprocessing function (if None, will load with model)
        threshold: Similarity threshold (0-1)
    
    Returns:
        tuple: (is_similar, similarity) - Boolean indicating similarity and the similarity score
    """
    if model is None or preprocess is None:
        model, preprocess = get_clip_model()
    
    try:
        # Get embedding for the image
        image_embedding = get_image_embedding(image_path_or_object, model, preprocess)
        
        # Normalize embeddings
        image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)
        target_embedding = target_embedding / target_embedding.norm(dim=-1, keepdim=True)
        
        # Calculate cosine similarity
        similarity = (100 * image_embedding @ target_embedding.T).item() / 100
        
        return similarity >= threshold, similarity
    finally:
        # Run garbage collection to free memory
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

def compute_similarity(text_features, image_features):
    return (text_features @ image_features.T).squeeze()

def filter_boxes_by_iou_and_enclosure(raw_boxes, iou_thresh):
    kept = []
    used = [False] * len(raw_boxes)

    for i, b1 in enumerate(raw_boxes):
        if used[i]:
            continue

        group = [i]
        for j in range(i + 1, len(raw_boxes)):
            if used[j]:
                continue
            if iou(b1["coords"], raw_boxes[j]["coords"]) > iou_thresh:
                group.append(j)
                used[j] = True

        # Within each group, remove boxes fully enclosed in others
        filtered_group = []
        for idx in group:
            boxA = raw_boxes[idx]
            x1a, y1a, x2a, y2a = boxA["coords"]
            enclosed = False
            for jdx in group:
                if idx == jdx:
                    continue
                boxB = raw_boxes[jdx]
                x1b, y1b, x2b, y2b = boxB["coords"]
                if x1b <= x1a and y1b <= y1a and x2b >= x2a and y2b >= y2a:
                    enclosed = True
                    break
            if not enclosed:
                filtered_group.append(boxA)

        # Keep only the biggest box from filtered group
        if filtered_group:
            best = max(filtered_group, key=lambda b: b["area"])
            kept.append(best)
        used[i] = True

    return kept

def iou(b1, b2):
    xa = max(b1[0], b2[0])
    ya = max(b1[1], b2[1])
    xb = min(b1[2], b2[2])
    yb = min(b1[3], b2[3])

    inter_area = max(0, xb - xa) * max(0, yb - ya)
    box1_area = (b1[2] - b1[0]) * (b1[3] - b1[1])
    box2_area = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area if union_area > 0 else 0

def encode_text(text):
    model, _ = get_clip_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    with torch.no_grad():
        text_token = clip.tokenize([text]).to(device)
        text_features = model.encode_text(text_token)
        return text_features.cpu().numpy()

def encode_image(image):
    model, preprocess = get_clip_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    with torch.no_grad():
        image_input = preprocess(image).unsqueeze(0).to(device)
        image_features = model.encode_image(image_input)
        return image_features.cpu().numpy()

