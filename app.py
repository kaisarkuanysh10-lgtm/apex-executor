from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# БАЗАНЫ ЖАДТА САҚТАУ (Vercel-де файл жазуға болмайды)
# check_same_thread=False арқылы Flask-тің әр түрлі сұраныстары бір базамен жұмыс істей алады
db_conn = sqlite3.connect(':memory:', check_same_thread=False)
db_conn.row_factory = sqlite3.Row

def init_db():
    cursor = db_conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    db_conn.commit()

# Сервер қосылғанда базаны бір рет құрып аламыз
init_db()

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
        
        if not username or not email or not password:
            flash('Барлық өрістерді толтырыңыз', 'error')
            return render_template('register.html')
            
        hashed = generate_password_hash(password)
        try:
            cursor = db_conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                         (username, email, hashed))
            db_conn.commit()
            flash('Тіркелу сәтті!', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Пайдаланушы аты немесе email бос емес', 'error')
            return render_template('register.html')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        cursor = db_conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Қате логин немесе пароль', 'error')
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
    return redirect(url_for('login'))
