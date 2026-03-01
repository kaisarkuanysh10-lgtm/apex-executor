from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import re
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-32chars!")

MAX_ATTEMPTS = 3
BLOCK_MINUTES = 15

# ─── DB Connection ───────────────────────────────────────────
def get_db():
    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            ip TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 1,
            blocked_until TIMESTAMP,
            last_attempt TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocked_ips (
            ip TEXT PRIMARY KEY,
            reason TEXT,
            blocked_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# ─── IP Security ─────────────────────────────────────────────
def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def is_blocked(ip):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT ip FROM blocked_ips WHERE ip=%s", (ip,))
    if cur.fetchone():
        cur.close(); conn.close()
        return True, "permanently"
    
    cur.execute("SELECT blocked_until FROM login_attempts WHERE ip=%s", (ip,))
    row = cur.fetchone()
    cur.close(); conn.close()
    
    if row and row['blocked_until'] and datetime.now() < row['blocked_until']:
        remaining = int((row['blocked_until'] - datetime.now()).total_seconds() / 60) + 1
        return True, f"{remaining} минут"
    return False, None

def fail_attempt(ip):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO login_attempts (ip, attempts, last_attempt)
        VALUES (%s, 1, NOW())
        ON CONFLICT (ip) DO UPDATE
        SET attempts = login_attempts.attempts + 1,
            last_attempt = NOW(),
            blocked_until = CASE
                WHEN login_attempts.attempts + 1 >= %s
                THEN NOW() + INTERVAL '%s minutes'
                ELSE NULL
            END
    """, (ip, MAX_ATTEMPTS, BLOCK_MINUTES))
    conn.commit()
    
    cur.execute("SELECT attempts FROM login_attempts WHERE ip=%s", (ip,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row['attempts'] if row else 1

def reset_attempts(ip):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM login_attempts WHERE ip=%s", (ip,))
    conn.commit()
    cur.close(); conn.close()

# ─── Validation ──────────────────────────────────────────────
def valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email)

def valid_password(pw):
    if len(pw) < 8:
        return False, "Пароль кемінде 8 символ болуы керек"
    if not re.search(r'[A-Z]', pw):
        return False, "Кемінде 1 бас әріп керек (A-Z)"
    if not re.search(r'[0-9]', pw):
        return False, "Кемінде 1 сан керек (0-9)"
    return True, "ok"

# ─── Routes ──────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    ip = get_ip()
    blocked, reason = is_blocked(ip)
    if blocked:
        flash(f'IP блокталған: {reason}', 'error')
        return render_template('login.html', blocked=True)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, username))
        user = cur.fetchone()
        cur.close(); conn.close()

        if user and check_password_hash(user['password'], password):
            reset_attempts(ip)
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            attempts = fail_attempt(ip)
            remaining = MAX_ATTEMPTS - attempts
            if remaining <= 0:
                flash(f'Тым көп қате! {BLOCK_MINUTES} минутқа блокталдыңыз.', 'error')
            else:
                flash(f'Қате пайдаланушы аты немесе пароль. {remaining} әрекет қалды.', 'error')

    return render_template('login.html', blocked=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if not all([username, email, password, confirm]):
            flash('Барлық өрістерді толтырыңыз', 'error')
            return render_template('register.html')
        if not valid_email(email):
            flash('Email форматы дұрыс емес', 'error')
            return render_template('register.html')
        ok, msg = valid_password(password)
        if not ok:
            flash(msg, 'error')
            return render_template('register.html')
        if password != confirm:
            flash('Парольдер сәйкес келмейді', 'error')
            return render_template('register.html')

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, generate_password_hash(password))
            )
            conn.commit()
            cur.close(); conn.close()
            flash('Тіркелу сәтті! Кіріңіз.', 'success')
            return redirect(url_for('login'))
        except psycopg2.errors.UniqueViolation:
            flash('Бұл пайдаланушы аты немесе email бұрыннан бар', 'error')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Init tables on first request
@app.before_request
def setup():
    try:
        init_db()
    except Exception as e:
        print(f"DB init error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
