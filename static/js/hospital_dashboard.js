// ================================================
// CUREVA — HOSPITAL DASHBOARD
// Case management, filtering, modal interactions
// ================================================

// State
let allCases = [];
let currentCase = null;
let filteredCases = [];

// DOM Elements
const caseList = document.getElementById('caseList');
const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');
const urgencyFilter = document.getElementById('urgencyFilter');
const departmentFilter = document.getElementById('departmentFilter');
const caseDetailModal = document.getElementById('caseDetailModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const logoutBtn = document.getElementById('logoutBtn');

// KPI Elements
const kpiElements = {
  pending: document.getElementById('stat-pending'),
  inreview: document.getElementById('stat-inreview'),
  accepted: document.getElementById('stat-accepted'),
  emergency: document.getElementById('stat-emergency'),
  resolved: document.getElementById('stat-resolved'),
  total: document.getElementById('stat-total')
};

// Modal Elements
const modalElements = {
  title: document.getElementById('modalTitle'),
  patientName: document.getElementById('patientName'),
  caseId: document.getElementById('caseId'),
  patientAge: document.getElementById('patientAge'),
  caseCreatedAt: document.getElementById('caseCreatedAt'),
  caseSource: document.getElementById('caseSource'),
  symptoms: document.getElementById('symptoms'),
  aiSummary: document.getElementById('aiSummary'),
  reportType: document.getElementById('reportType'),
  urgencyBadge: document.getElementById('urgencyBadge'),
  suggestedDept: document.getElementById('suggestedDept'),
  hospitalNotes: document.getElementById('hospitalNotes'),
  saveNotesBtn: document.getElementById('saveNotesBtn'),
  acceptBtn: document.getElementById('acceptBtn'),
  reviewBtn: document.getElementById('reviewBtn'),
  resolveBtn: document.getElementById('resolveBtn'),
  referBtn: document.getElementById('referBtn')
};

// ================================================
// INITIALIZATION
// ================================================
document.addEventListener('DOMContentLoaded', async () => {
  console.log('Hospital Dashboard Initialized');
  
  // Check authentication
  await checkAuth();
  
  // Load initial data
  await loadDepartments();
  await loadCases();
  await loadStats();
  
  // Setup event listeners
  setupEventListeners();
  
  // Auto-refresh cases every 10 seconds
  setInterval(loadCases, 10000);
  setInterval(loadStats, 15000);
});

// ================================================
// AUTHENTICATION
// ================================================
async function checkAuth() {
  try {
    const response = await fetch('/api/auth/me');
    const data = await response.json();
    
    if (!data.success) {
      window.location.href = '/login';
      return;
    }
    
    // Update hospital name
    const hospitalNameEl = document.getElementById('hospitalName');
    if (hospitalNameEl && data.user) {
      const hospitalName = data.user.username || 'Hospital';
      hospitalNameEl.textContent = hospitalName;
      localStorage.setItem('hospitalName', hospitalName);
    }
  } catch (error) {
    console.error('Auth check failed:', error);
    window.location.href = '/login';
  }
}

// ================================================
// DATA LOADING
// ================================================
async function loadCases() {
  try {
    const params = new URLSearchParams();
    
    // Add filter parameters
    const status = statusFilter.value;
    if (status && status !== 'all') {
      params.append('status', status);
    }
    
    const urgency = urgencyFilter.value;
    if (urgency && urgency !== 'all') {
      params.append('urgency', urgency);
    }
    
    const dept = departmentFilter.value;
    if (dept && dept !== 'all') {
      params.append('department', dept);
    }
    
    const search = searchInput.value;
    if (search) {
      params.append('search', search);
    }
    
    const response = await fetch(`/api/hospital/cases?${params}`);
    const data = await response.json();
    
    if (data.success) {
      allCases = data.cases || [];
      renderCases(allCases);
    }
  } catch (error) {
    console.error('Failed to load cases:', error);
    showError('Failed to load cases');
  }
}

async function loadStats() {
  try {
    const response = await fetch('/api/hospital/dashboard-stats');
    const data = await response.json();
    
    if (data.success && data.stats) {
      const stats = data.stats;
      
      if (kpiElements.pending) kpiElements.pending.textContent = stats.pending;
      if (kpiElements.inreview) kpiElements.inreview.textContent = stats.in_review;
      if (kpiElements.accepted) kpiElements.accepted.textContent = stats.accepted;
      if (kpiElements.emergency) kpiElements.emergency.textContent = stats.emergency;
      if (kpiElements.resolved) kpiElements.resolved.textContent = stats.resolved;
      if (kpiElements.total) kpiElements.total.textContent = stats.total_cases;
    }
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

async function loadDepartments() {
  try {
    const response = await fetch('/api/hospital/departments');
    const data = await response.json();
    
    if (data.success && data.departments) {
      // Populate department filter
      const departments = data.departments || [];
      
      // Clear existing options (keep the "All Departments" option)
      while (departmentFilter.children.length > 1) {
        departmentFilter.removeChild(departmentFilter.lastChild);
      }
      
      // Add department options
      departments.forEach(dept => {
        const option = document.createElement('option');
        option.value = dept;
        option.textContent = dept;
        departmentFilter.appendChild(option);
      });
    }
  } catch (error) {
    console.error('Failed to load departments:', error);
  }
}

// ================================================
// RENDERING
// ================================================
function renderCases(cases) {
  caseList.innerHTML = '';
  
  if (!cases || cases.length === 0) {
    caseList.innerHTML = `
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-light)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 12h6m-6 4h6M7 20h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v13a2 2 0 002 2z"/>
        </svg>
        <h3>No cases found</h3>
        <p>No cases match your filters</p>
      </div>
    `;
    return;
  }
  
  cases.forEach(caseObj => {
    const caseCard = createCaseCard(caseObj);
    caseList.appendChild(caseCard);
  });
}

function createCaseCard(caseObj) {
  const card = document.createElement('div');
  card.className = `case-card ${getUrgencyClass(caseObj.urgency_level)}`;
  card.id = `case-${caseObj.id}`;
  
  const timeAgo = getTimeAgo(caseObj.created_at);
  const urgencyBadgeClass = `badge badge-${getUrgencyBadgeClass(caseObj.urgency_level)}`;
  const statusBadgeClass = `badge badge-status-${caseObj.status}`;
  
  card.innerHTML = `
    <div class="case-info">
      <div class="case-header">
        <span class="case-patient-name">${escapeHtml(caseObj.patient_name)}</span>
        <span class="case-id">Case #${caseObj.id}</span>
      </div>
      <div class="case-summary">${escapeHtml(caseObj.symptoms_text || caseObj.ai_summary || 'No summary available')}</div>
      <div class="case-meta">
        <div class="case-meta-item">
          <span>Department:</span>
          <strong>${escapeHtml(caseObj.suggested_department || 'Not specified')}</strong>
        </div>
        <div class="case-meta-item">
          <span>Received:</span>
          <strong>${timeAgo}</strong>
        </div>
      </div>
    </div>
    <div class="case-actions">
      <div style="display: flex; gap: 8px; align-items: center;">
        <span class="${urgencyBadgeClass}">${caseObj.urgency_level}</span>
        <span class="${statusBadgeClass}">${formatStatus(caseObj.status)}</span>
        <button class="case-delete-btn" style="padding: 4px 8px; background: #fef2f2; border: 1px solid #fee2e2; color: #dc2626; border-radius: 4px; font-size: 12px; cursor: pointer; transition: all 0.2s ease;" onclick="deleteCase(event, ${caseObj.id})">🗑️ Delete</button>
      </div>
    </div>
  `;
  
  card.addEventListener('click', (e) => {
    if (e.target.className !== 'case-delete-btn' && !e.target.closest('.case-delete-btn')) {
      openCaseDetail(caseObj);
    }
  });
  
  return card;
}

// ================================================
// MODAL FUNCTIONS
// ================================================
function openCaseDetail(caseObj) {
  currentCase = caseObj;
  
  // Populate modal
  modalElements.title.textContent = `Case #${caseObj.id} - ${escapeHtml(caseObj.patient_name)}`;
  modalElements.patientName.textContent = escapeHtml(caseObj.patient_name);
  modalElements.caseId.textContent = `#${caseObj.id}`;
  modalElements.patientAge.textContent = 'Not specified';
  modalElements.caseCreatedAt.textContent = formatDate(caseObj.created_at);
  modalElements.caseSource.textContent = formatSource(caseObj.source);
  modalElements.symptoms.textContent = caseObj.symptoms_text || 'No symptoms provided';
  modalElements.aiSummary.textContent = caseObj.ai_summary || 'No summary generated';
  modalElements.reportType.textContent = caseObj.report_type || 'No report';
  modalElements.suggestedDept.textContent = caseObj.suggested_department || 'Not specified';
  modalElements.hospitalNotes.value = caseObj.hospital_notes || '';
  
  // Set urgency badge
  const urgencyClass = `badge badge-${getUrgencyBadgeClass(caseObj.urgency_level)}`;
  modalElements.urgencyBadge.innerHTML = `<span class="${urgencyClass}">${caseObj.urgency_level}</span>`;
  
  // Show modal
  caseDetailModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeCaseDetail() {
  caseDetailModal.style.display = 'none';
  document.body.style.overflow = 'auto';
  currentCase = null;
}

// ================================================
// CASE ACTIONS
// ================================================
async function acceptCase() {
  if (!currentCase) return;
  
  try {
    const response = await fetch(`/api/hospital/cases/${currentCase.id}/accept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    if (data.success) {
      showSuccess('Case accepted successfully');
      await loadCases();
      await loadStats();
      closeCaseDetail();
    } else {
      showError(data.error || 'Failed to accept case');
    }
  } catch (error) {
    console.error('Error accepting case:', error);
    showError('Failed to accept case');
  }
}

async function markInReview() {
  if (!currentCase) return;
  
  try {
    const response = await fetch(`/api/hospital/cases/${currentCase.id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    if (data.success) {
      showSuccess('Case marked as in review');
      await loadCases();
      await loadStats();
      closeCaseDetail();
    } else {
      showError(data.error || 'Failed to update case');
    }
  } catch (error) {
    console.error('Error updating case:', error);
    showError('Failed to update case');
  }
}

async function resolveCase() {
  if (!currentCase) return;
  
  try {
    const response = await fetch(`/api/hospital/cases/${currentCase.id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    if (data.success) {
      showSuccess('Case resolved successfully');
      await loadCases();
      await loadStats();
      closeCaseDetail();
    } else {
      showError(data.error || 'Failed to resolve case');
    }
  } catch (error) {
    console.error('Error resolving case:', error);
    showError('Failed to resolve case');
  }
}

async function referCase() {
  if (!currentCase) return;
  
  const notes = modalElements.hospitalNotes.value;
  
  try {
    const response = await fetch(`/api/hospital/cases/${currentCase.id}/refer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showSuccess('Case referred successfully');
      await loadCases();
      await loadStats();
      closeCaseDetail();
    } else {
      showError(data.error || 'Failed to refer case');
    }
  } catch (error) {
    console.error('Error referring case:', error);
    showError('Failed to refer case');
  }
}

async function saveNotes() {
  if (!currentCase) return;
  
  const notes = modalElements.hospitalNotes.value;
  
  try {
    const response = await fetch(`/api/hospital/cases/${currentCase.id}/add-notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showSuccess('Notes saved successfully');
      currentCase = data.case;
      await loadCases();
    } else {
      showError(data.error || 'Failed to save notes');
    }
  } catch (error) {
    console.error('Error saving notes:', error);
    showError('Failed to save notes');
  }
}

// ================================================
// EVENT LISTENERS
// ================================================
function setupEventListeners() {
  // Close modal
  closeModalBtn.addEventListener('click', closeCaseDetail);
  
  caseDetailModal.addEventListener('click', (e) => {
    if (e.target === caseDetailModal) {
      closeCaseDetail();
    }
  });
  
  // Filter and search
  searchInput.addEventListener('input', debounce(loadCases, 300));
  statusFilter.addEventListener('change', loadCases);
  urgencyFilter.addEventListener('change', loadCases);
  departmentFilter.addEventListener('change', loadCases);
  
  // Modal buttons
  modalElements.acceptBtn.addEventListener('click', acceptCase);
  modalElements.reviewBtn.addEventListener('click', markInReview);
  modalElements.resolveBtn.addEventListener('click', resolveCase);
  modalElements.referBtn.addEventListener('click', referCase);
  modalElements.saveNotesBtn.addEventListener('click', saveNotes);
  
  // Logout
  logoutBtn.addEventListener('click', logout);
}

// ================================================
// DELETE CASE FUNCTION
// ================================================
async function deleteCase(event, caseId) {
  event.stopPropagation();
  
  // Confirm delete
  if (!confirm('Are you sure you want to delete this case? This action cannot be undone.')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/cases/${caseId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Remove from DOM with animation
      const card = document.getElementById(`case-${caseId}`);
      if (card) {
        card.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
          card.remove();
          // Reload cases to ensure consistency
          loadCases();
        }, 300);
      }
      showNotification('Case deleted successfully', 'success');
    } else {
      showNotification(data.error || 'Failed to delete case', 'error');
    }
  } catch (error) {
    console.error('Error deleting case:', error);
    showNotification('Error deleting case', 'error');
  }
}

// ================================================
// UTILITY FUNCTIONS
// ================================================
function getUrgencyClass(urgency) {
  const mapping = {
    'Emergency': 'urgent',
    'High': 'high',
    'Medium': 'medium',
    'Low': 'low'
  };
  return mapping[urgency] || 'medium';
}

function getUrgencyBadgeClass(urgency) {
  const mapping = {
    'Emergency': 'emergency',
    'High': 'high',
    'Medium': 'medium',
    'Low': 'low'
  };
  return mapping[urgency] || 'medium';
}

function formatStatus(status) {
  const mapping = {
    'pending': 'Pending',
    'in_review': 'In Review',
    'accepted': 'Accepted',
    'resolved': 'Resolved',
    'referred': 'Referred'
  };
  return mapping[status] || status;
}

function formatSource(source) {
  const mapping = {
    'text': 'Text Input',
    'image': 'Image Upload',
    'voice': 'Voice Input'
  };
  return mapping[source] || source || 'Unknown';
}

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return dateString;
  }
}

function getTimeAgo(dateString) {
  if (!dateString) return 'Unknown';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch (error) {
    return 'Unknown';
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function debounce(func, delay) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

// ================================================
// NOTIFICATIONS
// ================================================
function showSuccess(message) {
  console.log('Success:', message);
  alert(message);
}

function showError(message) {
  console.error('Error:', message);
  alert('Error: ' + message);
}

function showNotification(message, type = 'info') {
  // Simple notification using alert for now
  // In production, you might want a toast notification UI
  if (type === 'success') {
    console.log('✓ Success:', message);
    alert(message);
  } else if (type === 'error') {
    console.error('✗ Error:', message);
    alert('Error: ' + message);
  } else {
    console.log('ℹ Info:', message);
    alert(message);
  }
}

// ================================================
// LOGOUT
// ================================================
async function logout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/';
  } catch (error) {
    console.error('Logout failed:', error);
    window.location.href = '/';
  }
}
