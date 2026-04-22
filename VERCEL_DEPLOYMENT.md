# 🚀 Cureva - Vercel Deployment Guide

## 🔧 Recent Fixes (April 2026)

The following critical issues have been fixed to resolve `FUNCTION_INVOCATION_FAILED` errors:

1. **Improved Serverless Entry Point** (`api/index.py`)
   - Added proper error handling with fallback app
   - Better error messages for debugging
   - Ensures Flask app imports correctly

2. **Enhanced Database Initialization** (`app.py`)
   - Better error handling for database initialization
   - Improved logging for troubleshooting
   - More informative error messages on startup

3. **Updated Vercel Configuration** (`vercel.json`)
   - Added `installCommand` to ensure dependencies are installed
   - Set production environment variables
   - Better timeout and memory configuration

4. **Added Health Check Endpoint** (`app.py`)
   - `/health` endpoint for Vercel monitoring
   - Helps diagnose deployment issues
   - Can be used for uptime monitoring

## Environment Variables Setup

Before deploying to Vercel, ensure these environment variables are configured in your Vercel Project Settings:

```env
# REQUIRED Environment Variables
GOOGLE_API_KEY=your_google_gemini_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here
SECRET_KEY=your_flask_secret_key_here
DATABASE_URL=postgresql://user:password@host:port/database

# Optional (Vercel sets these automatically)
FLASK_ENV=production
FLASK_DEBUG=0
```

**⚠️ CRITICAL**: All environment variables must be set in Vercel Project Settings → Environment Variables

## Deployment Steps

### 1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit - Ready for Vercel deployment"
git push origin main
```

### 2. **Connect to Vercel**
- Go to [vercel.com](https://vercel.com)
- Click "New Project"
- Import your GitHub repository
- Select "Python" as framework (if not auto-detected)
- Configure environment variables in Project Settings → Environment Variables

### 3. **Deploy**
- Click "Deploy"
- Vercel will automatically:
  - Install dependencies from `requirements.txt`
  - Build the application
  - Run the Flask app on serverless functions
  - Assign a `.vercel.app` domain

## Configuration Files Explained

### **vercel.json**
- Defines build process using Python 3.11
- Routes all requests to `api/index.py` (Flask app wrapper)
- Sets environment variables for production/development
- Configures Lambda function memory and timeout (60 seconds)

### **api/index.py**
- Entry point for Vercel serverless functions
- Wraps the Flask application
- Handles all routing and requests

### **wsgi.py**
- WSGI application interface for traditional deployment
- Can be used if migrating to WSGI servers like Gunicorn

### **.vercelignore**
- Specifies files/folders to ignore during deployment
- Excludes unnecessary files to reduce build size

## Database Considerations

**Current Setup**: SQLite (`health_tech.db`)
- ⚠️ **Problem**: Vercel's filesystem is ephemeral (temporary). SQLite data won't persist between deployments.

**Recommended Solutions**:

### Option 1: **PostgreSQL (Recommended for Production)**
```bash
# Update requirements.txt to include PostgreSQL driver
pip install psycopg2-binary
# Update DATABASE_URI in app.py:
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
```

### Option 2: **MongoDB (NoSQL Alternative)**
```bash
pip install pymongo
# Update models to use PyMongo
```

### Option 3: **Firebase Firestore (Fully Managed)**
```bash
pip install firebase-admin
# Use Firebase SDK for data persistence
```

### Option 4: **Vercel KV (Redis)**
```bash
pip install upstash-redis
# Use for sessions and temporary data
```

## Performance Optimization for Serverless

### 1. **Cold Start Optimization**
- Minimize dependencies in `requirements.txt`
- Remove unused packages
- Consider using Lambda layers

### 2. **Memory Configuration**
- Current: 1024 MB (suitable for medical data processing)
- Increase if image processing fails
- Maximum: 3008 MB

### 3. **Timeout Configuration**
- Current: 60 seconds
- Increase for AI analysis (up to 900 seconds max)
- Consider async processing for heavy tasks

## File Structure for Vercel

```
project/
├── api/
│   └── index.py              # Vercel serverless entry point
├── app.py                     # Main Flask application
├── wsgi.py                    # WSGI entry point
├── vercel.json               # Vercel configuration
├── .vercelignore             # Files to exclude from build
├── requirements.txt          # Python dependencies
├── models/
│   ├── __init__.py
│   ├── database.py
│   └── reports.py
├── services/
│   ├── gemini_service.py
│   ├── image_parser.py
│   └── maps_service.py
├── static/
│   ├── css/
│   ├── js/
│   └── assets/
├── templates/
│   ├── landing.html
│   ├── login.html
│   ├── patients/
│   └── hospitals/
└── instance/
    └── health_tech.db
```

## Deployment Checklist

- [ ] Environment variables configured in Vercel dashboard
- [ ] GitHub repository connected
- [ ] `vercel.json` configured correctly
- [ ] `requirements.txt` updated with all dependencies
- [ ] `api/index.py` created as serverless entry point
- [ ] API keys for Gemini and Maps services are valid
- [ ] Static files paths are correct
- [ ] Database strategy decided (SQLite → PostgreSQL recommended)
- [ ] CORS settings configured if needed
- [ ] Error logging configured
- [ ] Monitoring set up in Vercel dashboard

## 🆘 Troubleshooting Common Errors

### Error: `FUNCTION_INVOCATION_FAILED` (500 Internal Server Error)

**Causes & Solutions:**

1. **Missing Environment Variables**
   - ✅ Check Vercel Project Settings → Environment Variables
   - ✅ Ensure `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `SECRET_KEY` are set
   - ✅ Test with `/health` endpoint to check if app initialized

2. **Database Connection Issues**
   - ✅ Verify `DATABASE_URL` is set and valid (PostgreSQL required in production)
   - ✅ SQLite won't work on Vercel (ephemeral filesystem)
   - ✅ Use Render.com or similar for PostgreSQL hosting

3. **Python Dependency Issues**
   - ✅ Run `pip install -r requirements.txt` locally to test
   - ✅ Check that all imports in `app.py` are available
   - ✅ Verify Python 3.11 compatibility

4. **Import/Module Errors**
   - ✅ Check Vercel build logs for import errors
   - ✅ Verify relative imports in `api/index.py` are correct
   - ✅ Ensure models and services can be imported

5. **API Keys Invalid**
   - ✅ Verify Google Gemini API key is active
   - ✅ Check API quotas and rate limits
   - ✅ Ensure keys haven't been revoked

### Error: Static Files Return 404

```python
# Ensure static files configuration in app.py
app = Flask(__name__, static_folder='static', static_url_path='/static')
```

### Error: Database Initialization Hangs

- Reduce connection timeout in SQLAlchemy config
- Use connection pooling for better performance
- Consider serverless-friendly database (MongoDB, Firebase)

### Error: Cold Start Too Slow

- Optimize dependencies (remove unused packages)
- Consider increasing Lambda memory to 1536 MB or higher
- Use reserved concurrency in Vercel for critical endpoints

## Testing Before Deployment

```bash
# Test locally with production-like environment
export FLASK_ENV=production
export FLASK_DEBUG=0
export GOOGLE_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here
export SECRET_KEY=your_secret_here
python -m pip install -r requirements.txt
python app.py

# Test the health endpoint
curl http://localhost:5000/health
```

## Health Check URL

After deployment, monitor your application health:
```
https://your-app.vercel.app/health
```

This should return:
```json
{
  "status": "healthy",
  "service": "Cureva AI"
}
```

**Database Connection Timeout**
- Increase timeout in SQLAlchemy config
- Switch to PostgreSQL for better connection pooling

**API Rate Limiting**
- Implement caching for Gemini responses
- Rate limit hospital searches

## Scaling on Vercel

As traffic increases:
1. Upgrade to **Vercel Pro** for higher function limits
2. Implement **caching** (Vercel KV/Redis)
3. Migrate to **PostgreSQL** for concurrent connections
4. Use **CDN** for static assets (automatic with Vercel)
5. Implement **async processing** for long-running tasks

## Cost Estimation

**Free Tier**:
- 100,000 function invocations/month
- 5 GB bandwidth/month
- Suitable for MVP/testing

**Pro Tier** ($20/month):
- 1,000,000 function invocations/month
- 100 GB bandwidth/month
- Production-ready

## Support & Resources

- [Vercel Python Documentation](https://vercel.com/docs/runtimes/python)
- [Flask on Vercel](https://vercel.com/guides/deploying-a-python-flask-app-with-vercel)
- [Vercel Dashboard](https://vercel.com/dashboard)
