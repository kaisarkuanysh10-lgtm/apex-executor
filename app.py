from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import sqlite3
import os
import re
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ─── Настройки ──────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS = 3
BLOCK_DURATION = timedelta(minutes=15)
DB_PATH = "users.db"

# ─── База данных ────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS login_attempts (
        ip TEXT NOT NULL,
        attempts INTEGER DEFAULT 0,
        blocked_until TIMESTAMP,
        last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS blocked_ips (
        ip TEXT PRIMARY KEY,
        reason TEXT,
        blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ─── Защита от брутфорса ────────────────────────────────────
def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

def is_ip_blocked(ip):
    conn = get_db()
    # Проверяем перманентную блокировку
    blocked = conn.execute("SELECT * FROM blocked_ips WHERE ip=?", (ip,)).fetchone()
    if blocked:
        conn.close()
        return True, "permanently"
    
    # Проверяем временную блокировку
    row = conn.execute("SELECT * FROM login_attempts WHERE ip=?", (ip,)).fetchone()
    conn.close()
    
    if row and row['blocked_until']:
        blocked_until = datetime.fromisoformat(str(row['blocked_until']))
        if datetime.now() < blocked_until:
            remaining = int((blocked_until - datetime.now()).total_seconds() / 60)
            return True, f"{remaining} минут"
    return False, None

def record_failed_attempt(ip):
    conn = get_db()
    row = conn.execute("SELECT * FROM login_attempts WHERE ip=?", (ip,)).fetchone()
    
    if row:
        attempts = row['attempts'] + 1
        blocked_until = None
        if attempts >= MAX_LOGIN_ATTEMPTS:
            blocked_until = (datetime.now() + BLOCK_DURATION).isoformat()
        conn.execute(
            "UPDATE login_attempts SET attempts=?, blocked_until=?, last_attempt=? WHERE ip=?",
            (attempts, blocked_until, datetime.now().isoformat(), ip)
        )
    else:
        conn.execute(
            "INSERT INTO login_attempts (ip, attempts, last_attempt) VALUES (?, 1, ?)",
            (ip, datetime.now().isoformat())
        )
    conn.commit()
    conn.close()

def reset_attempts(ip):
    conn = get_db()
    conn.execute("DELETE FROM login_attempts WHERE ip=?", (ip,))
    conn.commit()
    conn.close()

def get_remaining_attempts(ip):
    conn = get_db()
    row = conn.execute("SELECT attempts FROM login_attempts WHERE ip=?", (ip,)).fetchone()
    conn.close()
    if row:
        return MAX_LOGIN_ATTEMPTS - row['attempts']
    return MAX_LOGIN_ATTEMPTS

# ─── Валидация ──────────────────────────────────────────────
def validate_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email)

def validate_password(password):
    if len(password) < 8:
        return False, "Пароль кемінде 8 символ болуы керек"
    if not re.search(r'[A-Z]', password):
        return False, "Кемінде 1 бас әріп болуы керек"
    if not re.search(r'[0-9]', password):
        return False, "Кемінде 1 сан болуы керек"
    return True, "OK"

# ─── Email хабарлама ────────────────────────────────────────
def send_email(to_email, subject, body):
    """
    Нақты email жіберу үшін SMTP_EMAIL және SMTP_PASS env айнымалыларын орнат.
    Мысалы: Gmail App Password пайдалан.
    """
    smtp_email = os.environ.get("SMTP_EMAIL")
    smtp_pass = os.environ.get("SMTP_PASS")
    
    if not smtp_email or not smtp_pass:
        print(f"[EMAIL SIM] To: {to_email} | Subject: {subject}\n{body}")
        return True
    
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = smtp_email
        msg['To'] = to_email
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_email, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ─── Маршруттар ─────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if not all([username, email, password, confirm]):
            flash('Барлық өрістерді толтырыңыз', 'error')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Email дұрыс емес', 'error')
            return render_template('register.html')
        
        valid, msg = validate_password(password)
        if not valid:
            flash(msg, 'error')
            return render_template('register.html')
        
        if password != confirm:
            flash('Парольдер сәйкес келмейді', 'error')
            return render_template('register.html')
        
        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username=? OR email=?", (username, email)
        ).fetchone()
        
        if existing:
            conn.close()
            flash('Бұл пайдаланушы аты немесе email бұрыннан бар', 'error')
            return render_template('register.html')
        
        hashed = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed)
        )
        conn.commit()
        conn.close()
        
        send_email(email, "Тіркелу сәтті өтті!", f"Сәлем {username}! Сайтымызға қош келдіңіз.")
        flash('Тіркелу сәтті! Кіріңіз.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    ip = get_client_ip()
    
    blocked, reason = is_ip_blocked(ip)
    if blocked:
        if reason == "permanently":
            flash('Сіздің IP мекенжайыңыз блокталған.', 'error')
        else:
            flash(f'Тым көп қате. {reason} кейін қайталаңыз.', 'error')
        return render_template('login.html', blocked=True)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? OR email=?", (username, username)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            reset_attempts(ip)
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            return redirect(url_for('dashboard'))
        else:
            record_failed_attempt(ip)
            remaining = get_remaining_attempts(ip)
            if remaining <= 0:
                flash(f'Тым көп қате. {int(BLOCK_DURATION.total_seconds()/60)} минутқа блокталдыңыз.', 'error')
            else:
                flash(f'Пайдаланушы аты немесе пароль қате. {remaining} әрекет қалды.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    flash('Шықтыңыз', 'info')
    return redirect(url_for('login'))

# ─── Admin: IP блоктау ──────────────────────────────────────
@app.route('/admin/block/<ip>')
def block_ip(ip):
    # Нақты жобада admin аутентификация қос!
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO blocked_ips (ip, reason) VALUES (?, 'manual')", (ip,))
    conn.commit()
    conn.close()
    return jsonify({"status": "blocked", "ip": ip})

init_db()
