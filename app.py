"""
CommuniSense - Real-Time Multimodal Communication for Hearing & Speech Impaired
Flask Backend - All Features Integrated
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import os, json, base64, tempfile, time, uuid, hashlib, re
from datetime import datetime
from io import BytesIO
from pymongo import MongoClient
app = Flask(__name__)
# Add these imports at the top with your other imports
from pymongo import MongoClient
from bson.objectid import ObjectId
app.secret_key = "communisense_secret_2024"
CORS(app)
from functools import wraps
from bson.objectid import ObjectId
# ============================================
# MONGODB ATLAS CONNECTION - COMMUNISENSE DATABASE
# ============================================

# Your connection string with correct password
MONGODB_URI = "mongodb+srv://sara_db_user:sara123@cluster0.hhaghbf.mongodb.net/?retryWrites=true&w=majority"

# Database name - COMMUNISENSE
DB_NAME = "communisense"

try:
    # Connect to MongoDB Atlas
    client = MongoClient(MONGODB_URI)
    
    # Use communisense database
    db = client[DB_NAME]
    
    # Test connection
    client.admin.command('ping')
    
    # Collections
    users_collection = db['users']
    activity_collection = db['activity_log']
    mood_collection = db['mood_entries']
    
    # Create indexes for faster queries
    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)
    activity_collection.create_index("user_id")
    activity_collection.create_index("timestamp")
    
    print("=" * 50)
    print("✅ MongoDB Atlas Connected Successfully!")
    print(f"📁 Database: {DB_NAME}")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
# ══════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
#  AUTH ROUTES (FIXED - Using MongoDB)
# ══════════════════════════════════════════════

# Helper functions for password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

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

@app.route("/number_recognition")
def number_recognition():
    return send_file("templates/number_recognition.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        # Find user in MongoDB
        user = users_collection.find_one({"username": username})
        
        if user and verify_password(password, user['password']):
            session["user_id"] = str(user['_id'])
            session["username"] = username
            return jsonify({"success": True, "username": username})
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/signup", methods=["POST"])
def api_signup():
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        
        if not username or not password or not email:
            return jsonify({"success": False, "error": "All fields required"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        
        # Check if user exists
        existing = users_collection.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing:
            return jsonify({"success": False, "error": "Username or email already taken"}), 409
        
        # Create new user
        user = {
            "username": username,
            "password": hash_password(password),
            "email": email,
            "created_at": datetime.now(),
            "last_login": None,
            "stats": {"detections": 0, "games": 0}
        }
        
        result = users_collection.insert_one(user)
        session["user_id"] = str(result.inserted_id)
        session["username"] = username
        
        return jsonify({"success": True, "username": username})
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/current_user", methods=["GET"])
def api_current_user():
    if "user_id" in session:
        return jsonify({"username": session["username"], "user_id": session["user_id"]})
    return jsonify({"username": None}), 401
# ══════════════════════════════════════════════
#  FEATURE PAGE ROUTES
# ══════════════════════════════════════════════

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

# Communication Cards (replaces lip_sync)
@app.route("/communication_cards")
def communication_cards_page():
    return render_template("communication_cards.html")

# Also keep emergency_comm if you have it
@app.route("/emergency_comm")
def emergency_comm_page():
    return render_template("communication_cards.html")

# Redirect from old lip_sync URL to new one
@app.route("/lip_sync")
def lip_sync_redirect():
    return redirect(url_for("communication_cards_page"))

# ══════════════════════════════════════════════
#  TEXT-TO-SPEECH API
# ══════════════════════════════════════════════

@app.route("/api/tts", methods=["POST"])
def api_tts():
    try:
        from gtts import gTTS
        
        data = request.json
        text = data.get("text", "")
        lang = data.get("lang", "en")
        
        if not text:
            return jsonify({"error": "No text provided", "success": False}), 400
        
        print(f"🎤 Generating TTS for: {text[:50]}... in language: {lang}")
        
        tts = gTTS(text=text, lang=lang, slow=False)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_b64 = base64.b64encode(mp3_fp.read()).decode()
        
        return jsonify({"audio": audio_b64, "success": True})
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

# ══════════════════════════════════════════════
#  SPEECH-TO-TEXT API
# ══════════════════════════════════════════════

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

# ══════════════════════════════════════════════
#  IMAGE GENERATION API (FIXED)
# ══════════════════════════════════════════════

@app.route("/api/image_gen", methods=["POST"])
def api_image_gen():
    try:
        import requests as req
        
        data = request.json
        prompt = data.get("prompt", "")
        
        if not prompt:
            return jsonify({"success": False, "error": "No prompt provided"}), 400
        
        API_URL = "https://image.sarafathima3700.workers.dev"
        API_KEY = "12345678"
        
        headers = {
            "Authorization": f"Bearer {API_KEY}", 
            "Content-Type": "application/json"
        }
        
        print(f"🎨 Generating image for prompt: {prompt[:50]}...")
        
        # Send request to worker with longer timeout
        resp = req.post(API_URL, headers=headers, json={"prompt": prompt}, timeout=90)
        
        if resp.status_code == 200:
            # Check if response is JSON or binary
            content_type = resp.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                # Worker returned JSON with base64 image
                response_data = resp.json()
                if 'image' in response_data:
                    print("✅ Image generated successfully (JSON response)")
                    return jsonify({
                        "success": True,
                        "image": response_data['image'],
                        "format": response_data.get('format', 'jpeg')
                    })
                elif 'data' in response_data:
                    # Some APIs return data field
                    print("✅ Image generated successfully (data field)")
                    return jsonify({
                        "success": True,
                        "image": response_data['data'],
                        "format": response_data.get('format', 'jpeg')
                    })
                else:
                    print(f"❌ No image in JSON response: {response_data.keys()}")
                    return jsonify({
                        "success": False, 
                        "error": "No image in response"
                    }), 500
            else:
                # Worker returned raw image data
                print("✅ Image generated successfully (raw binary)")
                img_b64 = base64.b64encode(resp.content).decode('utf-8')
                return jsonify({
                    "success": True,
                    "image": img_b64,
                    "format": "jpeg"
                })
        else:
            # Try to parse error from JSON response
            try:
                error_data = resp.json()
                error_msg = error_data.get('error', f"Worker error {resp.status_code}")
            except:
                error_msg = f"Worker error {resp.status_code}: {resp.text[:100]}"
            
            print(f"❌ Worker error: {error_msg}")
            return jsonify({
                "success": False, 
                "error": error_msg
            }), 500
            
    except req.exceptions.Timeout:
        print("❌ Request timeout")
        return jsonify({
            "success": False, 
            "error": "Request timeout - generation taking too long. Please try again."
        }), 504
    except req.exceptions.ConnectionError:
        print("❌ Connection error")
        return jsonify({
            "success": False, 
            "error": "Connection error - unable to reach image service"
        }), 503
    except Exception as e:
        print(f"❌ Image generation error: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Generation failed: {str(e)}"
        }), 500

# ══════════════════════════════════════════════
#  TRANSLATION API
# ══════════════════════════════════════════════

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

# ══════════════════════════════════════════════
#  EMOTION TRANSLATOR
# ══════════════════════════════════════════════

EMOTION_MAP = {
    "happy": {"emoji": "😊", "color": "#FFD700", "phrase": "I am feeling happy!", "sign": "☺️"},
    "sad": {"emoji": "😢", "color": "#4169E1", "phrase": "I am feeling sad.", "sign": "😔"},
    "angry": {"emoji": "😠", "color": "#FF4500", "phrase": "I am feeling angry!", "sign": "😤"},
    "scared": {"emoji": "😨", "color": "#9B59B6", "phrase": "I am scared.", "sign": "😰"},
    "excited": {"emoji": "🤩", "color": "#FF69B4", "phrase": "I am very excited!", "sign": "🎉"},
    "confused": {"emoji": "😕", "color": "#FFA500", "phrase": "I am confused.", "sign": "🤔"},
    "tired": {"emoji": "😴", "color": "#95A5A6", "phrase": "I am tired.", "sign": "💤"},
    "loved": {"emoji": "🥰", "color": "#FF1493", "phrase": "I feel loved.", "sign": "❤️"},
    "hungry": {"emoji": "🍔", "color": "#E67E22", "phrase": "I am hungry.", "sign": "🍽️"},
    "pain": {"emoji": "🤕", "color": "#E74C3C", "phrase": "I am in pain.", "sign": "😣"},
    "help": {"emoji": "🆘", "color": "#FF0000", "phrase": "I need help!", "sign": "🙋"},
    "yes": {"emoji": "✅", "color": "#2ECC71", "phrase": "Yes!", "sign": "👍"},
    "no": {"emoji": "❌", "color": "#E74C3C", "phrase": "No!", "sign": "👎"},
    "thanks": {"emoji": "🙏", "color": "#27AE60", "phrase": "Thank you!", "sign": "🤝"},
    "sorry": {"emoji": "😞", "color": "#7F8C8D", "phrase": "I am sorry.", "sign": "🙇"},
}

KEYWORD_EMOTION = {
    "happy|joy|great|good|wonderful|amazing|love|excited|fantastic": "happy",
    "sad|unhappy|depressed|crying|miss|lonely|heartbroken": "sad",
    "angry|mad|furious|rage|hate|annoyed|frustrated": "angry",
    "scared|afraid|fear|terrified|nervous|anxious|worried": "scared",
    "excited|thrill|pumped|awesome|wow|incredible": "excited",
    "confused|lost|unsure|dont understand|what|huh": "confused",
    "tired|sleepy|exhausted|fatigue|rest": "tired",
    "love|adore|care|sweet|darling": "loved",
    "hungry|food|eat|starving|meal|dinner|lunch|breakfast": "hungry",
    "pain|hurt|ache|ouch|injured|sick|ill": "pain",
    "help|emergency|sos|assist|please help|need help": "help",
    r"\byes\b|agree|correct|sure|okay|ok|yep": "yes",
    r"\bno\b|nope|never|disagree|refuse": "no",
    "thank|thanks|grateful|appreciate": "thanks",
    "sorry|apologize|forgive|pardon|excuse": "sorry",
}

@app.route("/api/emotion_translate", methods=["POST"])
def api_emotion_translate():
    data = request.json
    text = data.get("text", "").lower()
    detected = None
    for pattern, emotion in KEYWORD_EMOTION.items():
        if re.search(pattern, text):
            detected = emotion
            break
    if not detected:
        detected = "confused"
    info = EMOTION_MAP[detected]
    try:
        from gtts import gTTS
        tts = gTTS(text=info["phrase"], lang="en")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp.name)
        with open(tmp.name, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        os.unlink(tmp.name)
    except:
        audio_b64 = None
    return jsonify({"emotion": detected, "audio": audio_b64, **info})

# ══════════════════════════════════════════════
#  VISUAL ALERT SYSTEM
# ══════════════════════════════════════════════

ALERT_TYPES = {
    "doorbell": {"icon": "🔔", "color": "#F1C40F", "message": "Someone is at the door!", "priority": "medium"},
    "alarm": {"icon": "🚨", "color": "#E74C3C", "message": "ALARM! Emergency!", "priority": "high"},
    "baby": {"icon": "👶", "color": "#FF69B4", "message": "Baby is crying!", "priority": "high"},
    "phone": {"icon": "📱", "color": "#3498DB", "message": "Phone is ringing!", "priority": "medium"},
    "smoke": {"icon": "🔥", "color": "#E74C3C", "message": "Smoke detected! Danger!", "priority": "critical"},
    "dog": {"icon": "🐕", "color": "#E67E22", "message": "Dog is barking!", "priority": "low"},
    "knock": {"icon": "🚪", "color": "#9B59B6", "message": "Someone is knocking!", "priority": "medium"},
    "microwave": {"icon": "📟", "color": "#1ABC9C", "message": "Microwave is done!", "priority": "low"},
}

@app.route("/api/visual_alert", methods=["POST"])
def api_visual_alert():
    data = request.json
    alert_key = data.get("alert", "doorbell")
    alert = ALERT_TYPES.get(alert_key, ALERT_TYPES["doorbell"])
    return jsonify({"alert_type": alert_key, **alert, "timestamp": datetime.now().strftime("%H:%M:%S")})

@app.route("/api/visual_alert/types", methods=["GET"])
def api_alert_types():
    return jsonify({"alerts": ALERT_TYPES})

# ══════════════════════════════════════════════
#  SIGN LANGUAGE DICTIONARY
# ══════════════════════════════════════════════

SIGN_DICT = {
    "hello": {"gif_desc": "Wave hand side to side", "hand": "✋", "tip": "Open palm, wave gently"},
    "thank you": {"gif_desc": "Flat hand from chin forward", "hand": "🤲", "tip": "Touch chin, move hand forward"},
    "please": {"gif_desc": "Circular motion on chest", "hand": "🖐️", "tip": "Rub chest in circle"},
    "sorry": {"gif_desc": "Fist circles on chest", "hand": "✊", "tip": "Make fist, rub in circles"},
    "yes": {"gif_desc": "Fist nods up and down", "hand": "✊", "tip": "Nod your fist"},
    "no": {"gif_desc": "Index + middle tap thumb", "hand": "🤏", "tip": "Snap index+middle on thumb"},
    "love": {"gif_desc": "Cross arms over chest", "hand": "🤗", "tip": "Cross both arms on chest"},
    "help": {"gif_desc": "Thumbs up lifted by other hand", "hand": "👍", "tip": "One fist with thumb up, lift with flat hand"},
    "eat": {"gif_desc": "Fingers to mouth repeatedly", "hand": "🤌", "tip": "Pinched fingers tap mouth"},
    "water": {"gif_desc": "W hand taps chin", "hand": "🖖", "tip": "W-shape, tap chin twice"},
    "home": {"gif_desc": "Flat O to cheek then chin", "hand": "🏠", "tip": "Pinched fingers: cheek → chin"},
    "friend": {"gif_desc": "Hook index fingers together", "hand": "🤝", "tip": "Link index fingers both ways"},
    "mother": {"gif_desc": "5-hand taps chin", "hand": "🖐️", "tip": "Open hand, tap chin"},
    "father": {"gif_desc": "5-hand taps forehead", "hand": "🖐️", "tip": "Open hand, tap forehead"},
    "more": {"gif_desc": "Fingertips tap together", "hand": "🤌", "tip": "Both pinched hands tap together"},
    "stop": {"gif_desc": "Edge of hand chops palm", "hand": "🤚", "tip": "Flat hand chops flat palm"},
    "good": {"gif_desc": "Flat hand from chin moves forward", "hand": "🖐️", "tip": "Touch chin, bring hand forward"},
    "bad": {"gif_desc": "Hand flips from chin downward", "hand": "🤚", "tip": "Touch chin, flip hand down"},
    "beautiful": {"gif_desc": "5-hand circles face, closes", "hand": "✨", "tip": "Spread fingers around face, close to fist"},
    "school": {"gif_desc": "Clap hands twice", "hand": "👏", "tip": "Clap flat hands twice"},
}

@app.route("/api/sign_dictionary", methods=["GET"])
def api_sign_dictionary():
    query = request.args.get("q", "").lower().strip()
    if query:
        results = {k: v for k, v in SIGN_DICT.items() if query in k}
    else:
        results = SIGN_DICT
    return jsonify({"results": results, "total": len(results)})

# ══════════════════════════════════════════════
#  MOOD JOURNAL
# ══════════════════════════════════════════════

MOOD_STORE = {}

@app.route("/api/mood_journal", methods=["GET"])
def get_mood_journal():
    user = session.get("user", "guest")
    entries = MOOD_STORE.get(user, [])
    return jsonify({"entries": entries})

@app.route("/api/mood_journal", methods=["POST"])
def add_mood_entry():
    user = session.get("user", "guest")
    data = request.json
    entry = {
        "id": str(uuid.uuid4()),
        "mood": data.get("mood", "neutral"),
        "emoji": data.get("emoji", "😐"),
        "note": data.get("note", ""),
        "energy": data.get("energy", 5),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    if user not in MOOD_STORE:
        MOOD_STORE[user] = []
    MOOD_STORE[user].insert(0, entry)
    MOOD_STORE[user] = MOOD_STORE[user][:30]
    return jsonify({"success": True, "entry": entry})

@app.route("/api/mood_journal/<entry_id>", methods=["DELETE"])
def delete_mood_entry(entry_id):
    user = session.get("user", "guest")
    if user in MOOD_STORE:
        MOOD_STORE[user] = [e for e in MOOD_STORE[user] if e["id"] != entry_id]
    return jsonify({"success": True})

# ══════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    print("=" * 50)
    print("🚀 CommuniSense Backend Starting...")
    print("=" * 50)
    print("📁 Available Routes:")
    print("   - http://localhost:5000/")
    print("   - http://localhost:5000/login")
    print("   - http://localhost:5000/signup")
    print("   - http://localhost:5000/dashboard")
    print("   - http://localhost:5000/tts")
    print("   - http://localhost:5000/stt")
    print("   - http://localhost:5000/word_recog")
    print("   - http://localhost:5000/letter_recog")
    print("   - http://localhost:5000/number_recog")
    print("   - http://localhost:5000/games")
    print("   - http://localhost:5000/image_gen")
    print("   - http://localhost:5000/emotion_translate")
    print("   - http://localhost:5000/visual_alert")
    print("   - http://localhost:5000/sign_dictionary")
    print("   - http://localhost:5000/mood_journal")
    print("   - http://localhost:5000/communication_cards")
    print("   - http://localhost:5000/lip_sync (redirects to communication_cards)")
    print("=" * 50)
    app.run(debug=True, port=5000)
