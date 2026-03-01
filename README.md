# 🔐 APEX — Flask Auth жүйесі

## Қорғаныс мүмкіндіктері
- ✅ 3 рет қате → 15 минут блок
- ✅ IP перманент блоктау
- ✅ Пароль хэштеу (bcrypt)
- ✅ Email хабарлама (тіркелу кезінде)
- ✅ Пароль күші тексерілу (8+ символ, бас әріп, сан)
- ✅ SQL injection қорғаныс (parameterized queries)
- ✅ XSS қорғаныс (Jinja2 auto-escape)

---

## Орнату (Arch Linux)

```bash
cd flask-auth
pip install -r requirements.txt
python app.py
```

Браузерде: http://localhost:5000

---

## PythonAnywhere арқылы ТЕГІН хостинг

1. https://www.pythonanywhere.com — тіркел (тегін!)
2. Dashboard → "Web" → "Add new web app"
3. Flask таңда
4. Files бетінде файлдарды жүкте
5. Web бетінде "Reload" басқан соң сайтың live!

**Тегін домен:** `сенің_атың.pythonanywhere.com`

---

## Email қосу (Gmail)

1. Gmail → Параметрлер → 2FA қос
2. "App passwords" → жаңа пароль жасайды
3. Arch Linux терминалында:

```bash
export SMTP_EMAIL="сенің@gmail.com"
export SMTP_PASS="app_password_мұнда"
python app.py
```

---

## Домен атауы туралы

**Тегін:** `apex.pythonanywhere.com`  
**Ақылы (.com/.net/.onl):** Namecheap — жылына ~$10-15

apex-executor.onl сияқты домен үшін ақша керек.
Бірақ pythonanywhere тегін домені де жақсы жұмыс істейді!
