// ==================== GLOBAL STATE ====================
let currentConversationId = null;
let voiceText = "";
let isAnalyzing = false;
let isFirstMessage = true;
let lastAiResult = null; // Stores the last AI analysis for sending to hospitals

// ==================== STORAGE UTILITIES ====================
const STORAGE_KEY = "cureva_conversation_id";
const STORAGE_FIRST_MSG = "cureva_is_first_message";

function saveConversationId(id) {
  if (id) {
    localStorage.setItem(STORAGE_KEY, id);
    console.log(`💾 [STORE] Saved conversation_id ${id} to localStorage`);
  }
}

function loadConversationId() {
  const id = localStorage.getItem(STORAGE_KEY);
  if (id) {
    console.log(`📂 [LOAD] Loaded conversation_id ${id} from localStorage`);
    return parseInt(id);
  }
  return null;
}

function clearConversationId() {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(STORAGE_FIRST_MSG);
  console.log(`🗑️ [CLEAR] Cleared conversation_id from localStorage`);
}

function saveFirstMessageState(state) {
  localStorage.setItem(STORAGE_FIRST_MSG, state ? "true" : "false");
}

function loadFirstMessageState() {
  const state = localStorage.getItem(STORAGE_FIRST_MSG);
  return state === "true";
}

document.addEventListener("DOMContentLoaded", () => {

  const imageInput = document.getElementById("imageInput");
  const textInput = document.getElementById("textInput");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const recordBtn = document.getElementById("recordBtn");
  const voiceStatus = document.getElementById("voiceStatus");
  const uploadBtn = document.getElementById("uploadBtn");
  const chat = document.getElementById("chatOutput");
  const deleteConversationBtn = document.getElementById("deleteConversationBtn");

  // Load existing conversation from localStorage or backend
  initSession();

  /* ==================== DELETE CONVERSATION ==================== */
  deleteConversationBtn?.addEventListener("click", () => {
    if (!currentConversationId) return;
    
    if (confirm("Are you sure you want to delete this conversation?")) {
      fetch(`/api/conversation/${currentConversationId}`, {
        method: "DELETE"
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          clearConversationId();
          startFreshChat();
          console.log("✅ [DELETE] Conversation deleted and cleared from storage");
        }
      })
      .catch(err => console.error(err));
    }
  });

  /* ==================== ENTER KEY SUPPORT ==================== */
  textInput?.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !isAnalyzing) {
      e.preventDefault();
      analyzeBtn.click();
    }
  });

  /* ==================== IMAGE UPLOAD ==================== */
  if (uploadBtn && imageInput) {
    uploadBtn.addEventListener("click", () => {
      imageInput.click();
    });
  }

  imageInput?.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (!file) return;

    chat.innerHTML += `
      <div class="chat-message-user">
        📎 Image uploaded: ${file.name}
      </div>
    `;
  });

  /* ==================== VOICE INPUT ==================== */
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (SpeechRecognition && recordBtn) {
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recordBtn.addEventListener("click", () => {
      voiceText = "";
      recognition.start();
      voiceStatus.innerText = "Listening...";
      recordBtn.disabled = true;
    });

    recognition.onresult = (event) => {
      if (event.results.length > 0) {
        voiceText = event.results[0][0].transcript;
        voiceStatus.innerText = `Recorded: "${voiceText}"`;

        if (textInput) {
          textInput.value = voiceText;
          textInput.focus();
        }
      }
    };

    recognition.onerror = (event) => {
      voiceStatus.innerText = `Voice error: ${event.error}`;
    };

    recognition.onend = () => {
      recordBtn.disabled = false;
    };

  } else if (voiceStatus) {
    voiceStatus.innerText = "Voice input not supported in this browser.";
    if (recordBtn) recordBtn.disabled = true;
  }

  /* ==================== ANALYZE ==================== */
  analyzeBtn?.addEventListener("click", async () => {

    if (!currentConversationId) {
      alert("Please wait, setting up the session...");
      return;
    }

    const formData = new FormData();

    const imageFile = imageInput?.files[0];
    const typedText = textInput?.value.trim();
    const finalText = typedText || voiceText;

    if (!imageFile && !finalText) {
      alert("Please enter symptoms or upload image.");
      return;
    }

    isAnalyzing = true;
    analyzeBtn.disabled = true;

    /* USER MESSAGE */
    chat.innerHTML += `
      <div class="chat-message-user">
        ${escapeHtml(finalText || "Medical image submitted")}
      </div>
    `;

    chat.scrollTop = chat.scrollHeight;

    // Clear input after sending
    if (textInput) {
      textInput.value = "";
    }
    voiceText = "";

    if (imageFile) {
      formData.append("image", imageFile);
      imageInput.value = "";
    }

    if (finalText) {
      formData.append("text", finalText);
    }

    // Add conversation_id to form
    formData.append("conversation_id", currentConversationId);
    console.log(`📤 [SEND] Sending message to conversation ${currentConversationId}:`, finalText || "Image");

    // Add and store reference to loading message
    const loadingId = `loading-${Date.now()}`;
    chat.innerHTML += `
      <div class="chat-message-ai" id="${loadingId}">
        ⏳ Analyzing medical data using AI...
      </div>
    `;
    chat.scrollTop = chat.scrollHeight;

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        throw new Error("AI analysis failed");
      }

      const result = await response.json();
      console.log(`✅ [SAVED] Message saved to conversation ${currentConversationId}`);
      
      // Update localStorage to mark conversation as having messages
      saveConversationId(currentConversationId);
      
      // Remove loading message before showing result
      const loadingElement = document.getElementById(loadingId);
      if (loadingElement) {
        loadingElement.remove();
      }
      
      showResult(result);
      updateDeleteButton(true);

      // Auto-name the conversation from the first user message
      if (isFirstMessage && finalText) {
        isFirstMessage = false;
        saveFirstMessageState(false);
        const autoTitle = generateChatTitle(finalText);
        fetch(`/api/conversation/${currentConversationId}/title`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: autoTitle })
        }).then(() => {
          updatePageTitle(autoTitle);
          console.log(`✅ [TITLE] Updated conversation title to: ${autoTitle}`);
        }).catch(err => console.error("❌ [TITLE] Title update failed:", err));
      }

    } catch (err) {
      // Remove loading message on error
      const loadingElement = document.getElementById(loadingId);
      if (loadingElement) {
        loadingElement.remove();
      }
      console.error("❌ [ERROR] Failed to analyze:", err);
      showError(err.message);
    } finally {
      isAnalyzing = false;
      analyzeBtn.disabled = false;
    }
  });
});


// ==================== CONVERSATION MANAGEMENT ====================

function initSession() {
  console.log("🔄 [INIT] Starting session initialization...");
  
  // Always start fresh - clear any saved conversation and create a new one
  clearConversationId();
  createNewConversation();
  console.log("✨ [INIT] Fresh chat session created - ready for new analysis");
}

function createNewConversation() {
  fetch("/api/conversation/new", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "New Chat" })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      currentConversationId = data.conversation.id;
      isFirstMessage = true;
      saveConversationId(currentConversationId);
      saveFirstMessageState(true);
      clearChat();
      updatePageTitle("New Chat");
      updateDeleteButton(false);
      console.log(`✅ [CREATE] New conversation created: ${data.conversation.id}`);
    }
  })
  .catch(err => {
    console.error("❌ [CREATE] Failed to create conversation:", err);
  });
}

function startFreshChat() {
  // Called when user deletes current chat — create a brand new one
  createNewConversation();
}

function generateChatTitle(text) {
  if (!text) return "Medical Image Analysis";
  const words = text.trim().split(/\s+/);
  const title = words.slice(0, 6).join(" ");
  return title.length > 50 ? title.substring(0, 47) + "..." : title;
}

function displayMessages(messages) {
  const chat = document.getElementById("chatOutput");
  
  if (messages.length === 0) {
    chat.innerHTML = `
      <div class="empty-chat">
        <h3>Start Medical Analysis</h3>
        <p>
          Upload reports or describe symptoms to receive AI insights.
        </p>
      </div>
    `;
    return;
  }

  let html = "";
  messages.forEach((msg) => {
    if (msg.role === "user") {
      const msgTime = new Date(msg.created_at);
      const timeDisplay = msgTime.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true
      });

      html += `
        <div class="chat-message-user">
          ${escapeHtml(msg.content)}
          <div class="message-timestamp">${timeDisplay}</div>
        </div>
      `;
    } else if (msg.role === "assistant") {
      const msgTime = new Date(msg.created_at);
      const timeDisplay = msgTime.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true
      });

      try {
        const result = JSON.parse(msg.content);
        const responseHtml = generateResultHTML(result);
        
        // Extract the main div and add timestamp
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = responseHtml;
        const mainDiv = tempDiv.querySelector('.chat-message-ai');
        if (mainDiv) {
          mainDiv.innerHTML += `<div class="message-timestamp">${timeDisplay}</div>`;
          html += mainDiv.outerHTML;
        } else {
          // Fallback if main div not found - display raw response
          html += `
            <div class="chat-message-ai">
              <p>${escapeHtml(msg.content.substring(0, 200))}</p>
              <div class="message-timestamp">${timeDisplay}</div>
            </div>
          `;
        }
      } catch (err) {
        console.warn("Failed to parse assistant message:", err);
        html += `
          <div class="chat-message-ai">
            <p>${escapeHtml(msg.content)}</p>
            <div class="message-timestamp">${timeDisplay}</div>
          </div>
        `;
      }
    }
  });

  chat.innerHTML = html;
  const chatArea = document.querySelector('.chat-area');
  if (chatArea) {
    chatArea.scrollTop = chatArea.scrollHeight;
  }
}

function clearChat() {
  const chat = document.getElementById("chatOutput");
  chat.innerHTML = `
    <div class="empty-chat">
      <h3>Start Medical Analysis</h3>
      <p>
        Upload reports or describe symptoms to receive AI insights.
      </p>
    </div>
  `;
}

function updatePageTitle(title) {
  const pageTitle = document.getElementById("pageTitle");
  
  if (pageTitle) pageTitle.textContent = title;
}

function updateDeleteButton(show) {
  const deleteBtn = document.getElementById("deleteConversationBtn");
  if (deleteBtn) {
    deleteBtn.style.display = show ? "block" : "none";
  }
}


// ==================== RESPONSE DISPLAY ====================

function showResult(data) {
  const chat = document.getElementById("chatOutput");
  lastAiResult = data; // Save for hospital navigation

  const html = generateResultHTML(data);
  chat.innerHTML += html;
  chat.scrollTop = chat.scrollHeight;
}

function generateResultHTML(data) {
  let urgencyClass = "urgency-low";
  if (data.urgency === "High") {
    urgencyClass = "urgency-high";
  } else if (data.urgency === "Medium") {
    urgencyClass = "urgency-medium";
  }

  let html = `
    <div class="chat-message-ai">

      <div class="ai-response-header">
        <strong>Medical Assistant Analysis</strong>
      </div>

      <div class="ai-response-section">
        <h4>📋 What This Might Be</h4>
        <p>${data.patient_explanation || "Analysis could not be determined."}</p>
      </div>
  `;

  // Show key observations if available
  if (data.key_observations && data.key_observations.length > 0) {
    html += `
      <div class="ai-response-section">
        <h4>👁️ Important Findings</h4>
        <ul>
    `;
    data.key_observations.forEach(obs => {
      html += `<li>${escapeHtml(obs)}</li>`;
    });
    html += `
        </ul>
      </div>
    `;
  }

  // Show urgency level
  html += `
    <div class="ai-response-section ${urgencyClass}">
      <h4>⚠️ Urgency Level: <strong>${data.urgency || "Unknown"}</strong></h4>
      <p>${data.urgency_reasoning || "Assessment complete."}</p>
    </div>
  `;

  // Show self-care guidance if available
  if (data.self_care_guidance && data.self_care_guidance.length > 0) {
    html += `
      <div class="ai-response-section">
        <h4>💚 What You Can Do</h4>
        <ul>
    `;
    data.self_care_guidance.forEach(tip => {
      html += `<li>${escapeHtml(tip)}</li>`;
    });
    html += `
        </ul>
      </div>
    `;
  }

  // Show recommended next steps
  if (data.recommended_next_steps && data.recommended_next_steps.length > 0) {
    html += `
      <div class="ai-response-section">
        <h4>📞 Recommended Next Steps</h4>
        <ul>
    `;
    data.recommended_next_steps.forEach(step => {
      html += `<li>${escapeHtml(step)}</li>`;
    });
    html += `
        </ul>
      </div>
    `;
  }

  // Show suggested specialties (prioritize these over generic department)
  if (data.suggested_specialties && data.suggested_specialties.length > 0) {
    html += `
      <div class="ai-response-section">
        <h4>👨‍⚕️ Recommended Medical Specialties</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
    `;
    data.suggested_specialties.forEach(specialty => {
      html += `<span style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);">${escapeHtml(specialty)}</span>`;
    });
    html += `
        </div>
        <p style="font-size: 12px; color: #666; margin-top: 8px;">Refer to these specialists based on the findings from your primary doctor evaluation.</p>
      </div>
    `;
  } else if (data.suggested_department && data.suggested_department !== "General Medicine") {
    // Only show specific department if it's NOT generic
    html += `
      <div class="ai-response-section">
        <h4>🏥 Specialist Recommendation</h4>
        <p><strong>${escapeHtml(data.suggested_department)}</strong></p>
      </div>
    `;
  }

  // Add button for nearby hospitals
  const specialty = data.suggested_specialties?.[0] || data.suggested_department || '';
  html += `
    <div class="ai-response-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; padding: 16px; text-align: center;">
      <p style="color: rgba(255,255,255,0.9); margin: 0 0 10px 0; font-size: 13px;">Find a relevant hospital and send your case for review</p>
      <button onclick="navigateToHospitals('${escapeHtml(specialty)}', this)" style="background: white; color: #667eea; border: none; padding: 10px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: all 0.3s ease;">
        🏥 View Nearby Hospitals & Send Case
      </button>
    </div>
  `;

  // Disclaimer
  html += `
      <div class="ai-response-footer">
        <small>⚠️ Note: ${data.disclaimer || "This information is for educational purposes only and does not replace professional medical advice. Always consult a qualified healthcare professional."}</small>
      </div>

    </div>
  `;

  return html;
}

function showError(message) {
  const chat = document.getElementById("chatOutput");

  chat.innerHTML += `
    <div class="chat-message-ai error-message">
      ❌ <strong>Error:</strong> ${message}
      <br><small>Please try again or contact support if the problem persists.</small>
    </div>
  `;
}


// ==================== UTILITY FUNCTIONS ====================

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  // If today, show time only
  if (diffDays === 0) {
    const hours = String(date.getHours()).padStart(2, '0');
    const mins = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${mins}`;
  }

  // If yesterday
  if (diffDays === 1) {
    return "Yesterday";
  }

  // If this week
  if (diffDays < 7) {
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  }

  // Otherwise show date
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  });
}

// ==================== HOSPITAL NAVIGATION ====================

function sanitizeSpecialtyForSearch(specialty) {
  if (!specialty || typeof specialty !== 'string') return '';

  let clean = specialty.replace(/\(.*?\)/g, '').replace(/\[.*?\]/g, '').trim();
  const lower = clean.toLowerCase();

  const aliases = [
    { canonical: 'Radiology', keywords: ['radiology', 'xray', 'x-ray', 'imaging', 'ct', 'mri', 'ultrasound'] },
    { canonical: 'Pulmonology', keywords: ['pulmonology', 'pulmonary', 'lung', 'respiratory'] },
    { canonical: 'Cardiology', keywords: ['cardiology', 'cardiac', 'heart'] },
    { canonical: 'Orthopedics', keywords: ['orthopedic', 'orthopaedic', 'bone', 'joint', 'spine'] },
    { canonical: 'Neurology', keywords: ['neurology', 'brain', 'neuro'] },
    { canonical: 'Oncology', keywords: ['oncology', 'cancer', 'tumor'] },
    { canonical: 'Gynecology', keywords: ['gynecology', 'gynaecology', 'obstetrics'] },
    { canonical: 'Pediatrics', keywords: ['pediatrics', 'paediatrics', 'child', 'children'] },
    { canonical: 'Emergency', keywords: ['emergency', 'trauma', 'urgent'] }
  ];

  for (const item of aliases) {
    if (item.keywords.some(k => lower.includes(k))) {
      return item.canonical;
    }
  }

  return clean;
}

function navigateToHospitals(specialty) {
  // Store the specialty for the hospitals page to use
  const normalizedSpecialty = sanitizeSpecialtyForSearch(specialty);
  if (normalizedSpecialty) {
    sessionStorage.setItem('medicalSpecialty', normalizedSpecialty);
  }
  
  // Store the full AI analysis for case sending
  const lastUserMsg = document.querySelectorAll('.chat-message-user');
  let symptoms = '';
  if (lastUserMsg.length > 0) {
    symptoms = lastUserMsg[lastUserMsg.length - 1].textContent.trim();
  }
  
  const caseData = {
    symptoms: symptoms,
    ai_summary: lastAiResult?.patient_explanation || 'AI analysis completed',
    urgency: lastAiResult?.urgency || 'Medium',
    suggested_department: normalizedSpecialty || lastAiResult?.suggested_department || 'General Medicine',
    source: 'text'
  };
  sessionStorage.setItem('pendingCaseData', JSON.stringify(caseData));
  
  // Navigate to hospitals page
  window.location.href = '/patient/hospitals';
}
