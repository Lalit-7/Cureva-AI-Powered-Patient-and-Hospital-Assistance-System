from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==================== USER MODEL ====================
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='patient', nullable=False) # 'patient' or 'hospital'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to conversations and cases
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    cases = db.relationship('Case', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() + 'Z'
        }


# ==================== CONVERSATION MODEL ====================
class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to messages
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

    def get_effective_title(self):
        """Return a meaningful title; fallback to first user message when title is generic."""
        raw_title = (self.title or '').strip()
        generic_titles = {'', 'new chat', 'new conversation', 'untitled'}

        if raw_title.lower() not in generic_titles:
            return raw_title

        user_messages = [m for m in self.messages if m.role == 'user' and (m.content or '').strip()]
        if not user_messages:
            return 'New Chat'

        user_messages.sort(key=lambda m: m.created_at or datetime.utcnow())
        first_message = user_messages[0].content.strip()
        return first_message[:60] + ('...' if len(first_message) > 60 else '')
    
    def to_dict(self, include_messages=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.get_effective_title(),
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z',
            'message_count': len(self.messages)
        }
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in self.messages]
        return data


# ==================== MESSAGE MODEL ====================
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'image_filename': self.image_filename,
            'created_at': self.created_at.isoformat() + 'Z'
        }


# ==================== CASE MODEL ====================
class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name = db.Column(db.String(80), nullable=False)
    symptoms_text = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(50), nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    urgency_level = db.Column(db.String(20), nullable=True) # Low, Medium, High
    suggested_department = db.Column(db.String(100), nullable=True)
    hospital_id = db.Column(db.String(200), nullable=True)  # identifier of selected hospital
    hospital_name = db.Column(db.String(200), nullable=True)  # name of selected hospital
    status = db.Column(db.String(20), default='pending') # pending, in_review, accepted, resolved, referred
    source = db.Column(db.String(20), nullable=True) # text, image, voice
    hospital_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'symptoms_text': self.symptoms_text,
            'report_type': self.report_type,
            'ai_summary': self.ai_summary,
            'urgency_level': self.urgency_level,
            'suggested_department': self.suggested_department,
            'status': self.status,
            'source': self.source,
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital_name,
            'hospital_notes': self.hospital_notes,
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z'
        }


# ==================== PATIENT-HOSPITAL CONVERSATION MODEL ====================
class PatientHospitalConversation(db.Model):
    __tablename__ = 'patient_hospital_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    # Hospital who initiates the conversation
    hospital_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Patient in the conversation
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    hospital = db.relationship('User', foreign_keys=[hospital_id], backref='initiated_conversations')
    patient = db.relationship('User', foreign_keys=[patient_id], backref='received_conversations')
    messages = db.relationship('PatientHospitalMessage', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Track if patient has read the conversation (for notifications)
    patient_last_read = db.Column(db.DateTime, nullable=True)
    hospital_last_read = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self, include_messages=False, viewer_role=None):
        data = {
            'id': self.id,
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital.username if self.hospital else 'Unknown',
            'patient_id': self.patient_id,
            'patient_name': self.patient.username if self.patient else 'Unknown',
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z',
            'message_count': len(self.messages),
            'unread_count': 0
        }
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in sorted(self.messages, key=lambda m: m.created_at)]
        return data


# ==================== PATIENT-HOSPITAL MESSAGE MODEL ====================
class PatientHospitalMessage(db.Model):
    __tablename__ = 'patient_hospital_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('patient_hospital_conversations.id'), nullable=False)
    
    # Sender info
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    # Message content
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else 'Unknown',
            'sender_role': self.sender.role if self.sender else 'unknown',
            'content': self.content,
            'created_at': self.created_at.isoformat() + 'Z'
        }

