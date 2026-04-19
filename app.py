import sys
import io

# Fix Windows console encoding for emoji/unicode in print() statements
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from services.gemini_service import analyze_medical_input, analyze_medical_input_with_context
from services.maps_service import get_nearby_hospitals, extract_specialty_from_analysis
from models.database import db, User, Conversation, Message, Case, PatientHospitalConversation, PatientHospitalMessage
from dotenv import load_dotenv
import bcrypt
from datetime import datetime
import os
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_health_key_123")


def build_chat_title(text):
    """Create a short, readable conversation title from user text."""
    if not text:
        return "New Chat"
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return "New Chat"
    return cleaned[:60] + ("..." if len(cleaned) > 60 else "")


# ==================== PASSWORD HASHING FUNCTIONS ====================
def hash_password(password):
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, hashed_password):
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


# ==================== DATABASE CONFIG ====================
# Use PostgreSQL from environment variable (Render) or SQLite for local development
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Production: PostgreSQL from Render
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Development: Local SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///health_tech.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Create demo users if they don't exist
    demo_patient = User.query.filter_by(email='Patient_demo@gmail.com').first()
    if not demo_patient:
        demo_patient = User(
            username='Patient_Demo',
            email='Patient_demo@gmail.com',
            password=hash_password('demo_password'),  # Hashed with bcrypt
            role='patient'
        )
        db.session.add(demo_patient)
        db.session.commit()
        print("✅ Demo patient created: Patient_Demo (Patient_demo@gmail.com)")
        
    demo_hospital = User.query.filter_by(email='Demo_Hospital@gmail.com').first()
    if not demo_hospital:
        demo_hospital = User(
            username='Demo_Hospital',
            email='Demo_Hospital@gmail.com',
            password=hash_password('hospital_demo'),  # Hashed with bcrypt
            role='hospital'
        )
        db.session.add(demo_hospital)
        db.session.commit()
        print("✅ Demo hospital created: Demo_Hospital (Demo_Hospital@gmail.com)")
    
    # Get the demo user ID for use in routes
    DEMO_USER_ID = demo_patient.id

# ==================== AUTH DECORATORS ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                # Check if request is for HTML or API
                if request.path.startswith('/api/'):
                    return jsonify({"success": False, "error": "Unauthorized"}), 403
                return redirect(url_for('login'))
            
            if session.get('role') != role:
                # Check if request is for HTML or API
                if request.path.startswith('/api/'):
                    return jsonify({"success": False, "error": "Unauthorized"}), 403
                return redirect(url_for('landing'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== AUTH API ====================
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'patient')  # Get requested role from frontend
    
    user = User.query.filter_by(email=email, role=role).first()
    
    if user and verify_password(password, user.password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        return jsonify({
            "success": True, 
            "user": user.to_dict(),
            "redirect": "/patient" if user.role == 'patient' else "/hospital"
        })
        
    return jsonify({"success": False, "error": "Invalid credentials"}), 401


@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    """Register a new user (patient or hospital)"""
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    username = data.get('username', '').strip()
    role = data.get('role', 'patient').strip()
    
    # Validation
    if not email or not password or not username:
        return jsonify({"success": False, "error": "All fields are required"}), 400
    
    if len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
    
    if len(username) < 3:
        return jsonify({"success": False, "error": "Username must be at least 3 characters"}), 400
    
    if role not in ['patient', 'hospital']:
        return jsonify({"success": False, "error": "Invalid role"}), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"success": False, "error": "Email already registered"}), 409
    
    # Check if username already exists
    existing_username = User.query.filter_by(username=username).first()
    if existing_username:
        return jsonify({"success": False, "error": "Username already taken"}), 409
    
    try:
        # Create new user with hashed password
        new_user = User(
            username=username,
            email=email,
            password=hash_password(password),  # Hash password with bcrypt
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Log them in automatically
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['role'] = new_user.role
        
        return jsonify({
            "success": True,
            "message": f"Welcome {username}!",
            "user": new_user.to_dict(),
            "redirect": "/patient" if new_user.role == 'patient' else "/hospital"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Signup error: {e}")
        return jsonify({"success": False, "error": "Registration failed. Please try again"}), 500
def api_logout():
    session.clear()
    return jsonify({"success": True, "redirect": "/"})

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route("/api/auth/me", methods=["GET"])
def api_me():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({"success": True, "user": user.to_dict()})
    return jsonify({"success": False, "error": "Not logged in"}), 401

# ---------------- LANDING ----------------
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login")
def login():
    return render_template("login.html")

# ---------------- PATIENT ----------------
@app.route("/patient")
@role_required('patient')
def patient_dashboard():
    return render_template("patients/dashboard.html")

@app.route("/patient/analyze")
@role_required('patient')
def patient_analyze():
    return render_template("patients/analyze.html")

@app.route("/patient/history")
@role_required('patient')
def patient_history():
    return render_template("patients/history.html")

@app.route("/patient/messages")
@role_required('patient')
def patient_messages():
    user_role = session.get('role', 'patient')
    return render_template("patients/messages.html", user_id=session.get('user_id'), user_role=user_role)

@app.route("/patient/hospitals")
@role_required('patient')
def patient_hospitals():
    return render_template("patients/hospitals.html")

# ---------------- HOSPITAL ----------------
@app.route("/hospital")
@role_required('hospital')
def hospital_dashboard():
    return render_template("hospitals/dashboard.html")

@app.route("/hospital/messages")
@role_required('hospital')
def hospital_messages():
    user_role = session.get('role', 'hospital')
    return render_template("hospitals/messages.html", user_id=session.get('user_id'), user_role=user_role)

@app.route("/hospital/analytics")
@role_required('hospital')
def hospital_analytics():
    return render_template("hospitals/analytics.html")

@app.route("/hospital/settings")
@role_required('hospital')
def hospital_settings():
    return render_template("hospitals/settings.html")

@app.route("/patient/profile")
@role_required('patient')
def patient_profile():
    return render_template("patients/profile.html")

@app.route("/hospital/profile")
@role_required('hospital')
def hospital_profile():
    return render_template("hospitals/profile.html")


# ---------------- AI ANALYSIS API ----------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    text = request.form.get("text")
    file = request.files.get("image")
    conversation_id = request.form.get("conversation_id", type=int)

    image_bytes = file.read() if file else None

    print(f"📤 Analyze request - Conv ID: {conversation_id}, Text: {text[:50] if text else 'Image'}")

    # Get conversation context if conversation_id is provided
    previous_context = None
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        if conversation:
            # Get all previous messages for context
            previous_messages = Message.query.filter_by(
                conversation_id=conversation_id
            ).order_by(Message.created_at).all()
            previous_context = [msg.to_dict() for msg in previous_messages]
            print(f"✅ Found {len(previous_messages)} previous messages")

    # Analyze with context
    result = analyze_medical_input_with_context(
        text_input=text,
        image_bytes=image_bytes,
        previous_messages=previous_context
    )

    # Log and save messages
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        if conversation:
            is_generic_title = (conversation.title or '').strip().lower() in {'', 'new chat', 'new conversation', 'untitled'}

            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role='user',
                content=text or "Medical image submitted",
                image_filename=file.filename if file else None
            )
            db.session.add(user_message)
            print(f"💾 [MSG] Saved user message to conversation {conversation_id}")

            # Persist topic title from first typed/voice message.
            if text and is_generic_title:
                conversation.title = build_chat_title(text)
                print(f"📝 [TITLE] Updated conversation {conversation_id} title to '{conversation.title}'")
            
            # Save assistant response
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=json.dumps(result)
            )
            db.session.add(assistant_message)
            print(f"💾 [MSG] Saved AI response to conversation {conversation_id}")
            
            # Update conversation updated_at
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            print(f"✅ [SAVE] 2 messages saved to conversation {conversation_id}, total messages: {len(conversation.messages)}")
        else:
            print(f"⚠️ [WARN] Conversation {conversation_id} not found, messages not saved")
    else:
        print(f"⚠️ [WARN] No conversation_id provided, messages not saved")

    return jsonify(result)


# ==================== CONVERSATION API ROUTES ====================

@app.route("/api/conversation/new", methods=["POST"])
@login_required
def create_conversation():
    """Create a new conversation"""
    user_id = session.get('user_id', DEMO_USER_ID)
    data = request.json
    title = data.get("title", "New Chat")
    
    conversation = Conversation(
        user_id=user_id,
        title=title
    )
    db.session.add(conversation)
    db.session.commit()
    
    print(f"✅ [CREATE] Conversation {conversation.id} created for user {user_id}, title: '{title}'")
    
    return jsonify({
        "success": True,
        "conversation": conversation.to_dict()
    })


@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    """Get all conversations for current user"""
    user_id = session.get('user_id', DEMO_USER_ID)
    conversations = Conversation.query.filter_by(
        user_id=user_id
    ).order_by(Conversation.updated_at.desc()).all()
    
    print(f"📋 [FETCH] User {user_id} has {len(conversations)} conversations")
    for conv in conversations:
        print(f"   - Conv {conv.id}: '{conv.title}' ({len(conv.messages)} messages)")
    
    return jsonify({
        "success": True,
        "conversations": [conv.to_dict() for conv in conversations]
    })


@app.route("/api/conversation/<int:conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    """Get specific conversation with all messages"""
    user_id = session.get('user_id', DEMO_USER_ID)
    conversation = Conversation.query.get(conversation_id)
    
    if not conversation or conversation.user_id != user_id:
        print(f"❌ Conversation {conversation_id} not found or not owned by user {user_id}")
        return jsonify({
            "success": False,
            "error": "Conversation not found"
        }), 404
    
    print(f"📖 Fetching conversation {conversation_id} with {len(conversation.messages)} messages")
    
    return jsonify({
        "success": True,
        "conversation": conversation.to_dict(include_messages=True)
    })


@app.route("/api/conversation/<int:conversation_id>/title", methods=["PUT"])
def update_conversation_title(conversation_id):
    """Update conversation title"""
    user_id = session.get('user_id', DEMO_USER_ID)
    conversation = Conversation.query.get(conversation_id)
    
    if not conversation or conversation.user_id != user_id:
        return jsonify({
            "success": False,
            "error": "Conversation not found"
        }), 404
    
    data = request.json
    conversation.title = data.get("title", conversation.title)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "conversation": conversation.to_dict()
    })


@app.route("/api/conversation/<int:conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    user_id = session.get('user_id', DEMO_USER_ID)
    conversation = Conversation.query.get(conversation_id)
    
    if not conversation or conversation.user_id != user_id:
        return jsonify({
            "success": False,
            "error": "Conversation not found"
        }), 404
    
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Conversation deleted"
    })


# ==================== HOSPITAL SEARCH API ====================
@app.route("/api/nearby-hospitals", methods=["POST"])
def find_nearby_hospitals():
    """
    Find nearby hospitals based on user location and medical analysis
    
    Expected POST data:
    {
        "latitude": float,
        "longitude": float,
        "suggested_department": string,  (optional)
        "radius_km": int  (optional, default 5)
    }
    """
    try:
        data = request.json
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        suggested_department = data.get("suggested_department")
        radius_km = data.get("radius_km", 5)
        
        if latitude is None or longitude is None:
            return jsonify({
                "success": False,
                "error": "Latitude and longitude are required"
            }), 400
        
        # Get nearby hospitals
        result = get_nearby_hospitals(
            latitude=latitude,
            longitude=longitude,
            suggested_department=suggested_department,
            radius_km=radius_km,
            limit=5
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error finding nearby hospitals: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== CASE SEND API (PATIENT EXPLICIT ACTION) ====================
@app.route("/api/cases/send", methods=["POST"])
@role_required('patient')
def send_case():
    """
    Create a case ONLY when a patient explicitly selects a hospital and clicks Send Case.
    This is the correct flow — no auto-creation.
    """
    try:
        data = request.json
        user_id = session.get('user_id', DEMO_USER_ID)
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        # Required fields
        symptoms = data.get('symptoms', 'Not specified')
        ai_summary = data.get('ai_summary', 'No summary')
        urgency = data.get('urgency', 'Medium')
        suggested_department = data.get('suggested_department', 'General Medicine')
        hospital_id = data.get('hospital_id')  # hospital identifier
        hospital_name = data.get('hospital_name', 'Unknown Hospital')
        source = data.get('source', 'text')
        
        if not hospital_id:
            return jsonify({"success": False, "error": "Hospital selection required"}), 400
        
        new_case = Case(
            patient_id=user.id,
            patient_name=user.username,
            symptoms_text=symptoms,
            ai_summary=ai_summary,
            urgency_level=urgency,
            suggested_department=suggested_department,
            hospital_id=hospital_id,
            hospital_name=hospital_name,
            status='pending',
            source=source
        )
        db.session.add(new_case)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Case sent to hospital successfully",
            "case": new_case.to_dict()
        })
        
    except Exception as e:
        print(f"Error sending case: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/patient/cases", methods=["GET"])
@login_required
def patient_get_cases():
    """Get cases sent by the logged-in patient"""
    user_id = session.get('user_id')
    cases = Case.query.filter_by(patient_id=user_id).order_by(Case.created_at.desc()).all()
    return jsonify({
        "success": True,
        "cases": [c.to_dict() for c in cases]
    })


# ==================== CASE API (HOSPITAL / PATIENT) ====================
@app.route("/api/cases", methods=["GET"])
def get_cases():
    """Get all cases (Hospital only) or own cases (Patient)"""
    role = session.get('role', 'hospital') # Defaulting to hospital for testing
    user_id = session.get('user_id', DEMO_USER_ID)
    
    status_filter = request.args.get('status')
    
    query = Case.query
    
    if role == 'patient':
        query = query.filter_by(patient_id=user_id)
        
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    cases = query.order_by(Case.created_at.desc()).all()
    
    return jsonify({
        "success": True,
        "cases": [case.to_dict() for case in cases]
    })

@app.route("/api/cases/stats", methods=["GET"])
def get_cases_stats():
    """Get dashboard stats for hospital"""
    # Assuming hospital role checking
    
    pending_count = Case.query.filter_by(status='pending').count()
    in_review_count = Case.query.filter_by(status='in_review').count()
    resolved_count = Case.query.filter_by(status='resolved').count()
    high_priority_count = Case.query.filter_by(urgency_level='High').filter(Case.status != 'resolved').count()
    
    return jsonify({
        "success": True,
        "stats": {
            "pending": pending_count,
            "in_review": in_review_count,
            "resolved": resolved_count,
            "high_priority": high_priority_count
        }
    })

@app.route("/api/cases/<int:case_id>", methods=["GET"])
def get_case_detail(case_id):
    case_obj = Case.query.get(case_id)
    if not case_obj:
        return jsonify({"success": False, "error": "Case not found"}), 404
        
    return jsonify({
        "success": True,
        "case": case_obj.to_dict()
    })

@app.route("/api/cases/<int:case_id>/status", methods=["PUT"])
def update_case_status(case_id):
    case_obj = Case.query.get(case_id)
    if not case_obj:
        return jsonify({"success": False, "error": "Case not found"}), 404
        
    data = request.json
    new_status = data.get('status')
    
    if new_status in ['pending', 'in_review', 'accepted', 'resolved', 'referred']:
        case_obj.status = new_status
        db.session.commit()
        return jsonify({"success": True, "case": case_obj.to_dict()})
        
    return jsonify({"success": False, "error": "Invalid status"}), 400

@app.route("/api/cases/<int:case_id>/notes", methods=["PUT"])
def update_case_notes(case_id):
    case_obj = Case.query.get(case_id)
    if not case_obj:
        return jsonify({"success": False, "error": "Case not found"}), 404
        
    data = request.json
    notes = data.get('notes')
    
    if notes is not None:
        case_obj.hospital_notes = notes
        db.session.commit()
        return jsonify({"success": True, "case": case_obj.to_dict()})
        
    return jsonify({"success": False, "error": "Notes required"}), 400



@app.route("/api/hospital-map-data", methods=["POST"])
def get_hospital_map_data():
    """
    Get formatted hospital data for map display
    
    Expected POST data:
    {
        "latitude": float,
        "longitude": float,
        "suggested_department": string (optional),
        "radius_km": int (optional)
    }
    """
    try:
        data = request.json
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        suggested_department = data.get("suggested_department")
        radius_km = data.get("radius_km", 5)
        
        if latitude is None or longitude is None:
            return jsonify({
                "success": False,
                "error": "Location data required"
            }), 400
        
        result = get_nearby_hospitals(
            latitude=latitude,
            longitude=longitude,
            suggested_department=suggested_department,
            radius_km=radius_km,
            limit=5
        )
        
        # Format for map
        map_data = {
            "success": result['success'],
            "center": {
                "latitude": latitude,
                "longitude": longitude
            },
            "hospitals": result.get('hospitals', [])
        }
        
        return jsonify(map_data)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== HOSPITAL DASHBOARD API ====================
@app.route("/api/hospital/cases", methods=["GET"])
@login_required
def hospital_get_cases():
    """Get cases for hospital dashboard with filtering"""
    # Filter parameters
    status_filter = request.args.get('status')  # pending, in_review, accepted, resolved, referred
    urgency_filter = request.args.get('urgency')  # Low, Medium, High, Emergency
    department_filter = request.args.get('department')
    search_query = request.args.get('search')  # Search by patient name or case ID
    
    query = Case.query
    
    # Apply filters
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if urgency_filter and urgency_filter != 'all':
        query = query.filter_by(urgency_level=urgency_filter)
    
    if department_filter and department_filter != 'all':
        query = query.filter_by(suggested_department=department_filter)
    
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            (Case.patient_name.ilike(search_term)) |
            (Case.symptoms_text.ilike(search_term))
        )
    
    # Order by creation date (newest first)
    cases = query.order_by(Case.created_at.desc()).all()
    
    return jsonify({
        "success": True,
        "total": len(cases),
        "cases": [case.to_dict() for case in cases]
    })


@app.route("/api/hospital/cases/<int:case_id>", methods=["GET"])
def hospital_get_case_detail(case_id):
    """Get detailed view of a specific case for hospital"""
    case_obj = Case.query.get(case_id)
    
    if not case_obj:
        return jsonify({
            "success": False,
            "error": "Case not found"
        }), 404
    
    return jsonify({
        "success": True,
        "case": case_obj.to_dict()
    })


@app.route("/api/hospital/cases/<int:case_id>/accept", methods=["POST"])
def hospital_accept_case(case_id):
    """Hospital staff accepts a case"""
    case_obj = Case.query.get(case_id)
    
    if not case_obj:
        return jsonify({
            "success": False,
            "error": "Case not found"
        }), 404
    
    case_obj.status = 'accepted'
    case_obj.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Case accepted",
        "case": case_obj.to_dict()
    })


@app.route("/api/hospital/cases/<int:case_id>/review", methods=["POST"])
def hospital_review_case(case_id):
    """Hospital staff marks case as in review"""
    case_obj = Case.query.get(case_id)
    
    if not case_obj:
        return jsonify({
            "success": False,
            "error": "Case not found"
        }), 404
    
    case_obj.status = 'in_review'
    case_obj.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Case marked as in review",
        "case": case_obj.to_dict()
    })


@app.route("/api/hospital/cases/<int:case_id>/resolve", methods=["POST"])
def hospital_resolve_case(case_id):
    """Hospital staff marks case as resolved"""
    case_obj = Case.query.get(case_id)
    
    if not case_obj:
        return jsonify({
            "success": False,
            "error": "Case not found"
        }), 404
    
    case_obj.status = 'resolved'
    case_obj.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Case resolved",
        "case": case_obj.to_dict()
    })


@app.route("/api/hospital/cases/<int:case_id>/refer", methods=["POST"])
def hospital_refer_case(case_id):
    """Hospital staff refers case to another facility"""
    case_obj = Case.query.get(case_id)
    
    if not case_obj:
        return jsonify({
            "success": False,
            "error": "Case not found"
        }), 404
    
    data = request.json or {}
    notes = data.get('notes', '')
    
    case_obj.status = 'referred'
    case_obj.hospital_notes = notes
    case_obj.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Case referred",
        "case": case_obj.to_dict()
    })


@app.route("/api/hospital/cases/<int:case_id>/add-notes", methods=["POST"])
def hospital_add_case_notes(case_id):
    """Hospital staff adds notes to a case"""
    case_obj = Case.query.get(case_id)
    
    if not case_obj:
        return jsonify({
            "success": False,
            "error": "Case not found"
        }), 404
    
    data = request.json
    notes = data.get('notes')
    
    if not notes:
        return jsonify({
            "success": False,
            "error": "Notes are required"
        }), 400
    
    case_obj.hospital_notes = notes
    case_obj.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Notes added",
        "case": case_obj.to_dict()
    })


@app.route("/api/cases/<int:case_id>", methods=["DELETE"])
def delete_case(case_id):
    """Delete a case (hospital admin only)"""
    try:
        case_obj = Case.query.get(case_id)
        
        if not case_obj:
            return jsonify({
                "success": False,
                "error": "Case not found"
            }), 404
        
        # Delete associated conversation if exists
        patient_id = case_obj.patient_id
        # Delete patient-hospital conversations related to this case
        conversations = PatientHospitalConversation.query.filter_by(
            patient_id=patient_id
        ).all()
        
        for conv in conversations:
            db.session.delete(conv)
        
        # Delete the case
        db.session.delete(case_obj)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Case deleted successfully"
        })
        
    except Exception as e:
        print(f"Error deleting case: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/hospital/analytics", methods=["GET"])
@login_required
def hospital_get_analytics():
    """Get comprehensive, accurate analytics for hospital dashboard"""
    from datetime import timedelta, datetime
    
    # Get all cases
    all_cases = Case.query.all()
    total_cases = len(all_cases)
    
    # Status breakdown
    pending_cases = sum(1 for c in all_cases if c.status == 'pending')
    in_review_cases = sum(1 for c in all_cases if c.status == 'in_review')
    accepted_cases = sum(1 for c in all_cases if c.status == 'accepted')
    resolved_cases = sum(1 for c in all_cases if c.status == 'resolved')
    referred_cases = sum(1 for c in all_cases if c.status == 'referred')
    
    # Urgency breakdown
    high_priority_cases = sum(1 for c in all_cases if c.urgency_level in ['High', 'Emergency'])
    emergency_cases = sum(1 for c in all_cases if c.urgency_level == 'Emergency')
    high_urgency_unresolved = sum(1 for c in all_cases if c.urgency_level in ['High', 'Emergency'] and c.status not in ['resolved', 'referred'])
    
    # Success rate calculation
    success_rate = int((resolved_cases / total_cases * 100) if total_cases > 0 else 0)
    
    # Department-wise breakdown
    dept_breakdown = {}
    for case in all_cases:
        dept = case.suggested_department or 'Unspecified'
        if dept not in dept_breakdown:
            dept_breakdown[dept] = {'total': 0, 'resolved': 0, 'pending': 0, 'in_progress': 0}
        dept_breakdown[dept]['total'] += 1
        if case.status == 'resolved':
            dept_breakdown[dept]['resolved'] += 1
        elif case.status == 'pending':
            dept_breakdown[dept]['pending'] += 1
        elif case.status in ['in_review', 'accepted']:
            dept_breakdown[dept]['in_progress'] += 1
    
    # Sort departments by case count
    top_departments = sorted(dept_breakdown.items(), key=lambda x: x[1]['total'], reverse=True)
    
    # Urgency distribution
    urgency_dist = {}
    for case in all_cases:
        level = case.urgency_level or 'Unknown'
        urgency_dist[level] = urgency_dist.get(level, 0) + 1
    
    # Status percentage distribution
    status_percentage = {
        'resolved': int((resolved_cases / total_cases * 100) if total_cases > 0 else 0),
        'in_progress': int(((in_review_cases + accepted_cases) / total_cases * 100) if total_cases > 0 else 0),
        'pending': int((pending_cases / total_cases * 100) if total_cases > 0 else 0),
        'referred': int((referred_cases / total_cases * 100) if total_cases > 0 else 0),
    }
    
    # Average response time (based on created_at to updated_at)
    if all_cases:
        total_response_time = 0
        cases_with_updates = 0
        for case in all_cases:
            if case.updated_at and case.created_at:
                response_time = (case.updated_at - case.created_at).total_seconds() / 3600  # in hours
                total_response_time += response_time
                cases_with_updates += 1
        avg_response_time = total_response_time / cases_with_updates if cases_with_updates > 0 else 0
    else:
        avg_response_time = 0
    
    # Monthly case growth (last 30 days vs previous 30 days)
    today = datetime.utcnow()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)
    
    current_month_cases = sum(1 for c in all_cases if c.created_at >= thirty_days_ago)
    previous_month_cases = sum(1 for c in all_cases if sixty_days_ago <= c.created_at < thirty_days_ago)
    
    month_growth = 0
    if previous_month_cases > 0:
        month_growth = int(((current_month_cases - previous_month_cases) / previous_month_cases * 100))
    
    return jsonify({
        "success": True,
        "analytics": {
            "case_statistics": {
                "total_cases": total_cases,
                "pending": pending_cases,
                "in_review": in_review_cases,
                "accepted": accepted_cases,
                "resolved": resolved_cases,
                "referred": referred_cases,
                "high_priority": high_priority_cases,
                "emergency": emergency_cases,
                "success_rate": success_rate,
            },
            "department_breakdown": {dept: stats for dept, stats in top_departments},
            "urgency_distribution": urgency_dist,
            "status_percentage": status_percentage,
            "performance_metrics": {
                "average_response_time_hours": round(avg_response_time, 1),
                "current_month_cases": current_month_cases,
                "previous_month_cases": previous_month_cases,
                "month_growth_percentage": month_growth,
                "high_urgency_unresolved": high_urgency_unresolved,
            }
        }
    })


@app.route("/api/hospital/dashboard-stats", methods=["GET"])
@login_required
def hospital_get_dashboard_stats():
    """Get comprehensive stats for hospital dashboard"""
    from datetime import timedelta
    
    # Calculate stats
    total_cases = Case.query.count()
    pending_cases = Case.query.filter_by(status='pending').count()
    in_review_cases = Case.query.filter_by(status='in_review').count()
    accepted_cases = Case.query.filter_by(status='accepted').count()
    resolved_cases = Case.query.filter_by(status='resolved').count()
    high_urgency_cases = Case.query.filter_by(urgency_level='High').filter(Case.status.in_(['pending', 'in_review'])).count()
    emergency_cases = Case.query.filter_by(urgency_level='Emergency').filter(Case.status.in_(['pending', 'in_review'])).count()
    
    # Get distinct departments represented in cases
    all_cases = Case.query.all()
    unique_departments = set(c.suggested_department for c in all_cases if c.suggested_department)
    
    # Get urgency distribution
    urgency_dist = {}
    for case in all_cases:
        if case.urgency_level:
            urgency_dist[case.urgency_level] = urgency_dist.get(case.urgency_level, 0) + 1
    
    return jsonify({
        "success": True,
        "stats": {
            "total_cases": total_cases,
            "pending": pending_cases,
            "in_review": in_review_cases,
            "accepted": accepted_cases,
            "resolved": resolved_cases,
            "high_urgency": high_urgency_cases,
            "emergency": emergency_cases,
            "unique_departments": len(unique_departments),
            "urgency_distribution": urgency_dist
        }
    })


@app.route("/api/hospital/departments", methods=["GET"])
@login_required
def hospital_get_departments():
    """Get list of all unique departments from cases"""
    cases = Case.query.all()
    departments = sorted(list(set(c.suggested_department for c in cases if c.suggested_department)))
    
    return jsonify({
        "success": True,
        "departments": departments
    })


# ==================== PATIENT-HOSPITAL MESSAGING API ====================

@app.route("/api/messages/start-conversation", methods=["POST"])
@role_required('hospital')
def start_conversation():
    """
    Hospital initiates a new conversation with a patient
    Only hospitals can start conversations
    """
    try:
        data = request.json
        hospital_id = session.get('user_id')
        patient_id = data.get('patient_id')
        initial_message = data.get('message', '')
        
        if not patient_id:
            return jsonify({"success": False, "error": "Patient ID required"}), 400
        
        # Verify patient exists
        patient = User.query.get(patient_id)
        if not patient or patient.role != 'patient':
            return jsonify({"success": False, "error": "Patient not found"}), 404
        
        # Check if conversation already exists
        existing = PatientHospitalConversation.query.filter_by(
            hospital_id=hospital_id,
            patient_id=patient_id
        ).first()
        
        if existing:
            return jsonify({
                "success": False, 
                "error": "Conversation already exists with this patient",
                "conversation_id": existing.id
            }), 400
        
        # Create new conversation
        conversation = PatientHospitalConversation(
            hospital_id=hospital_id,
            patient_id=patient_id
        )
        db.session.add(conversation)
        db.session.flush()  # Get the conversation ID
        
        # Add initial message if provided
        if initial_message.strip():
            msg = PatientHospitalMessage(
                conversation_id=conversation.id,
                sender_id=hospital_id,
                content=initial_message
            )
            db.session.add(msg)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Conversation started",
            "conversation": conversation.to_dict(include_messages=True)
        })
        
    except Exception as e:
        print(f"Error starting conversation: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/messages/conversations", methods=["GET"])
@login_required
def get_messaging_conversations():
    """
    Get all conversations for current user (patient or hospital)
    """
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        
        if role == 'hospital':
            # Get all conversations initiated by this hospital
            conversations = PatientHospitalConversation.query.filter_by(
                hospital_id=user_id
            ).order_by(PatientHospitalConversation.updated_at.desc()).all()
        else:  # patient
            # Get all conversations where this user is the patient
            conversations = PatientHospitalConversation.query.filter_by(
                patient_id=user_id
            ).order_by(PatientHospitalConversation.updated_at.desc()).all()
        
        conversations_payload = []
        for conv in conversations:
            conv_data = conv.to_dict()
            ordered_messages = sorted(conv.messages, key=lambda m: m.created_at)

            # Provide a deterministic preview payload for list UI.
            if ordered_messages:
                conv_data['last_message'] = ordered_messages[-1].to_dict()
            else:
                conv_data['last_message'] = None

            # Track unread messages from the OTHER party
            if role == 'patient':
                cutoff = conv.patient_last_read
                unread_messages = [
                    m for m in ordered_messages
                    if m.sender_id == conv.hospital_id and (cutoff is None or m.created_at > cutoff)
                ]
                conv_data['unread_count'] = len(unread_messages)
            else:
                cutoff = conv.hospital_last_read
                unread_messages = [
                    m for m in ordered_messages
                    if m.sender_id == conv.patient_id and (cutoff is None or m.created_at > cutoff)
                ]
                conv_data['unread_count'] = len(unread_messages)

            conversations_payload.append(conv_data)

        return jsonify({
            "success": True,
            "conversations": conversations_payload
        })
        
    except Exception as e:
        print(f"Error fetching conversations: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/messages/conversation/<int:conversation_id>", methods=["GET"])
@login_required
def get_conversation_detail(conversation_id):
    """
    Get conversation with all messages
    User must be either the hospital or patient in the conversation
    """
    try:
        user_id = session.get('user_id')
        conversation = PatientHospitalConversation.query.get(conversation_id)
        
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        # Check access
        if conversation.hospital_id != user_id and conversation.patient_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403
        
        return jsonify({
            "success": True,
            "conversation": conversation.to_dict(include_messages=True)
        })
        
    except Exception as e:
        print(f"Error fetching conversation: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/messages/send", methods=["POST"])
@login_required
def send_message():
    """
    Send a message in a conversation
    User must be participant in the conversation
    """
    try:
        user_id = session.get('user_id')
        data = request.json
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({"success": False, "error": "Message cannot be empty"}), 400
        
        if not conversation_id:
            return jsonify({"success": False, "error": "Conversation ID required"}), 400
        
        conversation = PatientHospitalConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        # Check access
        if conversation.hospital_id != user_id and conversation.patient_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403
        
        # Create message
        message = PatientHospitalMessage(
            conversation_id=conversation_id,
            sender_id=user_id,
            content=content
        )
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Message sent",
            "data": message.to_dict()
        })
        
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/messages/mark-read/<int:conversation_id>", methods=["POST"])
@login_required
def mark_conversation_read(conversation_id):
    """
    Mark conversation as read by patient
    Only patient can mark as read (to track unread count)
    """
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        
        conversation = PatientHospitalConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        # Mark as read for the current role
        if role == 'patient' and conversation.patient_id == user_id:
            conversation.patient_last_read = datetime.utcnow()
            db.session.commit()
        elif role == 'hospital' and conversation.hospital_id == user_id:
            conversation.hospital_last_read = datetime.utcnow()
            db.session.commit()
        else:
            return jsonify({"success": False, "error": "Access denied"}), 403
        
        return jsonify({
            "success": True,
            "message": "Marked as read"
        })
        
    except Exception as e:
        print(f"Error marking read: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/messages/quick-poll", methods=["GET"])
@login_required
def poll_new_messages():
    """
    Poll for new messages (for real-time-ish updates)
    Returns conversations with unread messages
    """
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        
        if role == 'hospital':
            conversations = PatientHospitalConversation.query.filter_by(
                hospital_id=user_id
            ).all()
        else:  # patient
            conversations = PatientHospitalConversation.query.filter_by(
                patient_id=user_id
            ).all()
        
        # Return conversations updated in the last 30 seconds (for polling)
        from datetime import timedelta
        recent_cutoff = datetime.utcnow() - timedelta(seconds=30)
        
        recent_convs = [c for c in conversations if c.updated_at > recent_cutoff]
        
        return jsonify({
            "success": True,
            "conversations": [c.to_dict() for c in recent_convs],
            "has_unread": any(c.unread_count > 0 for c in conversations)
        })
        
    except Exception as e:
        print(f"Error polling messages: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/messages/patients-list", methods=["GET"])
@role_required('hospital')
def get_patients_for_messaging():
    """
    Get list of patients that hospital can message
    Returns all patients for simplicity (can be filtered by hospital's cases)
    """
    try:
        # Get all patients
        patients = User.query.filter_by(role='patient').all()
        
        user_id = session.get('user_id')
        
        # For each patient, check if conversation exists
        patient_list = []
        for patient in patients:
            existing_conv = PatientHospitalConversation.query.filter_by(
                hospital_id=user_id,
                patient_id=patient.id
            ).first()
            
            patient_list.append({
                'id': patient.id,
                'name': patient.username,
                'email': patient.email,
                'has_conversation': existing_conv is not None,
                'conversation_id': existing_conv.id if existing_conv else None
            })
        
        return jsonify({
            "success": True,
            "patients": patient_list
        })
        
    except Exception as e:
        print(f"Error fetching patients: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== START ================== 
if __name__ == "__main__":
    app.run(debug=True)


