# Cureva - Complete Testing Guide

## Overview

This guide covers testing Cureva locally with PostgreSQL and bcrypt authentication.

---

## Prerequisites

- Python 3.13+ installed
- Virtual environment activated
- Dependencies installed: `pip install -r requirements.txt`
- Flask server running: `python app.py`

**Database:**
- Local: SQLite (auto-created)
- Production: PostgreSQL on Render (configured in `.env`)

---

## Demo Accounts

### Pre-seeded Users (Available Immediately)

**Patient Demo:**
- Email: `Patient_demo@gmail.com`
- Password: `demo_password`

**Hospital Demo:**
- Email: `Demo_Hospital@gmail.com`
- Password: `hospital_demo`

### New Accounts

You can also create accounts by signing up:
1. Click "Sign up for free" on login page
2. Choose role (Patient or Hospital)
3. Enter username, email, password
4. Account created and auto-logged in

---

## Test Scenarios

### Scenario 1: Patient Login & AI Analysis

**Steps:**
1. Navigate to: `http://localhost:5000/`
2. Click "🔬 Analyze My Report" or go to login
3. Email: `Patient_demo@gmail.com`
4. Password: `demo_password`
5. Role: `Patient` (pre-selected)
6. Click "Sign In"

**Expected Results:**
- ✅ Redirected to `/patient` dashboard
- ✅ Dashboard shows "AI Medical Assistant" title
- ✅ Patient sidebar visible (Dashboard, History, Messages, Hospitals, Profile)
- ✅ No hospital features visible

**Test AI Chat:**
1. Go to Dashboard
2. Type symptom: "I have severe headache and fever for 3 days"
3. Click "Analyze" or press Enter
4. Expected: AI responds with:
   - Possible conditions
   - Suggested departments (Neurology, Internal Medicine, etc.)
   - Urgency level (Low/Medium/High)
   - Recommended actions

---

### Scenario 2: Hospital Login & Case Management

**Steps:**
1. Logout or open incognito window
2. Navigate to: `http://localhost:5000/login?role=hospital`
3. Or click "🏥 For Hospitals" from landing page
4. Email: `Demo_Hospital@gmail.com`
5. Password: `hospital_demo`
6. Role: `Hospital` (pre-selected)
7. Click "Sign In"

**Expected Results:**
- ✅ Redirected to `/hospital` dashboard
- ✅ Dashboard shows "Hospital Dashboard" title
- ✅ KPI cards show case statistics
- ✅ Hospital sidebar visible (Dashboard, Cases, Messages, Analytics, Profile)
- ✅ No patient features visible

**Test Case Management:**
1. Go to "Cases" tab
2. View list of cases sent by patients
3. Click on a case to see details:
   - Patient name
   - Symptoms/AI analysis
   - Medical images (if uploaded)
   - Urgency level
   - Suggested department
4. Expected: Full case history visible

---

### Scenario 3: Hospital Search & Case Sending

**As Patient:**
1. Login as patient
2. Go to "Hospitals" or "Hospital Search"
3. Expected: Leaflet map shows real nearby hospitals (OpenStreetMap)
4. Click on hospital marker
5. Hospital details shown (name, address, phone)
6. Click "Send Case" button
7. Expected: Case sent to hospital with all patient data

**Verify Case Received:**
1. Switch to hospital account
2. Go to "Cases" dashboard
3. Expected: New case appears in list from patient
4. Click to view full details

---

### Scenario 4: Signup (New Account)

**Steps:**
1. Navigate to: `http://localhost:5000/login`
2. Click "Sign up for free"
3. Fill form:
   - Role: Patient or Hospital
   - Username: `test_user_123`
   - Email: `test@example.com`
   - Password: `TestPass123`
   - Confirm: `TestPass123`
4. Click "Create Account"

**Expected Results:**
- ✅ Form validates (password length, confirmation match)
- ✅ Account created successfully
- ✅ Auto-logged in and redirected to dashboard
- ✅ Welcome message shown
- ✅ Profile shows new username/email

**Test Password Validation:**
- Try password < 6 chars → Error message shown
- Try mismatched passwords → Error message shown
- Try duplicate email → Error shown (if another user registered it)
- Try duplicate username → Error shown

---

### Scenario 5: Password Hashing Security
2. **Select**: "Patient" role
3. **Enter**: admin@cityhospital.com / admin_password (hospital credentials)
4. **Click**: "Sign In"
5. **Expected**: Error message "Invalid credentials"
6. **Result**: ✓ Cross-role login blocked

### Scenario 4: Logout Functionality
1. **Login as patient** (follow Scenario 1)
2. **In dashboard**: Click "Logout" button (top right)
3. **Expected**: Redirected to landing page (/)
4. **Verify**: Session cleared, cannot access `/patient` directly
5. **Test**: Try accessing `/patient` directly
6. **Expected**: Redirected to login page

### Scenario 5: Unauthorized Access Prevention
1. **Without logging in**: Try accessing http://localhost:5000/patient
2. **Expected**: Redirected to login page
3. **Without logging in**: Try accessing http://localhost:5000/hospital
4. **Expected**: Redirected to login page
5. **Result**: ✓ Direct dashboard access blocked

### Scenario 6: Cross-Portal Prevention (Patient as Hospital)
1. **Login as patient** (john@email.com)
2. **Try direct access**: Navigate to http://localhost:5000/hospital
3. **Expected**: Redirected to landing page (role mismatch)
4. **Result**: ✓ Patient cannot access hospital portal

### Scenario 7: Cross-Portal Prevention (Hospital as Patient)
1. **Login as hospital** (admin@cityhospital.com)
2. **Try direct access**: Navigate to http://localhost:5000/patient
3. **Expected**: Redirected to landing page (role mismatch)
4. **Result**: ✓ Hospital cannot access patient portal

### Scenario 8: Case Sending Demo (Patient → Hospital)
1. **Login as patient** (john@email.com)
2. **Go to**: Patient Dashboard → Hospitals
3. **Action**: Click "🔬 Request Location" button
4. **Result**: Loads nearby hospitals map
5. **Select**: Any hospital and click "📤 Send Case"
6. **Expected**: Success message appears
7. **Login as hospital** (admin@cityhospital.com)
8. **Go to**: Hospital Dashboard
9. **Verify**: New case appears in "Pending Cases" queue
10. **Result**: ✓ Case correctly appears in hospital dashboard

### Scenario 9: Role Switching
1. **Login as patient** (john@email.com)
2. **Logout**
3. **Login as hospital** (admin@cityhospital.com)
4. **Expected**: Successfully switches roles
5. **Verify**: Hospital dashboard loads correctly
6. **Result**: ✓ Multiple role sessions work properly

### Scenario 10: Session Persistence
1. **Login as patient**
2. **Close browser tab** (session should persist)
3. **Refresh page**
4. **Expected**: Still logged in as patient
5. **Result**: ✓ Session persists across page refreshes

## API Endpoint Testing

### Protected Endpoints (Require Authentication)
```bash
# Patient
GET /api/patient/cases - Returns patient's cases only
POST /api/cases/send - Only patients can send cases

# Hospital  
GET /api/hospital/cases - Returns all cases to any logged-in hospital
GET /api/hospital/dashboard-stats - Returns hospital statistics
GET /api/hospital/departments - Returns department list
```

### Test with cURL (if needed)
```bash
# Test unauthorized access
curl http://localhost:5000/api/patient/cases
# Expected: 403 Unauthorized

# After login (session cookie required)
curl -b "session_cookie" http://localhost:5000/api/patient/cases
# Expected: 200 OK with JSON response
```

## Success Indicators

✓ Patient logs in → Patient dashboard loads
✓ Hospital logs in → Hospital dashboard loads
✓ Both portals show only role-appropriate features
✓ Cross-role login attempts are rejected
✓ Logout clears session completely
✓ Direct dashboard access redirects to login
✓ Cases sent by patients appear in hospital dashboard
✓ UI feels responsive and professional

## Common Issues & Solutions

### Issue: "Invalid credentials" on correct password
- **Cause**: Wrong role selected in login form
- **Solution**: Make sure radio button matches account role (Patient/Hospital)

### Issue: Redirects to landing page after login
- **Cause**: Role mismatch between login form and account
- **Solution**: Select correct role before entering credentials

### Issue: Can't access hospital dashboard after login
- **Cause**: Session not properly stored
- **Solution**: Clear browser cache and try again

### Issue: Cases not appearing in hospital dashboard
- **Cause**: Hospital dashboard JS not fetching updated data
- **Solution**: Refresh the page or check browser console for errors

## Files Modified Summary

| File | Changes |
|------|---------|
| app.py | Role-based routes, role_required decorator, logout endpoints |
| login.html | Role parameter handling, auto-selection |
| landing.html | Role-specific navigation links |
| patients/dashboard.html | Logout button & handler |
| hospitals/dashboard.html | Logout button & handler |

## Performance Notes

- First load may be slow (initialization)
- Database queries optimized with indexed lookups
- Session validation fast (in-memory)
- Case filtering efficient with proper SQL queries

## Notes

- This is a demo implementation
- In production, use password hashing (bcrypt)
- Add CSRF protection for form submissions
- Implement rate limiting on login endpoint
- Consider hospital-specific case scoping
