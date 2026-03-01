# 🚀 Vercel + PostgreSQL орнату нұсқаулығы

## 1-қадам: Neon.tech — тегін PostgreSQL

1. https://neon.tech — тіркел (GitHub арқылы жылдам)
2. "New Project" → атын қой (мысалы: apex-db)
3. **Connection string** көшір — осылай болады:
   ```
   postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
4. Осы мәтінді сақта!

---

## 2-қадам: GitHub-қа жүкте

```bash
cd apex-vercel
git init
git add .
git commit -m "initial"
git remote add origin https://github.com/СЕНІҢ_АТЫ/apex-executor.git
git push -u origin main
```

---

## 3-қадам: Vercel Environment Variables қос

1. vercel.com → сенің жобаң → **Settings** → **Environment Variables**
2. Мына екі айнымалыны қос:

| Name | Value |
|------|-------|
| `DATABASE_URL` | postgresql://... (Neon-дан көшірген) |
| `SECRET_KEY` | кез-келген ұзын кездейсоқ мәтін |

3. **Save** → **Redeploy**

---

## 4-қадам: Redeploy

Vercel dashboard → Deployments → **Redeploy** басқан соң сайтың жұмыс істейді! ✅

---

## Неге бұрын қате шықты?

SQLite файлдарды сақтайды, бірақ Vercel serverless — яғни файлдарды сақтай алмайды.
PostgreSQL (Neon) — бұлтта тұрады, мәселе жоқ! ✅
