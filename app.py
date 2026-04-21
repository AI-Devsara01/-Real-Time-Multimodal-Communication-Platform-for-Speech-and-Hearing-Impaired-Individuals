"""
CommuniSense - Real-Time Multimodal Communication Platform
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, send_from_directory
from flask_cors import CORS
import os
import json
import base64
import tempfile
import time
import uuid
import hashlib
import re
from datetime import datetime
from io import BytesIO

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "communisense_secret_2024"
CORS(app)

# ============================================
# SIMPLE FILE-BASED STORAGE
# ============================================

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

USERS = load_users()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# ============================================
# AUTH ROUTES
# ============================================

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login_page"))

@app.route("/login")
def login_page():
    return send_file("templates/login.html")

@app.route("/signup")
def signup_page():
    return send_file("templates/signup.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login_page"))
    return send_file("templates/dashboard.html")

@app.route("/api/signup", methods=["POST"])
def api_signup():
    global USERS
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        
        if not username or not password or not email:
            return jsonify({"success": False, "error": "All fields required"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        
        USERS = load_users()
        
        if username in USERS:
            return jsonify({"success": False, "error": "Username already taken"}), 409
        
        for existing_user in USERS.values():
            if existing_user.get('email') == email:
                return jsonify({"success": False, "error": "Email already registered"}), 409
        
        USERS[username] = {
            "password": hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "stats": {"detections": 0, "games": 0}
        }
        
        save_users(USERS)
        
        session["username"] = username
        
        return jsonify({"success": True, "username": username})
        
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        USERS = load_users()
        
        if username not in USERS:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        if not verify_password(password, USERS[username]["password"]):
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        session["username"] = username
        
        return jsonify({"success": True, "username": username})
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/current_user", methods=["GET"])
def api_current_user():
    if "username" in session:
        return jsonify({"username": session["username"]})
    return jsonify({"username": None}), 401

# ============================================
# FEATURE PAGE ROUTES
# ============================================

@app.route("/tts")
def tts_page():
    return send_file("templates/tts.html")

@app.route("/stt")
def stt_page():
    return send_file("templates/stt.html")

@app.route("/word_recog")
def word_recog_page():
    return send_file("templates/word_recog.html")

@app.route("/letter_recog")
def letter_recog_page():
    return send_file("templates/letter_recog.html")

@app.route("/number_recog")
def number_recog_page():
    return send_file("templates/number_recog.html")

@app.route("/games")
def games_page():
    return send_file("templates/games.html")

@app.route("/image_gen")
def image_gen_page():
    return send_file("templates/image_gen.html")

@app.route("/emotion_translate")
def emotion_translate_page():
    return send_file("templates/emotion_translate.html")

@app.route("/visual_alert")
def visual_alert_page():
    return send_file("templates/visual_alert.html")

@app.route("/sign_dictionary")
def sign_dictionary_page():
    return send_file("templates/sign_dictionary.html")

@app.route("/mood_journal")
def mood_journal_page():
    return send_file("templates/mood_journal.html")

@app.route("/communication_cards")
def communication_cards_page():
    return send_file("templates/communication_cards.html")

@app.route("/lip_sync")
def lip_sync_redirect():
    return redirect(url_for("communication_cards_page"))

# ============================================
# STATIC FILES
# ============================================

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ============================================
# API ENDPOINTS
# ============================================

@app.route("/api/tts", methods=["POST"])
def api_tts():
    try:
        from gtts import gTTS
        
        data = request.json
        text = data.get("text", "")
        lang = data.get("lang", "en")
        
        if not text:
            return jsonify({"error": "No text provided", "success": False}), 400
        
        tts = gTTS(text=text, lang=lang, slow=False)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_b64 = base64.b64encode(mp3_fp.read()).decode()
        
        return jsonify({"audio": audio_b64, "success": True})
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/api/stt", methods=["POST"])
def api_stt():
    try:
        import speech_recognition as sr
        lang = request.form.get("lang", "en-US")
        if "audio" not in request.files:
            return jsonify({"error": "No audio file"}), 400
        audio_file = request.files["audio"]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        audio_file.save(tmp.name)
        r = sr.Recognizer()
        with sr.AudioFile(tmp.name) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language=lang)
        os.unlink(tmp.name)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/image_gen", methods=["POST"])
def api_image_gen():
    try:
        import requests as req
        data = request.json
        prompt = data.get("prompt", "")
        if not prompt:
            return jsonify({"error": "No prompt"}), 400
        API_URL = "https://image.sarafathima3700.workers.dev"
        API_KEY = "12345678"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        resp = req.post(API_URL, headers=headers, json={"prompt": prompt}, timeout=90)
        if resp.status_code == 200:
            img_b64 = base64.b64encode(resp.content).decode()
            return jsonify({"image": img_b64, "format": "jpeg", "success": True})
        return jsonify({"error": f"Worker error {resp.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/translate", methods=["POST"])
def api_translate():
    try:
        from deep_translator import GoogleTranslator
        data = request.json
        text = data.get("text", "")
        src = data.get("src", "auto")
        dest = data.get("dest", "hi")
        result = GoogleTranslator(source=src, target=dest).translate(text)
        return jsonify({"translated": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    print("=" * 50)
    print("🚀 CommuniSense Backend Starting...")
    print("=" * 50)
    print("📁 Templates folder: templates/")
    print("📁 Static folder: static/")
    print("🌐 Visit: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
