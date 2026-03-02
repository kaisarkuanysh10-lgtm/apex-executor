from flask import Flask, request, redirect, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, re, psycopg2, psycopg2.extras, random, string, smtplib, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "apex-studio-ultra-2026-xK9mP")

# ═══════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════
def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        verified BOOLEAN DEFAULT FALSE,
        apelx INTEGER DEFAULT 0,
        avatar_color TEXT DEFAULT '#e74c3c',
        avatar_icon TEXT DEFAULT '😊',
        bio TEXT DEFAULT '',
        gender TEXT DEFAULT '',
        birth_year INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT DEFAULT ''")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_year INTEGER DEFAULT 0")
    c.execute("""CREATE TABLE IF NOT EXISTS used_usernames(
        username TEXT PRIMARY KEY,
        released_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS verify_codes(
        email TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        username TEXT,
        password_hash TEXT,
        expires_at TIMESTAMP,
        attempts INT DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reset_codes(
        email TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        expires_at TIMESTAMP,
        attempts INT DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS login_attempts(
        ip TEXT PRIMARY KEY,
        attempts INT DEFAULT 1,
        blocked_until TIMESTAMP,
        last_attempt TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS games(
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        genre TEXT DEFAULT 'Adventure',
        thumbnail_url TEXT DEFAULT '',
        thumbnail_emoji TEXT DEFAULT '🎮',
        thumbnail_color TEXT DEFAULT '#3498db',
        creator_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        plays INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        dislikes INTEGER DEFAULT 0,
        published BOOLEAN DEFAULT FALSE,
        max_players INTEGER DEFAULT 10,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS game_reviews(
        id SERIAL PRIMARY KEY,
        game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        liked BOOLEAN NOT NULL,
        comment TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(game_id, user_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS friends(
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        friend_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(user_id, friend_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications(
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        from_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS bans(
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        reason TEXT DEFAULT '',
        banned_by INTEGER REFERENCES users(id),
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT DEFAULT ''")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_year INTEGER DEFAULT 0")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE")
    c.execute("""CREATE TABLE IF NOT EXISTS game_plays(
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
        played_at TIMESTAMP DEFAULT NOW()
    )""")
    conn.commit(); c.close(); conn.close()

def q(sql, params=(), one=False, commit=False):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute(sql, params)
        if commit:
            if one:
                result = c.fetchone()
            else:
                result = c.rowcount
            conn.commit()
        elif one:
            result = c.fetchone()
        else:
            result = c.fetchall()
        c.close(); conn.close()
        return result
    except Exception as e:
        print(f"DB Error: {e}")
        return None

# ═══════════════════════════════════════════════════
# EMAIL
# ═══════════════════════════════════════════════════
def send_code_email(to, username, code, purpose="verify"):
    su = os.environ.get("SMTP_EMAIL")
    sp = os.environ.get("SMTP_PASS")
    subj = "Apex Studio — Verify Your Account" if purpose=="verify" else "Apex Studio — Reset Password"
    html = f"""<!DOCTYPE html><html><body style="background:#0f0f1a;margin:0;padding:40px;font-family:Arial,sans-serif">
<div style="max-width:520px;margin:0 auto;background:#16213e;border-radius:12px;overflow:hidden">
  <div style="background:linear-gradient(135deg,#e74c3c,#c0392b);padding:28px;text-align:center">
    <div style="font-size:2rem;font-weight:900;color:white;letter-spacing:.1em">APEX STUDIO</div>
  </div>
  <div style="padding:36px">
    <p style="color:#e2e8f0;font-size:1rem;margin-bottom:8px">Hello, <strong style="color:white">{username}</strong>!</p>
    <p style="color:#718096;margin-bottom:24px">{"Verify your Apex Studio account" if purpose=="verify" else "Reset your password"} using this code:</p>
    <div style="background:#0d1117;border:2px solid #e74c3c;border-radius:10px;padding:28px;text-align:center;margin-bottom:24px">
      <div style="font-size:3rem;font-weight:900;color:#e74c3c;letter-spacing:.6em">{code}</div>
      <div style="color:#4a5568;font-size:.75rem;margin-top:10px;letter-spacing:.2em">EXPIRES IN 10 MINUTES</div>
    </div>
    <p style="color:#4a5568;font-size:.8rem">If you didn't request this, ignore this email.</p>
  </div>
</div></body></html>"""
    if not su or not sp:
        print(f"[EMAIL] {to}: {code}")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subj; msg["From"] = f"Apex Studio <{su}>"; msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(su, sp); s.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}"); return False

def gen_code(): return ''.join(random.choices(string.digits, k=8))

# ═══════════════════════════════════════════════════
# SECURITY
# ═══════════════════════════════════════════════════
def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def check_block(ip):
    row = q("SELECT blocked_until FROM login_attempts WHERE ip=%s", (ip,), one=True)
    if row and row['blocked_until'] and datetime.now() < row['blocked_until']:
        mins = int((row['blocked_until'] - datetime.now()).total_seconds()/60)+1
        return True, mins
    return False, 0

def record_fail(ip):
    q("""INSERT INTO login_attempts(ip,attempts,last_attempt) VALUES(%s,1,NOW())
        ON CONFLICT(ip) DO UPDATE SET attempts=login_attempts.attempts+1,last_attempt=NOW(),
        blocked_until=CASE WHEN login_attempts.attempts+1>=3
        THEN NOW()+(15*INTERVAL'1 minute') ELSE NULL END""", (ip,), commit=True)
    row = q("SELECT attempts FROM login_attempts WHERE ip=%s", (ip,), one=True)
    return row['attempts'] if row else 1

def clear_block(ip):
    q("DELETE FROM login_attempts WHERE ip=%s", (ip,), commit=True)

# ═══════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════
def valid_email(e): return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', e))
BAD_WORDS = ["fuck","shit","ass","bitch","cunt","dick","pussy","cock","nigger","fag","whore","slut","rape","nazi","porn","nude"]

def valid_username(u):
    if len(u) < 4: return False, "Username must be at least 4 characters"
    if len(u) > 20: return False, "Max 20 characters"
    if not re.match(r"^[a-zA-Z0-9_]+$", u): return False, "Only English letters, numbers, and _"
    if u.count("_") > 1: return False, "Only one underscore (_) allowed"
    if u.startswith("_") or u.endswith("_"): return False, "Underscore cannot be at start or end"
    ul = u.lower().replace("_", "")
    for bw in BAD_WORDS:
        if bw in ul: return False, "This username contains a prohibited word"
    return True, "ok"
def valid_pw(pw):
    if len(pw) < 8: return False, "At least 8 characters"
    if not re.search(r'[A-Z]', pw): return False, "At least 1 uppercase letter"
    if not re.search(r'[0-9]', pw): return False, "At least 1 number"
    return True, "ok"

# ═══════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════
def get_user():
    if 'uid' not in session: return None
    return q("SELECT * FROM users WHERE id=%s", (session['uid'],), one=True)

def get_user_dict():
    u = get_user()
    return dict(u) if u else None

GENRES = ["Adventure","Roleplay","Tycoon","Obby","FPS","Racing","Survival","Horror","Simulator","RPG","PvP","Building","Puzzle","Sports"]
EMOJIS = ["🎮","🏝️","🏙️","🧟","🏎️","⚔️","☁️","🌈","🔨","🚀","🐉","🥷","🌊","👻","🌾","🌋","❄️","🎯","🛡️","💎"]
COLORS = ["#e74c3c","#3498db","#2ecc71","#f39c12","#8e44ad","#1abc9c","#e67e22","#2c3e50","#16a085","#d35400","#c0392b","#27ae60"]
GAME_BG = [
    {"t":"Zombie Rush","i":"🧟","c":"#e74c3c","p":"top:5%;left:2%;rotate(-8deg)"},
    {"t":"Sky Wars","i":"☁️","c":"#3498db","p":"top:8%;left:13%;rotate(5deg)"},
    {"t":"Dungeon Quest","i":"⚔️","c":"#8e44ad","p":"top:3%;left:24%;rotate(-4deg)"},
    {"t":"City Tycoon","i":"🏙️","c":"#4ecdc4","p":"top:10%;left:35%;rotate(7deg)"},
    {"t":"Racing World","i":"🏎️","c":"#f39c12","p":"top:4%;left:48%;rotate(-6deg)"},
    {"t":"Obby Paradise","i":"🌈","c":"#e91e63","p":"top:9%;left:61%;rotate(4deg)"},
    {"t":"Build Battle","i":"🔨","c":"#2ecc71","p":"top:5%;left:74%;rotate(-5deg)"},
    {"t":"Survival","i":"🏝️","c":"#ff6b35","p":"top:8%;left:87%;rotate(6deg)"},
    {"t":"Ghost Hunt","i":"👻","c":"#7b1fa2","p":"bottom:6%;left:1%;rotate(7deg)"},
    {"t":"Dragon Land","i":"🐉","c":"#f44336","p":"bottom:4%;left:12%;rotate(-5deg)"},
    {"t":"Space Battle","i":"🚀","c":"#00bcd4","p":"bottom:9%;left:23%;rotate(4deg)"},
    {"t":"Ocean Tycoon","i":"🌊","c":"#0288d1","p":"bottom:5%;left:36%;rotate(-7deg)"},
    {"t":"Farm Life","i":"🌾","c":"#558b2f","p":"bottom:8%;left:50%;rotate(5deg)"},
    {"t":"Lava Run","i":"🌋","c":"#bf360c","p":"bottom:4%;left:63%;rotate(-4deg)"},
    {"t":"Ice Kingdom","i":"❄️","c":"#4fc3f7","p":"bottom:7%;left:76%;rotate(6deg)"},
    {"t":"Ninja World","i":"🥷","c":"#212121","p":"bottom:3%;left:89%;rotate(-6deg)"},
]

CSS = """<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{--red:#e74c3c;--red2:#c0392b;--bg:#1a1a2e;--surf:#16213e;--surf2:#0f3460;--surf3:#0a1628;
  --border:#1e3a5f;--text:#e2e8f0;--muted:#718096;--green:#2ecc71;--yellow:#f1c40f;--blue:#3498db;
  --font:'Nunito',sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh}
a{text-decoration:none;color:inherit}
img{max-width:100%;border-radius:8px}

/* SIDEBAR */
.layout{display:flex;min-height:100vh}
.sidebar{width:72px;background:var(--surf3);border-right:1px solid var(--border);
  display:flex;flex-direction:column;align-items:center;padding:12px 0;position:fixed;
  top:0;left:0;height:100vh;z-index:50;gap:4px}
.sb-logo{width:44px;height:44px;background:var(--red);border-radius:10px;
  display:flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:900;
  color:white;margin-bottom:8px;letter-spacing:-.05em;font-size:.75rem;text-align:center;line-height:1.2}
.sb-item{width:52px;height:52px;border-radius:10px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:3px;cursor:pointer;transition:all .2s;
  color:var(--muted);border:none;background:transparent;font-family:var(--font)}
.sb-item:hover,.sb-item.active{background:var(--surf2);color:var(--text)}
.sb-item .sb-icon{font-size:1.3rem}
.sb-item .sb-label{font-size:.6rem;font-weight:700}

/* TOP BAR */
.topbar{height:54px;background:var(--surf);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:12px;padding:0 20px;position:sticky;top:0;z-index:40}
.search-bar{flex:1;max-width:400px;display:flex;align-items:center;gap:8px;
  background:var(--surf2);border:1px solid var(--border);border-radius:24px;padding:8px 16px}
.search-bar input{background:transparent;border:none;outline:none;color:var(--text);
  font-family:var(--font);font-size:.9rem;width:100%}
.search-bar input::placeholder{color:var(--muted)}
.topbar-right{display:flex;align-items:center;gap:12px;margin-left:auto}
.apelx-badge{background:var(--surf2);border:1px solid var(--yellow);border-radius:20px;
  padding:5px 14px;font-size:.82rem;font-weight:800;color:var(--yellow);display:flex;align-items:center;gap:6px}
.notif-btn{width:36px;height:36px;border-radius:50%;background:var(--surf2);border:none;
  color:var(--muted);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.1rem}
.user-pill{display:flex;align-items:center;gap:8px;padding:4px 12px 4px 4px;
  background:var(--surf2);border-radius:24px;cursor:pointer}
.user-av{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:1rem;font-weight:700}

/* MAIN CONTENT */
.main{margin-left:72px;flex:1}
.content{padding:24px 28px}
.page-title{font-size:1.6rem;font-weight:900;margin-bottom:4px}
.section{margin-bottom:32px}
.section-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.section-title{font-size:1.05rem;font-weight:800;display:flex;align-items:center;gap:8px}
.see-all{font-size:.82rem;color:var(--muted);font-weight:700;cursor:pointer}
.see-all:hover{color:var(--red)}

/* CONNECTIONS ROW */
.conn-row{display:flex;gap:16px;overflow-x:auto;padding-bottom:4px}
.conn-row::-webkit-scrollbar{height:4px}
.conn-row::-webkit-scrollbar-track{background:var(--surf)}
.conn-row::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}
.conn-item{display:flex;flex-direction:column;align-items:center;gap:6px;cursor:pointer;min-width:72px}
.conn-av{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-size:1.8rem;position:relative;border:3px solid var(--border);transition:border-color .2s}
.conn-av:hover{border-color:var(--red)}
.conn-av .online-dot{position:absolute;bottom:2px;right:2px;width:14px;height:14px;
  background:var(--green);border-radius:50%;border:2px solid var(--surf)}
.conn-name{font-size:.72rem;font-weight:700;text-align:center;color:var(--muted);max-width:72px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.conn-status{font-size:.65rem;color:var(--muted);text-align:center;max-width:72px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.add-conn{width:64px;height:64px;border-radius:50%;background:var(--surf2);
  border:3px dashed var(--border);display:flex;align-items:center;justify-content:center;
  font-size:1.8rem;color:var(--muted);cursor:pointer;transition:all .2s}
.add-conn:hover{border-color:var(--red);color:var(--red)}

/* FEATURED / TODAY'S PICKS */
.picks-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.pick-card{border-radius:10px;overflow:hidden;cursor:pointer;transition:all .2s;
  border:1px solid transparent;position:relative}
.pick-card:hover{transform:translateY(-3px);border-color:rgba(255,255,255,.1);
  box-shadow:0 8px 30px rgba(0,0,0,.5)}
.pick-thumb{height:160px;display:flex;align-items:center;justify-content:center;font-size:4rem;
  position:relative;background:var(--surf2)}
.pick-thumb img{width:100%;height:100%;object-fit:cover;position:absolute;inset:0;border-radius:0}
.pick-badge{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.75);color:white;
  font-size:.72rem;font-weight:800;padding:3px 8px;border-radius:4px;backdrop-filter:blur(4px)}
.pick-info{padding:10px 12px;background:var(--surf)}
.pick-title{font-size:.9rem;font-weight:800;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pick-sub{font-size:.75rem;color:var(--muted)}

/* GAMES GRID */
.games-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:16px}
.game-card{background:var(--surf);border-radius:10px;overflow:hidden;border:1px solid var(--border);
  transition:all .2s;cursor:pointer}
.game-card:hover{transform:translateY(-3px);border-color:var(--red);box-shadow:0 8px 24px rgba(0,0,0,.4)}
.game-thumb{height:110px;display:flex;align-items:center;justify-content:center;font-size:3rem;
  position:relative;background:var(--surf2)}
.game-thumb img{width:100%;height:100%;object-fit:cover;position:absolute;inset:0}
.game-plays{position:absolute;bottom:6px;right:8px;background:rgba(0,0,0,.75);
  border-radius:10px;padding:2px 8px;font-size:.68rem;color:white;font-weight:700;backdrop-filter:blur(4px)}
.game-body{padding:10px 12px}
.game-title{font-size:.88rem;font-weight:800;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.game-creator{font-size:.72rem;color:var(--muted)}
.game-meta{display:flex;align-items:center;justify-content:space-between;margin-top:6px}
.game-genre{font-size:.68rem;color:var(--muted);background:var(--surf2);padding:2px 7px;border-radius:8px}
.game-likes{font-size:.72rem;color:var(--green);font-weight:700}

/* GAME DETAIL */
.game-detail-thumb{width:100%;max-height:400px;border-radius:12px;overflow:hidden;
  background:var(--surf2);display:flex;align-items:center;justify-content:center;
  font-size:8rem;position:relative;margin-bottom:20px}
.game-detail-thumb img{width:100%;height:100%;object-fit:cover}
.play-btn{width:100%;padding:16px;background:var(--blue);color:white;border:none;
  border-radius:10px;font-size:1.1rem;font-weight:900;cursor:pointer;font-family:var(--font);
  transition:all .2s;display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:12px}
.play-btn:hover{background:#2980b9;transform:translateY(-1px)}
.action-row{display:flex;gap:8px;margin-bottom:20px}
.action-btn{flex:1;padding:10px;background:var(--surf2);border:1px solid var(--border);
  border-radius:8px;color:var(--text);font-family:var(--font);font-size:.85rem;font-weight:700;
  cursor:pointer;text-align:center;transition:all .2s}
.action-btn:hover{border-color:var(--red);color:var(--red)}
.action-btn.liked{color:var(--green);border-color:var(--green)}
.action-btn.disliked{color:var(--red);border-color:var(--red)}

/* REVIEW */
.review-item{background:var(--surf2);border-radius:8px;padding:14px;margin-bottom:10px;border:1px solid var(--border)}
.review-head{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.review-av{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.9rem}
.review-name{font-size:.82rem;font-weight:800}
.review-badge{font-size:.72rem;padding:2px 7px;border-radius:10px;font-weight:700}
.review-like{background:rgba(46,204,113,.15);color:var(--green)}
.review-dislike{background:rgba(231,76,60,.15);color:var(--red)}
.review-text{font-size:.85rem;color:var(--muted);line-height:1.5}

/* FORMS */
.fg{margin-bottom:16px}
.fg label{display:block;font-size:.75rem;font-weight:700;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em}
.fg input,.fg select,.fg textarea{width:100%;padding:11px 14px;background:var(--surf3);
  border:1.5px solid var(--border);border-radius:8px;color:var(--text);font-family:var(--font);
  font-size:.95rem;outline:none;transition:all .2s}
.fg input:focus,.fg select,.fg textarea:focus{border-color:var(--red)}
.fg select{cursor:pointer}
.fg textarea{resize:vertical;min-height:100px}
.fg input::placeholder,.fg textarea::placeholder{color:var(--muted)}
.hint{font-size:.72rem;color:var(--muted);margin-top:5px}
.code-inp{text-align:center;font-size:2rem;font-weight:900;letter-spacing:.4em;color:var(--red) !important;border-color:var(--red) !important}
.btn{padding:11px 22px;background:var(--red);color:white;border:none;border-radius:8px;
  font-size:.9rem;font-weight:800;cursor:pointer;font-family:var(--font);transition:all .2s;display:inline-block}
.btn:hover{background:var(--red2);transform:translateY(-1px)}
.btn.outline{background:transparent;border:2px solid var(--red);color:var(--red)}
.btn.outline:hover{background:var(--red);color:white}
.btn.green{background:var(--green)}
.btn.green:hover{background:#27ae60}
.btn.full{width:100%;text-align:center}
.btn.blue{background:var(--blue)}
.btn.blue:hover{background:#2980b9}

/* TABS */
.tabs{display:flex;gap:0;background:var(--surf2);padding:4px;border-radius:8px;width:fit-content;margin-bottom:20px}
.tab{padding:7px 20px;border-radius:6px;font-size:.88rem;font-weight:700;color:var(--muted);
  cursor:pointer;border:none;background:transparent;font-family:var(--font);transition:all .2s}
.tab.active{background:var(--red);color:white}

/* PROFILE */
.profile-banner{height:160px;background:linear-gradient(135deg,var(--surf2),var(--surf3));border-radius:12px;margin-bottom:-60px;position:relative}
.profile-av-wrap{margin-left:24px;position:relative;display:inline-block}
.profile-av{width:100px;height:100px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:3rem;border:4px solid var(--bg)}
.profile-info{padding:16px 24px 24px;display:flex;align-items:flex-end;gap:16px}
.profile-name{font-size:1.5rem;font-weight:900;margin-bottom:4px}
.profile-stats{display:flex;gap:20px;margin-top:12px}
.pstat{text-align:center}
.pstat-n{font-size:1.2rem;font-weight:900;color:var(--yellow)}
.pstat-l{font-size:.7rem;color:var(--muted)}

/* SETTINGS */
.settings-wrap{display:grid;grid-template-columns:200px 1fr;gap:20px;max-width:900px}
.settings-nav{background:var(--surf);border-radius:10px;padding:8px;height:fit-content;border:1px solid var(--border)}
.settings-nav-item{padding:10px 14px;border-radius:7px;font-size:.88rem;font-weight:700;
  color:var(--muted);cursor:pointer;transition:all .2s}
.settings-nav-item:hover,.settings-nav-item.active{background:var(--surf2);color:var(--text)}
.settings-panel{background:var(--surf);border-radius:10px;padding:24px;border:1px solid var(--border)}
.settings-title{font-size:1rem;font-weight:800;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)}

/* ALERTS */
.al{padding:11px 14px;border-radius:8px;font-size:.85rem;margin-bottom:14px;display:flex;gap:8px;line-height:1.5}
.al-e{background:rgba(231,76,60,.1);border:1px solid rgba(231,76,60,.3);color:#fc8181}
.al-s{background:rgba(46,204,113,.1);border:1px solid rgba(46,204,113,.3);color:#68d391}
.al-i{background:rgba(52,152,219,.1);border:1px solid rgba(52,152,219,.3);color:#90cdf4}

/* LANDING */
.land-bg{position:fixed;inset:0;background:#0f0f1a;overflow:hidden}
.land-overlay{position:fixed;inset:0;
  background:linear-gradient(to right,rgba(0,0,0,.9) 0%,rgba(0,0,0,.6) 40%,rgba(0,0,0,.6) 60%,rgba(0,0,0,.9) 100%),
  linear-gradient(to bottom,rgba(0,0,0,.8) 0%,transparent 25%,transparent 75%,rgba(0,0,0,.8) 100%);z-index:1}
.land-center{position:fixed;inset:0;z-index:2;display:flex;align-items:center;justify-content:center}
.auth-box{background:rgba(22,33,62,.94);border:1px solid rgba(255,255,255,.1);border-radius:16px;
  padding:32px;width:100%;max-width:420px;backdrop-filter:blur(20px);box-shadow:0 20px 60px rgba(0,0,0,.7)}
.auth-tabs{display:flex;gap:0;margin-bottom:20px;border-radius:8px;overflow:hidden;border:1px solid rgba(255,255,255,.12)}
.auth-tab{flex:1;padding:10px;text-align:center;font-weight:800;font-size:.9rem;
  cursor:pointer;border:none;font-family:var(--font);transition:all .2s}
.auth-tab.active{background:var(--red);color:white}
.auth-tab.inactive{background:rgba(255,255,255,.05);color:rgba(255,255,255,.4)}
.auth-tab.inactive:hover{background:rgba(255,255,255,.1);color:white}
.land-logo{position:fixed;top:16px;left:24px;z-index:10;font-size:1.5rem;font-weight:900;color:white}
.land-logo span{color:var(--red)}
.land-login-btn{position:fixed;top:14px;right:20px;z-index:10;padding:9px 24px;
  background:white;color:#0f0f1a;border:none;border-radius:8px;font-size:.9rem;font-weight:800;
  cursor:pointer;font-family:var(--font);box-shadow:0 4px 16px rgba(0,0,0,.3)}
.land-login-btn:hover{background:#f0f0f0}
.bg-card{position:absolute;width:120px;height:150px;border-radius:12px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;
  border:2px solid rgba(255,255,255,.12);box-shadow:0 8px 32px rgba(0,0,0,.5)}
.bg-card-icon{font-size:2.6rem}
.bg-card-title{font-size:.68rem;font-weight:800;color:white;text-align:center;padding:0 6px;line-height:1.3}

/* MISC */
.empty{text-align:center;padding:48px 20px;color:var(--muted)}
.empty-icon{font-size:3rem;margin-bottom:12px}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.72rem;font-weight:700}
.badge-red{background:rgba(231,76,60,.2);color:var(--red)}
.badge-green{background:rgba(46,204,113,.2);color:var(--green)}
.badge-yellow{background:rgba(241,196,15,.2);color:var(--yellow)}
.divider{height:1px;background:var(--border);margin:20px 0}

/* GRID EMOJIS */
.emoji-grid{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.emoji-opt{width:42px;height:42px;border-radius:8px;background:var(--surf3);border:2px solid var(--border);
  display:flex;align-items:center;justify-content:center;font-size:1.3rem;cursor:pointer;transition:all .2s}
.emoji-opt:hover,.emoji-opt.sel{border-color:var(--red);background:rgba(231,76,60,.1)}
.color-grid{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.color-opt{width:30px;height:30px;border-radius:50%;cursor:pointer;border:3px solid transparent;transition:all .2s}
.color-opt:hover,.color-opt.sel{border-color:white;transform:scale(1.15)}

@media(max-width:768px){
  .picks-grid{grid-template-columns:repeat(2,1fr)}
  .games-grid{grid-template-columns:repeat(2,1fr)}
  .settings-wrap{grid-template-columns:1fr}
}
</style>"""

def al(msg, k="e"):
    ic = {"e":"⚠","s":"✓","i":"ℹ"}
    return f'<div class="al al-{k}"><span>{ic.get(k,"!")}</span><span>{msg}</span></div>'

def fmt_plays(n):
    if n >= 1000000: return f"{n/1000000:.1f}M"
    if n >= 1000: return f"{n/1000:.1f}K"
    return str(n)

def user_avatar(u, size=36):
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{u.get("avatar_color","#e74c3c")};display:flex;align-items:center;justify-content:center;font-size:{size*0.55}px;flex-shrink:0">{u.get("avatar_icon","😊")}</div>'

def sidebar(active="home"):
    items = [
        ("home", "🏠", "Home", "/home"),
        ("games", "📊", "Charts", "/games"),
        ("create", "✏️", "Create", "/create"),
        ("avatar", "👤", "Avatar", "/avatar"),
        ("chat", "💬", "Chat", "/chat"),
        ("party", "🎉", "Party", "#"),
        ("more", "•••", "More", "#"),
    ]
    links = ''.join([f'<a href="{url}"><button class="sb-item {"active" if a==active else ""}">'
        f'<span class="sb-icon">{icon}</span><span class="sb-label">{label}</span>'
        f'</button></a>' for a, icon, label, url in items])
    return f'<div class="sidebar"><div class="sb-logo">APEX</div>{links}</div>'

def topbar(user):
    udict = dict(user)
    return f"""<div class="topbar">
      <form action="/search" method="GET" style="flex:1;max-width:400px">
        <div class="search-bar">
          <span style="color:var(--muted)">🔍</span>
          <input type="text" name="q" placeholder="Search" autocomplete="off">
        </div>
      </form>
      <div class="topbar-right">
        <div class="apelx-badge">⬡ {udict.get('apelx',0):,} Apelx</div>
        <a href="/notifications" style="position:relative">
          <button class="notif-btn">🔔</button>
          {f'<span style="position:absolute;top:-2px;right:-2px;background:var(--red);color:white;border-radius:50%;width:16px;height:16px;font-size:.6rem;font-weight:800;display:flex;align-items:center;justify-content:center">'+str(unread_count)+'</span>' if (unread_count:=( (q("SELECT COUNT(*) as n FROM notifications WHERE user_id=%s AND is_read=FALSE",(udict["id"],),one=True) or {{}}).get("n",0) )) > 0 else ''}
        </a>
        <a href="/profile/{udict['id']}">
          <div class="user-pill">
            {user_avatar(udict, 30)}
            <span style="font-size:.85rem;font-weight:800">{udict['username']}</span>
          </div>
        </a>
      </div>
    </div>"""

def layout(content, user, active="home"):
    udict = dict(user)
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apex Studio</title>{CSS}</head>
<body>
{sidebar(active)}
<div class="main">
  {topbar(udict)}
  <div class="content">{content}</div>
</div>
</body></html>"""

def auth_page(body, modal="register"):
    bg = ''.join([f"""<div class="bg-card" style="position:absolute;{g['p'].split(';')[0]};{g['p'].split(';')[1] if ';' in g['p'] else ''};background:linear-gradient(135deg,{g['c']}99,{g['c']}55)">
      <div class="bg-card-icon">{g['i']}</div>
      <div class="bg-card-title">{g['t']}</div>
    </div>""" for g in GAME_BG])

    reg_tab = 'active' if modal == 'register' else 'inactive'
    log_tab = 'active' if modal == 'login' else 'inactive'

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apex Studio</title>{CSS}</head>
<body style="overflow:hidden;height:100vh">
<div class="land-bg">{bg}</div>
<div class="land-overlay"></div>
<div class="land-logo">APEX<span>STUDIO</span></div>
<a href="/?modal=login"><button class="land-login-btn">Log In</button></a>
<div class="land-center">
  <div class="auth-box">
    <div class="auth-tabs">
      <button class="auth-tab {reg_tab}" onclick="location.href='/?modal=register'">Sign Up</button>
      <button class="auth-tab {log_tab}" onclick="location.href='/?modal=login'">Log In</button>
    </div>
    {body}
  </div>
</div>
</body></html>"""

# ═══════════════════════════════════════════════════
# DEMO USERS FOR CONNECTIONS ROW
# ═══════════════════════════════════════════════════
DEMO_CONNECTIONS = [
    {"name":"Danuardjai","icon":"😈","color":"#e74c3c","status":"Zombie Rush","online":True},
    {"name":"Goodperson55","icon":"🌸","color":"#e91e63","status":"City Tycoon","online":True},
    {"name":"ErkebulanT","icon":"😎","color":"#3498db","status":"Sky Wars","online":True},
    {"name":"omer_k","icon":"🎮","color":"#8e44ad","status":"Online","online":True},
    {"name":"Liveing_L","icon":"⚔️","color":"#2c3e50","status":"Dungeon Quest","online":True},
    {"name":"Suslik","icon":"🐹","color":"#27ae60","status":"Build Battle","online":False},
    {"name":"Данияр","icon":"🎯","color":"#d35400","status":"Offline","online":False},
    {"name":"zopiewn","icon":"🦊","color":"#c0392b","status":"Offline","online":False},
    {"name":"phoebe","icon":"🌙","color":"#7b1fa2","status":"Offline","online":False},
]

FEATURED = [
    {"t":"Zombie Rush","sub":"New Season","desc":"Fight endless waves","i":"🧟","c":"#c0392b","plays":3100000},
    {"t":"Volleyball Legends","sub":"New Mode","desc":"Bump, set, spike!","i":"🏐","c":"#3498db","plays":1800000},
    {"t":"Project Delta","sub":"","desc":"Survive a nuclear world","i":"🌍","c":"#2c3e50","plays":987000},
    {"t":"Sniper Duels","sub":"","desc":"Step up and take your shot","i":"🎯","c":"#7f8c8d","plays":2400000},
]

# ═══════════════════════════════════════════════════
# ROUTES — LANDING
# ═══════════════════════════════════════════════════
@app.route('/')
def index():
    user = get_user_dict()
    if user: return redirect('/home')
    modal = request.args.get('modal', 'register')
    err = session.pop('auth_err', None)
    flash_s = session.pop('auth_ok', None)

    if modal == 'login':
        body = f"""
        {al(err,'e') if err else ''}{al(flash_s,'s') if flash_s else ''}
        <form method="POST" action="/login" autocomplete="off">
          <div class="fg"><label>Username or Email</label>
          <input type="text" name="username" placeholder="Username" required></div>
          <div class="fg"><label>Password</label>
          <input type="password" name="password" placeholder="Password" required></div>
          <div style="text-align:right;margin-bottom:14px">
            <a href="/forgot" style="font-size:.82rem;color:var(--red);font-weight:700">Forgot password?</a>
          </div>
          <button type="submit" class="btn full">Log In</button>
        </form>"""
    else:
        body = f"""
        <div style="text-align:center;font-size:1rem;font-weight:900;color:white;margin-bottom:16px;letter-spacing:.03em">SIGN UP AND START HAVING FUN!</div>
        {al(err,'e') if err else ''}
        <form method="POST" action="/register" autocomplete="off">
          <div class="fg"><label>Username</label>
          <input type="text" name="username" placeholder="Min 4 chars (letters, numbers, _)" required minlength="4" maxlength="20"></div>
          <div class="fg"><label>Email</label>
          <input type="email" name="email" placeholder="your@email.com" required></div>
          <div class="fg"><label>Password</label>
          <input type="password" name="password" placeholder="Create a password" required></div>
          <button type="submit" class="btn full">Sign Up</button>
        </form>
        <div style="font-size:.72rem;color:rgba(255,255,255,.35);text-align:center;margin-top:12px;line-height:1.5">
          By clicking Sign Up, you agree to our Terms of Use
        </div>"""
    return auth_page(body, modal)

# ═══════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════
@app.route('/login', methods=['POST'])
def login():
    try: init_db(); ensure_admin()
    except: pass
    ip = get_ip()
    blocked, mins = check_block(ip)
    if blocked:
        session['auth_err'] = f"Too many attempts. Try again in {mins} minute(s)."
        return redirect('/?modal=login')
    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    try:
        user = q("SELECT * FROM users WHERE username=%s AND verified=TRUE", (username,), one=True)
        if user and check_password_hash(user['password'], password):
            clear_block(ip)
            if user.get('is_banned'):
                ban_info = q("SELECT reason,expires_at FROM bans WHERE user_id=%s ORDER BY created_at DESC LIMIT 1",(user['id'],),one=True)
                reason = dict(ban_info)['reason'] if ban_info else 'Violation of Terms of Use'
                session['auth_err'] = f"Your account has been banned. Reason: {reason}"
                return redirect('/?modal=login')
            session['uid'] = user['id']
            return redirect('/home')
        else:
            n = record_fail(ip); rem = 3-n
            blk, m = check_block(ip)
            if blk: session['auth_err'] = f"Too many attempts. Blocked for {m} minutes."
            else: session['auth_err'] = f"Incorrect username or password. {rem} attempt(s) remaining."
            return redirect('/?modal=login')
    except Exception as e:
        session['auth_err'] = f"Error: {str(e)[:60]}"
        return redirect('/?modal=login')

@app.route('/register', methods=['POST'])
def register():
    try: init_db()
    except: pass
    username = request.form.get('username','').strip()
    email = request.form.get('email','').strip()
    password = request.form.get('password','')
    confirm = request.form.get('confirm','')
    err = None
    email = username.lower() + "@apexstudio.game"  # internal placeholder
    birth_month = request.form.get('birth_month','')
    birth_day = request.form.get('birth_day','')
    birth_year = request.form.get('birth_year','')
    gender = request.form.get('gender','')

    if not all([username, password, birth_month, birth_day, birth_year]):
        err = "Please fill in all required fields"
    else:
        ok,msg = valid_username(username)
        if not ok: err=msg
    if err:
        session['auth_err'] = err
        return redirect('/?modal=register')
    try:
        if q("SELECT username FROM used_usernames WHERE username=%s", (username.lower(),), one=True):
            session['auth_err'] = "This username is no longer available"
            return redirect('/?modal=register')
        if q("SELECT id FROM users WHERE username=%s OR email=%s", (username,email), one=True):
            session['auth_err'] = "Username or email already exists"
            return redirect('/?modal=register')
        code = gen_code()
        expires = datetime.now() + timedelta(minutes=10)
        # Create account directly - no email verification needed
        pw_hash = generate_password_hash(password)
        result = q("INSERT INTO users(username,email,password,verified,gender,birth_year) VALUES(%s,%s,%s,TRUE,%s,%s) RETURNING id",
            (username, email, pw_hash, gender, int(birth_year) if birth_year.isdigit() else 0), one=True, commit=True)
        if result:
            session['uid'] = result['id']
            return redirect('/home')
        else:
            session['auth_err'] = "Account creation failed. Try again."
            return redirect('/?modal=register')
    except Exception as e:
        session['auth_err'] = f"Error: {str(e)[:60]}"
        return redirect('/?modal=register')

@app.route('/verify', methods=['GET','POST'])
def verify():
    email = session.get('pending_email')
    username = session.get('pending_uname','User')
    gender = session.get('pending_gender','')
    birth_year = session.get('pending_birth_year','0')
    if not email: return redirect('/')
    err = ""
    if request.method == 'POST':
        code = request.form.get('code','').strip().replace(' ','')
        row = q("SELECT * FROM verify_codes WHERE email=%s", (email,), one=True)
        if not row: err = al("Code not found. Register again.","e")
        elif row['attempts'] >= 5: err = al("Too many attempts. Register again.","e")
        elif datetime.now() > row['expires_at']: err = al("Code expired. Register again.","e")
        elif row['code'] != code:
            q("UPDATE verify_codes SET attempts=attempts+1 WHERE email=%s",(email,),commit=True)
            err = al(f"Wrong code. {5-row['attempts']-1} attempts remaining.","e")
        else:
            q("INSERT INTO users(username,email,password,verified) VALUES(%s,%s,%s,TRUE) ON CONFLICT DO NOTHING",
                (row['username'],email,row['password_hash']),commit=True)
            q("UPDATE users SET gender=%s,birth_year=%s WHERE email=%s",(gender,int(birth_year) if birth_year.isdigit() else 0,email),commit=True)
            q("DELETE FROM verify_codes WHERE email=%s",(email,),commit=True)
            user = q("SELECT id FROM users WHERE email=%s",(email,),one=True)
            session.pop('pending_email',None); session.pop('pending_uname',None)
            if user.get('is_banned'):
                ban_info = q("SELECT reason,expires_at FROM bans WHERE user_id=%s ORDER BY created_at DESC LIMIT 1",(user['id'],),one=True)
                reason = dict(ban_info)['reason'] if ban_info else 'Violation of Terms of Use'
                session['auth_err'] = f"Your account has been banned. Reason: {reason}"
                return redirect('/?modal=login')
            session['uid'] = user['id']
            return redirect('/home')
    masked = email[:2]+"***@"+email.split('@')[1] if '@' in email else email
    body = f"""<div style="background:var(--surf);border-radius:12px;padding:28px;border:1px solid var(--border);max-width:440px;margin:40px auto">
      <div style="font-size:1.5rem;font-weight:900;margin-bottom:6px">Verify Your Email</div>
      <div style="color:var(--muted);margin-bottom:20px">We sent an 8-digit code to <strong style="color:white">{masked}</strong></div>
      {err}
      <form method="POST">
        <div class="fg"><label>8-Digit Code</label>
        <input type="text" name="code" class="code-inp" placeholder="00000000" maxlength="8" inputmode="numeric" required autocomplete="one-time-code"></div>
        <button type="submit" class="btn full">Verify & Continue →</button>
      </form>
      <div style="text-align:center;margin-top:14px;font-size:.82rem;color:var(--muted)">
        Code expires in 10 minutes • <a href="/" style="color:var(--red)">Back</a>
      </div>
    </div>"""
    return f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{CSS}</head><body style='background:var(--bg)'>{body}</body></html>"

@app.route('/forgot', methods=['GET','POST'])
def forgot():
    msg = ""
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        if valid_email(email):
            user = q("SELECT username FROM users WHERE email=%s AND verified=TRUE",(email,),one=True)
            if user:
                code = gen_code()
                expires = datetime.now()+timedelta(minutes=10)
                q("""INSERT INTO reset_codes(email,code,expires_at) VALUES(%s,%s,%s)
                    ON CONFLICT(email) DO UPDATE SET code=%s,expires_at=%s,attempts=0""",
                    (email,code,expires,code,expires),commit=True)
                send_code_email(email,user['username'],code,"reset")
            session['reset_email'] = email
            msg = al("If an account exists, a reset code was sent to that email.","s")
        else: msg = al("Enter a valid email.","e")
    body = f"""<div style="max-width:440px;margin:80px auto;background:var(--surf);border-radius:12px;padding:28px;border:1px solid var(--border)">
      <div style="font-size:1.5rem;font-weight:900;margin-bottom:6px">Forgot Password?</div>
      <div style="color:var(--muted);margin-bottom:20px">Enter your email to receive a reset code</div>
      {msg}
      <form method="POST">
        <div class="fg"><label>Email Address</label>
        <input type="email" name="email" placeholder="your@email.com" required></div>
        <button type="submit" class="btn full">Send Reset Code</button>
      </form>
      {'<div style="text-align:center;margin-top:16px"><a href="/reset-password" style="color:var(--red);font-weight:700">I already have a code →</a></div>' if msg else ''}
      <div style="text-align:center;margin-top:14px"><a href="/?modal=login" style="color:var(--muted);font-size:.85rem">← Back to Login</a></div>
    </div>"""
    return f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{CSS}</head><body style='background:var(--bg)'>{body}</body></html>"

@app.route('/reset-password', methods=['GET','POST'])
def reset_password():
    email = session.get('reset_email')
    if not email: return redirect('/forgot')
    msg = ""
    if request.method == 'POST':
        code = request.form.get('code','').strip()
        new_pw = request.form.get('password','')
        confirm = request.form.get('confirm','')
        ok,emsg = valid_pw(new_pw)
        if not ok: msg = al(emsg,"e")
        elif new_pw != confirm: msg = al("Passwords do not match","e")
        else:
            row = q("SELECT * FROM reset_codes WHERE email=%s",(email,),one=True)
            if not row or row['code'] != code: msg = al("Invalid code","e")
            elif datetime.now() > row['expires_at']: msg = al("Code expired","e")
            else:
                q("UPDATE users SET password=%s WHERE email=%s",(generate_password_hash(new_pw),email),commit=True)
                q("DELETE FROM reset_codes WHERE email=%s",(email,),commit=True)
                session.pop('reset_email',None)
                session['auth_ok'] = "Password updated! Please log in."
                return redirect('/?modal=login')
    body = f"""<div style="max-width:440px;margin:80px auto;background:var(--surf);border-radius:12px;padding:28px;border:1px solid var(--border)">
      <div style="font-size:1.5rem;font-weight:900;margin-bottom:20px">Reset Password</div>
      {msg}
      <form method="POST">
        <div class="fg"><label>Reset Code</label>
        <input type="text" name="code" class="code-inp" placeholder="00000000" maxlength="8" inputmode="numeric" required></div>
        <div class="fg"><label>New Password</label>
        <input type="password" name="password" placeholder="Min 8 chars, 1 uppercase, 1 number" required></div>
        <div class="fg"><label>Confirm New Password</label>
        <input type="password" name="confirm" placeholder="Repeat password" required></div>
        <button type="submit" class="btn full">Reset Password</button>
      </form>
    </div>"""
    return f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{CSS}</head><body style='background:var(--bg)'>{body}</body></html>"

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

# ═══════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════
@app.route('/home')
def home():
    user = get_user_dict()
    if not user: return redirect('/')
    # Connections row
    conn_html = f"""<div class="conn-item"><div class="add-conn">+</div><div class="conn-name">Connect</div></div>"""
    for c in DEMO_CONNECTIONS:
        dot = '<span class="online-dot"></span>' if c['online'] else ''
        conn_html += f"""<div class="conn-item">
          <div class="conn-av" style="background:{c['color']};font-size:1.8rem">{c['icon']}{dot}</div>
          <div class="conn-name">{c['name']}</div>
          <div class="conn-status">{c['status']}</div>
        </div>"""

    # Today's picks
    picks_html = ""
    for g in FEATURED:
        badge = f'<div class="pick-badge">{g["sub"]}</div>' if g['sub'] else ''
        picks_html += f"""<a href="/games"><div class="pick-card">
          <div class="pick-thumb" style="background:linear-gradient(135deg,{g['c']}aa,{g['c']}55)">
            <span>{g['i']}</span>{badge}
          </div>
          <div class="pick-info">
            <div class="pick-title">{g['t']}</div>
            <div class="pick-sub">{g['desc']}</div>
          </div>
        </div></a>"""

    # User games (recent)
    user_games = q("SELECT g.*,u.username,u.avatar_icon,u.avatar_color FROM games g JOIN users u ON g.creator_id=u.id WHERE g.published=TRUE AND g.is_private=FALSE ORDER BY g.plays DESC LIMIT 8") or []
    games_html = ""
    for g in user_games:
        gd = dict(g)
        thumb = f'<img src="{gd["thumbnail_url"]}" alt="" onerror="this.style.display=\'none\'">' if gd.get('thumbnail_url') else ''
        games_html += f"""<a href="/game/{gd['id']}"><div class="game-card">
          <div class="game-thumb" style="background:linear-gradient(135deg,{gd['thumbnail_color']}aa,{gd['thumbnail_color']}55)">
            {thumb}<span style="position:relative;z-index:1">{gd['thumbnail_emoji']}</span>
            <span class="game-plays">👥 {fmt_plays(gd['plays'])}</span>
          </div>
          <div class="game-body">
            <div class="game-title">{gd['title']}</div>
            <div class="game-creator">By {gd['username']}</div>
            <div class="game-meta">
              <span class="game-genre">{gd['genre']}</span>
              <span class="game-likes">👍 {gd['likes']}</span>
            </div>
          </div>
        </div></a>"""

    if not games_html:
        games_html = '<div class="empty"><div class="empty-icon">🎮</div>No games yet. <a href="/create" style="color:var(--red)">Be the first to create one!</a></div>'

    content = f"""
    <div class="page-title">Home</div>
    <div class="section">
      <div class="section-head">
        <div class="section-title">Connections ({len(DEMO_CONNECTIONS)})</div>
        <a href="#" class="see-all">See All ›</a>
      </div>
      <div class="conn-row">{conn_html}</div>
    </div>
    <div class="section">
      <div class="section-head">
        <div class="section-title">Today's Picks</div>
        <div style="font-size:.8rem;color:var(--muted)">A curated selection of daily highlights</div>
      </div>
      <div class="picks-grid">{picks_html}</div>
    </div>
    <div class="section">
      <div class="section-head">
        <div class="section-title">🔥 Community Games</div>
        <a href="/games" class="see-all">See All ›</a>
      </div>
      <div class="games-grid">{games_html}</div>
    </div>"""
    return layout(content, user, "home")

# ═══════════════════════════════════════════════════
# GAMES
# ═══════════════════════════════════════════════════
@app.route('/games')
def games():
    user = get_user_dict()
    if not user: return redirect('/')
    genre = request.args.get('genre','')
    sq = request.args.get('q','')
    sql = "SELECT g.*,u.username,u.avatar_icon,u.avatar_color FROM games g JOIN users u ON g.creator_id=u.id WHERE g.published=TRUE AND (g.is_private=FALSE OR g.creator_id=%s)"
    params.append(user['id'])
    params = []
    if genre: sql += " AND g.genre=%s"; params.append(genre)
    if sq: sql += " AND LOWER(g.title) LIKE %s"; params.append(f"%{sq.lower()}%")
    sql += " ORDER BY g.plays DESC"
    all_games = q(sql, params) or []

    genre_btns = '<a href="/games"><button class="tab ' + ('active' if not genre else '') + '">All</button></a>'
    for g in GENRES:
        genre_btns += f'<a href="/games?genre={g}"><button class="tab {"active" if genre==g else ""}">{g}</button></a>'

    cards = ""
    for g in all_games:
        gd = dict(g)
        thumb = f'<img src="{gd["thumbnail_url"]}" alt="" onerror="this.style.display=\'none\'">' if gd.get('thumbnail_url') else ''
        cards += f"""<a href="/game/{gd['id']}"><div class="game-card">
          <div class="game-thumb" style="background:linear-gradient(135deg,{gd['thumbnail_color']}aa,{gd['thumbnail_color']}55)">
            {thumb}<span style="position:relative;z-index:1">{gd['thumbnail_emoji']}</span>
            <span class="game-plays">👥 {fmt_plays(gd['plays'])}</span>
          </div>
          <div class="game-body">
            <div class="game-title">{gd['title']}</div>
            <div class="game-creator">By {gd['username']}</div>
            <div class="game-meta">
              <span class="game-genre">{gd['genre']}</span>
              <span class="game-likes">👍 {gd['likes']}</span>
            </div>
          </div>
        </div></a>"""

    if not cards:
        cards = '<div class="empty" style="grid-column:1/-1"><div class="empty-icon">🔍</div>No games found. <a href="/create" style="color:var(--red)">Create one!</a></div>'

    content = f"""
    <div class="page-title" style="margin-bottom:16px">Charts</div>
    <div style="overflow-x:auto;padding-bottom:8px;margin-bottom:20px">
      <div class="tabs" style="width:max-content">{genre_btns}</div>
    </div>
    <div class="games-grid">{cards}</div>"""
    return layout(content, user, "games")

# ═══════════════════════════════════════════════════
# GAME DETAIL
# ═══════════════════════════════════════════════════
@app.route('/game/<int:gid>')
def game_detail(gid):
    user = get_user_dict()
    if not user: return redirect('/')
    g = q("SELECT g.*,u.username,u.avatar_icon,u.avatar_color FROM games g JOIN users u ON g.creator_id=u.id WHERE g.id=%s",(gid,),one=True)
    if not g or not g['published']: return redirect('/games')
    gd = dict(g)
    if gd.get('is_private') and gd.get('creator_id') != user['id']: return redirect('/games')

    # Increment plays
    q("UPDATE games SET plays=plays+1 WHERE id=%s",(gid,),commit=True)
    q("INSERT INTO game_plays(user_id,game_id) VALUES(%s,%s)",(user['id'],gid),commit=True)

    # Reviews
    reviews = q("SELECT r.*,u.username,u.avatar_icon,u.avatar_color FROM game_reviews r JOIN users u ON r.user_id=u.id WHERE r.game_id=%s ORDER BY r.created_at DESC LIMIT 20",(gid,)) or []
    my_review = q("SELECT * FROM game_reviews WHERE game_id=%s AND user_id=%s",(gid,user['id']),one=True)

    thumb = f'<img src="{gd["thumbnail_url"]}" alt="" style="width:100%;height:100%;object-fit:cover">' if gd.get('thumbnail_url') else ''
    reviews_html = ""
    for r in reviews:
        rd = dict(r)
        badge = '<span class="review-badge review-like">👍 Liked</span>' if rd['liked'] else '<span class="review-badge review-dislike">👎 Disliked</span>'
        reviews_html += f"""<div class="review-item">
          <div class="review-head">
            <div class="review-av" style="background:{rd['avatar_color']}">{rd['avatar_icon']}</div>
            <span class="review-name">{rd['username']}</span>
            {badge}
          </div>
          {'<div class="review-text">'+rd['comment']+'</div>' if rd.get('comment') else ''}
        </div>"""

    review_form = ""
    if not my_review:
        review_form = f"""<form method="POST" action="/game/{gid}/review" style="margin-top:16px;background:var(--surf2);border-radius:8px;padding:16px;border:1px solid var(--border)">
          <div class="fg"><label>Your Review</label>
          <textarea name="comment" placeholder="What did you think? (optional)"></textarea></div>
          <div style="display:flex;gap:8px">
            <button type="submit" name="liked" value="1" class="btn green">👍 Like</button>
            <button type="submit" name="liked" value="0" class="btn outline">👎 Dislike</button>
          </div>
        </form>"""
    else:
        b = '👍 You liked this' if my_review['liked'] else '👎 You disliked this'
        review_form = f'<div style="margin-top:16px;padding:12px;background:var(--surf2);border-radius:8px;font-size:.85rem;color:var(--muted)">{b}</div>'

    total_ratings = gd['likes'] + gd['dislikes']
    like_pct = int(gd['likes']/total_ratings*100) if total_ratings > 0 else 0

    content = f"""
    <div style="display:grid;grid-template-columns:1fr 320px;gap:24px">
      <div>
        <div class="game-detail-thumb" style="height:360px;background:linear-gradient(135deg,{gd['thumbnail_color']}aa,{gd['thumbnail_color']}44)">
          {thumb}
          <span style="position:relative;z-index:1;font-size:7rem">{gd['thumbnail_emoji']}</span>
        </div>
        <div style="background:var(--surf);border-radius:10px;padding:20px;border:1px solid var(--border)">
          <div style="display:flex;gap:16px;margin-bottom:16px">
            <div class="tabs" style="margin:0">
              <button class="tab active">About</button>
              <button class="tab">Store</button>
              <button class="tab">Servers</button>
            </div>
          </div>
          <p style="color:var(--muted);line-height:1.7;margin-bottom:16px">{gd['description'] or 'No description provided.'}</p>
          <div style="display:flex;gap:16px;flex-wrap:wrap">
            <div><span style="color:var(--muted);font-size:.8rem">Genre</span><div style="font-weight:700">{gd['genre']}</div></div>
            <div><span style="color:var(--muted);font-size:.8rem">Max Players</span><div style="font-weight:700">{gd['max_players']}</div></div>
            <div><span style="color:var(--muted);font-size:.8rem">Total Plays</span><div style="font-weight:700">{fmt_plays(gd['plays'])}</div></div>
            <div><span style="color:var(--muted);font-size:.8rem">Rating</span><div style="font-weight:700;color:var(--green)">{like_pct}% 👍</div></div>
          </div>
        </div>
        <div style="margin-top:20px">
          <div style="font-size:1rem;font-weight:800;margin-bottom:14px">Reviews ({total_ratings})</div>
          {review_form}
          <div style="margin-top:16px">{reviews_html if reviews_html else '<div class="empty"><div class="empty-icon">💬</div>No reviews yet. Be the first!</div>'}</div>
        </div>
      </div>
      <div>
        <button class="play-btn" id="play-btn" onclick="showLauncher(this)">▶ Play</button>
        <div id="launcher-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;align-items:center;justify-content:center">
          <div style="background:#16213e;border:2px solid #1e3a5f;border-radius:20px;padding:40px 36px;max-width:480px;width:92%;text-align:center;box-shadow:0 30px 80px rgba(0,0,0,.8)">
            <div style="font-size:3rem;margin-bottom:14px">🚀</div>
            <div style="font-size:1.4rem;font-weight:900;color:white;margin-bottom:10px">Launch Apex Studio</div>
            <div style="color:#718096;margin-bottom:28px;line-height:1.7;font-size:.95rem">You need the Apex Studio app to play games.<br>Download it for your system below.</div>
            <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px">
              <a href="/download/win64"><button style="padding:13px 24px;background:#e74c3c;color:white;border:none;border-radius:10px;font-weight:800;cursor:pointer;font-size:.95rem;font-family:inherit;width:100%">⬇ Windows 7 / 10 / 11 (64-bit)</button></a>
              <a href="/download/linux64"><button style="padding:13px 24px;background:#2c3e50;color:white;border:none;border-radius:10px;font-weight:800;cursor:pointer;font-size:.95rem;font-family:inherit;width:100%">⬇ Linux 64-bit (Arch, Ubuntu...)</button></a>
            </div>
            <div style="font-size:.78rem;color:#4a5568;margin-bottom:16px">Free download • 64-bit • No subscription required</div>
            <button onclick="closeLauncher()" style="background:transparent;border:1px solid #2d3748;border-radius:8px;color:#718096;cursor:pointer;font-family:inherit;padding:8px 20px">✕ Close</button>
          </div>
        </div>
        <script>
          function showLauncher(btn){{var m=document.getElementById("launcher-modal");m.style.display="flex";}}
          function closeLauncher(){{document.getElementById("launcher-modal").style.display="none";}}
          document.addEventListener("keydown",function(e){{if(e.key==="Escape")closeLauncher();}});
        </script>
        <div class="action-row">
          <a href="/game/{gid}/like"><div class="action-btn {'liked' if my_review and my_review['liked'] else ''}">👍 {gd['likes']}</div></a>
          <a href="/game/{gid}/dislike"><div class="action-btn {'disliked' if my_review and not my_review['liked'] else ''}">👎 {gd['dislikes']}</div></a>
          <div class="action-btn">⭐ Favorite</div>
        </div>
        <div style="background:var(--surf);border-radius:10px;padding:16px;border:1px solid var(--border)">
          <div style="font-size:.85rem;font-weight:800;margin-bottom:12px">Creator</div>
          <a href="/profile/{gd['creator_id']}">
            <div style="display:flex;align-items:center;gap:10px">
              <div style="width:40px;height:40px;border-radius:50%;background:{gd['avatar_color']};display:flex;align-items:center;justify-content:center;font-size:1.3rem">{gd['avatar_icon']}</div>
              <div style="font-weight:700">{gd['username']}</div>
            </div>
          </a>
        </div>
        <div style="background:var(--surf);border-radius:10px;padding:16px;border:1px solid var(--border);margin-top:12px">
          <div style="font-size:.85rem;font-weight:800;margin-bottom:8px">Active Servers</div>
          <div style="color:var(--muted);font-size:.85rem">No active servers right now</div>
        </div>
      </div>
    </div>
    <div style="margin-top:8px"><a href="/games" style="color:var(--muted);font-size:.85rem">← Back to Games</a></div>"""
    return layout(f'<div class="page-title" style="margin-bottom:16px">{gd["title"]}</div>{content}', user)

@app.route('/game/<int:gid>/review', methods=['POST'])
def submit_review(gid):
    user = get_user_dict()
    if not user: return redirect('/')
    liked = request.form.get('liked','1') == '1'
    comment = request.form.get('comment','').strip()[:500]
    existing = q("SELECT id FROM game_reviews WHERE game_id=%s AND user_id=%s",(gid,user['id']),one=True)
    if not existing:
        q("INSERT INTO game_reviews(game_id,user_id,liked,comment) VALUES(%s,%s,%s,%s)",(gid,user['id'],liked,comment),commit=True)
        if liked: q("UPDATE games SET likes=likes+1 WHERE id=%s",(gid,),commit=True)
        else: q("UPDATE games SET dislikes=dislikes+1 WHERE id=%s",(gid,),commit=True)
    return redirect(f'/game/{gid}')

# ═══════════════════════════════════════════════════
# CREATE / PUBLISH GAME
# ═══════════════════════════════════════════════════
@app.route('/create', methods=['GET','POST'])
def create():
    user = get_user_dict()
    if not user: return redirect('/')
    msg = ""
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        desc = request.form.get('description','').strip()
        genre = request.form.get('genre','Adventure')
        emoji = request.form.get('emoji','🎮')
        color = request.form.get('color','#3498db')
        thumb_url = request.form.get('thumbnail_url','').strip()
        max_pl = int(request.form.get('max_players','10'))
        publish = request.form.get('publish','0') == '1'
        is_priv = request.form.get('is_private','0') == '1'
        thumb_url2 = request.form.get('thumbnail_url2','').strip()
        final_thumb = thumb_url2 if thumb_url2 else thumb_url

        if not title: msg = al("Game title is required","e")
        elif len(title) < 3: msg = al("Title must be at least 3 characters","e")
        else:
            try:
                result = q("""INSERT INTO games(title,description,genre,thumbnail_emoji,thumbnail_color,thumbnail_url,creator_id,max_players,published,is_private)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (title,desc,genre,emoji,color,final_thumb,user['id'],max_pl,publish,is_priv),one=True)
                if result:
                    gid = result['id']
                    if publish:
                        return redirect(f'/game/{gid}')
                    else:
                        msg = al(f'Game "<strong>{title}</strong>" saved! <a href="/game/{gid}" style="color:var(--green)">View game</a>','s')
            except Exception as e:
                msg = al(f"Error: {str(e)[:60]}","e")

    # My games list
    my_games = q("SELECT * FROM games WHERE creator_id=%s ORDER BY created_at DESC",(user['id'],)) or []
    my_games_html = ""
    for g in my_games:
        gd = dict(g)
        status = '<span class="badge badge-green">Published</span>' if gd['published'] else '<span class="badge badge-yellow">Draft</span>'
        my_games_html += f"""<div style="display:flex;align-items:center;gap:12px;padding:12px;background:var(--surf2);border-radius:8px;border:1px solid var(--border);margin-bottom:8px">
          <div style="width:48px;height:48px;border-radius:8px;background:{gd['thumbnail_color']};display:flex;align-items:center;justify-content:center;font-size:1.6rem;flex-shrink:0">{gd['thumbnail_emoji']}</div>
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{gd['title']}</div>
            <div style="font-size:.75rem;color:var(--muted)">{gd['genre']} • {fmt_plays(gd['plays'])} plays</div>
          </div>
          {status}
          <div style="display:flex;gap:6px">
            <a href="/edit-game/{gd['id']}"><button style="padding:6px 12px;background:var(--surf);border:1px solid var(--border);border-radius:6px;color:var(--text);font-family:var(--font);font-size:.78rem;font-weight:700;cursor:pointer">Edit</button></a>
            {'<a href="/publish-game/'+str(gd['id'])+'"><button style="padding:6px 12px;background:var(--green);border:none;border-radius:6px;color:white;font-family:var(--font);font-size:.78rem;font-weight:700;cursor:pointer">Publish</button></a>' if not gd['published'] else f'<a href="/game/{gd["id"]}"><button style="padding:6px 12px;background:var(--blue);border:none;border-radius:6px;color:white;font-family:var(--font);font-size:.78rem;font-weight:700;cursor:pointer">View</button></a>'}
          </div>
        </div>"""

    emoji_opts = ''.join([f'<div class="emoji-opt" onclick="document.getElementById(\'sel_emoji\').value=\'{e}\';this.parentNode.querySelectorAll(\'.emoji-opt\').forEach(x=>x.classList.remove(\'sel\'));this.classList.add(\'sel\')">{e}</div>' for e in EMOJIS])
    color_opts = ''.join([f'<div class="color-opt" style="background:{c}" onclick="document.getElementById(\'sel_color\').value=\'{c}\';this.parentNode.querySelectorAll(\'.color-opt\').forEach(x=>x.classList.remove(\'sel\'));this.classList.add(\'sel\')"></div>' for c in COLORS])
    genre_opts = ''.join([f'<option value="{g}">{g}</option>' for g in GENRES])

    content = f"""
    <div style="display:grid;grid-template-columns:1fr 380px;gap:24px">
      <div>
        <div class="page-title" style="margin-bottom:20px">Create Game</div>
        {msg}
        <div style="background:var(--surf);border-radius:10px;padding:24px;border:1px solid var(--border)">
          <form method="POST">
            <div class="fg"><label>Game Title *</label>
            <input type="text" name="title" placeholder="Give your game a great name" required maxlength="50"></div>
            <div class="fg"><label>Description</label>
            <textarea name="description" placeholder="Describe your game..." rows="4"></textarea></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
              <div class="fg"><label>Genre</label>
              <select name="genre">{genre_opts}</select></div>
              <div class="fg"><label>Max Players</label>
              <input type="number" name="max_players" value="10" min="1" max="100"></div>
            </div>
            <div class="fg"><label>Game Icon</label>
            <input type="hidden" name="emoji" id="sel_emoji" value="🎮">
            <div class="emoji-grid">{emoji_opts}</div></div>
            <div class="fg"><label>Card Color</label>
            <input type="hidden" name="color" id="sel_color" value="#3498db">
            <div class="color-grid">{color_opts}</div></div>
            <div class="fg"><label>Thumbnail Image URL <span style="color:var(--muted);font-weight:400">(optional)</span></label>
            <input type="url" name="thumbnail_url" placeholder="https://example.com/image.png"></div>
            <div class="fg"><label>Thumbnail Image URL</label>
            <input type="url" name="thumbnail_url2" placeholder="Paste a direct image link (https://...)">
            <div class="hint">The image players will see on your game card</div></div>
            <div class="fg"><label>Visibility</label>
            <div style="display:flex;gap:10px;margin-top:6px">
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer;background:var(--surf3);border:2px solid var(--border);border-radius:8px;padding:12px 16px;flex:1;transition:all .2s">
                <input type="radio" name="is_private" value="0" checked style="accent-color:var(--red);width:16px;height:16px">
                <div><div style="font-weight:800;font-size:.9rem">🌐 Public</div><div style="font-size:.72rem;color:var(--muted);margin-top:2px">Everyone can see & play</div></div>
              </label>
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer;background:var(--surf3);border:2px solid var(--border);border-radius:8px;padding:12px 16px;flex:1;transition:all .2s">
                <input type="radio" name="is_private" value="1" style="accent-color:var(--red);width:16px;height:16px">
                <div><div style="font-weight:800;font-size:.9rem">🔒 Private</div><div style="font-size:.72rem;color:var(--muted);margin-top:2px">Only you can see it</div></div>
              </label>
            </div></div>
            <div style="display:flex;gap:10px;margin-top:8px">
              <button type="submit" class="btn outline">Save as Draft</button>
              <button type="submit" name="publish" value="1" class="btn green">🌐 Publish</button>
            </div>
          </form>
        </div>
      </div>
      <div>
        <div style="font-size:1rem;font-weight:800;margin-bottom:14px">My Games ({len(my_games)})</div>
        {my_games_html if my_games_html else '<div class="empty"><div class="empty-icon">🎮</div>No games yet. Create your first!</div>'}
      </div>
    </div>"""
    return layout(content, user, "create")

@app.route('/publish-game/<int:gid>')
def publish_game(gid):
    user = get_user_dict()
    if not user: return redirect('/')
    q("UPDATE games SET published=TRUE WHERE id=%s AND creator_id=%s",(gid,user['id']),commit=True)
    return redirect(f'/game/{gid}')

@app.route('/edit-game/<int:gid>', methods=['GET','POST'])
def edit_game(gid):
    user = get_user_dict()
    if not user: return redirect('/')
    g = q("SELECT * FROM games WHERE id=%s AND creator_id=%s",(gid,user['id']),one=True)
    if not g: return redirect('/create')
    gd = dict(g)
    msg = ""
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        desc = request.form.get('description','').strip()
        genre = request.form.get('genre','Adventure')
        emoji = request.form.get('emoji',gd['thumbnail_emoji'])
        color = request.form.get('color',gd['thumbnail_color'])
        thumb_url = request.form.get('thumbnail_url','').strip()
        max_pl = int(request.form.get('max_players','10'))
        q("UPDATE games SET title=%s,description=%s,genre=%s,thumbnail_emoji=%s,thumbnail_color=%s,thumbnail_url=%s,max_players=%s,updated_at=NOW() WHERE id=%s",
            (title,desc,genre,emoji,color,thumb_url,max_pl,gid),commit=True)
        msg = al("Game updated successfully!","s")
        gd = dict(q("SELECT * FROM games WHERE id=%s",(gid,),one=True))

    emoji_opts = ''.join([f'<div class="emoji-opt {"sel" if e==gd["thumbnail_emoji"] else ""}" onclick="document.getElementById(\'sel_emoji\').value=\'{e}\';this.parentNode.querySelectorAll(\'.emoji-opt\').forEach(x=>x.classList.remove(\'sel\'));this.classList.add(\'sel\')">{e}</div>' for e in EMOJIS])
    color_opts = ''.join([f'<div class="color-opt {"sel" if c==gd["thumbnail_color"] else ""}" style="background:{c}" onclick="document.getElementById(\'sel_color\').value=\'{c}\';this.parentNode.querySelectorAll(\'.color-opt\').forEach(x=>x.classList.remove(\'sel\'));this.classList.add(\'sel\')"></div>' for c in COLORS])
    genre_opts = ''.join([f'<option value="{g}" {"selected" if g==gd["genre"] else ""}>{g}</option>' for g in GENRES])

    content = f"""
    <div class="page-title" style="margin-bottom:20px">Edit: {gd['title']}</div>
    {msg}
    <div style="background:var(--surf);border-radius:10px;padding:24px;border:1px solid var(--border);max-width:600px">
      <form method="POST">
        <div class="fg"><label>Game Title</label>
        <input type="text" name="title" value="{gd['title']}" required maxlength="50"></div>
        <div class="fg"><label>Description</label>
        <textarea name="description" rows="4">{gd['description'] or ''}</textarea></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="fg"><label>Genre</label><select name="genre">{genre_opts}</select></div>
          <div class="fg"><label>Max Players</label><input type="number" name="max_players" value="{gd['max_players']}" min="1" max="100"></div>
        </div>
        <div class="fg"><label>Game Icon</label>
        <input type="hidden" name="emoji" id="sel_emoji" value="{gd['thumbnail_emoji']}">
        <div class="emoji-grid">{emoji_opts}</div></div>
        <div class="fg"><label>Card Color</label>
        <input type="hidden" name="color" id="sel_color" value="{gd['thumbnail_color']}">
        <div class="color-grid">{color_opts}</div></div>
        <div class="fg"><label>Thumbnail Image URL</label>
        <input type="url" name="thumbnail_url" value="{gd['thumbnail_url'] or ''}" placeholder="https://..."></div>
        <div style="display:flex;gap:10px">
          <button type="submit" class="btn">Save Changes</button>
          {'<a href="/publish-game/'+str(gid)+'"><button type="button" class="btn green">🌐 Publish</button></a>' if not gd['published'] else f'<a href="/game/{gid}"><button type="button" class="btn blue">View Game</button></a>'}
          <a href="/create"><button type="button" class="btn outline">← Back</button></a>
        </div>
      </form>
    </div>"""
    return layout(content, user, "create")

# ═══════════════════════════════════════════════════
# PROFILE
# ═══════════════════════════════════════════════════
@app.route('/profile/<int:uid>')
def profile(uid):
    user = get_user_dict()
    if not user: return redirect('/')
    target = q("SELECT * FROM users WHERE id=%s",(uid,),one=True)
    if not target: return redirect('/home')
    td = dict(target)
    games = q("SELECT * FROM games WHERE creator_id=%s AND published=TRUE ORDER BY plays DESC",(uid,)) or []
    is_me = uid == user['id']
    joined = td.get('created_at', datetime.now())
    if isinstance(joined,str): joined = datetime.now()

    games_html = ""
    for g in games:
        gd = dict(g)
        games_html += f"""<a href="/game/{gd['id']}"><div class="game-card">
          <div class="game-thumb" style="background:linear-gradient(135deg,{gd['thumbnail_color']}aa,{gd['thumbnail_color']}44)">
            <span style="font-size:2.5rem">{gd['thumbnail_emoji']}</span>
            <span class="game-plays">👥 {fmt_plays(gd['plays'])}</span>
          </div>
          <div class="game-body">
            <div class="game-title">{gd['title']}</div>
            <div class="game-meta"><span class="game-genre">{gd['genre']}</span><span class="game-likes">👍 {gd['likes']}</span></div>
          </div>
        </div></a>"""

    content = f"""
    <div style="background:var(--surf);border-radius:12px;overflow:hidden;border:1px solid var(--border);margin-bottom:20px">
      <div style="height:140px;background:linear-gradient(135deg,{td['avatar_color']}44,var(--surf2))"></div>
      <div style="padding:0 24px 24px;margin-top:-50px">
        <div style="display:flex;align-items:flex-end;gap:16px;margin-bottom:16px">
          <div style="width:90px;height:90px;border-radius:50%;background:{td['avatar_color']};display:flex;align-items:center;justify-content:center;font-size:2.8rem;border:4px solid var(--surf);flex-shrink:0">{td['avatar_icon']}</div>
          <div style="flex:1;padding-bottom:4px">
            <div style="font-size:1.5rem;font-weight:900">{td['username']}</div>
            <div style="font-size:.82rem;color:var(--muted)">Member since {joined.strftime('%B %Y')}</div>
          </div>
          {'<a href="/settings"><button class="btn outline">⚙ Edit Profile</button></a>' if is_me else f'<a href="/add-friend/{uid}"><button class="btn">+ Add Friend</button></a>' + (f' <a href="/admin/ban/{uid}"><button class="btn" style="background:#e74c3c;margin-left:6px">🔨 Ban</button></a>' if user and user.get("username")==ADMIN_USERNAME else '')}
        </div>
        {f'<div style="color:var(--muted);font-size:.9rem;margin-bottom:16px">{td["bio"]}</div>' if td.get('bio') else ''}
        <div style="display:flex;gap:24px">
          <div class="pstat"><div class="pstat-n">{len(games)}</div><div class="pstat-l">Games</div></div>
          <div class="pstat"><div class="pstat-n">⬡ {td.get('apelx',0):,}</div><div class="pstat-l">Apelx</div></div>
        </div>
      </div>
    </div>
    <div style="font-size:1rem;font-weight:800;margin-bottom:14px">Games by {td['username']} ({len(games)})</div>
    <div class="games-grid">{games_html if games_html else '<div class="empty" style="grid-column:1/-1"><div class="empty-icon">🎮</div>No published games yet.</div>'}</div>"""
    return layout(content, user)

# ═══════════════════════════════════════════════════
# AVATAR
# ═══════════════════════════════════════════════════
AVATAR_ITEMS = [
    {"icon":"😊","color":"#e74c3c","name":"Classic Red","price":0},
    {"icon":"😎","color":"#3498db","name":"Cool Blue","price":0},
    {"icon":"🥷","color":"#2c3e50","name":"Ninja Dark","price":500},
    {"icon":"🤖","color":"#95a5a6","name":"Robot","price":800},
    {"icon":"🧙","color":"#8e44ad","name":"Wizard","price":1200},
    {"icon":"🛡️","color":"#c0392b","name":"Knight","price":1500},
    {"icon":"👨‍🚀","color":"#2980b9","name":"Astronaut","price":2000},
    {"icon":"🐉","color":"#e74c3c","name":"Dragon","price":3000},
    {"icon":"🔥","color":"#f39c12","name":"Phoenix","price":5000},
    {"icon":"💎","color":"#1abc9c","name":"Diamond","price":8000},
    {"icon":"⚡","color":"#f1c40f","name":"Lightning","price":10000},
    {"icon":"🌙","color":"#7b1fa2","name":"Moonwalker","price":15000},
]

@app.route('/avatar', methods=['GET','POST'])
def avatar():
    user = get_user_dict()
    if not user: return redirect('/')
    msg = ""
    if request.method == 'POST':
        icon = request.form.get('icon','😊')
        color = request.form.get('color','#e74c3c')
        av = next((a for a in AVATAR_ITEMS if a['icon']==icon and a['color']==color), None)
        if av:
            if av['price'] > 0 and user.get('apelx',0) < av['price']:
                msg = al(f"Not enough Apelx! You need ⬡ {av['price']:,} but have ⬡ {user.get('apelx',0):,}.","e")
            else:
                cost = av['price'] if av['price'] > 0 else 0
                q("UPDATE users SET avatar_icon=%s,avatar_color=%s,apelx=apelx-%s WHERE id=%s",(icon,color,cost,user['id']),commit=True)
                user = get_user_dict()
                msg = al(f"Avatar updated to {icon}!","s")

    cards = ""
    for a in AVATAR_ITEMS:
        is_equipped = user.get('avatar_icon')==a['icon'] and user.get('avatar_color')==a['color']
        can_afford = user.get('apelx',0) >= a['price'] or a['price'] == 0
        cards += f"""<div style="background:var(--surf2);border-radius:10px;padding:16px;text-align:center;border:2px solid {'var(--yellow)' if is_equipped else 'var(--border)'};position:relative">
          {'<div style="position:absolute;top:8px;right:8px;font-size:.65rem;font-weight:800;color:var(--yellow)">✓ ON</div>' if is_equipped else ''}
          <div style="font-size:2.8rem;width:60px;height:60px;border-radius:50%;background:{a['color']};display:flex;align-items:center;justify-content:center;margin:0 auto 10px">{a['icon']}</div>
          <div style="font-size:.85rem;font-weight:800;margin-bottom:4px">{a['name']}</div>
          <div style="font-size:.75rem;color:{'var(--muted)' if a['price']==0 else 'var(--yellow)'};margin-bottom:10px">{'Free' if a['price']==0 else f'⬡ {a["price"]:,}'}</div>
          {'<div style="font-size:.72rem;color:var(--yellow)">Equipped</div>' if is_equipped else f'<form method="POST"><input type="hidden" name="icon" value="{a["icon"]}"><input type="hidden" name="color" value="{a["color"]}"><button type="submit" class="btn {"outline" if not can_afford else ""}" style="padding:7px 14px;font-size:.78rem">{"Equip" if a["price"]==0 else ("Buy & Equip" if can_afford else "Not enough ⬡")}</button></form>'}
        </div>"""

    content = f"""
    <div class="page-title" style="margin-bottom:6px">Avatar Shop</div>
    <div style="color:var(--muted);margin-bottom:20px">Your balance: <strong style="color:var(--yellow)">⬡ {user.get('apelx',0):,} Apelx</strong></div>
    {msg}
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px">{cards}</div>"""
    return layout(content, user, "avatar")

# ═══════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════
@app.route('/settings', methods=['GET','POST'])
def settings():
    user = get_user_dict()
    if not user: return redirect('/')
    tab = request.args.get('tab','account')
    msg = ""

    if request.method == 'POST':
        action = request.form.get('action','')
        if action == 'change_username':
            new = request.form.get('new_username','').strip()
            ok,emsg = valid_username(new)
            if not ok: msg = al(emsg,"e")
            elif user.get('apelx',0) < 1000: msg = al("Need ⬡ 1,000 Apelx to change username","e")
            else:
                if q("SELECT username FROM used_usernames WHERE username=%s",(new.lower(),),one=True):
                    msg = al("This username was previously used and is unavailable","e")
                elif q("SELECT id FROM users WHERE username=%s AND id!=%s",(new,user['id']),one=True):
                    msg = al("Username already taken","e")
                else:
                    q("INSERT INTO used_usernames(username) VALUES(%s) ON CONFLICT DO NOTHING",(user['username'].lower(),),commit=True)
                    q("UPDATE users SET username=%s,apelx=apelx-1000 WHERE id=%s",(new,user['id']),commit=True)
                    msg = al(f"Username changed to <strong>{new}</strong>! ⬡ 1,000 deducted.","s")

        elif action == 'change_password':
            old = request.form.get('old_password','')
            new = request.form.get('new_password','')
            conf = request.form.get('confirm_password','')
            if not check_password_hash(user['password'],old): msg = al("Current password incorrect","e")
            elif new != conf: msg = al("New passwords don't match","e")
            else:
                ok,emsg = valid_pw(new)
                if not ok: msg = al(emsg,"e")
                else:
                    q("UPDATE users SET password=%s WHERE id=%s",(generate_password_hash(new),user['id']),commit=True)
                    msg = al("Password updated successfully!","s")

        elif action == 'link_email':
            new_email = request.form.get('new_email','').strip()
            if not valid_email(new_email): msg = al("Invalid email address","e")
            else:
                existing = q("SELECT id FROM users WHERE email=%s AND id!=%s",(new_email,user['id']),one=True)
                if existing: msg = al("This email is already used by another account","e")
                else:
                    q("UPDATE users SET email=%s,email_verified=FALSE WHERE id=%s",(new_email,user['id']),commit=True)
                    msg = al("Email linked! You can now use it to recover your password.","s")
        elif action == 'update_bio':
            bio = request.form.get('bio','').strip()[:200]
            q("UPDATE users SET bio=%s WHERE id=%s",(bio,user['id']),commit=True)
            msg = al("Bio updated!","s")

        user = get_user_dict()

    real_email = user.get('email','') if not user.get('email','').endswith('@apexstudio.game') else ''
    email_status = ''
    if real_email:
        email_status = f'<span class="badge badge-green">✓ Verified</span>' if user.get('email_verified') else f'<span class="badge badge-yellow">Not verified</span>'
    account_tab = f"""
    <div class="settings-title">Account Info</div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;padding:14px;background:var(--surf3);border-radius:8px;border:1px solid var(--border)">
      <div style="flex:1"><div style="color:var(--muted);font-size:.78rem;margin-bottom:2px">Username</div>
      <div style="font-weight:700">{user['username']}</div></div>
    </div>
    <div class="settings-title" style="margin-top:20px">🔒 Change Password</div>
    <form method="POST" style="margin-bottom:24px">
      <input type="hidden" name="action" value="change_password">
      <div class="fg"><label>Current Password</label>
      <input type="password" name="old_password" placeholder="Enter current password" required></div>
      <div class="fg"><label>New Password</label>
      <input type="password" name="new_password" placeholder="Create new password" required></div>
      <div class="fg"><label>Confirm New Password</label>
      <input type="password" name="confirm_password" placeholder="Repeat new password" required></div>
      <button type="submit" class="btn outline">Update Password</button>
    </form>
    <div class="settings-title">📧 Link Email Address</div>
    {'<div style="margin-bottom:12px;padding:12px;background:var(--surf3);border-radius:8px;display:flex;align-items:center;gap:10px"><span>'+real_email+'</span>'+email_status+'</div>' if real_email else '<div style="color:var(--muted);font-size:.85rem;margin-bottom:12px">No email linked. Add one to recover your account and receive notifications.</div>'}
    <form method="POST">
      <input type="hidden" name="action" value="link_email">
      <div class="fg"><label>Email Address</label>
      <input type="email" name="new_email" placeholder="your@email.com" {'value="'+real_email+'"' if real_email else ''} required></div>
      <button type="submit" class="btn">{'Update Email' if real_email else 'Link Email'}</button>
    </form>
    <div class="settings-title" style="margin-top:24px">Bio</div>
    <form method="POST">
      <input type="hidden" name="action" value="update_bio">
      <div class="fg"><textarea name="bio" placeholder="Tell others about yourself..." rows="3">{user.get('bio','')}</textarea></div>
      <button type="submit" class="btn">Save Bio</button>
    </form>"""

    username_tab = f"""
    <div class="settings-title">Change Username</div>
    {al('Costs ⬡ 1,000 Apelx. Your old username becomes available for others. Balance: ⬡ '+str(user.get('apelx',0)),'i')}
    <form method="POST">
      <input type="hidden" name="action" value="change_username">
      <div class="fg"><label>New Username</label>
      <input type="text" name="new_username" placeholder="Min 4 chars" required minlength="4" maxlength="20"></div>
      <button type="submit" class="btn">Change Username — ⬡ 1,000</button>
    </form>"""

    security_tab = f"""
    <div class="settings-title">Change Password</div>
    <form method="POST">
      <input type="hidden" name="action" value="change_password">
      <div class="fg"><label>Current Password</label>
      <input type="password" name="old_password" placeholder="Enter current password" required></div>
      <div class="fg"><label>New Password</label>
      <input type="password" name="new_password" placeholder="Min 8 chars, 1 uppercase, 1 number" required></div>
      <div class="fg"><label>Confirm New Password</label>
      <input type="password" name="confirm_password" placeholder="Repeat new password" required></div>
      <button type="submit" class="btn outline">Update Password</button>
    </form>"""

    tabs_map = {"account":account_tab,"username":username_tab}
    nav_items = [("account","👤 Account & Password"),("username","✏️ Change Username")]
    nav_html = ''.join([f'<a href="/settings?tab={k}"><div class="settings-nav-item {"active" if tab==k else ""}">{label}</div></a>' for k,label in nav_items])

    content = f"""
    <div class="page-title" style="margin-bottom:20px">Settings</div>
    {msg}
    <div class="settings-wrap">
      <div class="settings-nav">{nav_html}</div>
      <div class="settings-panel">{tabs_map.get(tab,account_tab)}</div>
    </div>"""
    return layout(content, user)

# ═══════════════════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════════════════
@app.route('/search')
def search():
    user = get_user_dict()
    if not user: return redirect('/')
    q_str = request.args.get('q','').strip()
    games = q("SELECT g.*,u.username FROM games g JOIN users u ON g.creator_id=u.id WHERE g.published=TRUE AND LOWER(g.title) LIKE %s ORDER BY g.plays DESC LIMIT 20",
        (f"%{q_str.lower()}%",)) or [] if q_str else []
    cards = ''.join([f"""<a href="/game/{gd['id']}"><div class="game-card">
      <div class="game-thumb" style="background:linear-gradient(135deg,{gd['thumbnail_color']}aa,{gd['thumbnail_color']}44)">
        <span style="font-size:2.5rem">{gd['thumbnail_emoji']}</span>
        <span class="game-plays">👥 {fmt_plays(gd['plays'])}</span>
      </div>
      <div class="game-body">
        <div class="game-title">{gd['title']}</div>
        <div class="game-creator">By {gd['username']}</div>
        <div class="game-meta"><span class="game-genre">{gd['genre']}</span><span class="game-likes">👍 {gd['likes']}</span></div>
      </div>
    </div></a>""" for gd in [dict(g) for g in games]])
    content = f"""
    <div class="page-title" style="margin-bottom:20px">Search: "{q_str}"</div>
    <div class="games-grid">{cards if cards else '<div class="empty" style="grid-column:1/-1"><div class="empty-icon">🔍</div>No results found for "'+q_str+'"</div>'}</div>"""
    return layout(content, user)


# ═══════════════════════════════════════════════════
# GLOBAL CHAT
# ═══════════════════════════════════════════════════
@app.route('/chat', methods=['GET','POST'])
def chat():
    user = get_user_dict()
    if not user: return redirect('/')
    msg_err = ""
    if request.method == 'POST':
        txt = request.form.get('message','').strip()[:300]
        if txt:
            q("INSERT INTO messages(user_id,content) VALUES(%s,%s)",(user['id'],txt),commit=True)
        return redirect('/chat')

    msgs = q("""SELECT m.*,u.username,u.avatar_icon,u.avatar_color
        FROM messages m JOIN users u ON m.user_id=u.id
        ORDER BY m.created_at DESC LIMIT 80""") or []
    msgs = list(reversed(msgs))

    msgs_html = ""
    for m in msgs:
        md = dict(m)
        ts = md['created_at']
        ts_str = ts.strftime('%H:%M') if hasattr(ts,'strftime') else ''
        is_me = md['user_id'] == user['id']
        align = "flex-direction:row-reverse;" if is_me else ""
        bubble_bg = "var(--red)" if is_me else "var(--surf2)"
        radius = "12px 4px 12px 12px" if is_me else "4px 12px 12px 12px"
        name_align = "text-align:right;" if is_me else ""
        msgs_html += f"""<div style="display:flex;gap:10px;align-items:flex-end;{align}margin-bottom:14px">
          <div style="width:32px;height:32px;border-radius:50%;background:{md['avatar_color']};display:flex;align-items:center;justify-content:center;font-size:.95rem;flex-shrink:0">{md['avatar_icon']}</div>
          <div style="max-width:68%">
            <div style="font-size:.7rem;color:var(--muted);margin-bottom:3px;{name_align}">{md['username']} · {ts_str}</div>
            <div style="background:{bubble_bg};padding:10px 14px;border-radius:{radius};font-size:.9rem;line-height:1.5;word-break:break-word">{md['content']}</div>
          </div>
        </div>"""

    online_html = ""
    for conn in DEMO_CONNECTIONS:
        if conn["online"]:
            online_html += f"""<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--border)">
              <div style="width:30px;height:30px;border-radius:50%;background:{conn['color']};display:flex;align-items:center;justify-content:center;font-size:.9rem;flex-shrink:0">{conn['icon']}</div>
              <div>
                <div style="font-size:.82rem;font-weight:700">{conn['name']}</div>
                <div style="font-size:.68rem;color:var(--green)">● {conn['status']}</div>
              </div>
            </div>"""

    content = f"""
    <div class="page-title" style="margin-bottom:16px">💬 Global Chat</div>
    <div style="display:grid;grid-template-columns:1fr 260px;gap:16px;height:calc(100vh - 150px)">
      <div style="display:flex;flex-direction:column;background:var(--surf);border-radius:12px;border:1px solid var(--border);overflow:hidden">
        <div id="msgs" style="flex:1;overflow-y:auto;padding:20px">
          {msgs_html or '<div class="empty"><div class="empty-icon">💬</div>No messages yet!</div>'}
        </div>
        <div style="padding:14px 16px;border-top:1px solid var(--border);background:var(--surf3)">
          <form method="POST" style="display:flex;gap:10px" autocomplete="off">
            <input name="message" placeholder="Type a message... (max 300 chars)" maxlength="300"
              style="flex:1;padding:11px 16px;background:var(--surf2);border:1.5px solid var(--border);border-radius:24px;color:var(--text);font-family:var(--font);font-size:.9rem;outline:none"
              required autofocus>
            <button type="submit" class="btn" style="border-radius:24px;padding:11px 20px">Send</button>
          </form>
        </div>
      </div>
      <div style="background:var(--surf);border-radius:12px;border:1px solid var(--border);padding:16px;overflow-y:auto">
        <div style="font-size:.88rem;font-weight:800;margin-bottom:12px">🟢 Online ({len([x for x in DEMO_CONNECTIONS if x["online"]])})</div>
        {online_html}
      </div>
    </div>
    <script>
      var el=document.getElementById("msgs");
      if(el) el.scrollTop=el.scrollHeight;
      setTimeout(function(){{location.reload()}},6000);
    </script>"""
    return layout(content, user)

@app.route('/download/win64')
def dl_win():
    return redirect('https://github.com')  # placeholder

@app.route('/download/linux64')
def dl_linux():
    return redirect('https://github.com')  # placeholder

if __name__ == '__main__':
    ensure_admin()
    app.run(debug=True)
