from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, re, psycopg2, psycopg2.extras
import smtplib, random, string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "apex-ultra-secret-2026-xK9mP2qL8nR5")

MAX_ATTEMPTS = 3
BLOCK_MINUTES = 15
CODE_EXPIRE_MINUTES = 10

# ════════════════════════════════════════════════════════════════
# CSS & HTML HELPERS
# ════════════════════════════════════════════════════════════════
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#02040a;--surface:#080d1a;--surface2:#0d1525;
  --border:#162040;--border2:#1e2f55;
  --cyan:#00e5ff;--pink:#ff2d6b;--green:#00ff88;
  --yellow:#ffe600;--text:#d0dff5;--muted:#4a6080;
  --font-head:'Orbitron',monospace;--font-body:'Exo 2',sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{min-height:100vh;background:var(--bg);color:var(--text);font-family:var(--font-body)}

/* ANIMATED BACKGROUND */
body{position:relative;overflow-x:hidden}
body::before{
  content:'';position:fixed;inset:0;
  background:
    radial-gradient(ellipse 600px 400px at 80% 10%, rgba(0,229,255,.04) 0%, transparent 70%),
    radial-gradient(ellipse 500px 350px at 10% 80%, rgba(255,45,107,.03) 0%, transparent 70%),
    linear-gradient(rgba(0,229,255,.02) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,229,255,.02) 1px,transparent 1px);
  background-size:100% 100%,100% 100%,50px 50px,50px 50px;
  pointer-events:none;z-index:0;
}

/* SCANLINES */
body::after{
  content:'';position:fixed;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.15) 2px,rgba(0,0,0,.15) 4px);
  pointer-events:none;z-index:1;
}

/* LAYOUT */
.page{position:relative;z-index:2;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}

/* LOGO */
.logo-wrap{text-align:center;margin-bottom:36px}
.logo{font-family:var(--font-head);font-size:3rem;font-weight:900;letter-spacing:.5em;color:var(--cyan);
  text-shadow:0 0 30px rgba(0,229,255,.6),0 0 60px rgba(0,229,255,.3);
  animation:pulse 3s ease-in-out infinite}
@keyframes pulse{0%,100%{text-shadow:0 0 30px rgba(0,229,255,.6),0 0 60px rgba(0,229,255,.3)}
  50%{text-shadow:0 0 50px rgba(0,229,255,.9),0 0 100px rgba(0,229,255,.5)}}
.logo-tagline{font-size:.7rem;letter-spacing:.4em;color:var(--muted);text-transform:uppercase;margin-top:6px}

/* CARD */
.card{
  width:100%;max-width:460px;
  background:var(--surface);
  border:1px solid var(--border2);
  border-radius:2px;padding:40px;
  position:relative;
  box-shadow:0 0 60px rgba(0,0,0,.8),0 0 30px rgba(0,229,255,.05),inset 0 1px 0 rgba(0,229,255,.08);
}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent 0%,var(--cyan) 50%,transparent 100%)}
.card.pink::before{background:linear-gradient(90deg,transparent 0%,var(--pink) 50%,transparent 100%)}
.card.green::before{background:linear-gradient(90deg,transparent 0%,var(--green) 50%,transparent 100%)}

/* CORNER BRACKETS */
.card::after{content:'';position:absolute;inset:6px;border:1px solid transparent;
  border-top-color:rgba(0,229,255,.15);border-left-color:rgba(0,229,255,.15);pointer-events:none}
.br-tl,.br-tr,.br-bl,.br-br{position:absolute;width:16px;height:16px;border-color:var(--cyan);border-style:solid}
.br-tl{top:0;left:0;border-width:2px 0 0 2px}
.br-tr{top:0;right:0;border-width:2px 2px 0 0}
.br-bl{bottom:0;left:0;border-width:0 0 2px 2px}
.br-br{bottom:0;right:0;border-width:0 2px 2px 0}
.card.pink .br-tl,.card.pink .br-tr,.card.pink .br-bl,.card.pink .br-br{border-color:var(--pink)}
.card.green .br-tl,.card.green .br-tr,.card.green .br-bl,.card.green .br-br{border-color:var(--green)}

/* TITLE */
.card-title{font-family:var(--font-head);font-size:1.3rem;font-weight:700;letter-spacing:.15em;
  text-transform:uppercase;color:#fff;margin-bottom:4px}
.card-sub{font-size:.75rem;letter-spacing:.2em;color:var(--muted);margin-bottom:28px;font-family:var(--font-head)}

/* ALERTS */
.alert{padding:12px 16px;border-radius:2px;font-size:.85rem;margin-bottom:20px;
  display:flex;align-items:flex-start;gap:10px;line-height:1.5}
.alert-icon{flex-shrink:0;font-size:.9rem;margin-top:1px}
.alert-error{background:rgba(255,45,107,.08);border:1px solid rgba(255,45,107,.3);color:#ff6b8a}
.alert-success{background:rgba(0,255,136,.07);border:1px solid rgba(0,255,136,.3);color:var(--green)}
.alert-info{background:rgba(0,229,255,.07);border:1px solid rgba(0,229,255,.25);color:var(--cyan)}

/* FORM */
.fg{margin-bottom:20px}
.fg label{display:block;font-size:.68rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
  color:var(--muted);margin-bottom:8px;font-family:var(--font-head)}
.fg input{
  width:100%;padding:13px 16px;
  background:rgba(0,229,255,.03);
  border:1px solid var(--border2);
  border-radius:2px;color:var(--text);
  font-family:var(--font-body);font-size:.95rem;
  transition:all .25s;outline:none;
}
.fg input:focus{border-color:var(--cyan);background:rgba(0,229,255,.06);
  box-shadow:0 0 0 3px rgba(0,229,255,.1),0 0 20px rgba(0,229,255,.08)}
.fg input::placeholder{color:var(--muted)}
.fg input.pink-focus:focus{border-color:var(--pink);background:rgba(255,45,107,.05);
  box-shadow:0 0 0 3px rgba(255,45,107,.1)}
.hint{font-size:.72rem;color:var(--muted);margin-top:6px;letter-spacing:.05em}

/* CODE INPUT */
.code-input{
  width:100%;padding:16px;text-align:center;
  font-family:var(--font-head);font-size:1.8rem;letter-spacing:.4em;
  background:rgba(0,229,255,.04);border:1px solid var(--cyan);
  border-radius:2px;color:var(--cyan);outline:none;
  box-shadow:0 0 20px rgba(0,229,255,.1),inset 0 0 20px rgba(0,229,255,.03);
}
.code-input:focus{box-shadow:0 0 30px rgba(0,229,255,.2),inset 0 0 20px rgba(0,229,255,.05)}

/* BUTTONS */
.btn{
  width:100%;padding:14px;background:transparent;
  border:1px solid var(--cyan);color:var(--cyan);
  font-family:var(--font-head);font-size:.8rem;font-weight:700;
  letter-spacing:.25em;text-transform:uppercase;
  cursor:pointer;border-radius:2px;transition:all .25s;
  position:relative;overflow:hidden;margin-top:6px;
}
.btn::before{content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,var(--cyan),rgba(0,229,255,.6));
  transform:translateX(-100%);transition:transform .3s;z-index:0}
.btn:hover::before{transform:translateX(0)}
.btn:hover{color:var(--bg);box-shadow:0 0 30px rgba(0,229,255,.4)}
.btn span{position:relative;z-index:1}
.btn.pink{border-color:var(--pink);color:var(--pink)}
.btn.pink::before{background:linear-gradient(135deg,var(--pink),rgba(255,45,107,.6))}
.btn.pink:hover{box-shadow:0 0 30px rgba(255,45,107,.4)}
.btn.green{border-color:var(--green);color:var(--green)}
.btn.green::before{background:linear-gradient(135deg,var(--green),rgba(0,255,136,.6))}
.btn.green:hover{box-shadow:0 0 30px rgba(0,255,136,.4)}

/* DIVIDER */
.divider{display:flex;align-items:center;gap:12px;margin:20px 0}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:var(--border2)}
.divider span{font-size:.7rem;letter-spacing:.15em;color:var(--muted);font-family:var(--font-head)}

/* LINK */
.foot{text-align:center;margin-top:22px;font-size:.82rem;color:var(--muted)}
.foot a{color:var(--cyan);text-decoration:none;letter-spacing:.05em;transition:all .2s}
.foot a:hover{text-shadow:0 0 10px var(--cyan)}

/* DASHBOARD GRID */
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:28px}
.stat{background:var(--surface2);border:1px solid var(--border2);border-radius:2px;padding:16px}
.stat-label{font-family:var(--font-head);font-size:.6rem;letter-spacing:.2em;color:var(--muted);text-transform:uppercase;margin-bottom:6px}
.stat-val{font-family:var(--font-head);font-size:.95rem;color:var(--green)}

/* TIMER */
.timer{text-align:center;font-family:var(--font-head);font-size:.8rem;color:var(--yellow);
  letter-spacing:.1em;margin-top:10px}

/* BLOCKED */
.blocked-box{text-align:center;padding:24px;border:1px solid rgba(255,45,107,.3);
  border-radius:2px;background:rgba(255,45,107,.05)}
.blocked-icon{font-size:2.5rem;margin-bottom:12px}
.blocked-title{font-family:var(--font-head);font-size:1rem;color:var(--pink);letter-spacing:.15em;margin-bottom:8px}
.blocked-sub{font-size:.85rem;color:var(--muted)}

/* STRENGTH BAR */
.strength{margin-top:8px;height:3px;border-radius:2px;background:var(--border);overflow:hidden}
.strength-fill{height:100%;transition:all .3s;border-radius:2px}

@keyframes fadeIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.card{animation:fadeIn .4s ease}
</style>
"""

def page(title, body):
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — APEX</title>{CSS}</head>
<body><div class="page">{body}</div></body></html>"""

def alert(msg, kind="error"):
    icons = {"error":"⚠", "success":"✓", "info":"◈"}
    return f'<div class="alert alert-{kind}"><span class="alert-icon">{icons.get(kind,"!")}</span><span>{msg}</span></div>'

def corners():
    return '<div class="br-tl"></div><div class="br-tr"></div><div class="br-bl"></div><div class="br-br"></div>'

# ════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════
def get_db():
    url = os.environ.get("DATABASE_URL","")
    if not url:
        raise Exception("DATABASE_URL not set in environment variables")
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS verify_codes(
        email TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        username TEXT,
        password_hash TEXT,
        expires_at TIMESTAMP NOT NULL,
        attempts INT DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS login_attempts(
        ip TEXT PRIMARY KEY,
        attempts INT DEFAULT 1,
        blocked_until TIMESTAMP,
        last_attempt TIMESTAMP DEFAULT NOW()
    )""")
    conn.commit(); c.close(); conn.close()

# ════════════════════════════════════════════════════════════════
# EMAIL
# ════════════════════════════════════════════════════════════════
def send_verification_email(to_email, code, username):
    smtp_user = os.environ.get("SMTP_EMAIL")
    smtp_pass = os.environ.get("SMTP_PASS")
    if not smtp_user or not smtp_pass:
        print(f"[EMAIL SIM] Code for {to_email}: {code}")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "APEX — Your Verification Code"
        msg["From"]    = f"APEX Security <{smtp_user}>"
        msg["To"]      = to_email
        html = f"""<!DOCTYPE html><html><body style="background:#02040a;margin:0;padding:40px;font-family:'Courier New',monospace">
<div style="max-width:500px;margin:0 auto;background:#080d1a;border:1px solid #1e2f55;padding:40px;border-radius:2px">
  <div style="text-align:center;margin-bottom:30px">
    <div style="font-size:2.5rem;font-weight:900;letter-spacing:.5em;color:#00e5ff;text-shadow:0 0 20px rgba(0,229,255,.5)">APEX</div>
    <div style="font-size:.7rem;letter-spacing:.3em;color:#4a6080;margin-top:6px">SECURE ACCESS PORTAL</div>
  </div>
  <div style="border-top:1px solid #1e2f55;padding-top:30px">
    <p style="color:#d0dff5;font-size:.95rem;margin-bottom:8px">Hello, <strong style="color:#00e5ff">{username}</strong></p>
    <p style="color:#d0dff5;font-size:.95rem;margin-bottom:24px">Welcome to APEX. Use the code below to verify your account:</p>
    <div style="background:#02040a;border:1px solid #00e5ff;padding:24px;text-align:center;margin-bottom:24px;box-shadow:0 0 30px rgba(0,229,255,.1)">
      <div style="font-size:2.8rem;letter-spacing:.5em;color:#00e5ff;font-weight:900;text-shadow:0 0 20px rgba(0,229,255,.5)">{code}</div>
      <div style="font-size:.72rem;color:#4a6080;margin-top:10px;letter-spacing:.2em">THIS CODE EXPIRES IN {CODE_EXPIRE_MINUTES} MINUTES</div>
    </div>
    <p style="color:#4a6080;font-size:.8rem;margin:0">If you did not create an APEX account, ignore this email.</p>
  </div>
  <div style="border-top:1px solid #1e2f55;margin-top:30px;padding-top:20px;text-align:center">
    <div style="font-size:.7rem;letter-spacing:.15em;color:#4a6080">APEX CORPORATION — CLASSIFIED SYSTEM</div>
  </div>
</div></body></html>"""
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def generate_code():
    return ''.join(random.choices(string.digits, k=8))

# ════════════════════════════════════════════════════════════════
# SECURITY
# ════════════════════════════════════════════════════════════════
def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def check_block(ip):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT attempts,blocked_until FROM login_attempts WHERE ip=%s", (ip,))
        row = c.fetchone(); c.close(); conn.close()
        if row and row['blocked_until'] and datetime.now() < row['blocked_until']:
            mins = int((row['blocked_until'] - datetime.now()).total_seconds()/60)+1
            return True, mins
        return False, 0
    except: return False, 0

def record_fail(ip):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""INSERT INTO login_attempts(ip,attempts,last_attempt) VALUES(%s,1,NOW())
            ON CONFLICT(ip) DO UPDATE SET attempts=login_attempts.attempts+1,last_attempt=NOW(),
            blocked_until=CASE WHEN login_attempts.attempts+1>=%s THEN NOW()+(%s*INTERVAL'1 minute') ELSE NULL END""",
            (ip,MAX_ATTEMPTS,BLOCK_MINUTES))
        c.execute("SELECT attempts FROM login_attempts WHERE ip=%s",(ip,))
        row=c.fetchone(); conn.commit(); c.close(); conn.close()
        return row['attempts'] if row else 1
    except: return 1

def clear_attempts(ip):
    try:
        conn=get_db();c=conn.cursor()
        c.execute("DELETE FROM login_attempts WHERE ip=%s",(ip,))
        conn.commit();c.close();conn.close()
    except: pass

# ════════════════════════════════════════════════════════════════
# VALIDATION
# ════════════════════════════════════════════════════════════════
def valid_email(e): return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$',e))
def valid_pw(pw):
    if len(pw)<8: return False,"Password must be at least 8 characters"
    if not re.search(r'[A-Z]',pw): return False,"Must contain at least 1 uppercase letter (A-Z)"
    if not re.search(r'[0-9]',pw): return False,"Must contain at least 1 number (0-9)"
    return True,"ok"

# ════════════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return redirect('/dashboard' if 'uid' in session else '/login')

# ── LOGIN ────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    try: init_db()
    except Exception as e:
        body = f"""<div class="logo-wrap"><div class="logo">APEX</div><div class="logo-tagline">Secure Access Portal</div></div>
        <div class="card">{corners()}<div class="card-title">System Error</div>
        {alert(f"DATABASE_URL not configured. Please set environment variables in Vercel.", "error")}</div>"""
        return page("Error", body)

    ip = get_ip()
    blocked, mins = check_block(ip)
    err = ""

    if request.method == 'POST' and not blocked:
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        try:
            conn=get_db();c=conn.cursor()
            c.execute("SELECT * FROM users WHERE (username=%s OR email=%s) AND verified=TRUE",(username,username))
            user=c.fetchone();c.close();conn.close()
            if user and check_password_hash(user['password'],password):
                clear_attempts(ip)
                session['uid']=user['id'];session['uname']=user['username'];session['email']=user['email']
                return redirect('/dashboard')
            else:
                n=record_fail(ip); rem=MAX_ATTEMPTS-n
                blocked2,mins2=check_block(ip)
                if blocked2: blocked,mins=True,mins2; err=""
                else: err=alert(f"Invalid credentials. {rem} attempt{'s' if rem!=1 else ''} remaining.","error")
        except Exception as e:
            err=alert(f"Database error: {str(e)[:80]}","error")

    if blocked:
        form=f"""<div class="blocked-box">
          <div class="blocked-icon">⛔</div>
          <div class="blocked-title">Access Temporarily Blocked</div>
          <div class="blocked-sub">Too many failed attempts.<br>Try again in {mins} minute{'s' if mins!=1 else ''}.</div>
        </div>"""
    else:
        form=f"""{err}
        <form method="POST" autocomplete="off">
          <div class="fg"><label>Username or Email</label>
          <input type="text" name="username" placeholder="Enter username or email" required></div>
          <div class="fg"><label>Password</label>
          <input type="password" name="password" placeholder="Enter password" required></div>
          <button type="submit" class="btn"><span>Sign In →</span></button>
        </form>"""

    body=f"""<div class="logo-wrap"><div class="logo">APEX</div><div class="logo-tagline">Secure Access Portal</div></div>
    <div class="card">{corners()}
      <div class="card-title">Sign In</div>
      <div class="card-sub">// auth.login</div>
      {form}
      <div class="divider"><span>New here?</span></div>
      <div class="foot"><a href="/register">Create an account →</a></div>
    </div>"""
    return page("Sign In", body)

# ── REGISTER ─────────────────────────────────────────────────
@app.route('/register', methods=['GET','POST'])
def register():
    try: init_db()
    except: pass
    err=""

    if request.method=='POST':
        username=request.form.get('username','').strip()
        email=request.form.get('email','').strip()
        password=request.form.get('password','')
        confirm=request.form.get('confirm','')

        e=None
        if not all([username,email,password,confirm]): e="All fields are required"
        elif len(username)<3: e="Username must be at least 3 characters"
        elif not valid_email(email): e="Invalid email format"
        elif password!=confirm: e="Passwords do not match"
        else:
            ok,msg=valid_pw(password)
            if not ok: e=msg

        if e:
            err=alert(e,"error")
        else:
            try:
                conn=get_db();c=conn.cursor()
                c.execute("SELECT id FROM users WHERE username=%s OR email=%s",(username,email))
                if c.fetchone():
                    err=alert("Username or email already exists","error")
                    c.close();conn.close()
                else:
                    code=generate_code()
                    expires=datetime.now()+timedelta(minutes=CODE_EXPIRE_MINUTES)
                    c.execute("""INSERT INTO verify_codes(email,code,username,password_hash,expires_at)
                        VALUES(%s,%s,%s,%s,%s) ON CONFLICT(email) DO UPDATE SET
                        code=%s,username=%s,password_hash=%s,expires_at=%s,attempts=0""",
                        (email,code,username,generate_password_hash(password),expires,
                         code,username,generate_password_hash(password),expires))
                    conn.commit();c.close();conn.close()
                    send_verification_email(email,code,username)
                    session['pending_email']=email
                    session['pending_username']=username
                    return redirect('/verify')
            except Exception as ex:
                err=alert(f"Error: {str(ex)[:80]}","error")

    body=f"""<div class="logo-wrap"><div class="logo">APEX</div><div class="logo-tagline">New User Registration</div></div>
    <div class="card pink">{corners()}
      <div class="card-title">Create Account</div>
      <div class="card-sub">// auth.register</div>
      {err}
      <form method="POST" autocomplete="off">
        <div class="fg"><label>Username</label>
        <input type="text" name="username" placeholder="Choose a username" required minlength="3" maxlength="20"></div>
        <div class="fg"><label>Email Address</label>
        <input type="email" name="email" placeholder="your@email.com" required></div>
        <div class="fg"><label>Password</label>
        <input type="password" name="password" placeholder="Create a strong password" required>
        <div class="hint">// Min 8 chars · 1 uppercase letter · 1 number</div></div>
        <div class="fg"><label>Confirm Password</label>
        <input type="password" name="confirm" placeholder="Repeat your password" required></div>
        <button type="submit" class="btn pink"><span>Send Verification Code →</span></button>
      </form>
      <div class="divider"><span>Have an account?</span></div>
      <div class="foot"><a href="/login">← Sign In</a></div>
    </div>"""
    return page("Create Account", body)

# ── VERIFY ───────────────────────────────────────────────────
@app.route('/verify', methods=['GET','POST'])
def verify():
    email=session.get('pending_email')
    username=session.get('pending_username','User')
    if not email:
        return redirect('/register')
    err=""

    if request.method=='POST':
        code=request.form.get('code','').strip().replace(' ','')
        try:
            conn=get_db();c=conn.cursor()
            c.execute("SELECT * FROM verify_codes WHERE email=%s",(email,))
            row=c.fetchone()
            if not row:
                err=alert("No verification code found. Please register again.","error")
            elif row['attempts']>=5:
                err=alert("Too many incorrect attempts. Please register again.","error")
            elif datetime.now()>row['expires_at']:
                err=alert("Code has expired. Please register again.","error")
            elif row['code']!=code:
                c.execute("UPDATE verify_codes SET attempts=attempts+1 WHERE email=%s",(email,))
                conn.commit()
                rem=5-row['attempts']-1
                err=alert(f"Incorrect code. {rem} attempt{'s' if rem!=1 else ''} remaining.","error")
            else:
                # Code correct — create user
                c.execute("INSERT INTO users(username,email,password,verified) VALUES(%s,%s,%s,TRUE) ON CONFLICT DO NOTHING",
                    (row['username'],email,row['password_hash']))
                c.execute("DELETE FROM verify_codes WHERE email=%s",(email,))
                conn.commit()
                c.execute("SELECT * FROM users WHERE email=%s",(email,))
                user=c.fetchone()
                c.close();conn.close()
                session.pop('pending_email',None);session.pop('pending_username',None)
                session['uid']=user['id'];session['uname']=user['username'];session['email']=user['email']
                return redirect('/welcome')
            c.close();conn.close()
        except Exception as ex:
            err=alert(f"Error: {str(ex)[:80]}","error")

    masked=email[:2]+"***@"+email.split('@')[1] if '@' in email else email
    body=f"""<div class="logo-wrap"><div class="logo">APEX</div><div class="logo-tagline">Email Verification</div></div>
    <div class="card green">{corners()}
      <div class="card-title">Verify Email</div>
      <div class="card-sub">// auth.verify</div>
      {alert(f"An 8-digit code was sent to <strong>{masked}</strong>. Check your inbox (and spam folder).","info")}
      {err}
      <form method="POST">
        <div class="fg"><label>Enter 8-Digit Code</label>
        <input type="text" name="code" class="code-input" placeholder="00000000"
          maxlength="8" pattern="[0-9]{{8}}" inputmode="numeric" required autocomplete="one-time-code"></div>
        <button type="submit" class="btn green"><span>Verify & Activate →</span></button>
      </form>
      <div class="timer">Code expires in {CODE_EXPIRE_MINUTES} minutes</div>
      <div class="foot" style="margin-top:16px"><a href="/register">← Back to registration</a></div>
    </div>"""
    return page("Verify Email", body)

# ── WELCOME ──────────────────────────────────────────────────
@app.route('/welcome')
def welcome():
    if 'uid' not in session: return redirect('/login')
    uname=session.get('uname','User')
    email=session.get('email','')
    body=f"""<div class="logo-wrap"><div class="logo">APEX</div></div>
    <div class="card green">{corners()}
      <div style="text-align:center;padding:10px 0 20px">
        <div style="font-size:3rem;margin-bottom:12px">✦</div>
        <div class="card-title" style="text-align:center;font-size:1.6rem;color:var(--green)">Access Granted</div>
        <div style="font-family:var(--font-head);font-size:.75rem;letter-spacing:.2em;color:var(--muted);margin:8px 0 24px">// authentication.successful</div>
        <p style="color:var(--text);font-size:1rem;margin-bottom:6px">Welcome to <span style="color:#00e5ff;font-weight:600">APEX</span>, <strong style="color:var(--green)">{uname}</strong>!</p>
        <p style="color:var(--muted);font-size:.85rem;margin-bottom:28px">Your account has been verified and activated.</p>
        <div style="background:var(--surface2);border:1px solid var(--border2);padding:16px;border-radius:2px;margin-bottom:24px;text-align:left">
          <div style="font-family:var(--font-head);font-size:.65rem;color:var(--muted);letter-spacing:.2em;margin-bottom:4px">REGISTERED EMAIL</div>
          <div style="font-family:var(--font-head);font-size:.9rem;color:var(--cyan)">{email}</div>
        </div>
        <a href="/dashboard" style="display:inline-block;padding:13px 32px;border:1px solid var(--green);color:var(--green);font-family:var(--font-head);font-size:.8rem;letter-spacing:.2em;text-decoration:none;text-transform:uppercase;transition:all .2s">Enter Dashboard →</a>
      </div>
    </div>"""
    return page("Welcome", body)

# ── DASHBOARD ────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'uid' not in session: return redirect('/login')
    uname=session.get('uname','User')
    email=session.get('email','')
    body=f"""<div class="logo-wrap"><div class="logo">APEX</div><div class="logo-tagline">Mission Control</div></div>
    <div class="card">{corners()}
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px">
        <div style="width:44px;height:44px;border-radius:50%;background:rgba(0,229,255,.1);border:2px solid var(--cyan);
          display:flex;align-items:center;justify-content:center;font-family:var(--font-head);font-size:1.1rem;color:var(--cyan);
          box-shadow:0 0 20px rgba(0,229,255,.3);flex-shrink:0">{uname[0].upper()}</div>
        <div>
          <div style="font-family:var(--font-head);font-size:1rem;color:#fff">{uname}</div>
          <div style="font-size:.78rem;color:var(--muted)">{email}</div>
        </div>
        <div style="margin-left:auto;font-family:var(--font-head);font-size:.65rem;letter-spacing:.15em;
          color:var(--green);background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.3);
          padding:4px 10px;border-radius:2px">● ONLINE</div>
      </div>
      <div class="stat-grid">
        <div class="stat"><div class="stat-label">Security Level</div><div class="stat-val">MAXIMUM</div></div>
        <div class="stat"><div class="stat-label">Status</div><div class="stat-val">VERIFIED</div></div>
        <div class="stat"><div class="stat-label">2FA Email</div><div class="stat-val">ACTIVE</div></div>
        <div class="stat"><div class="stat-label">Access</div><div class="stat-val">GRANTED</div></div>
      </div>
      <a href="/logout" style="display:block;width:100%;padding:13px;text-align:center;background:transparent;
        border:1px solid var(--pink);color:var(--pink);font-family:var(--font-head);font-size:.8rem;
        letter-spacing:.25em;text-decoration:none;text-transform:uppercase;transition:all .2s;
        border-radius:2px">Sign Out →</a>
    </div>"""
    return page("Dashboard", body)

# ── LOGOUT ───────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__=='__main__':
    app.run(debug=True)
