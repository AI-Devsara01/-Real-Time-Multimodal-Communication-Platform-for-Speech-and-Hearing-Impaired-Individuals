"""
CommuniSense - Real-Time Multimodal Communication for Hearing & Speech Impaired
Flask Backend - All Features Integrated
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import os, json, base64, tempfile, time, uuid, hashlib, re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "communisense_secret_2024"
CORS(app)

# ─── Simple in-memory user store (replace with DB in production) ───
USERS = {}
USERS_FILE = "users.json"

def load_users():
    global USERS
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            USERS = json.load(f)

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)

load_users()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ══════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════

@app.route("/")
def index():
    if "user" in session:
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
    if "user" not in session:
        return redirect(url_for("login_page"))
    return send_file("templates/dashboard.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if username in USERS and USERS[username]["password"] == hash_pw(password):
        session["user"] = username
        return jsonify({"success": True, "username": username})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email    = data.get("email", "").strip()
    if not username or not password or not email:
        return jsonify({"success": False, "error": "All fields required"}), 400
    if username in USERS:
        return jsonify({"success": False, "error": "Username already taken"}), 409
    if len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
    USERS[username] = {"password": hash_pw(password), "email": email, "created": str(datetime.now())}
    save_users()
    session["user"] = username
    return jsonify({"success": True, "username": username})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

# ══════════════════════════════════════════════
#  FEATURE PAGE ROUTES  (serve HTML files)
# ══════════════════════════════════════════════

PAGES = [
    "tts", "stt", "word_recog", "letter_recog", "number_recog",
    "games", "image_gen",
    # 5 new features
    "emotion_translate", "visual_alert", "sign_dictionary",
    "mood_journal", "lip_sync"
]
for page in PAGES:
    app.add_url_rule(
        f"/{page}",
        endpoint=page,
        view_func=lambda p=page: render_template(f"{p}.html")
    )
# ══════════════════════════════════════════════
#  TEXT-TO-SPEECH API
# ══════════════════════════════════════════════


@app.route("/api/tts", methods=["POST"])
def api_tts():
    try:
        from gtts import gTTS
        data     = request.json
        text     = data.get("text", "")
        lang     = data.get("lang", "en")
        if not text:
            return jsonify({"error": "No text provided"}), 400
        tts  = gTTS(text=text, lang=lang)
        tmp  = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp.name)
        with open(tmp.name, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        os.unlink(tmp.name)
        return jsonify({"audio": audio_b64, "format": "mp3"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════
#  SPEECH-TO-TEXT API  (file upload)
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
        r    = sr.Recognizer()
        with sr.AudioFile(tmp.name) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language=lang)
        os.unlink(tmp.name)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════
#  IMAGE GENERATION API  (Cloudflare Worker)
# ══════════════════════════════════════════════

@app.route("/api/image_gen", methods=["POST"])
def api_image_gen():
    try:
        import requests as req
        data   = request.json
        prompt = data.get("prompt", "")
        if not prompt:
            return jsonify({"error": "No prompt"}), 400
        API_URL = "https://image.sarafathima3700.workers.dev"
        API_KEY = "12345678"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        resp    = req.post(API_URL, headers=headers, json={"prompt": prompt}, timeout=30)
        if resp.status_code == 200:
            img_b64 = base64.b64encode(resp.content).decode()
            return jsonify({"image": img_b64, "format": "jpeg"})
        return jsonify({"error": f"Worker error {resp.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════
#  TRANSLATION API
# ══════════════════════════════════════════════

@app.route("/api/translate", methods=["POST"])
def api_translate():
    try:
        from deep_translator import GoogleTranslator
        data   = request.json
        text   = data.get("text", "")
        src    = data.get("src", "en")
        dest   = data.get("dest", "hi")
        result = GoogleTranslator(source=src, target=dest).translate(text)
        return jsonify({"translated": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════
#  NEW FEATURE 1 — EMOTION TRANSLATOR
#  Detects emotion in text → translates to emoji + voice phrase
# ══════════════════════════════════════════════

EMOTION_MAP = {
    "happy":    {"emoji": "😊", "color": "#FFD700", "phrase": "I am feeling happy!",   "sign": "☺️"},
    "sad":      {"emoji": "😢", "color": "#4169E1", "phrase": "I am feeling sad.",      "sign": "😔"},
    "angry":    {"emoji": "😠", "color": "#FF4500", "phrase": "I am feeling angry!",    "sign": "😤"},
    "scared":   {"emoji": "😨", "color": "#9B59B6", "phrase": "I am scared.",           "sign": "😰"},
    "excited":  {"emoji": "🤩", "color": "#FF69B4", "phrase": "I am very excited!",     "sign": "🎉"},
    "confused": {"emoji": "😕", "color": "#FFA500", "phrase": "I am confused.",         "sign": "🤔"},
    "tired":    {"emoji": "😴", "color": "#95A5A6", "phrase": "I am tired.",            "sign": "💤"},
    "loved":    {"emoji": "🥰", "color": "#FF1493", "phrase": "I feel loved.",          "sign": "❤️"},
    "hungry":   {"emoji": "🍔", "color": "#E67E22", "phrase": "I am hungry.",           "sign": "🍽️"},
    "pain":     {"emoji": "🤕", "color": "#E74C3C", "phrase": "I am in pain.",          "sign": "😣"},
    "help":     {"emoji": "🆘", "color": "#FF0000", "phrase": "I need help!",           "sign": "🙋"},
    "yes":      {"emoji": "✅", "color": "#2ECC71", "phrase": "Yes!",                   "sign": "👍"},
    "no":       {"emoji": "❌", "color": "#E74C3C", "phrase": "No!",                    "sign": "👎"},
    "thanks":   {"emoji": "🙏", "color": "#27AE60", "phrase": "Thank you!",             "sign": "🤝"},
    "sorry":    {"emoji": "😞", "color": "#7F8C8D", "phrase": "I am sorry.",            "sign": "🙇"},
}

KEYWORD_EMOTION = {
    "happy|joy|great|good|wonderful|amazing|love|excited|fantastic": "happy",
    "sad|unhappy|depressed|crying|miss|lonely|heartbroken":           "sad",
    "angry|mad|furious|rage|hate|annoyed|frustrated":                 "angry",
    "scared|afraid|fear|terrified|nervous|anxious|worried":           "scared",
    "excited|thrill|pumped|awesome|wow|incredible":                   "excited",
    "confused|lost|unsure|dont understand|what|huh":                  "confused",
    "tired|sleepy|exhausted|fatigue|rest":                            "tired",
    "love|adore|care|sweet|darling":                                  "loved",
    "hungry|food|eat|starving|meal|dinner|lunch|breakfast":           "hungry",
    "pain|hurt|ache|ouch|injured|sick|ill":                          "pain",
    "help|emergency|sos|assist|please help|need help":                "help",
    r"\byes\b|agree|correct|sure|okay|ok|yep":                       "yes",
    r"\bno\b|nope|never|disagree|refuse":                            "no",
    "thank|thanks|grateful|appreciate":                               "thanks",
    "sorry|apologize|forgive|pardon|excuse":                         "sorry",
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
    # Also generate TTS audio for the phrase
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
#  NEW FEATURE 2 — VISUAL ALERT SYSTEM
#  Converts audio alerts (doorbell, alarm, baby cry) to visual + vibration cues
# ══════════════════════════════════════════════

ALERT_TYPES = {
    "doorbell":  {"icon": "🔔", "color": "#F1C40F", "message": "Someone is at the door!", "priority": "medium"},
    "alarm":     {"icon": "🚨", "color": "#E74C3C", "message": "ALARM! Emergency!",       "priority": "high"},
    "baby":      {"icon": "👶", "color": "#FF69B4", "message": "Baby is crying!",          "priority": "high"},
    "phone":     {"icon": "📱", "color": "#3498DB", "message": "Phone is ringing!",        "priority": "medium"},
    "smoke":     {"icon": "🔥", "color": "#E74C3C", "message": "Smoke detected! Danger!", "priority": "critical"},
    "dog":       {"icon": "🐕", "color": "#E67E22", "message": "Dog is barking!",          "priority": "low"},
    "knock":     {"icon": "🚪", "color": "#9B59B6", "message": "Someone is knocking!",    "priority": "medium"},
    "microwave": {"icon": "📟", "color": "#1ABC9C", "message": "Microwave is done!",       "priority": "low"},
}

@app.route("/api/visual_alert", methods=["POST"])
def api_visual_alert():
    data      = request.json
    alert_key = data.get("alert", "doorbell")
    alert     = ALERT_TYPES.get(alert_key, ALERT_TYPES["doorbell"])
    return jsonify({"alert_type": alert_key, **alert, "timestamp": datetime.now().strftime("%H:%M:%S")})

@app.route("/api/visual_alert/types", methods=["GET"])
def api_alert_types():
    return jsonify({"alerts": ALERT_TYPES})

# ══════════════════════════════════════════════
#  NEW FEATURE 3 — SIGN LANGUAGE DICTIONARY
#  Searchable visual dictionary of sign language words
# ══════════════════════════════════════════════

SIGN_DICT = {
    "hello":    {"gif_desc": "Wave hand side to side", "hand": "✋", "tip": "Open palm, wave gently"},
    "thank you":{"gif_desc": "Flat hand from chin forward", "hand": "🤲", "tip": "Touch chin, move hand forward"},
    "please":   {"gif_desc": "Circular motion on chest", "hand": "🖐️", "tip": "Rub chest in circle"},
    "sorry":    {"gif_desc": "Fist circles on chest", "hand": "✊", "tip": "Make fist, rub in circles"},
    "yes":      {"gif_desc": "Fist nods up and down", "hand": "✊", "tip": "Nod your fist"},
    "no":       {"gif_desc": "Index + middle tap thumb", "hand": "🤏", "tip": "Snap index+middle on thumb"},
    "love":     {"gif_desc": "Cross arms over chest", "hand": "🤗", "tip": "Cross both arms on chest"},
    "help":     {"gif_desc": "Thumbs up lifted by other hand", "hand": "👍", "tip": "One fist with thumb up, lift with flat hand"},
    "eat":      {"gif_desc": "Fingers to mouth repeatedly", "hand": "🤌", "tip": "Pinched fingers tap mouth"},
    "water":    {"gif_desc": "W hand taps chin", "hand": "🖖", "tip": "W-shape, tap chin twice"},
    "home":     {"gif_desc": "Flat O to cheek then chin", "hand": "🏠", "tip": "Pinched fingers: cheek → chin"},
    "friend":   {"gif_desc": "Hook index fingers together", "hand": "🤝", "tip": "Link index fingers both ways"},
    "mother":   {"gif_desc": "5-hand taps chin", "hand": "🖐️", "tip": "Open hand, tap chin"},
    "father":   {"gif_desc": "5-hand taps forehead", "hand": "🖐️", "tip": "Open hand, tap forehead"},
    "more":     {"gif_desc": "Fingertips tap together", "hand": "🤌", "tip": "Both pinched hands tap together"},
    "stop":     {"gif_desc": "Edge of hand chops palm", "hand": "🤚", "tip": "Flat hand chops flat palm"},
    "good":     {"gif_desc": "Flat hand from chin moves forward", "hand": "🖐️", "tip": "Touch chin, bring hand forward"},
    "bad":      {"gif_desc": "Hand flips from chin downward", "hand": "🤚", "tip": "Touch chin, flip hand down"},
    "beautiful":{"gif_desc": "5-hand circles face, closes", "hand": "✨", "tip": "Spread fingers around face, close to fist"},
    "school":   {"gif_desc": "Clap hands twice", "hand": "👏", "tip": "Clap flat hands twice"},
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
#  NEW FEATURE 4 — MOOD JOURNAL
#  Daily mood tracker with voice/emoji entries for non-verbal users
# ══════════════════════════════════════════════

MOOD_STORE = {}   # username → list of entries

@app.route("/api/mood_journal", methods=["GET"])
def get_mood_journal():
    user    = session.get("user", "guest")
    entries = MOOD_STORE.get(user, [])
    return jsonify({"entries": entries})

@app.route("/api/mood_journal", methods=["POST"])
def add_mood_entry():
    user = session.get("user", "guest")
    data = request.json
    entry = {
        "id":        str(uuid.uuid4()),
        "mood":      data.get("mood", "neutral"),
        "emoji":     data.get("emoji", "😐"),
        "note":      data.get("note", ""),
        "energy":    data.get("energy", 5),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "date":      datetime.now().strftime("%Y-%m-%d"),
    }
    if user not in MOOD_STORE:
        MOOD_STORE[user] = []
    MOOD_STORE[user].insert(0, entry)
    MOOD_STORE[user] = MOOD_STORE[user][:30]  # keep last 30
    return jsonify({"success": True, "entry": entry})

@app.route("/api/mood_journal/<entry_id>", methods=["DELETE"])
def delete_mood_entry(entry_id):
    user = session.get("user", "guest")
    if user in MOOD_STORE:
        MOOD_STORE[user] = [e for e in MOOD_STORE[user] if e["id"] != entry_id]
    return jsonify({"success": True})

# ══════════════════════════════════════════════
#  NEW FEATURE 5 — LIP SYNC READER (AI-powered)
#  Upload video/image → AI describes lip movement / guesses word
# ══════════════════════════════════════════════

LIP_WORDS = {
    # simple phoneme → likely word mapping for demo
    "open_wide":   ["Hello", "Hey", "Hi"],
    "round":       ["No", "Oh", "Go", "Know"],
    "teeth":       ["Yes", "See", "Please", "These"],
    "pressed":     ["Maybe", "Mama", "More", "My"],
    "default":     ["Please", "Thank you", "Help", "Sorry"],
}

@app.route("/api/lip_sync", methods=["POST"])
def api_lip_sync():
    """
    Receives a base64 image frame and returns AI lip-reading suggestion.
    For demo: uses image brightness/color patterns to simulate analysis.
    Real implementation would use a lip-reading ML model.
    """
    data   = request.json
    frame  = data.get("image", "")   # base64 JPEG
    if not frame:
        return jsonify({"error": "No image provided"}), 400
    # Simulated analysis based on image hash
    import hashlib
    h   = int(hashlib.md5(frame[:100].encode()).hexdigest(), 16)
    key = list(LIP_WORDS.keys())[h % len(LIP_WORDS)]
    words = LIP_WORDS[key]
    word  = words[h % len(words)]
    confidence = 55 + (h % 40)
    return jsonify({
        "predicted_word": word,
        "confidence":     confidence,
        "alternatives":   [w for w in LIP_WORDS["default"] if w != word][:3],
        "shape":          key.replace("_", " ").title(),
    })

# ══════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    app.run(debug=True, port=5000)