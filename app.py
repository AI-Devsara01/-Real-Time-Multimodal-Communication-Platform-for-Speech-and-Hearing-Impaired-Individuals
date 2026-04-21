"""
CommuniSense - Real-Time Multimodal Communication Platform
With MongoDB Data Storage
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import os, json, base64, tempfile, time, uuid, hashlib, re
from datetime import datetime
from io import BytesIO
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "communisense_secret_2024"
CORS(app)

# ============================================
# MONGODB CONNECTION
# ============================================

# Get connection string from environment variable (Render) or use default
MONGODB_URI = os.environ.get('MONGODB_URI', "mongodb+srv://sara_db_user:sara123@cluster0.hhaghbf.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = "communisense"

# Initialize collections
users_collection = None
activity_collection = None

try:
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB ping successful!")
    
    # Get database
    db = client[DB_NAME]
    users_collection = db['users']
    activity_collection = db['activity_log']
    
    # Create indexes for unique usernames and emails
    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)
    
    print(f"✅ MongoDB Connected Successfully!")
    print(f"📁 Database: {DB_NAME}")
    print(f"📁 Users collection: {users_collection.count_documents({})} users")
    
except Exception as e:
    print(f"❌ MongoDB Error: {e}")
    print("⚠️ Please check:")
    print("   1. IP whitelist in MongoDB Atlas (add 0.0.0.0/0)")
    print("   2. Environment variable MONGODB_URI is set correctly")

# ============================================
# HELPER FUNCTIONS
# ============================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def log_activity(user_id, activity_type, details):
    """Log user activity to MongoDB"""
    if activity_collection:
        try:
            activity_collection.insert_one({
                'user_id': user_id,
                'type': activity_type,
                'details': details,
                'timestamp': datetime.now()
            })
        except:
            pass

# ============================================
# AUTH ROUTES
# ============================================

@app.route("/")
def index():
    if "user_id" in session:
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
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return send_file("templates/dashboard.html")

@app.route("/api/signup", methods=["POST"])
def api_signup():
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        
        # Validation
        if not username or not password or not email:
            return jsonify({"success": False, "error": "All fields required"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        
        # Check if MongoDB is connected
        if users_collection is None:
            return jsonify({"success": False, "error": "Database not connected. Please try again later."}), 500
        
        # Check if user exists
        existing_user = users_collection.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            if existing_user['username'] == username:
                return jsonify({"success": False, "error": "Username already taken"}), 409
            else:
                return jsonify({"success": False, "error": "Email already registered"}), 409
        
        # Create new user
        user = {
            'username': username,
            'password': hash_password(password),
            'email': email,
            'created_at': datetime.now(),
            'last_login': None,
            'stats': {
                'total_detections': 0,
                'games_played': 0,
                'words_learned': 0
            }
        }
        
        result = users_collection.insert_one(user)
        
        # Log activity
        log_activity(str(result.inserted_id), 'signup', f'User {username} signed up')
        
        # Create session
        session['user_id'] = str(result.inserted_id)
        session['username'] = username
        
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
        
        # Check if MongoDB is connected
        if users_collection is None:
            return jsonify({"success": False, "error": "Database not connected. Please try again later."}), 500
        
        # Find user
        user = users_collection.find_one({"username": username})
        
        if not user:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        # Verify password
        if not verify_password(password, user['password']):
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        # Update last login
        users_collection.update_one(
            {"_id": user['_id']},
            {"$set": {"last_login": datetime.now()}}
        )
        
        # Log activity
        log_activity(str(user['_id']), 'login', f'User {username} logged in')
        
        # Create session
        session['user_id'] = str(user['_id'])
        session['username'] = username
        
        return jsonify({"success": True, "username": username})
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def api_logout():
    if 'user_id' in session:
        log_activity(session['user_id'], 'logout', f'User {session["username"]} logged out')
    session.clear()
    return jsonify({"success": True})

@app.route("/api/current_user", methods=["GET"])
def api_current_user():
    if 'user_id' in session:
        return jsonify({
            "username": session['username'],
            "user_id": session['user_id']
        })
    return jsonify({"username": None}), 401

@app.route("/api/user/stats", methods=["GET"])
def api_user_stats():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
        if user:
            return jsonify({
                "stats": user.get('stats', {}),
                "joined": user.get('created_at', datetime.now()).strftime("%Y-%m-%d"),
                "last_login": user.get('last_login', datetime.now()).strftime("%Y-%m-%d %H:%M") if user.get('last_login') else "Never"
            })
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# FEATURE PAGE ROUTES
# ============================================

@app.route("/tts")
def tts_page():
    return render_template("tts.html")

@app.route("/stt")
def stt_page():
    return render_template("stt.html")

@app.route("/word_recog")
def word_recog_page():
    return render_template("word_recog.html")

@app.route("/letter_recog")
def letter_recog_page():
    return render_template("letter_recog.html")

@app.route("/number_recog")
def number_recog_page():
    return render_template("number_recog.html")

@app.route("/games")
def games_page():
    return render_template("games.html")

@app.route("/image_gen")
def image_gen_page():
    return render_template("image_gen.html")

@app.route("/emotion_translate")
def emotion_translate_page():
    return render_template("emotion_translate.html")

@app.route("/visual_alert")
def visual_alert_page():
    return render_template("visual_alert.html")

@app.route("/sign_dictionary")
def sign_dictionary_page():
    return render_template("sign_dictionary.html")

@app.route("/mood_journal")
def mood_journal_page():
    return render_template("mood_journal.html")

@app.route("/communication_cards")
def communication_cards_page():
    return render_template("communication_cards.html")

@app.route("/lip_sync")
def lip_sync_redirect():
    return redirect(url_for("communication_cards_page"))

# ============================================
# API ENDPOINTS (TTS, STT, etc.)
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
    print("=" * 50)
    print("🚀 CommuniSense Backend Starting...")
    print("=" * 50)
    print("📁 Database: MongoDB - communisense")
    print("🌐 Visit: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
