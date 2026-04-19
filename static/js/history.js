// ==================== HISTORY PAGE ====================

document.addEventListener("DOMContentLoaded", () => {
  console.log("📖 [HISTORY] Page loaded, fetching conversations...");
  loadConversationsList();
});

function loadConversationsList() {
  console.log("📡 [HISTORY] Fetching conversations from backend...");
  fetch("/api/conversations")
    .then(res => res.json())
    .then(data => {
      console.log("📥 [HISTORY] Response received:", data);
      if (data.success) {
        console.log(`✅ [HISTORY] Found ${data.conversations.length} conversations`);
        displayConversationsList(data.conversations);
      } else {
        console.error("❌ [HISTORY] API error:", data.error);
      }
    })
    .catch(err => {
      console.error("❌ [HISTORY] Network error loading conversations:", err);
    });
}

function displayConversationsList(conversations) {
  const listContainer = document.getElementById("conversationsList");

  if (conversations.length === 0) {
    console.log("📖 [HISTORY] No conversations to display");
    listContainer.innerHTML = `
      <div class="empty-state">
        <h3>No conversations yet</h3>
        <p>Start a new chat on the Dashboard to begin</p>
      </div>
    `;
    return;
  }

  console.log(`📖 [HISTORY] Displaying ${conversations.length} conversations`);
  let html = '<div class="conversations-grid">';

  conversations.forEach(conv => {
    const date = new Date(conv.created_at);
    const dateStr = formatDateProper(date);
    const lastUpdated = new Date(conv.updated_at);
    const updatedStr = formatTimeAgo(lastUpdated);

    html += `
      <div class="conversation-card" data-id="${conv.id}">
        <div class="conversation-card-header">
          <h3>${escapeHtml(conv.title)}</h3>
          <div class="card-header-right">
            <span class="msg-count">${conv.message_count} messages</span>
            <button class="btn-delete-card" data-id="${conv.id}" title="Delete conversation">
              🗑️
            </button>
          </div>
        </div>
        <div class="conversation-card-footer">
          <small class="date-created">Created: ${dateStr}</small>
          <small class="date-updated">Updated: ${updatedStr}</small>
        </div>
      </div>
    `;
  });

  html += '</div>';
  listContainer.innerHTML = html;

  // Add click listeners (ignore clicks on delete button)
  document.querySelectorAll(".conversation-card").forEach(card => {
    card.addEventListener("click", (e) => {
      if (e.target.closest(".btn-delete-card")) return;
      const id = parseInt(card.dataset.id);
      console.log(`📖 [HISTORY] Clicked conversation ${id}`);
      viewConversation(id);
    });
  });

  // Delete button listeners on cards
  document.querySelectorAll(".btn-delete-card").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = parseInt(btn.dataset.id);
      console.log(`🗑️ [HISTORY] Deleting conversation ${id}`);
      deleteConversation(id);
    });
  });
}

function viewConversation(conversationId) {
  console.log(`📡 [HISTORY] Fetching details for conversation ${conversationId}...`);
  fetch(`/api/conversation/${conversationId}`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        console.log(`✅ [HISTORY] Loaded ${data.conversation.messages.length} messages for conversation ${conversationId}`);
        // Save to localStorage for dashboard to load
        localStorage.setItem("cureva_conversation_id", conversationId);
        localStorage.setItem("cureva_is_first_message", "false");
        displayConversationDetail(data.conversation);
      } else {
        console.error("❌ [HISTORY] Failed to load conversation:", data.error);
      }
    })
    .catch(err => {
      console.error("❌ [HISTORY] Error loading conversation:", err);
    });
}

function displayConversationDetail(conversation) {
  const detailContainer = document.getElementById("conversationDetail");

  const createdDate = new Date(conversation.created_at);
  const dateStr = formatDateProper(createdDate);
  const timeStr = createdDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  let html = `
    <div class="detail-content">
      <div class="detail-header">
        <div class="detail-header-top">
          <h2>${escapeHtml(conversation.title)}</h2>
          <button class="btn-delete-detail" data-id="${conversation.id}" title="Delete this conversation">
            🗑️ Delete
          </button>
        </div>
        <p class="detail-meta">
          <strong>Date:</strong> ${dateStr} at ${timeStr}
          <br>
          <strong>Messages:</strong> ${conversation.messages.length}
        </p>
      </div>

      <div class="messages-container">
  `;

  if (conversation.messages.length === 0) {
    html += `<p class="no-messages">No messages in this conversation</p>`;
  } else {
    conversation.messages.forEach(msg => {
      if (msg.role === "user") {
        const msgTime = new Date(msg.created_at);
        const timeDisplay = msgTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        html += `
          <div class="message message-user">
            <div class="message-content">
              <p>${escapeHtml(msg.content)}</p>
              <small class="message-time">${timeDisplay}</small>
            </div>
          </div>
        `;
      } else if (msg.role === "assistant") {
        const msgTime = new Date(msg.created_at);
        const timeDisplay = msgTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        try {
          const result = JSON.parse(msg.content);
          const responseHtml = generateDetailedResponseHTML(result);

          html += `
            <div class="message message-assistant">
              ${responseHtml}
              <small class="message-time">${timeDisplay}</small>
            </div>
          `;
        } catch (e) {
          html += `
            <div class="message message-assistant">
              <div class="message-content">
                <p>${escapeHtml(msg.content)}</p>
              </div>
              <small class="message-time">${timeDisplay}</small>
            </div>
          `;
        }
      }
    });
  }

  html += `
      </div>
    </div>
  `;

  detailContainer.innerHTML = html;

  // Delete button in detail view
  const deleteDetailBtn = detailContainer.querySelector(".btn-delete-detail");
  if (deleteDetailBtn) {
    deleteDetailBtn.addEventListener("click", () => {
      const id = parseInt(deleteDetailBtn.dataset.id);
      deleteConversation(id);
    });
  }

  // Update active card in list
  document.querySelectorAll(".conversation-card").forEach(card => {
    card.classList.remove("active");
  });
  const activeCard = document.querySelector(`[data-id="${conversation.id}"]`);
  if (activeCard) {
    activeCard.classList.add("active");
  }
}

function deleteConversation(conversationId) {
  if (!confirm("Delete this conversation? This cannot be undone.")) return;

  fetch(`/api/conversation/${conversationId}`, { method: "DELETE" })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        // Clear detail panel if it was showing this conversation
        const detailContainer = document.getElementById("conversationDetail");
        detailContainer.innerHTML = `
          <div class="detail-empty">
            <h3>Conversation deleted</h3>
            <p>Select another conversation to view details</p>
          </div>
        `;
        // Reload the list
        loadConversationsList();
      }
    })
    .catch(err => console.error("Delete failed:", err));
}

function generateDetailedResponseHTML(data) {
  let urgencyClass = "urgency-low";
  if (data.urgency === "High") {
    urgencyClass = "urgency-high";
  } else if (data.urgency === "Medium") {
    urgencyClass = "urgency-medium";
  }

  let html = `<div class="ai-response-detail">`;

  // Main explanation
  html += `
    <div class="response-section">
      <h4>What the AI Found</h4>
      <p>${escapeHtml(data.patient_explanation || "Analysis could not be determined.")}</p>
    </div>
  `;

  // Key observations
  if (data.key_observations && data.key_observations.length > 0) {
    html += `
      <div class="response-section">
        <h4>Important Findings</h4>
        <ul>
    `;
    data.key_observations.forEach(obs => {
      html += `<li>${escapeHtml(obs)}</li>`;
    });
    html += `</ul></div>`;
  }

  // Urgency
  html += `
    <div class="response-section ${urgencyClass}">
      <h4>Urgency: <strong>${data.urgency || "Unknown"}</strong></h4>
      <p>${escapeHtml(data.urgency_reasoning || "Assessment complete.")}</p>
    </div>
  `;

  // Self-care
  if (data.self_care_guidance && data.self_care_guidance.length > 0) {
    html += `
      <div class="response-section">
        <h4>What You Can Do</h4>
        <ul>
    `;
    data.self_care_guidance.forEach(tip => {
      html += `<li>${escapeHtml(tip)}</li>`;
    });
    html += `</ul></div>`;
  }

  // Next steps
  if (data.recommended_next_steps && data.recommended_next_steps.length > 0) {
    html += `
      <div class="response-section">
        <h4>Recommended Next Steps</h4>
        <ul>
    `;
    data.recommended_next_steps.forEach(step => {
      html += `<li>${escapeHtml(step)}</li>`;
    });
    html += `</ul></div>`;
  }

  // Department
  if (data.suggested_department && data.suggested_department !== "General Medicine") {
    html += `
      <div class="response-section">
        <h4>Specialist: <strong>${escapeHtml(data.suggested_department)}</strong></h4>
      </div>
    `;
  }

  html += `</div>`;
  return html;
}

// ==================== UTILITY FUNCTIONS ====================

function formatDateProper(date) {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

function formatTimeAgo(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 30) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return formatDateProper(date);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
