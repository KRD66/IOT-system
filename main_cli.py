import os
import pickle
import numpy as np
import librosa
import speech_recognition as sr
from datetime import datetime

# Constants
DATA_DIR = "data"
ENROLLED_FILE = os.path.join(DATA_DIR, "enrolled_voices.pkl")
LOG_FILE = os.path.join(DATA_DIR, "access_log.txt")
REQUIRED_PHRASE = "open the door"
ADMIN_PASSWORD = "admin123"  # Change this later!

# Create data folder if not exists
os.makedirs(DATA_DIR, exist_ok=True)

# Load/save enrolled users
def load_enrolled():
    if os.path.exists(ENROLLED_FILE):
        with open(ENROLLED_FILE, 'rb') as f:
            return pickle.load(f)
    return {}  # username -> list of MFCC features

def save_enrolled(enrolled):
    with open(ENROLLED_FILE, 'wb') as f:
        pickle.dump(enrolled, f)

# Log access
def log_access(username, success):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "GRANTED" if success else "DENIED"
    user = username if username else "Unknown"
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} | User: {user} | Access: {status}\n")
    print(f"[{timestamp}] Access {status} for {user}")

# Extract MFCC features (mean vector)
def extract_features(audio_data, sample_rate=16000):
    try:
        audio_array = np.frombuffer(audio_data, np.int16).astype(np.float32) / 32768.0
        mfcc = librosa.feature.mfcc(y=audio_array, sr=sample_rate, n_mfcc=13)
        return np.mean(mfcc, axis=1)
    except Exception as e:
        print("Feature extraction error:", e)
        return None

# Compare voice (cosine similarity)
def voice_match(stored_features, new_feature, threshold=0.75):
    if new_feature is None:
        return False
    similarities = []
    for stored in stored_features:
        dot = np.dot(stored, new_feature)
        norm = np.linalg.norm(stored) * np.linalg.norm(new_feature)
        sim = dot / norm if norm != 0 else 0
        similarities.append(sim)
    return max(similarities) > threshold if similarities else False

# Record audio
def record_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening... Speak now!")
        print(f"(Say: '{REQUIRED_PHRASE}')")
        audio = r.listen(source, timeout=10, phrase_time_limit=10)
    return audio

# Main functions
def admin_login():
    password = input("Enter admin password: ")
    return password == ADMIN_PASSWORD

def enroll_user(enrolled):
    username = input("Enter new username: ").strip()
    if not username:
        return

    print(f"\nEnrolling {username}. Please say the phrase '{REQUIRED_PHRASE}' 3 times clearly.\n")
    features = []
    r = sr.Recognizer()

    for i in range(3):
        audio = record_audio()
        try:
            text = r.recognize_google(audio).lower()
            if REQUIRED_PHRASE not in text:
                print(f"✗ Wrong phrase. You said: '{text}'")
                print("Enrollment failed.\n")
                return
            print(f"✓ Phrase correct ({i+1}/3)")
        except sr.UnknownValueError:
            print("✗ Could not understand audio.")
            return

        feature = extract_features(audio.get_wav_data())
        if feature is not None:
            features.append(feature)
            print(f"✓ Voice sample {i+1}/3 recorded\n")
        else:
            print("✗ Error processing voice sample\n")
            return

    enrolled[username] = features
    save_enrolled(enrolled)
    print(f"✓ {username} enrolled successfully!\n")
    log_access("Admin", True)  # Log admin action

def try_unlock(enrolled):
    print("\n=== Unlock Attempt ===")
    audio = record_audio()

    # Check phrase
    r = sr.Recognizer()
    try:
        spoken = r.recognize_google(audio).lower()
        if REQUIRED_PHRASE not in spoken:
            print(f"✗ Wrong phrase! You said: '{spoken}'")
            log_access("Unknown", False)
            return
        print("✓ Phrase correct")
    except sr.UnknownValueError:
        print("✗ Could not understand audio")
        log_access("Unknown", False)
        return

    # Check voice
    feature = extract_features(audio.get_wav_data())
    matched_user = None
    for username, features in enrolled.items():
        if voice_match(features, feature):
            matched_user = username
            break

    if matched_user:
        print(f"✓ Voice matched! Welcome, {matched_user}!")
        log_access(matched_user, True)
    else:
        print("✗ Voice not recognized")
        log_access("Unknown", False)

# Main menu
def main():
    enrolled = load_enrolled()
    print("Voice Access Control System (CLI Version)")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("1. Admin: Enroll new user")
        print("2. Unlock with voice")
        print("3. View recent logs")
        print("4. Exit")
        
        choice = input("\nChoose an option (1-4): ").strip()

        if choice == "1":
            print("\n--- Admin Mode ---")
            if admin_login():
                print("✓ Admin authenticated")
                enroll_user(enrolled)
                enrolled = load_enrolled()  # Refresh
            else:
                print("✗ Wrong password\n")
        
        elif choice == "2":
            try_unlock(enrolled)
        
        elif choice == "3":
            print("\n--- Recent Access Logs ---")
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    lines = f.readlines()[-10:]  # Last 10
                    for line in lines:
                        print(line.strip())
            else:
                print("No logs yet.")
        
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()