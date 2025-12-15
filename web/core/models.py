import os
import pickle
import numpy as np
import librosa
from datetime import datetime
from django.conf import settings

REQUIRED_PHRASE = "open the door"
ADMIN_PASSWORD = "admin123"  # CHANGE THIS!

def load_enrolled():
    if os.path.exists(settings.ENROLLED_FILE):
        with open(settings.ENROLLED_FILE, 'rb') as f:
            return pickle.load(f)
    return {}

def save_enrolled(enrolled):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    with open(settings.ENROLLED_FILE, 'wb') as f:
        pickle.dump(enrolled, f)

def log_access(username, success):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "GRANTED" if success else "DENIED"
    user = username if username else "Unknown"
    with open(settings.LOG_FILE, 'a') as f:
        f.write(f"{timestamp} | User: {user} | Access: {status}\n")

def extract_features(wav_bytes):
    try:
        audio_array = np.frombuffer(wav_bytes, np.int16).astype(np.float32) / 32768.0
        mfcc = librosa.feature.mfcc(y=audio_array, sr=16000, n_mfcc=13)
        return np.mean(mfcc, axis=1)
    except:
        return None

def voice_match(stored_features, new_feature, threshold=0.75):
    if new_feature is None:
        return False, None
    similarities = []
    for stored in stored_features:
        dot = np.dot(stored, new_feature)
        norm = np.linalg.norm(stored) * np.linalg.norm(new_feature)
        sim = dot / norm if norm != 0 else 0
        similarities.append(sim)
    if similarities:
        max_sim = max(similarities)
        if max_sim > threshold:
            return True, max_sim
    return False, 0