import os
import pickle
import numpy as np
import librosa
from datetime import datetime
from django.conf import settings

REQUIRED_PHRASE = "open the door"  # Fixed phrase for all
ADMIN_PASSWORD = "admin123"  # CHANGE THIS IN PRODUCTION!

def load_enrolled():
    if os.path.exists(settings.ENROLLED_FILE):
        with open(settings.ENROLLED_FILE, 'rb') as f:
            return pickle.load(f)
    return {}  # username -> {'details': {'full_name': str, 'email': str, 'role': str}, 'features': list of MFCC}

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

def get_user_entry_count(username):
    if os.path.exists(settings.LOG_FILE):
        count = 0
        with open(settings.LOG_FILE, 'r') as f:
            for line in f:
                if f"User: {username} | Access: GRANTED" in line:
                    count += 1
        return count
    return 0

from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path

encoder = VoiceEncoder()

def extract_features(wav_bytes):
    try:
        # Convert bytes to wav file temporarily or use numpy
        from io import BytesIO
        import wave
        import numpy as np
        
        # Load wav from bytes
        with BytesIO(wav_bytes) as wav_io:
            with wave.open(wav_io, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Preprocess and get embedding
        preprocessed_wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(preprocessed_wav)
        return embedding
    except Exception as e:
        print("Embedding error:", e)
        return None

def voice_match(stored_features, new_feature, threshold=0.75):
    if new_feature is None:
        return False, 0
    similarities = [np.dot(stored, new_feature) for stored in stored_features]  # Cosine similarity (embeddings are normalized)
    max_sim = max(similarities) if similarities else 0
    return max_sim > threshold, max_sim

