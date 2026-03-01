from flask import Flask, request, redirect, url_for, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, re, psycopg2, psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "apex-secret-key-change-this-123!")

MAX_ATTEMPTS = 3
BLOCK_MINUTES = 15

# ── CSS общий ────────────────────────────────────────────────
BASE_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#050810;--panel:#0a0f1e;--border:#1a2744;--accent:#00d4ff;--accent2:#ff3c6e;--text:#c8d8f0;--muted:#4a6080;--success:#00ff9d;--error:#ff3c6e;--mono:'Share Tech Mono',monospace;--sans:'Rajdhani',sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;display:flex;align-items:center;justify-content:center;position:relative;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,212,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none}
.orb{position:fixed;border-radius:50%;filter:blur(80px);pointer-events:none}
.o1{width:400px;height:400px;background:rgba(0,212,255,.06);top:-100px;right:-100px}
.o2{width:300px;height:300px;background:rgba(255,60,110,.05);bottom:-50px;left:-50px}
.wrap{position:relative;z-index:1;width:100%;max-width:420px;padding:20px}
.logo{text-align:center;margin-bottom:28px}
.logo-t{font-family:var(--mono);font-size:2rem;letter-spacing:.3em;color:var(--accent);text-shadow:0 0 20px rgba(0,212,255,.5)}
.logo-s{font-size:.75rem;letter-spacing:.2em;color:var(--muted);text-transform:uppercase;margin-top:4px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:4px;padding:36px;position:relative;box-shadow:0 0 40px rgba(0,0,0,.6),inset 0 1px 0 rgba(0,212,255,.1)}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--accent),transparent)}
.card.r::before{background:linear-gradient(90deg,transparent,var(--accent2),transparent)}
.ctitle{font-size:1.4rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#fff;margin-bottom:6px}
.csub{font-size:.85rem;color:var(--muted);margin-bottom:24px;font-family:var(--mono)}
.corner{position:absolute;width:12px;height:12px;border-color:var(--accent);border-style:solid;opacity:.5}
.card.r .corner{border-color:var(--accent2)}
.tl{top:8px;left:8px;border-width:1px 0 0 1px}.tr{top:8px;right:8px;border-width:1px 1px 0 0}
.bl{bottom:8px;left:8px;border-width:0 0 1px 1px}.br{bottom:8px;right:8px;border-width:0 1px 1px 0}
.flash{padding:10px 14px;border-radius:3px;font-size:.85rem;font-family:var(--mono);margin-bottom:16px;display:flex;gap:8px;align-items:center}
.flash::before{content:'▶';font-size:.7rem}
.fe{background:rgba(255,60,110,.1);border:1px solid rgba(255,60,110,.3);color:var(--error)}
.fs{background:rgba(0,255,157,.1);border:1px solid rgba(0,255,157,.3);color:var(--success)}
.fi{background:rgba(0,212,255,.1);border:1px solid rgba(0,212,255,.3);color:var(--accent)}
.fg{margin-bottom:18px}
label{display:block;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;font-family:var(--mono)}
input{width:100%;padding:12px 14px;background:rgba(0,212,255,.03);border:1px solid var(--border);border-radius:3px;color:var(--text);font-family:var(--mono);font-size:.95rem;transition:all .2s;outline:none}
input:focus{border-color:var(--accent);background:rgba(0,212,255,.06);box-shadow:0 0 0 3px rgba(0,212,255,.08)}
input::placeholder{color:var(--muted)}
.hint{font-size:.72rem;color:var(--muted);font-family:var(--mono);margin-top:5px}
.btn{width:100%;padding:13px;background:transparent;border:1px solid var(--accent);color:var(--accent);font-family:var(--mono);font-size:.9rem;letter-spacing:.2em;text-transform:uppercase;cursor:pointer;border-radius:3px;transition:all .2s;position:relative;overflow:hidden;margin-top:8px}
.btn::before{content:'';position:absolute;inset:0;background:var(--accent);transform:scaleX(0);transform-origin:left;transition:transform .2s;z-index:0}
.btn:hover::before{transform:scaleX(1)}
.btn:hover{color:var(--bg)}
.btn span{position:relative;z-index:1}
.btn2{border-color:var(--accent2);color:var(--accent2)}
.btn2::before{background:var(--accent2)}
.lrow{text-align:center;margin-top:20px;font-size:.85rem;color:var(--muted);font-family:var(--mono)}
.lrow a{color:var(--accent);text-decoration:none}
.lrow a:hover{text-shadow:0 0 8px var(--accent)}
.blocked{text-align:center;padding:20px;font-family:var(--mono);color:var(--error);font-size:.9rem;border:1px solid rgba(255,60,110,.3);border-radius:3px;background:rgba(255,60,110,.05)}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
.cur::after{content:'_';animation:blink 1s infinite;color:var(--accent)}
.cur2::after{color:var(--accent2)}
</style>
"""

def page(title, body, extra_css=""):
    return f"""<!DOCTYPE html><html lang="kk"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Apex</title>{BASE_CSS}{extra_css}</head>
<body><div class="orb o1"></div><div class="orb o2"></div>{body}</body></html>"""

# ── DB ───────────────────────────────────────────────────────
def get_db():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise Exception("DATABASE_URL орнатылмаған! Vercel → Settings → Environment Variables")
    conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW())""")
    c.execute("""CREATE TABLE IF NOT EXISTS login_attempts(
        ip TEXT PRIMARY KEY, attempts INT DEFAULT 1,
        blocked_until TIMESTAMP, last_attempt TIMESTAMP DEFAULT NOW())""")
    conn.commit(); c.close(); conn.close()

# ── Security ─────────────────────────────────────────────────
def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def check_block(ip):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT attempts, blocked_until FROM login_attempts WHERE ip=%s", (ip,))
        row = c.fetchone(); c.close(); conn.close()
        if row and row['blocked_until'] and datetime.now() < row['blocked_until']:
            mins = int((row['blocked_until'] - datetime.now()).total_seconds() / 60) + 1
            return True, f"{mins} минут"
        return False, None
    except: return False, None

def fail(ip):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""INSERT INTO login_attempts(ip,attempts,last_attempt) VALUES(%s,1,NOW())
            ON CONFLICT(ip) DO UPDATE SET
            attempts=login_attempts.attempts+1, last_attempt=NOW(),
            blocked_until=CASE WHEN login_attempts.attempts+1>=%s
            THEN NOW()+(%s * INTERVAL '1 minute') ELSE NULL END""",
            (ip, MAX_ATTEMPTS, BLOCK_MINUTES))
        c.execute("SELECT attempts FROM login_attempts WHERE ip=%s", (ip,))
        row = c.fetchone(); conn.commit(); c.close(); conn.close()
        return row['attempts'] if row else 1
    except: return 1

def reset(ip):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("DELETE FROM login_attempts WHERE ip=%s", (ip,))
        conn.commit(); c.close(); conn.close()
    except: pass

# ── Validation ───────────────────────────────────────────────
def valid_email(e): return re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', e)
def valid_pw(pw):
    if len(pw)<8: return False,"Пароль кемінде 8 символ"
    if not re.search(r'[A-Z]',pw): return False,"Кемінде 1 бас әріп (A-Z)"
    if not re.search(r'[0-9]',pw): return False,"Кемінде 1 сан (0-9)"
    return True,"ok"

# ── Routes ───────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect('/dashboard' if 'uid' in session else '/login')

@app.route('/login', methods=['GET','POST'])
def login():
    ip = get_ip()
    flash_html = ""
    
    try: init_db()
    except Exception as e:
        flash_html = f'<div class="flash fe">⚠️ DB қате: DATABASE_URL орнатылмаған!</div>'

    blocked, reason = check_block(ip)
    
    if request.method == 'POST' and not blocked:
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        try:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username,username))
            user = c.fetchone(); c.close(); conn.close()
            if user and check_password_hash(user['password'], password):
                reset(ip)
                session['uid'] = user['id']
                session['uname'] = user['username']
                return redirect('/dashboard')
            else:
                attempts = fail(ip)
                remaining = MAX_ATTEMPTS - attempts
                if remaining <= 0:
                    flash_html = f'<div class="flash fe">Тым көп қате! {BLOCK_MINUTES} минутқа блокталдыңыз.</div>'
                    blocked = True
                else:
                    flash_html = f'<div class="flash fe">Қате пайдаланушы/пароль. {remaining} әрекет қалды.</div>'
        except Exception as e:
            flash_html = f'<div class="flash fe">Қате: {str(e)[:100]}</div>'

    if blocked:
        form = f'<div class="blocked">⛔ Қол жеткізу {reason} шектелген.<br>Кейінірек қайталаңыз.</div>'
    else:
        form = f"""
        {flash_html}
        <form method="POST">
          <div class="fg"><label>Пайдаланушы аты / Email</label>
          <input type="text" name="username" placeholder="username немесе email" required></div>
          <div class="fg"><label>Пароль</label>
          <input type="password" name="password" placeholder="••••••••" required></div>
          <button type="submit" class="btn"><span>Кіру →</span></button>
        </form>"""

    body = f"""<div class="wrap">
      <div class="logo"><div class="logo-t">APEX</div><div class="logo-s">Secure Access Portal</div></div>
      <div class="card">
        <div class="corner tl"></div><div class="corner tr"></div>
        <div class="corner bl"></div><div class="corner br"></div>
        <div class="ctitle">Кіру</div>
        <div class="csub">// auth.login<span class="cur"></span></div>
        {form if not blocked else flash_html + form}
        <div class="lrow">Аккаунт жоқ па? <a href="/register">Тіркелу</a></div>
      </div></div>"""
    return page("Кіру", body)

@app.route('/register', methods=['GET','POST'])
def register():
    flash_html = ""
    try: init_db()
    except: pass
    
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        email    = request.form.get('email','').strip()
        password = request.form.get('password','')
        confirm  = request.form.get('confirm','')
        
        err = None
        if not all([username,email,password,confirm]): err="Барлық өрістерді толтырыңыз"
        elif not valid_email(email): err="Email форматы дұрыс емес"
        elif password != confirm: err="Парольдер сәйкес келмейді"
        else:
            ok, msg = valid_pw(password)
            if not ok: err = msg
        
        if err:
            flash_html = f'<div class="flash fe">{err}</div>'
        else:
            try:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
                    (username, email, generate_password_hash(password)))
                conn.commit(); c.close(); conn.close()
                # Redirect with success
                return page("Тіркелу", f"""<div class="wrap">
                  <div class="logo"><div class="logo-t">APEX</div></div>
                  <div class="card">
                    <div class="corner tl"></div><div class="corner tr"></div>
                    <div class="corner bl"></div><div class="corner br"></div>
                    <div class="flash fs">✓ Тіркелу сәтті! Кіріңіз.</div>
                    <div class="lrow" style="margin-top:0"><a href="/login">← Кіру бетіне өту</a></div>
                  </div></div>""")
            except psycopg2.errors.UniqueViolation:
                flash_html = '<div class="flash fe">Бұл пайдаланушы аты немесе email бар</div>'
            except Exception as e:
                flash_html = f'<div class="flash fe">Қате: {str(e)[:100]}</div>'

    body = f"""<div class="wrap">
      <div class="logo"><div class="logo-t">APEX</div><div class="logo-s">New User Registration</div></div>
      <div class="card r">
        <div class="corner tl"></div><div class="corner tr"></div>
        <div class="corner bl"></div><div class="corner br"></div>
        <div class="ctitle">Тіркелу</div>
        <div class="csub">// auth.register<span class="cur cur2"></span></div>
        {flash_html}
        <form method="POST">
          <div class="fg"><label>Пайдаланушы аты</label>
          <input type="text" name="username" placeholder="apex_user" required minlength="3" maxlength="20"></div>
          <div class="fg"><label>Email</label>
          <input type="email" name="email" placeholder="user@example.com" required></div>
          <div class="fg"><label>Пароль</label>
          <input type="password" name="password" placeholder="••••••••" required>
          <div class="hint">// 8+ символ, бас әріп, сан</div></div>
          <div class="fg"><label>Парольді растау</label>
          <input type="password" name="confirm" placeholder="••••••••" required></div>
          <button type="submit" class="btn btn2"><span>Тіркелу →</span></button>
        </form>
        <div class="lrow">Аккаунт бар ма? <a href="/login">Кіру</a></div>
      </div></div>"""
    return page("Тіркелу", body)

@app.route('/dashboard')
def dashboard():
    if 'uid' not in session:
        return redirect('/login')
    uname = session.get('uname','?')
    body = f"""<div class="wrap">
      <div class="logo"><div class="logo-t">APEX</div></div>
      <div class="card" style="text-align:center">
        <div class="corner tl"></div><div class="corner tr"></div>
        <div class="corner bl"></div><div class="corner br"></div>
        <div style="width:48px;height:48px;border-radius:50%;background:rgba(0,255,157,.1);border:2px solid var(--success);display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:1.2rem;box-shadow:0 0 20px rgba(0,255,157,.3)">✓</div>
        <div class="ctitle">Сәлем, <span style="color:var(--accent)">{uname}</span>!</div>
        <div class="csub" style="margin-bottom:24px">// access.granted</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:24px">
          <div style="background:rgba(0,212,255,.04);border:1px solid var(--border);border-radius:3px;padding:14px;text-align:left">
            <div style="font-family:var(--mono);font-size:.68rem;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px">Status</div>
            <div style="font-family:var(--mono);font-size:.9rem;color:var(--success)">ONLINE</div>
          </div>
          <div style="background:rgba(0,212,255,.04);border:1px solid var(--border);border-radius:3px;padding:14px;text-align:left">
            <div style="font-family:var(--mono);font-size:.68rem;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px">Security</div>
            <div style="font-family:var(--mono);font-size:.9rem;color:var(--success)">ACTIVE</div>
          </div>
        </div>
        <a href="/logout" style="display:inline-block;padding:11px 28px;background:transparent;border:1px solid var(--accent2);color:var(--accent2);font-family:var(--mono);font-size:.85rem;letter-spacing:.15em;text-transform:uppercase;text-decoration:none;border-radius:3px;transition:all .2s">Шығу →</a>
      </div></div>"""
    return page("Dashboard", body)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
