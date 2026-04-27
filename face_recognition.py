# # attendance_system/ai_modules/face_recognition.py
# import os
# import face_recognition
# import pickle
# from pathlib import Path
# import numpy as np

# DATA_DIR = Path(__file__).resolve().parents[1] / "face_dataset"
# ENCODINGS_FILE = DATA_DIR / "encodings.pkl"

# # Ensure dataset dir exists
# DATA_DIR.mkdir(parents=True, exist_ok=True)

# def enroll_user(user_id: str, image_paths: list):
#     """
#     Save provided face images into dataset folder and update encodings.
#     image_paths: list of file paths (or paths from Flask upload) containing an image with user's face.
#     """
#     user_dir = DATA_DIR / user_id
#     user_dir.mkdir(exist_ok=True)
#     for i, img_path in enumerate(image_paths):
#         ext = os.path.splitext(img_path)[1] or ".jpg"
#         dest = user_dir / f"{user_id}_{i}{ext}"
#         # If path is already in dataset or uploaded copy, copy it; for simplicity assume direct file path given
#         if os.path.abspath(img_path) != str(dest):
#             with open(img_path, "rb") as rf, open(dest, "wb") as wf:
#                 wf.write(rf.read())
#     # After saving images, rebuild encodings
#     build_encodings()

# def build_encodings():
#     """
#     Walk the face_dataset folder, compute face encodings and save to encodings.pkl
#     Format saved: {"user_id": [enc1, enc2, ...], ...}
#     """
#     encodings = {}
#     for user_dir in DATA_DIR.iterdir():
#         if not user_dir.is_dir(): continue
#         user_id = user_dir.name
#         encs = []
#         for img_file in user_dir.iterdir():
#             try:
#                 img = face_recognition.load_image_file(str(img_file))
#                 faces = face_recognition.face_encodings(img)
#                 if faces:
#                     encs.append(faces[0])
#             except Exception as e:
#                 print("Error encoding", img_file, e)
#         if encs:
#             encodings[user_id] = encs
#     # Save
#     with open(ENCODINGS_FILE, "wb") as f:
#         pickle.dump(encodings, f)

# def load_encodings():
#     if not ENCODINGS_FILE.exists():
#         return {}
#     with open(ENCODINGS_FILE, "rb") as f:
#         return pickle.load(f)

# def recognize_faces_in_frame(frame, tolerance=0.5):
#     """
#     Input: BGR frame (OpenCV)
#     Returns list of dicts: [{'user_id': 'bob', 'location': (top,right,bottom,left), 'distance': 0.36}, ...]
#     """
#     rgb = frame[:, :, ::-1]
#     encodings_db = load_encodings()
#     if not encodings_db:
#         return []

#     known_encs = []
#     known_ids = []
#     for uid, encs in encodings_db.items():
#         for e in encs:
#             known_encs.append(e)
#             known_ids.append(uid)
#     if not known_encs:
#         return []

#     face_locations = face_recognition.face_locations(rgb)
#     face_encodings = face_recognition.face_encodings(rgb, face_locations)
#     results = []
#     for loc, enc in zip(face_locations, face_encodings):
#         distances = face_recognition.face_distance(known_encs, enc)
#         best_idx = np.argmin(distances)
#         best_distance = float(distances[best_idx])
#         if best_distance <= tolerance:
#             matched_id = known_ids[best_idx]
#             results.append({"user_id": matched_id, "location": loc, "distance": best_distance})
#     return results



#NEW CODE GOES BELOW:
import os
import glob
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

import numpy as np
import cv2
import face_recognition

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "face_dataset"
ENCODINGS_FILE = BASE_DIR / "encodings" / "encodings.pkl"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(ENCODINGS_FILE.parent).mkdir(parents=True, exist_ok=True)

# Cache for performance
_CACHE = {
    "mt": None,           # modification time of encodings.pkl
    "ids": [],
    "encodings": []
}

# -----------------------
# Utility Functions
# -----------------------

def _load_encodings_from_disk():
    """Load encodings.pkl into memory if present."""
    if not ENCODINGS_FILE.exists():
        _CACHE.update({"mt": None, "ids": [], "encodings": []})
        return

    mt = os.path.getmtime(ENCODINGS_FILE)
    if _CACHE["mt"] == mt:
        return  # cache up-to-date

    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)

    _CACHE["mt"] = mt
    _CACHE["ids"] = data.get("ids", [])
    _CACHE["encodings"] = data.get("encodings", [])


def enroll_user(user_id: str, image_paths: list):
    """
    Save provided face images into dataset folder and update encodings.
    image_paths: list of file paths containing an image with user's face.
    """
    user_dir = DATA_DIR / user_id
    user_dir.mkdir(exist_ok=True)
    for i, img_path in enumerate(image_paths):
        ext = os.path.splitext(img_path)[1] or ".jpg"
        dest = user_dir / f"{user_id}_{i}{ext}"
        if os.path.abspath(img_path) != str(dest):
            with open(img_path, "rb") as rf, open(dest, "wb") as wf:
                wf.write(rf.read())
    build_encodings()


def build_encodings() -> Tuple[int, int]:
    """
    Scan face_dataset/<user_id>/* images, compute encodings, and save to ENCODINGS_FILE.
    Returns (num_users, num_images_encoded).
    """
    all_encodings = []
    all_ids = []

    num_users = 0
    num_images = 0

    for user_dir in DATA_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        user_id = user_dir.name
        num_users += 1

        image_paths = []
        for pattern in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
            image_paths.extend(glob.glob(str(user_dir / pattern)))

        for img_path in image_paths:
            image = cv2.imread(img_path)
            if image is None:
                continue
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")  # "cnn" if GPU available
            encs = face_recognition.face_encodings(rgb, boxes)
            for enc in encs:
                all_encodings.append(enc)
                all_ids.append(user_id)
                num_images += 1

    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump({"ids": all_ids, "encodings": all_encodings}, f)

    # update cache
    _CACHE.update({
        "mt": os.path.getmtime(ENCODINGS_FILE) if ENCODINGS_FILE.exists() else None,
        "ids": all_ids,
        "encodings": all_encodings
    })

    return num_users, num_images


def load_encodings():
    """
    Load encodings into cache and return dict-like { 'ids': [...], 'encodings': [...] }
    """
    _load_encodings_from_disk()
    return {"ids": _CACHE["ids"], "encodings": _CACHE["encodings"]}


def recognize_faces_in_frame(frame, tolerance: float = 0.5) -> List[Dict]:
    """
    Input: BGR frame (OpenCV)
    Output: list of dicts
    [{'user_id': 'bob', 'location': (top,right,bottom,left), 'distance': 0.36}, ...]
    """
    _load_encodings_from_disk()
    known_encodings = _CACHE["encodings"]
    known_ids = _CACHE["ids"]

    if not known_encodings:
        return []

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model="hog")
    encs = face_recognition.face_encodings(rgb, boxes)

    results = []
    for enc, (top, right, bottom, left) in zip(encs, boxes):
        distances = face_recognition.face_distance(known_encodings, enc)
        if len(distances) == 0:
            continue
        best_idx = int(np.argmin(distances))
        best_distance = float(distances[best_idx])
        if best_distance <= tolerance:
            results.append({
                "user_id": known_ids[best_idx],
                "location": (top, right, bottom, left),
                "distance": best_distance
            })

    return results
