# 🚀 Cureva - Complete Deployment Guide (Vercel + PostgreSQL)

## **Overview**

This guide shows how to deploy Cureva to production using:
- **Frontend + Backend:** Vercel (serverless)
- **Database:** PostgreSQL on Render.com (already created)
- **Deployment Time:** ~5-10 minutes

---

## **Part 1: Pre-Deployment Checklist ✅**

### **What You Already Have:**
- ✅ PostgreSQL database from Render: `postgresql://cureva_db_user:KMjjDQgTag2csGy1A0TOsrKeO6Oiuhk8@dpg-d7idpc0sfn5c73e7k3h0-a.oregon-postgres.render.com/cureva_db`
- ✅ Vercel account (sign up at [vercel.com](https://vercel.com))
- ✅ GitHub account (sign up at [github.com](https://github.com))
- ✅ Code updated with PostgreSQL support

### **What You Need to Do:**
1. Initialize Git in your project
2. Push code to GitHub
3. Connect GitHub repo to Vercel
4. Add environment variables to Vercel
5. Deploy

---

## **Part 2: Step-by-Step Deployment**

### **STEP 1: Initialize Git & Push to GitHub**

**What:** Create a GitHub repository and push your code there

**Why:** Vercel automatically deploys from GitHub - every push triggers a new deployment

**Commands:**

```bash
# Navigate to project directory (you're already there)
cd "C:\Users\lalit\OneDrive\Desktop\Cureva AI-Powered Patient and Hospital Assistance System"

# Initialize git
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Cureva ready for production with PostgreSQL and bcrypt"

# Add GitHub remote (replace YOUR_USERNAME and YOUR_REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**⚠️ Important:** Create the repository on GitHub first:
1. Go to [github.com/new](https://github.com/new)
2. Repository name: `cureva-healthcare-app` (or your choice)
3. Click "Create repository"
4. GitHub will show you the commands above

---

### **STEP 2: Create `.vercelignore` File**

**What:** Tells Vercel which files NOT to deploy

**Why:** Reduces deployment size and avoids uploading unnecessary files

**File content:**

```
.git
.gitignore
.env
.venv
__pycache__
*.pyc
node_modules/
.DS_Store
instance/health_tech.db
*.db
.pytest_cache
.coverage
htmlcov/
```

**Create this file** at project root with the content above.

---

### **STEP 3: Connect Vercel to GitHub**

**What:** Link your GitHub repo to Vercel so it auto-deploys on every push

**Steps:**

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Add New" → "Project"
3. Click "Import Git Repository"
4. Paste your GitHub repo URL: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME`
5. Click "Import"
6. Vercel will detect your project is Python/Flask

---

### **STEP 4: Configure Environment Variables in Vercel**

**What:** Add sensitive credentials (database URL, API keys) to Vercel

**Why:** These are secrets - NEVER commit them to GitHub

**Steps:**

1. In Vercel Project → Settings → Environment Variables
2. Add the following variables:

| Variable Name | Value |
|---|---|
| `DATABASE_URL` | `postgresql://cureva_db_user:KMjjDQgTag2csGy1A0TOsrKeO6Oiuhk8@dpg-d7idpc0sfn5c73e7k3h0-a.oregon-postgres.render.com/cureva_db` |
| `GOOGLE_API_KEY` | Your Gemini API key |
| `GEMINI_API_KEY` | Your Gemini API key |
| `SECRET_KEY` | Generate a random string (e.g., `your_super_secret_key_12345`) |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `0` |

3. Click "Save" for each variable

**How to generate SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

### **STEP 5: Deploy!**

**What:** Trigger the deployment

**Steps:**

1. After adding environment variables, click "Deploy"
2. Vercel will:
   - Install dependencies from `requirements.txt`
   - Build your Flask app
   - Create serverless functions
   - Assign you a `.vercel.app` domain
3. Wait 2-3 minutes for deployment to complete

**Your app will be live at:** `https://your-project-name.vercel.app`

---

## **Part 3: Verify Deployment**

### **Check Status:**
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click your project
3. Look for green checkmark (deployment successful)
4. If red X, click "Deployments" to see error logs

### **Test Your App:**
1. Click your project domain (e.g., `cureva-app.vercel.app`)
2. Visit the landing page
3. Try logging in with demo credentials:
   - **Patient:** `Patient_demo@gmail.com` / `demo_password`
   - **Hospital:** `Demo_Hospital@gmail.com` / `hospital_demo`
4. Chat with AI, search hospitals, send case
5. Switch to hospital account and verify you received it

---

## **Part 4: After Deployment**

### **Auto-Redeployment:**
- Every time you `git push` to GitHub, Vercel automatically redeploys
- No manual action needed
- Takes 2-3 minutes per deployment

### **Monitor Performance:**
- Vercel Dashboard → Deployments tab
- See build logs, errors, response times
- Real-time monitoring

### **Access Database:**
- Render Dashboard → Your PostgreSQL instance
- View database stats, backups, connections
- Real users' data is stored here

### **Update Code:**
```bash
# Make code changes locally
# Then:
git add .
git commit -m "Your message"
git push origin main
# Vercel automatically redeploys!
```

---

## **Part 5: Troubleshooting**

### **Issue: "Module not found" error**

**Solution:** Check `requirements.txt` has all dependencies
```bash
pip freeze > requirements.txt
git add requirements.txt
git push
```

### **Issue: Database connection failed**

**Solution:** Verify `DATABASE_URL` in Vercel environment variables is correct
1. Vercel Dashboard → Settings → Environment Variables
2. Check `DATABASE_URL` value
3. Make sure no typos

### **Issue: App works locally but fails on Vercel**

**Common Causes:**
- Missing environment variables → Check Vercel Settings
- File paths using Windows-specific paths → Use relative paths
- Static files not served → Ensure `static/` folder exists
- Port binding → Vercel assigns port automatically (don't hardcode)

### **Issue: Render PostgreSQL won't connect**

**Solution:** 
1. Check Render status at [status.render.com](https://status.render.com)
2. Verify database is still running (Render free tier might sleep after 15 min inactivity)
3. Check `DATABASE_URL` has correct format

---

## **Part 6: Quick Reference**

### **Your Deployment URLs:**
- **Live App:** `https://your-project-name.vercel.app`
- **Vercel Dashboard:** `https://vercel.com/dashboard`
- **Render Database:** `https://dashboard.render.com`
- **GitHub Repo:** `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME`

### **Demo Accounts (Works Everywhere):**
- **Patient:** `Patient_demo@gmail.com` / `demo_password`
- **Hospital:** `Demo_Hospital@gmail.com` / `hospital_demo`

### **System Architecture:**
```
User Browser
    ↓
Vercel (Frontend + Backend)
    ↓
Render PostgreSQL
    ↓
Real User Data
```

### **Key Files:**
- `app.py` - Main Flask application
- `api/index.py` - Vercel serverless entry point
- `vercel.json` - Vercel configuration
- `.env` - Local environment variables (NOT deployed)
- `requirements.txt` - Python dependencies
- `models/database.py` - Database schema

---

## **Need Help?**

**Common Commands:**

```bash
# Check git status
git status

# View git log
git log --oneline

# Undo last commit (careful!)
git reset --soft HEAD~1

# Push changes
git push origin main

# Create new branch
git checkout -b feature-name

# View deployed app logs
# Go to Vercel Dashboard → Deployments → Click build
```

---

## **Checklist Before Going Live:**

- [ ] Code pushed to GitHub
- [ ] Vercel project created and connected
- [ ] All environment variables added in Vercel
- [ ] Deployment shows green checkmark
- [ ] Can access app at Vercel URL
- [ ] Demo accounts work (patient & hospital)
- [ ] AI chat responds
- [ ] Hospital search works
- [ ] Can send case to hospital
- [ ] Hospital can receive case

**Once all checked: ✅ You're Live!**

---

**Questions?** Refer to:
- [Vercel Docs](https://vercel.com/docs)
- [Flask Deployment Guide](https://flask.palletsprojects.com/deployment/)
- [Render Docs](https://render.com/docs)
