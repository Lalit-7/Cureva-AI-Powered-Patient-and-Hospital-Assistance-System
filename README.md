# 🏥 Cureva - AI-Powered Patient & Hospital Assistance System

**Live Demo:** https://cureva-healthcare.vercel.app *(coming soon)*

---

## **Overview**

Cureva is an AI-powered healthcare platform that connects patients with hospitals. It provides:

- ✅ **AI Medical Analysis** - Chat with AI for symptom analysis & medical report understanding
- ✅ **Real Nearby Hospitals** - Find hospitals near you using interactive maps
- ✅ **Case Management** - Send medical cases to hospitals with full medical history
- ✅ **Hospital Dashboard** - Hospitals receive and manage patient cases
- ✅ **Secure Messaging** - Real-time patient-hospital communication
- ✅ **Medical Records** - Centralized patient health records

---

## **Tech Stack**

### **Backend**
- **Framework:** Flask 3.0.0 (Python)
- **Database:** PostgreSQL (Render.com)
- **ORM:** SQLAlchemy 2.0
- **Authentication:** Bcrypt password hashing
- **API:** RESTful JSON endpoints

### **Frontend**
- **HTML5, CSS3, JavaScript** (Vanilla - no frameworks)
- **Maps:** Leaflet + OpenStreetMap
- **UI:** Custom responsive design

### **AI/ML**
- **LLM:** Google Gemini API (medical analysis)
- **Image Recognition:** Gemini for medical report analysis

### **Deployment**
- **Hosting:** Vercel (serverless)
- **Database:** PostgreSQL on Render.com
- **File Format:** Python 3.11

### **Dependencies**
```
Flask==3.0.0
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.48
psycopg2-binary==2.9.9 (PostgreSQL driver)
bcrypt==4.1.2 (password hashing)
google-generativeai==0.3.0 (Gemini API)
python-dotenv==1.0.0
requests==2.31.0
```

---

## **Quick Start**

### **Local Development**

1. **Clone/Navigate to project:**
```bash
cd "C:\Users\lalit\OneDrive\Desktop\Cureva AI-Powered Patient and Hospital Assistance System"
```

2. **Create virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create `.env` file:**
```env
GEMINI_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_api_key_here
FLASK_ENV=development
SECRET_KEY=your_secret_key
```

5. **Run the app:**
```bash
python app.py
```

6. **Open browser:**
```
http://localhost:5000
```

---

## **Demo Accounts**

### **Pre-seeded Demo Users:**

**Patient Demo:**
- Email: `Patient_demo@gmail.com`
- Password: `demo_password`

**Hospital Demo:**
- Email: `Demo_Hospital@gmail.com`
- Password: `hospital_demo`

**OR sign up for new account:**
- Click "Sign up for free" on login page
- Create patient or hospital account
- Auto-login after signup

---

## **Database**

### **Local Development**
- Uses SQLite (`health_tech.db`)
- Auto-creates on first run
- Demo users created automatically

### **Production (Vercel)**
- Uses PostgreSQL on Render.com
- Connection via `DATABASE_URL` environment variable
- Persistent data across deployments

### **Database Models**

```
Users (patients & hospitals)
├── Conversations (AI chat with patient)
│   └── Messages
├── Cases (medical cases sent to hospitals)
└── PatientHospitalConversations (messaging between patient & hospital)
    └── PatientHospitalMessages
```

---

## **API Endpoints**

### **Authentication**
- `POST /api/auth/login` - Login
- `POST /api/auth/signup` - Register new account
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### **Patient**
- `GET /patient` - Patient dashboard
- `POST /api/analyze-text` - Analyze symptoms (AI)
- `POST /api/analyze-image` - Analyze medical images (AI)
- `GET /api/nearby-hospitals` - Find nearby hospitals
- `POST /api/send-case` - Send case to hospital
- `GET /api/patient/cases` - View sent cases
- `GET /api/patient/messages` - View hospital messages

### **Hospital**
- `GET /hospital` - Hospital dashboard
- `GET /api/hospital/cases` - View received cases
- `GET /api/hospital/messages` - View patient messages
- `POST /api/hospital/respond` - Send message to patient

---

## **File Structure**

```
├── app.py                          # Main Flask application
├── models/
│   ├── __init__.py
│   └── database.py                # SQLAlchemy models (User, Case, Message)
├── services/
│   ├── gemini_service.py          # AI analysis (Google Gemini)
│   ├── maps_service.py            # Hospital search (OpenStreetMap)
│   └── image_parser.py            # Medical image handling
├── templates/
│   ├── landing.html               # Home page
│   ├── login.html                 # Login/Signup page
│   ├── patients/                  # Patient pages
│   │   ├── dashboard.html
│   │   ├── messages.html
│   │   └── ...
│   └── hospitals/                 # Hospital pages
│       ├── dashboard.html
│       ├── cases.html
│       └── ...
├── static/
│   ├── css/                       # Stylesheets
│   └── js/                        # Client-side JS
├── api/
│   └── index.py                   # Vercel serverless entry point
├── requirements.txt               # Python dependencies
├── vercel.json                    # Vercel configuration
├── wsgi.py                        # WSGI app interface
└── .env                           # Environment variables (local only)
```

---

## **Deployment**

### **Deploy to Vercel**

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete step-by-step instructions.

**Quick summary:**
1. Push code to GitHub
2. Connect GitHub repo to Vercel
3. Add environment variables in Vercel settings
4. Deploy (automatic on each git push)

---

## **Testing**

See [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md) for detailed testing instructions.

**Quick test:**
```bash
python app.py
# Visit http://localhost:5000
# Login with: Patient_demo@gmail.com / demo_password
# Test AI chat → Hospital search → Send case
```

---

## **Security**

- ✅ Passwords hashed with bcrypt (never stored plain text)
- ✅ Session-based authentication
- ✅ HTTPS enforced on Vercel
- ✅ Environment variables for secrets (not in code)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ CORS enabled for API access

---

## **Performance**

- Serverless deployment (Vercel) = auto-scaling
- Database connection pooling (PostgreSQL)
- Image optimization for medical uploads
- Lazy loading of hospital maps
- Caching for nearby hospital searches

---

## **Future Enhancements**

- [ ] Real hospital integrations via APIs
- [ ] Video consultations
- [ ] Prescription management
- [ ] Insurance verification
- [ ] Mobile app (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] Doctor search & booking
- [ ] Lab test ordering

---

## **Support & Contact**

For issues or questions:
- GitHub Issues: https://github.com/YOUR_USERNAME/cureva-healthcare-app/issues
- Email: support@cureva.com

---

## **License**

MIT License - See LICENSE file for details

---

## **Author**

Built with ❤️ for healthcare
