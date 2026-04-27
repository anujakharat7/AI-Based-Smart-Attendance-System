# attendance_system/ai_modules/liveness_detection.py
import cv2
import numpy as np
import dlib
from scipy.spatial import distance as dist

# You need shape_predictor_68_face_landmarks.dat -> download manually and place path here
SHAPE_PREDICTOR_PATH = "c:/Users/viraj/Downloads/attendance_system/attendance_system/models/shape_predictor_68_face_landmarks.dat"

detector = dlib.get_frontal_face_detector()
predictor = None
try:
    predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
except Exception as e:
    print("dlib predictor not found; liveness blink detection won't work until you download the model:", e)

# Eye aspect ratio helper
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    eps = 1e-6
    return (A + B) / (2.0 * (C + eps))

# Indexes for 68-landmark model
LEFT_EYE_IDX = list(range(36, 42))
RIGHT_EYE_IDX = list(range(42, 48))

# Simple blink detector: count frames with EAR < threshold
EAR_THRESHOLD = 0.22
CONSEC_FRAMES = 2

class BlinkDetector:
    def __init__(self):
        self.counter = 0
        self.blinks = 0

    def process(self, gray_frame, rect):
        """
        rect: dlib rectangle or (top,right,bottom,left)
        returns True if blink detected recently (i.e., we saw a blink)
        """
        if predictor is None:
            return False
        if isinstance(rect, tuple):
            top, right, bottom, left = rect
            rect_dlib = dlib.rectangle(left, top, right, bottom)
        else:
            rect_dlib = rect

        shape = predictor(gray_frame, rect_dlib)
        coords = []
        for i in range(0,68):
            coords.append((shape.part(i).x, shape.part(i).y))
        leftEye = [coords[i] for i in LEFT_EYE_IDX]
        rightEye = [coords[i] for i in RIGHT_EYE_IDX]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0

        if ear < EAR_THRESHOLD:
            self.counter += 1
        else:
            if self.counter >= CONSEC_FRAMES:
                self.blinks += 1
                self.counter = 0
                return True
            self.counter = 0
        return False
