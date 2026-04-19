# Quick Start Testing Guide

## 🟢 Ready to Test - Updated with PostgreSQL & Bcrypt

This guide shows how to test Cureva locally and on production (Vercel).

---

## ⚡ Local Testing (5 minutes)

### **Step 1: Start the App**

```bash
# Make sure you're in the project directory
cd "C:\Users\lalit\OneDrive\Desktop\Cureva AI-Powered Patient and Hospital Assistance System"

# Run the Flask app
python app.py
```

✅ You should see:
```
✅ Demo patient created: Patient_Demo (Patient_demo@gmail.com)
✅ Demo hospital created: Demo_Hospital (Demo_Hospital@gmail.com)
 * Running on http://127.0.0.1:5000
```

### **Step 2: Access the App**

Open browser and go to: `http://localhost:5000`

### **Step 3: Login as Patient**

**Demo Account:**
- Email: `Patient_demo@gmail.com`
- Password: `demo_password`
- Role: Patient

Or create a new account:
- Click "Sign up for free"
- Enter username, email, password
- Select Patient role
- Click "Create Account"

### **Step 4: Test Patient Features**

1. **Chat with AI:**
   - Go to Dashboard
   - Type symptom: "I have chest pain and shortness of breath"
   - AI analyzes and gives urgency level
   
2. **Upload Medical Report (Optional):**
   - Click "Upload Report"
   - Upload X-ray or image
   - AI analyzes the medical image

3. **Find Nearby Hospitals:**
   - Click "Hospital Search" or "Hospitals"
   - Map shows real nearby hospitals (OpenStreetMap)
   - Click on hospital to see details
   
4. **Send Case to Hospital:**
   - Click hospital on map
   - Click "Send Case"
   - Select "Demo_Hospital"
   - Case sent!

### **Step 5: Switch to Hospital Account**

**Hospital Demo Account:**
- Email: `Demo_Hospital@gmail.com`
- Password: `hospital_demo`
- Role: Hospital

Or logout and login as hospital.

### **Step 6: View Cases on Hospital Dashboard**

1. Hospital Dashboard
2. Look for "Cases" or "Messages" section
3. You should see the case sent from patient
4. Click to view details
5. Send response message

---

## 🚀 Production Testing (Vercel)

### ✅ Hospital Features
- [ ] Click "New Conversation" button
- [ ] See list of patients
- [ ] Select a patient
- [ ] Initial message auto-filled
- [ ] Conversation created successfully
- [ ] Search conversations by patient name
- [ ] Send multiple messages
- [ ] See unread badge for patient replies
- [ ] Messages persist after refresh
- [ ] Timestamps show correctly

### ✅ Patient Features
- [ ] See incoming conversation automatically
- [ ] Unread badge shows "1"
- [ ] Click to open conversation
- [ ] Read hospital message
- [ ] Badge disappears after reading
- [ ] Reply with message
- [ ] Search hospitals by name
- [ ] Messages persist after refresh
- [ ] See hospital name correctly

### ✅ Real-Time Features
- [ ] Open both hospital and patient in separate windows
- [ ] Hospital sends message
- [ ] Patient sees it within 4 seconds
- [ ] Patient replies
- [ ] Hospital sees reply within 3 seconds
- [ ] Unread badges update in real-time

### ✅ Error Handling
- [ ] Try to send empty message (should be blocked)
- [ ] Logout and see redirect to login
- [ ] Try to access conversation as wrong user (should fail)
- [ ] Network disconnect - polling stops gracefully

### ✅ UI/UX
- [ ] Conversation list scrolls smoothly
- [ ] Message area scrolls to bottom on new message
- [ ] Send button disables while sending
- [ ] Input clears after sending
- [ ] Professional design matches Cureva theme

---

## 📊 Expected Results

### Hospital Starting Conversation
```
1. Hospital clicks "New Conversation"
2. Modal shows available patients
3. Hospital selects patient
4. Conversation created with initial message
5. Appears in conversation list
6. Patient automatically sees it ✓
```

### Patient Receiving Message
```
1. Hospital sends message
2. Patient sees conversation appear in Messages
3. Unread badge shows count
4. Patient clicks to open
5. Message visible with timestamp
6. Badge disappears ✓
```

### Bidirectional Messaging
```
1. Patient replies to hospital message
2. Message sent successfully
3. Hospital sees reply within 3 seconds
4. Conversation updated_at timestamp changes
5. Both see full message history
6. Format shows sender appropriately ✓
```

---

## 🔍 Browser Console Testing

Open DevTools (F12) and check:

1. **No JavaScript errors** - Console should be clean
2. **API calls working** - Network tab shows 200 responses
3. **Payload correct** - Messages sent with proper structure
4. **Session maintained** - User stays logged in

---

## 📱 Mobile Testing

Test on mobile device or using DevTools device emulation:

- [ ] Conversation list responsive
- [ ] Chat window readable on small screens
- [ ] Input box accessible
- [ ] Send button clickable
- [ ] No layout breaks

---

## 🚀 Production Checklist

Before deploying to Vercel:

- [ ] Test all messaging flows work
- [ ] No error logs in console
- [ ] Performance acceptable (polling smooth)
- [ ] Database properly configured
- [ ] Environment variables set
- [ ] Session handling works
- [ ] Security decorators active

---

## 💾 Database Verification

Check database has new tables:

```bash
# In Python shell or DB viewer
# Should exist:
# - patient_hospital_conversations (table)
# - patient_hospital_messages (table)
```

---

## 🎓 Understanding Message Flow

### Start Conversation Flow
```
Hospital -> POST /api/messages/start-conversation
  Patient ID provided
  Initial message optional
  
Backend:
  Create PatientHospitalConversation row
  Create PatientHospitalMessage row (if message provided)
  Return conversation object

Response:
  Success with conversation ID and details
  
Patient sees:
  New conversation in their Messages list
```

### Send Message Flow
```
User -> POST /api/messages/send
  Conversation ID provided
  Message content provided
  
Backend:
  Verify user is participant
  Create PatientHospitalMessage row
  Update conversation updated_at
  
Response:
  Success with message object

Other user sees:
  Message appears within polling interval
```

### Real-Time Polling Flow
```
Frontend:
  Every 3-4 seconds: GET /api/messages/quick-poll
  
Backend:
  Return conversations updated in last 30 seconds
  
Frontend:
  If conversation updated:
    Fetch full conversation
    Re-render chat window
    Show new message
```

---

## 📋 Troubleshooting

### Messages not appearing for patient
- Check polling is running (console logs)
- Verify conversation was created in hospital database
- Check patient logged in with correct account
- Hard refresh page

### Unread badge not showing
- Message might be marked read already
- Check patient_last_read timestamp
- Try sending new message

### Timestamp shows wrong time
- Check server time correct
- Client time might be wrong
- Timestamps stored in UTC

### Can't start conversation
- Verify hospital logged in
- Patient must exist in database
- Check console for specific error

---

## 🎯 Success Criteria

You'll know it's working when:

✅ Hospital can start conversation with patient
✅ Patient automatically sees it in Messages
✅ Both can send and receive messages
✅ Unread badges track correctly
✅ Messages persist in database
✅ Real-time updates within 4 seconds
✅ No JavaScript errors in console
✅ UI is clean and responsive
✅ Logout/login works properly
✅ All security checks pass

---

**You're all set! Start testing now.** 🚀
