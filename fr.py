import os
import face_recognition
import pickle

DATASET_DIR = "face_dataset"
ENCODINGS_FILE = "encodings/encodings.pkl"

def build_encodings():
    known_encodings = []
    known_ids = []

    for user_id in os.listdir(DATASET_DIR):
        user_folder = os.path.join(DATASET_DIR, user_id)
        if not os.path.isdir(user_folder):
            continue

        for img_name in os.listdir(user_folder):
            img_path = os.path.join(user_folder, img_name)
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)

            if len(encodings) > 0:
                known_encodings.append(encodings[0])
                known_ids.append(user_id)

    data = {"encodings": known_encodings, "ids": known_ids}
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)
    print("Encodings updated successfully.")
