from flask import Flask, request, redirect, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, re, psycopg2, psycopg2.extras, random, string, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "apex-studio-ultra-secret-2026")

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
        avatar TEXT DEFAULT 'default',
        bio TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS used_usernames(
        username TEXT PRIMARY KEY,
        released_at TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS verify_codes(
        email TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        username TEXT,
        password_hash TEXT,
        expires_at TIMESTAMP NOT NULL,
        attempts INT DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reset_codes(
        email TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
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
        description TEXT,
        genre TEXT,
        thumbnail TEXT DEFAULT 'default',
        creator_id INTEGER REFERENCES users(id),
        plays INTEGER DEFAULT 0,
        rating FLOAT DEFAULT 0,
        rating_count INTEGER DEFAULT 0,
        published BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews(
        id SERIAL PRIMARY KEY,
        game_id INTEGER REFERENCES games(id),
        user_id INTEGER REFERENCES users(id),
        rating INTEGER CHECK(rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(game_id, user_id)
    )""")
    conn.commit(); c.close(); conn.close()

# ═══════════════════════════════════════════════════
# DEMO DATA
# ═══════════════════════════════════════════════════
DEMO_GAMES = [
    {"title":"Survival Island","genre":"Survival","plays":"2.4M","rating":"4.8","desc":"Survive on a mysterious island with friends!","color":"#ff6b35","icon":"🏝️"},
    {"title":"City Tycoon","genre":"Tycoon","plays":"1.8M","rating":"4.6","desc":"Build your own city from scratch!","color":"#4ecdc4","icon":"🏙️"},
    {"title":"Zombie Rush","genre":"FPS","plays":"3.1M","rating":"4.7","desc":"Fight endless waves of zombies!","color":"#45b7d1","icon":"🧟"},
    {"title":"Racing World","genre":"Racing","plays":"987K","rating":"4.5","desc":"Race against players worldwide!","color":"#f7dc6f","icon":"🏎️"},
    {"title":"Dungeon Quest","genre":"RPG","plays":"1.2M","rating":"4.9","desc":"Epic RPG adventure awaits!","color":"#bb8fce","icon":"⚔️"},
    {"title":"Sky Wars","genre":"PvP","plays":"4.5M","rating":"4.8","desc":"Fight to be the last one standing!","color":"#85c1e9","icon":"☁️"},
    {"title":"Obby Paradise","genre":"Obby","plays":"2.9M","rating":"4.4","desc":"Complete crazy obstacle courses!","color":"#f1948a","icon":"🌈"},
    {"title":"Build Battle","genre":"Building","plays":"1.6M","rating":"4.6","desc":"Build the best and win!","color":"#82e0aa","icon":"🔨"},
]

AVATARS = [
    {"id":"default","name":"Classic","color":"#4a90d9","icon":"😊","price":0},
    {"id":"ninja","name":"Ninja","color":"#2c3e50","icon":"🥷","price":500},
    {"id":"robot","name":"Robot","color":"#95a5a6","icon":"🤖","price":800},
    {"id":"wizard","name":"Wizard","color":"#8e44ad","icon":"🧙","price":1200},
    {"id":"knight","name":"Knight","color":"#c0392b","icon":"🛡️","price":1500},
    {"id":"astronaut","name":"Astronaut","color":"#2980b9","icon":"👨‍🚀","price":2000},
    {"id":"dragon","name":"Dragon","color":"#e74c3c","icon":"🐉","price":3000},
    {"id":"phoenix","name":"Phoenix","color":"#f39c12","icon":"🔥","price":5000},
]

# ═══════════════════════════════════════════════════
# EMAIL
# ═══════════════════════════════════════════════════
def send_email(to, subject, html_body):
    su = os.environ.get("SMTP_EMAIL")
    sp = os.environ.get("SMTP_PASS")
    if not su or not sp:
        print(f"[EMAIL] To:{to} Subject:{subject}")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Apex Studio <{su}>"
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(su, sp)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def email_template(title, content):
    return f"""<!DOCTYPE html><html><body style="background:#1a1a2e;margin:0;padding:40px;font-family:Arial,sans-serif">
<div style="max-width:520px;margin:0 auto;background:#16213e;border-radius:12px;overflow:hidden;border:1px solid #0f3460">
  <div style="background:linear-gradient(135deg,#e74c3c,#c0392b);padding:30px;text-align:center">
    <div style="font-size:2rem;font-weight:900;color:white;letter-spacing:.1em">APEX STUDIO</div>
    <div style="color:rgba(255,255,255,.7);font-size:.8rem;margin-top:4px">Official Notification</div>
  </div>
  <div style="padding:36px">
    <h2 style="color:white;margin:0 0 16px;font-size:1.3rem">{title}</h2>
    {content}
  </div>
  <div style="background:#0d1117;padding:20px;text-align:center">
    <div style="color:#4a5568;font-size:.75rem">© 2026 Apex Studio. All rights reserved.</div>
  </div>
</div></body></html>"""

def code_email(code, username, purpose="verification"):
    content = f"""<p style="color:#a0aec0;margin:0 0 24px">Hello <strong style="color:white">{username}</strong>,</p>
    <p style="color:#a0aec0;margin:0 0 24px">Your {'verification' if purpose=='verification' else 'password reset'} code:</p>
    <div style="background:#0d1117;border:2px solid #e74c3c;border-radius:8px;padding:24px;text-align:center;margin:0 0 24px">
      <div style="font-size:2.5rem;font-weight:900;color:#e74c3c;letter-spacing:.5em">{code}</div>
      <div style="color:#4a5568;font-size:.75rem;margin-top:8px">EXPIRES IN 10 MINUTES</div>
    </div>
    <p style="color:#4a5568;font-size:.8rem;margin:0">If you didn't request this, ignore this email.</p>"""
    subj = "Apex Studio — Verify Your Account" if purpose=="verification" else "Apex Studio — Reset Password"
    return email_template(subj.split("—")[1].strip(), content), subj

def gen_code(): return ''.join(random.choices(string.digits, k=8))

# ═══════════════════════════════════════════════════
# SECURITY
# ═══════════════════════════════════════════════════
def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def check_block(ip):
    try:
        conn=get_db();c=conn.cursor()
        c.execute("SELECT blocked_until FROM login_attempts WHERE ip=%s",(ip,))
        row=c.fetchone();c.close();conn.close()
        if row and row['blocked_until'] and datetime.now()<row['blocked_until']:
            mins=int((row['blocked_until']-datetime.now()).total_seconds()/60)+1
            return True,mins
        return False,0
    except: return False,0

def record_fail(ip):
    try:
        conn=get_db();c=conn.cursor()
        c.execute("""INSERT INTO login_attempts(ip,attempts,last_attempt) VALUES(%s,1,NOW())
            ON CONFLICT(ip) DO UPDATE SET attempts=login_attempts.attempts+1,last_attempt=NOW(),
            blocked_until=CASE WHEN login_attempts.attempts+1>=3
            THEN NOW()+(15*INTERVAL'1 minute') ELSE NULL END""",(ip,))
        c.execute("SELECT attempts FROM login_attempts WHERE ip=%s",(ip,))
        row=c.fetchone();conn.commit();c.close();conn.close()
        return row['attempts'] if row else 1
    except: return 1

def clear_block(ip):
    try:
        conn=get_db();c=conn.cursor()
        c.execute("DELETE FROM login_attempts WHERE ip=%s",(ip,))
        conn.commit();c.close();conn.close()
    except: pass

# ═══════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════
def valid_email(e): return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$',e))
def valid_username(u):
    if len(u)<4: return False,"Username must be at least 4 characters"
    if len(u)>20: return False,"Username must be under 20 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$',u): return False,"Only letters, numbers, and underscores allowed"
    return True,"ok"
def valid_pw(pw):
    if len(pw)<8: return False,"Password must be at least 8 characters"
    if not re.search(r'[A-Z]',pw): return False,"Must include at least 1 uppercase letter"
    if not re.search(r'[0-9]',pw): return False,"Must include at least 1 number"
    return True,"ok"

# ═══════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════
CSS = """<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{--red:#e74c3c;--red2:#c0392b;--bg:#1a1a2e;--surface:#16213e;--surface2:#0f3460;--border:#1e3a5f;--text:#e2e8f0;--muted:#718096;--green:#2ecc71;--yellow:#f1c40f;--blue:#3498db;--font:'Nunito',sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
html,body{min-height:100vh;background:var(--bg);color:var(--text);font-family:var(--font)}
a{text-decoration:none;color:inherit}

/* NAV */
.nav{background:var(--surface);border-bottom:2px solid var(--red);padding:0 24px;display:flex;align-items:center;gap:16px;height:56px;position:sticky;top:0;z-index:100;box-shadow:0 2px 20px rgba(0,0,0,.5)}
.nav-logo{font-size:1.3rem;font-weight:900;color:var(--red);letter-spacing:.05em;margin-right:8px}
.nav-links{display:flex;gap:4px;flex:1}
.nav-link{padding:6px 14px;border-radius:6px;font-size:.88rem;font-weight:700;color:var(--muted);transition:all .2s;cursor:pointer}
.nav-link:hover,.nav-link.active{background:var(--surface2);color:var(--text)}
.nav-right{display:flex;align-items:center;gap:10px;margin-left:auto}
.nav-apelx{background:var(--surface2);border:1px solid var(--yellow);border-radius:20px;padding:4px 12px;font-size:.82rem;font-weight:800;color:var(--yellow);display:flex;align-items:center;gap:6px}
.nav-avatar{width:32px;height:32px;border-radius:50%;background:var(--red);display:flex;align-items:center;justify-content:center;font-size:1rem;cursor:pointer;border:2px solid var(--surface2)}
.nav-btn{padding:7px 16px;background:var(--red);color:white;border-radius:20px;font-size:.85rem;font-weight:800;cursor:pointer;border:none;transition:all .2s}
.nav-btn:hover{background:var(--red2);transform:translateY(-1px)}
.nav-btn.outline{background:transparent;border:2px solid var(--red);color:var(--red)}
.nav-btn.outline:hover{background:var(--red);color:white}

/* LAYOUT */
.container{max-width:1200px;margin:0 auto;padding:24px}
.page-inner{padding:24px}

/* HERO (landing) */
.hero{min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;padding:40px 20px;background:radial-gradient(ellipse 800px 600px at 50% 30%,rgba(231,76,60,.08),transparent)}
.hero-logo{font-size:4rem;font-weight:900;color:white;margin-bottom:8px}
.hero-logo span{color:var(--red)}
.hero-sub{font-size:1.1rem;color:var(--muted);margin-bottom:40px;max-width:500px}
.hero-btns{display:flex;gap:16px;justify-content:center;flex-wrap:wrap}
.hero-btn{padding:14px 36px;border-radius:8px;font-size:1rem;font-weight:800;cursor:pointer;border:none;transition:all .2s;font-family:var(--font)}
.hero-btn.primary{background:var(--red);color:white;box-shadow:0 4px 20px rgba(231,76,60,.4)}
.hero-btn.primary:hover{background:var(--red2);transform:translateY(-2px);box-shadow:0 6px 30px rgba(231,76,60,.5)}
.hero-btn.secondary{background:var(--surface);color:var(--text);border:2px solid var(--border)}
.hero-btn.secondary:hover{border-color:var(--red);color:var(--red)}
.hero-stats{display:flex;gap:40px;justify-content:center;margin-top:48px;flex-wrap:wrap}
.hero-stat{text-align:center}
.hero-stat-num{font-size:2rem;font-weight:900;color:white}
.hero-stat-label{font-size:.8rem;color:var(--muted);margin-top:2px}

/* AUTH MODAL */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;z-index:200;backdrop-filter:blur(4px)}
.modal{background:var(--surface);border-radius:16px;padding:36px;width:100%;max-width:420px;border:1px solid var(--border);box-shadow:0 20px 60px rgba(0,0,0,.8);position:relative}
.modal-title{font-size:1.5rem;font-weight:900;margin-bottom:4px}
.modal-sub{font-size:.85rem;color:var(--muted);margin-bottom:24px}
.modal-close{position:absolute;top:16px;right:16px;background:var(--surface2);border:none;color:var(--muted);width:32px;height:32px;border-radius:50%;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center}

/* FORMS */
.fg{margin-bottom:16px}
.fg label{display:block;font-size:.78rem;font-weight:700;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em}
.fg input,.fg select,.fg textarea{width:100%;padding:11px 14px;background:var(--bg);border:1.5px solid var(--border);border-radius:8px;color:var(--text);font-family:var(--font);font-size:.95rem;outline:none;transition:all .2s}
.fg input:focus,.fg select:focus,.fg textarea:focus{border-color:var(--red);background:rgba(231,76,60,.04)}
.fg input::placeholder{color:var(--muted)}
.fg textarea{resize:vertical;min-height:80px}
.hint{font-size:.72rem;color:var(--muted);margin-top:5px}
.code-inp{text-align:center;font-size:2rem;font-weight:900;letter-spacing:.4em;color:var(--red);border-color:var(--red) !important}
.btn-full{width:100%;padding:12px;background:var(--red);color:white;border:none;border-radius:8px;font-size:.95rem;font-weight:800;cursor:pointer;font-family:var(--font);transition:all .2s;margin-top:4px}
.btn-full:hover{background:var(--red2);transform:translateY(-1px)}
.btn-full.outline{background:transparent;border:2px solid var(--red);color:var(--red)}
.btn-full.outline:hover{background:var(--red);color:white}
.btn-full.green{background:var(--green)}
.btn-full.green:hover{background:#27ae60}
.form-switch{text-align:center;margin-top:16px;font-size:.85rem;color:var(--muted)}
.form-switch a{color:var(--red);font-weight:700}

/* ALERT */
.al{padding:11px 14px;border-radius:8px;font-size:.85rem;margin-bottom:16px;display:flex;gap:8px;align-items:flex-start;line-height:1.5}
.al-e{background:rgba(231,76,60,.1);border:1px solid rgba(231,76,60,.3);color:#fc8181}
.al-s{background:rgba(46,204,113,.1);border:1px solid rgba(46,204,113,.3);color:#68d391}
.al-i{background:rgba(52,152,219,.1);border:1px solid rgba(52,152,219,.3);color:#90cdf4}

/* GAME CARDS */
.section-title{font-size:1.3rem;font-weight:900;margin-bottom:16px;display:flex;align-items:center;gap:10px}
.section-title span{font-size:.8rem;font-weight:600;color:var(--muted);background:var(--surface2);padding:3px 10px;border-radius:20px}
.games-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:32px}
.game-card{background:var(--surface);border-radius:12px;overflow:hidden;border:1px solid var(--border);transition:all .2s;cursor:pointer}
.game-card:hover{transform:translateY(-4px);border-color:var(--red);box-shadow:0 8px 30px rgba(0,0,0,.4)}
.game-thumb{height:120px;display:flex;align-items:center;justify-content:center;font-size:3rem;position:relative}
.game-plays{position:absolute;bottom:6px;right:8px;background:rgba(0,0,0,.7);border-radius:10px;padding:2px 8px;font-size:.7rem;color:white;font-weight:700}
.game-info{padding:12px}
.game-title{font-size:.9rem;font-weight:800;margin-bottom:4px}
.game-meta{display:flex;align-items:center;justify-content:space-between}
.game-genre{font-size:.72rem;color:var(--muted);background:var(--surface2);padding:2px 8px;border-radius:10px}
.game-rating{font-size:.75rem;color:var(--yellow);font-weight:700}

/* AVATAR GRID */
.avatar-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px}
.avatar-card{background:var(--surface);border-radius:12px;padding:16px;text-align:center;border:2px solid var(--border);cursor:pointer;transition:all .2s}
.avatar-card:hover{border-color:var(--red);transform:translateY(-2px)}
.avatar-card.owned{border-color:var(--green)}
.avatar-card.equipped{border-color:var(--yellow);background:rgba(241,196,15,.05)}
.avatar-icon{font-size:2.5rem;margin-bottom:8px}
.avatar-name{font-size:.85rem;font-weight:800;margin-bottom:4px}
.avatar-price{font-size:.75rem;font-weight:700}

/* PROFILE */
.profile-header{background:var(--surface);border-radius:16px;padding:28px;margin-bottom:20px;border:1px solid var(--border);display:flex;align-items:center;gap:24px}
.profile-av{width:80px;height:80px;border-radius:50%;background:var(--red);display:flex;align-items:center;justify-content:center;font-size:2.5rem;border:4px solid var(--surface2);flex-shrink:0}
.profile-name{font-size:1.6rem;font-weight:900}
.profile-joined{font-size:.82rem;color:var(--muted);margin-top:4px}
.profile-stats{display:flex;gap:24px;margin-top:12px;flex-wrap:wrap}
.pstat{text-align:center}
.pstat-num{font-size:1.2rem;font-weight:900;color:var(--yellow)}
.pstat-label{font-size:.72rem;color:var(--muted)}

/* SETTINGS */
.settings-section{background:var(--surface);border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid var(--border)}
.settings-title{font-size:1rem;font-weight:800;margin-bottom:16px;color:var(--text)}

/* STORE */
.store-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px}
.store-card{background:var(--surface);border-radius:12px;padding:20px;text-align:center;border:1px solid var(--border);transition:all .2s}
.store-card:hover{border-color:var(--yellow);transform:translateY(-2px)}
.store-amount{font-size:2rem;font-weight:900;color:var(--yellow);margin-bottom:4px}
.store-apelx{font-size:.8rem;color:var(--muted);margin-bottom:16px}
.store-price{font-size:1.1rem;font-weight:800;color:white;margin-bottom:12px}
.store-btn{width:100%;padding:10px;background:var(--yellow);color:var(--bg);border:none;border-radius:8px;font-weight:900;cursor:pointer;font-family:var(--font);font-size:.9rem}
.store-btn:hover{background:#d4ac0d}

/* TABS */
.tabs{display:flex;gap:4px;margin-bottom:24px;background:var(--surface);padding:6px;border-radius:10px;width:fit-content}
.tab{padding:8px 20px;border-radius:7px;font-size:.88rem;font-weight:700;color:var(--muted);cursor:pointer;transition:all .2s;border:none;background:transparent;font-family:var(--font)}
.tab.active{background:var(--red);color:white}

/* MISC */
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.72rem;font-weight:700}
.badge-red{background:rgba(231,76,60,.2);color:var(--red);border:1px solid rgba(231,76,60,.3)}
.badge-green{background:rgba(46,204,113,.2);color:var(--green);border:1px solid rgba(46,204,113,.3)}
.badge-yellow{background:rgba(241,196,15,.2);color:var(--yellow);border:1px solid rgba(241,196,15,.3)}
.divider{height:1px;background:var(--border);margin:20px 0}
.empty{text-align:center;padding:48px 20px;color:var(--muted);font-size:.95rem}
.empty-icon{font-size:3rem;margin-bottom:12px}

/* BLOCKED */
.blocked{text-align:center;padding:24px;background:rgba(231,76,60,.08);border:1px solid rgba(231,76,60,.2);border-radius:10px}

/* RESPONSIVE */
@media(max-width:600px){
  .hero-logo{font-size:2.5rem}
  .nav-links{display:none}
  .profile-header{flex-direction:column;text-align:center}
}
</style>"""

def nav(user=None):
    if user:
        av = next((a for a in AVATARS if a['id']==user.get('avatar','default')), AVATARS[0])
        return f"""<nav class="nav">
          <a href="/" class="nav-logo">APEX<span style="color:white">STUDIO</span></a>
          <div class="nav-links">
            <a href="/games" class="nav-link">🎮 Games</a>
            <a href="/avatars" class="nav-link">👤 Avatars</a>
            <a href="/store" class="nav-link">💰 Store</a>
          </div>
          <div class="nav-right">
            <div class="nav-apelx">⬡ {user.get('apelx',0):,} Apelx</div>
            <a href="/profile" class="nav-avatar" title="{user['username']}">{av['icon']}</a>
            <a href="/logout"><button class="nav-btn outline">Log Out</button></a>
          </div>
        </nav>"""
    return f"""<nav class="nav">
      <a href="/" class="nav-logo">APEX<span style="color:white">STUDIO</span></a>
      <div class="nav-links">
        <a href="/games" class="nav-link">🎮 Games</a>
        <a href="/store" class="nav-link">💰 Store</a>
      </div>
      <div class="nav-right">
        <a href="/?modal=login"><button class="nav-btn outline">Log In</button></a>
        <a href="/?modal=register"><button class="nav-btn">Sign Up</button></a>
      </div>
    </nav>"""

def page(title, body, user=None):
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Apex Studio</title>{CSS}</head>
<body>{nav(user)}{body}</body></html>"""

def al(msg, kind="e"):
    icons={"e":"⚠","s":"✓","i":"ℹ"}
    return f'<div class="al al-{kind}"><span>{icons.get(kind,"!")}</span><span>{msg}</span></div>'

def get_user():
    if 'uid' not in session: return None
    try:
        conn=get_db();c=conn.cursor()
        c.execute("SELECT * FROM users WHERE id=%s",(session['uid'],))
        u=c.fetchone();c.close();conn.close()
        return dict(u) if u else None
    except: return None

# ═══════════════════════════════════════════════════
# LANDING
# ═══════════════════════════════════════════════════
@app.route('/')
def index():
    user = get_user()
    if user: return redirect('/games')
    modal = request.args.get('modal','')

    modal_html = ""
    if modal == 'login':
        modal_html = login_modal()
    elif modal == 'register':
        modal_html = register_modal()

    games_preview = ''.join([f"""
    <div class="game-card" style="flex-shrink:0;width:160px">
      <div class="game-thumb" style="background:linear-gradient(135deg,{g['color']}33,{g['color']}11)">
        <span>{g['icon']}</span>
        <span class="game-plays">{g['plays']}</span>
      </div>
      <div class="game-info">
        <div class="game-title">{g['title']}</div>
        <div class="game-meta">
          <span class="game-genre">{g['genre']}</span>
          <span class="game-rating">★ {g['rating']}</span>
        </div>
      </div>
    </div>""" for g in DEMO_GAMES[:6]])

    body = f"""
    <div class="hero">
      <div class="hero-logo">APEX<span>STUDIO</span></div>
      <p class="hero-sub">The ultimate platform for gaming and creativity. Play millions of games or create your own!</p>
      <div class="hero-btns">
        <a href="/?modal=register"><button class="hero-btn primary">Create Account</button></a>
        <a href="/?modal=login"><button class="hero-btn secondary">Log In</button></a>
      </div>
      <div class="hero-stats">
        <div class="hero-stat"><div class="hero-stat-num">50M+</div><div class="hero-stat-label">Active Players</div></div>
        <div class="hero-stat"><div class="hero-stat-num">2M+</div><div class="hero-stat-label">Games</div></div>
        <div class="hero-stat"><div class="hero-stat-num">100K+</div><div class="hero-stat-label">Creators</div></div>
      </div>
      <div style="margin-top:48px;width:100%;max-width:1000px">
        <div style="font-size:1.1rem;font-weight:800;margin-bottom:16px;text-align:left">🔥 Popular Games</div>
        <div style="display:flex;gap:16px;overflow-x:auto;padding-bottom:8px">{games_preview}</div>
      </div>
    </div>
    {modal_html}"""
    return page("Home", body)

def login_modal(err=""):
    return f"""<div class="modal-bg" onclick="if(event.target===this)window.location='/'">
    <div class="modal">
      <button class="modal-close" onclick="window.location='/'">✕</button>
      <div class="modal-title">Welcome back!</div>
      <div class="modal-sub">Log in to your Apex Studio account</div>
      {err}
      <form method="POST" action="/login">
        <div class="fg"><label>Username or Email</label>
        <input type="text" name="username" placeholder="Enter username or email" required></div>
        <div class="fg"><label>Password</label>
        <input type="password" name="password" placeholder="Enter password" required></div>
        <div style="text-align:right;margin-bottom:12px">
          <a href="/forgot" style="font-size:.82rem;color:var(--red)">Forgot password?</a>
        </div>
        <button type="submit" class="btn-full">Log In</button>
      </form>
      <div class="form-switch">Don't have an account? <a href="/?modal=register">Sign Up</a></div>
    </div></div>"""

def register_modal(err=""):
    return f"""<div class="modal-bg" onclick="if(event.target===this)window.location='/'">
    <div class="modal">
      <button class="modal-close" onclick="window.location='/'">✕</button>
      <div class="modal-title">Join Apex Studio</div>
      <div class="modal-sub">Create your free account today</div>
      {err}
      <form method="POST" action="/register">
        <div class="fg"><label>Username</label>
        <input type="text" name="username" placeholder="Choose a username (min 4 chars)" required minlength="4" maxlength="20"></div>
        <div class="fg"><label>Email Address</label>
        <input type="email" name="email" placeholder="your@email.com" required></div>
        <div class="fg"><label>Password</label>
        <input type="password" name="password" placeholder="Min 8 chars, 1 uppercase, 1 number" required>
        <div class="hint">• At least 8 characters • 1 uppercase letter • 1 number</div></div>
        <div class="fg"><label>Confirm Password</label>
        <input type="password" name="confirm" placeholder="Repeat your password" required></div>
        <button type="submit" class="btn-full">Create Account →</button>
      </form>
      <div class="form-switch">Already have an account? <a href="/?modal=login">Log In</a></div>
    </div></div>"""

# ═══════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════
@app.route('/login', methods=['POST'])
def login():
    try: init_db()
    except: pass
    ip = get_ip()
    blocked, mins = check_block(ip)
    if blocked:
        return page("Log In", f"""<div class="container" style="max-width:460px;margin-top:60px">
          <div class="blocked"><div style="font-size:2rem;margin-bottom:8px">⛔</div>
          <div style="font-weight:800;margin-bottom:6px">Access Temporarily Blocked</div>
          <div style="color:var(--muted);font-size:.9rem">Too many failed attempts. Try again in {mins} minute{'s' if mins!=1 else ''}.</div>
          </div><div style="text-align:center;margin-top:16px"><a href="/" style="color:var(--red)">← Back to Home</a></div>
          </div>""")

    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    try:
        conn=get_db();c=conn.cursor()
        c.execute("SELECT * FROM users WHERE (username=%s OR email=%s) AND verified=TRUE",(username,username))
        user=c.fetchone();c.close();conn.close()
        if user and check_password_hash(user['password'],password):
            clear_block(ip)
            session['uid']=user['id']
            return redirect('/games')
        else:
            n=record_fail(ip); rem=3-n
            blocked2,mins2=check_block(ip)
            if blocked2:
                err=al(f"Too many failed attempts. Blocked for {mins2} minutes.","e")
            else:
                err=al(f"Incorrect username or password. {rem} attempt{'s' if rem!=1 else ''} remaining.","e")
            return page("Log In", login_modal(err))
    except Exception as e:
        return page("Log In", login_modal(al(f"Error: {str(e)[:60]}","e")))

@app.route('/register', methods=['POST'])
def register():
    try: init_db()
    except: pass

    username=request.form.get('username','').strip()
    email=request.form.get('email','').strip()
    password=request.form.get('password','')
    confirm=request.form.get('confirm','')

    err=None
    if not all([username,email,password,confirm]): err="All fields are required"
    else:
        ok,msg=valid_username(username)
        if not ok: err=msg
        elif not valid_email(email): err="Invalid email format"
        elif password!=confirm: err="Passwords do not match"
        else:
            ok2,msg2=valid_pw(password)
            if not ok2: err=msg2

    if err:
        return page("Sign Up", register_modal(al(err,"e")))

    try:
        conn=get_db();c=conn.cursor()
        # Check used usernames
        c.execute("SELECT username FROM used_usernames WHERE username=%s",(username.lower(),))
        if c.fetchone():
            c.close();conn.close()
            return page("Sign Up", register_modal(al("This username is no longer available","e")))
        c.execute("SELECT id FROM users WHERE username=%s OR email=%s",(username,email))
        if c.fetchone():
            c.close();conn.close()
            return page("Sign Up", register_modal(al("Username or email already exists","e")))

        code=gen_code()
        expires=datetime.now()+timedelta(minutes=10)
        c.execute("""INSERT INTO verify_codes(email,code,username,password_hash,expires_at)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(email) DO UPDATE SET
            code=%s,username=%s,password_hash=%s,expires_at=%s,attempts=0""",
            (email,code,username,generate_password_hash(password),expires,
             code,username,generate_password_hash(password),expires))
        conn.commit();c.close();conn.close()

        html,subj=code_email(code,username,"verification")
        send_email(email,subj,html)
        session['pending_email']=email
        session['pending_uname']=username
        return redirect('/verify')
    except Exception as e:
        return page("Sign Up", register_modal(al(f"Error: {str(e)[:60]}","e")))

@app.route('/verify', methods=['GET','POST'])
def verify():
    email=session.get('pending_email')
    username=session.get('pending_uname','User')
    if not email: return redirect('/')
    err=""

    if request.method=='POST':
        code=request.form.get('code','').strip().replace(' ','')
        try:
            conn=get_db();c=conn.cursor()
            c.execute("SELECT * FROM verify_codes WHERE email=%s",(email,))
            row=c.fetchone()
            if not row: err=al("Code not found. Please register again.","e")
            elif row['attempts']>=5: err=al("Too many attempts. Please register again.","e")
            elif datetime.now()>row['expires_at']: err=al("Code expired. Please register again.","e")
            elif row['code']!=code:
                c.execute("UPDATE verify_codes SET attempts=attempts+1 WHERE email=%s",(email,))
                conn.commit(); rem=5-row['attempts']-1
                err=al(f"Wrong code. {rem} attempt{'s' if rem!=1 else ''} remaining.","e")
            else:
                c.execute("INSERT INTO users(username,email,password,verified) VALUES(%s,%s,%s,TRUE) ON CONFLICT DO NOTHING",
                    (row['username'],email,row['password_hash']))
                c.execute("DELETE FROM verify_codes WHERE email=%s",(email,))
                conn.commit()
                c.execute("SELECT id FROM users WHERE email=%s",(email,))
                u=c.fetchone();c.close();conn.close()
                session.pop('pending_email',None);session.pop('pending_uname',None)
                session['uid']=u['id']
                return redirect('/games')
            if conn: c.close();conn.close()
        except Exception as ex:
            err=al(f"Error: {str(ex)[:60]}","e")

    masked=email[:2]+"***@"+email.split('@')[1] if '@' in email else email
    body=f"""<div class="container" style="max-width:460px;margin-top:60px">
      <div style="text-align:center;margin-bottom:28px">
        <div style="font-size:1.8rem;font-weight:900">Verify Your Email</div>
        <div style="color:var(--muted);margin-top:6px;font-size:.9rem">We sent an 8-digit code to <strong style="color:white">{masked}</strong></div>
      </div>
      <div style="background:var(--surface);border-radius:12px;padding:28px;border:1px solid var(--border)">
        {err}
        <form method="POST">
          <div class="fg"><label>Enter 8-Digit Code</label>
          <input type="text" name="code" class="code-inp" placeholder="00000000"
            maxlength="8" pattern="[0-9]{{8}}" inputmode="numeric" required autocomplete="one-time-code"></div>
          <button type="submit" class="btn-full">Verify & Continue →</button>
        </form>
        <div style="text-align:center;margin-top:14px;font-size:.82rem;color:var(--muted)">
          Code expires in 10 minutes • <a href="/register" style="color:var(--red)">Back</a>
        </div>
      </div>
    </div>"""
    return page("Verify Email", body)

@app.route('/forgot', methods=['GET','POST'])
def forgot():
    msg=""
    if request.method=='POST':
        email=request.form.get('email','').strip()
        if valid_email(email):
            try:
                conn=get_db();c=conn.cursor()
                c.execute("SELECT username FROM users WHERE email=%s AND verified=TRUE",(email,))
                u=c.fetchone()
                if u:
                    code=gen_code()
                    expires=datetime.now()+timedelta(minutes=10)
                    c.execute("""INSERT INTO reset_codes(email,code,expires_at) VALUES(%s,%s,%s)
                        ON CONFLICT(email) DO UPDATE SET code=%s,expires_at=%s,attempts=0""",
                        (email,code,expires,code,expires))
                    conn.commit()
                    html,subj=code_email(code,u['username'],"reset")
                    send_email(email,subj,html)
                c.close();conn.close()
                msg=al("If an account exists with that email, a reset code was sent.","s")
                session['reset_email']=email
                return redirect('/reset-password')
            except: msg=al("An error occurred. Please try again.","e")
        else: msg=al("Please enter a valid email address.","e")

    body=f"""<div class="container" style="max-width:440px;margin-top:60px">
      <div style="text-align:center;margin-bottom:28px">
        <div style="font-size:1.8rem;font-weight:900">Forgot Password?</div>
        <div style="color:var(--muted);font-size:.9rem;margin-top:6px">Enter your email to receive a reset code</div>
      </div>
      <div style="background:var(--surface);border-radius:12px;padding:28px;border:1px solid var(--border)">
        {msg}
        <form method="POST">
          <div class="fg"><label>Email Address</label>
          <input type="email" name="email" placeholder="your@email.com" required></div>
          <button type="submit" class="btn-full">Send Reset Code →</button>
        </form>
        <div style="text-align:center;margin-top:14px"><a href="/?modal=login" style="color:var(--red);font-size:.85rem">← Back to Login</a></div>
      </div>
    </div>"""
    return page("Forgot Password", body)

@app.route('/reset-password', methods=['GET','POST'])
def reset_password():
    email=session.get('reset_email')
    if not email: return redirect('/forgot')
    msg=""

    if request.method=='POST':
        code=request.form.get('code','').strip()
        new_pw=request.form.get('password','')
        confirm=request.form.get('confirm','')
        ok,emsg=valid_pw(new_pw)
        if not ok: msg=al(emsg,"e")
        elif new_pw!=confirm: msg=al("Passwords do not match","e")
        else:
            try:
                conn=get_db();c=conn.cursor()
                c.execute("SELECT * FROM reset_codes WHERE email=%s",(email,))
                row=c.fetchone()
                if not row or row['code']!=code: msg=al("Invalid or expired code","e")
                elif datetime.now()>row['expires_at']: msg=al("Code expired. Request a new one.","e")
                else:
                    c.execute("UPDATE users SET password=%s WHERE email=%s",
                        (generate_password_hash(new_pw),email))
                    c.execute("DELETE FROM reset_codes WHERE email=%s",(email,))
                    conn.commit();c.close();conn.close()
                    session.pop('reset_email',None)
                    return page("Password Reset", f"""<div class="container" style="max-width:440px;margin-top:80px;text-align:center">
                      <div style="font-size:3rem;margin-bottom:16px">✅</div>
                      <div style="font-size:1.5rem;font-weight:900;margin-bottom:8px">Password Updated!</div>
                      <div style="color:var(--muted);margin-bottom:24px">Your password has been successfully changed.</div>
                      <a href="/?modal=login"><button class="btn-full" style="max-width:200px">Log In Now →</button></a>
                    </div>""")
                if conn: c.close();conn.close()
            except Exception as ex: msg=al(f"Error: {str(ex)[:60]}","e")

    body=f"""<div class="container" style="max-width:440px;margin-top:60px">
      <div style="text-align:center;margin-bottom:28px">
        <div style="font-size:1.8rem;font-weight:900">Reset Password</div>
        <div style="color:var(--muted);font-size:.9rem;margin-top:6px">Enter the code sent to your email</div>
      </div>
      <div style="background:var(--surface);border-radius:12px;padding:28px;border:1px solid var(--border)">
        {msg}
        <form method="POST">
          <div class="fg"><label>8-Digit Code</label>
          <input type="text" name="code" class="code-inp" placeholder="00000000" maxlength="8" inputmode="numeric" required></div>
          <div class="fg"><label>New Password</label>
          <input type="password" name="password" placeholder="Min 8 chars, 1 uppercase, 1 number" required></div>
          <div class="fg"><label>Confirm New Password</label>
          <input type="password" name="confirm" placeholder="Repeat new password" required></div>
          <button type="submit" class="btn-full">Reset Password →</button>
        </form>
      </div>
    </div>"""
    return page("Reset Password", body)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ═══════════════════════════════════════════════════
# GAMES
# ═══════════════════════════════════════════════════
@app.route('/games')
def games():
    user=get_user()
    if not user: return redirect('/')
    cards=''.join([f"""
    <div class="game-card">
      <div class="game-thumb" style="background:linear-gradient(135deg,{g['color']}33,{g['color']}11)">
        <span>{g['icon']}</span><span class="game-plays">👥 {g['plays']}</span>
      </div>
      <div class="game-info">
        <div class="game-title">{g['title']}</div>
        <div style="font-size:.78rem;color:var(--muted);margin:3px 0 6px">{g['desc'][:40]}...</div>
        <div class="game-meta">
          <span class="game-genre">{g['genre']}</span>
          <span class="game-rating">★ {g['rating']}</span>
        </div>
      </div>
    </div>""" for g in DEMO_GAMES])

    body=f"""<div class="page-inner">
      <div class="section-title">🔥 Popular Games <span>Updated daily</span></div>
      <div class="games-grid">{cards}</div>
      <div class="section-title">🆕 New & Trending <span>This week</span></div>
      <div class="games-grid">{cards}</div>
    </div>"""
    return page("Games", body, user)

# ═══════════════════════════════════════════════════
# AVATARS / SKINS
# ═══════════════════════════════════════════════════
@app.route('/avatars')
def avatars():
    user=get_user()
    if not user: return redirect('/')
    cards=''.join([f"""
    <div class="avatar-card {'equipped' if user.get('avatar')==a['id'] else ''}">
      <div class="avatar-icon">{a['icon']}</div>
      <div class="avatar-name">{a['name']}</div>
      <div class="avatar-price" style="color:{'var(--green)' if a['price']==0 else 'var(--yellow)'}">
        {'Free' if a['price']==0 else f"⬡ {a['price']:,} Apelx"}
      </div>
      {'<div style="font-size:.72rem;color:var(--yellow);margin-top:6px;font-weight:700">✓ Equipped</div>' if user.get('avatar')==a['id'] else
       f'<a href="/equip/{a["id"]}"><button style="margin-top:8px;padding:6px 16px;background:var(--red);color:white;border:none;border-radius:6px;font-family:var(--font);font-size:.8rem;font-weight:700;cursor:pointer">{"Equip" if a["price"]==0 else "Buy & Equip"}</button></a>'}
    </div>""" for a in AVATARS])

    body=f"""<div class="page-inner">
      <div class="section-title">👤 Avatar Shop <span>Customize your look</span></div>
      <div style="margin-bottom:20px">{al('Your Apelx balance: <strong>⬡ '+str(user.get('apelx',0))+' Apelx</strong>','i')}</div>
      <div class="avatar-grid">{cards}</div>
    </div>"""
    return page("Avatars", body, user)

@app.route('/equip/<avatar_id>')
def equip(avatar_id):
    user=get_user()
    if not user: return redirect('/')
    av=next((a for a in AVATARS if a['id']==avatar_id),None)
    if not av: return redirect('/avatars')
    if av['price']>0 and user.get('apelx',0)<av['price']:
        return redirect('/store')
    try:
        conn=get_db();c=conn.cursor()
        if av['price']>0:
            c.execute("UPDATE users SET apelx=apelx-%s,avatar=%s WHERE id=%s",(av['price'],avatar_id,user['id']))
        else:
            c.execute("UPDATE users SET avatar=%s WHERE id=%s",(avatar_id,user['id']))
        conn.commit();c.close();conn.close()
    except: pass
    return redirect('/avatars')

# ═══════════════════════════════════════════════════
# STORE
# ═══════════════════════════════════════════════════
@app.route('/store')
def store():
    user=get_user()
    if not user: return redirect('/')
    packages=[
        {"apelx":40,"price":"$1.00","bonus":""},
        {"apelx":80,"price":"$2.00","bonus":""},
        {"apelx":400,"price":"$6.00","bonus":"🎁 Best Value!"},
        {"apelx":1000,"price":"$10.00","bonus":"🔥 Popular"},
        {"apelx":2200,"price":"$20.00","bonus":"⭐ Most Popular"},
        {"apelx":6000,"price":"$50.00","bonus":"💎 Premium"},
    ]
    cards=''.join([f"""
    <div class="store-card">
      {'<div style="background:var(--red);color:white;border-radius:20px;padding:3px 10px;font-size:.72rem;font-weight:800;margin-bottom:10px;display:inline-block">'+p['bonus']+'</div>' if p['bonus'] else '<div style="height:26px;margin-bottom:10px"></div>'}
      <div class="store-amount">⬡ {p['apelx']:,}</div>
      <div class="store-apelx">Apelx</div>
      <div class="store-price">{p['price']}</div>
      <button class="store-btn" onclick="alert('Payment system coming soon!')">Buy Now</button>
    </div>""" for p in packages])

    body=f"""<div class="page-inner">
      <div class="section-title">💰 Apelx Store <span>Power up your experience</span></div>
      <div style="margin-bottom:20px">{al('Your balance: <strong>⬡ '+str(user.get('apelx',0))+' Apelx</strong>','i')}</div>
      <div class="store-grid">{cards}</div>
      <div style="margin-top:24px;padding:16px;background:var(--surface);border-radius:10px;border:1px solid var(--border);color:var(--muted);font-size:.82rem">
        🔒 All transactions are secure. Apelx is virtual currency for use within Apex Studio only.
      </div>
    </div>"""
    return page("Store", body, user)

# ═══════════════════════════════════════════════════
# PROFILE
# ═══════════════════════════════════════════════════
@app.route('/profile')
def profile():
    user=get_user()
    if not user: return redirect('/')
    av=next((a for a in AVATARS if a['id']==user.get('avatar','default')),AVATARS[0])
    joined=user.get('created_at',datetime.now())
    if isinstance(joined,str): joined=datetime.now()
    body=f"""<div class="page-inner">
      <div class="profile-header">
        <div class="profile-av">{av['icon']}</div>
        <div>
          <div class="profile-name">{user['username']}</div>
          <div class="profile-joined">Joined {joined.strftime('%B %Y')}</div>
          <div class="profile-stats">
            <div class="pstat"><div class="pstat-num">⬡ {user.get('apelx',0):,}</div><div class="pstat-label">Apelx</div></div>
            <div class="pstat"><div class="pstat-num">0</div><div class="pstat-label">Games Played</div></div>
            <div class="pstat"><div class="pstat-num">0</div><div class="pstat-label">Friends</div></div>
          </div>
        </div>
        <a href="/settings" style="margin-left:auto"><button class="nav-btn outline">⚙ Settings</button></a>
      </div>
      <div style="background:var(--surface);border-radius:12px;padding:24px;border:1px solid var(--border)">
        <div class="section-title">🎮 Recent Activity</div>
        <div class="empty"><div class="empty-icon">🎮</div>No games played yet.<br>Explore the games section!</div>
      </div>
    </div>"""
    return page("Profile", body, user)

# ═══════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════
@app.route('/settings', methods=['GET','POST'])
def settings():
    user=get_user()
    if not user: return redirect('/')
    msg=""

    if request.method=='POST':
        action=request.form.get('action')
        if action=='change_username':
            new_name=request.form.get('new_username','').strip()
            ok,emsg=valid_username(new_name)
            if not ok: msg=al(emsg,"e")
            elif user.get('apelx',0)<1000: msg=al("Changing username costs ⬡ 1,000 Apelx. You don't have enough.","e")
            else:
                try:
                    conn=get_db();c=conn.cursor()
                    c.execute("SELECT username FROM used_usernames WHERE username=%s",(new_name.lower(),))
                    if c.fetchone(): msg=al("This username was previously used and is no longer available.","e")
                    else:
                        c.execute("SELECT id FROM users WHERE username=%s AND id!=%s",(new_name,user['id']))
                        if c.fetchone(): msg=al("This username is already taken.","e")
                        else:
                            # Reserve old username
                            c.execute("INSERT INTO used_usernames(username) VALUES(%s) ON CONFLICT DO NOTHING",(user['username'].lower(),))
                            c.execute("UPDATE users SET username=%s,apelx=apelx-1000 WHERE id=%s",(new_name,user['id']))
                            conn.commit(); msg=al(f"Username changed to <strong>{new_name}</strong>! ⬡ 1,000 Apelx deducted.","s")
                    c.close();conn.close()
                except Exception as e: msg=al(f"Error: {str(e)[:60]}","e")

        elif action=='change_password':
            old=request.form.get('old_password','')
            new=request.form.get('new_password','')
            conf=request.form.get('confirm_password','')
            if not check_password_hash(user['password'],old): msg=al("Current password is incorrect.","e")
            elif new!=conf: msg=al("New passwords do not match.","e")
            else:
                ok,emsg=valid_pw(new)
                if not ok: msg=al(emsg,"e")
                else:
                    try:
                        conn=get_db();c=conn.cursor()
                        c.execute("UPDATE users SET password=%s WHERE id=%s",(generate_password_hash(new),user['id']))
                        conn.commit();c.close();conn.close()
                        msg=al("Password updated successfully!","s")
                    except: msg=al("Error updating password.","e")

    user=get_user()
    body=f"""<div class="page-inner" style="max-width:600px">
      <div style="font-size:1.5rem;font-weight:900;margin-bottom:20px">⚙ Settings</div>
      {msg}

      <div class="settings-section">
        <div class="settings-title">👤 Change Username</div>
        <div style="margin-bottom:16px">{al('Costs <strong>⬡ 1,000 Apelx</strong>. Your old username becomes available for others after you change it. Current balance: ⬡ '+str(user.get('apelx',0)),'i')}</div>
        <form method="POST">
          <input type="hidden" name="action" value="change_username">
          <div class="fg"><label>New Username</label>
          <input type="text" name="new_username" placeholder="New username (min 4 chars)" required minlength="4" maxlength="20"></div>
          <button type="submit" class="btn-full">Change Username — ⬡ 1,000</button>
        </form>
      </div>

      <div class="settings-section">
        <div class="settings-title">🔒 Change Password</div>
        <form method="POST">
          <input type="hidden" name="action" value="change_password">
          <div class="fg"><label>Current Password</label>
          <input type="password" name="old_password" placeholder="Enter current password" required></div>
          <div class="fg"><label>New Password</label>
          <input type="password" name="new_password" placeholder="Min 8 chars, 1 uppercase, 1 number" required></div>
          <div class="fg"><label>Confirm New Password</label>
          <input type="password" name="confirm_password" placeholder="Repeat new password" required></div>
          <button type="submit" class="btn-full outline">Update Password</button>
        </form>
      </div>

      <div class="settings-section">
        <div class="settings-title">📧 Account Info</div>
        <div style="color:var(--muted);font-size:.9rem;margin-bottom:6px">Username: <strong style="color:white">{user['username']}</strong></div>
        <div style="color:var(--muted);font-size:.9rem">Email: <strong style="color:white">{user['email']}</strong></div>
      </div>
    </div>"""
    return page("Settings", body, user)

if __name__=='__main__':
    init_db()
    app.run(debug=True)
