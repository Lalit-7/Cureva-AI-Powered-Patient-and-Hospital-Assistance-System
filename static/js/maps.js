// ================================================
// CUREVA — HOSPITAL MAP + CASE SENDING
// ================================================

let map = null;
let userMarker = null;
let hospitalMarkers = [];
let hospitalsData = [];
let pendingCaseData = null; // AI analysis data from patient dashboard

// Load pending case data from sessionStorage
try {
  const raw = sessionStorage.getItem('pendingCaseData');
  if (raw) pendingCaseData = JSON.parse(raw);
} catch (e) {
  console.warn('No pending case data found');
}

// --------------------------------------------------
// REQUEST LOCATION AND SEARCH
// --------------------------------------------------
function requestLocationAndSearch() {
    const infoSection = document.getElementById('infoSection');
    const loadingState = document.getElementById('loadingState');
    const mapContainer = document.getElementById('mapContainer');
    
    infoSection.classList.add('hidden');
    loadingState.classList.remove('hidden');
    
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        loadingState.classList.add('hidden');
        infoSection.classList.remove('hidden');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            
            console.log('User location:', latitude, longitude);
            
            mapContainer.classList.remove('hidden');
            infoSection.classList.add('hidden');
            
            // Small delay to let CSS layout recalculate before initializing map
            setTimeout(() => {
                initializeMap(latitude, longitude);
                fetchNearbyHospitals(latitude, longitude);
            }, 150);
        },
        function(error) {
            console.error('Geolocation error:', error);
            let errorMsg = 'Unable to get your location. ';
            if (error.code === error.PERMISSION_DENIED) {
                errorMsg += 'Please enable location access in your browser settings.';
            } else if (error.code === error.POSITION_UNAVAILABLE) {
                errorMsg += 'Location information is unavailable.';
            } else if (error.code === error.TIMEOUT) {
                errorMsg += 'Location request timed out.';
            }
            
            alert(errorMsg);
            loadingState.classList.add('hidden');
            infoSection.classList.remove('hidden');
        }
    );
}

// --------------------------------------------------
// INITIALIZE MAP (with tile fix)
// --------------------------------------------------
function initializeMap(latitude, longitude) {
    if (map) {
        map.remove();
        map = null;
    }
    
    map = L.map('map', {
        center: [latitude, longitude],
        zoom: 13,
        zoomControl: true
    });
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // User location marker
    const userIcon = L.divIcon({
        html: `<div style="background: #14b8a6; border: 3px solid white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                 <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                   <path d="M10 2C6.13 2 3 5.13 3 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                 </svg>
               </div>`,
        iconSize: [40, 40],
        className: 'user-marker'
    });
    
    userMarker = L.marker([latitude, longitude], { icon: userIcon }).addTo(map);
    userMarker.bindPopup('<strong>Your Location</strong>');
    
    // CRITICAL FIX: Force Leaflet to recalculate container dimensions
    // This fixes the gray tile bug when the map container was initially hidden
    setTimeout(() => {
        if (map) map.invalidateSize();
    }, 200);
    
    setTimeout(() => {
        if (map) map.invalidateSize();
    }, 600);
}

// --------------------------------------------------
// FETCH NEARBY HOSPITALS
// --------------------------------------------------
async function fetchNearbyHospitals(latitude, longitude, suggestedDept = null) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 22000);

    // Use specialty from sessionStorage if not passed directly
    if (!suggestedDept) {
        suggestedDept = sessionStorage.getItem('medicalSpecialty');
    }

    try {
        const response = await fetch('/api/nearby-hospitals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal,
            body: JSON.stringify({
                latitude: latitude,
                longitude: longitude,
                suggested_department: suggestedDept,
                radius_km: 5
            })
        });

        clearTimeout(timeoutId);
        const data = await response.json();
        
        if (!data.success || !data.hospitals || data.hospitals.length === 0) {
            showEmptyState();
            document.getElementById('loadingState').classList.add('hidden');
            return;
        }
        
        hospitalsData = data.hospitals;
        
        // Render both map markers and list
        displayHospitalsOnMap(hospitalsData);
        renderHospitalList(hospitalsData, suggestedDept);
        
        // Hide overlays
        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('infoSection').classList.add('hidden');
        document.getElementById('loadingState').classList.add('hidden');
        
    } catch (error) {
        clearTimeout(timeoutId);
        console.error('Error fetching hospitals:', error);
        if (error.name === 'AbortError') {
            alert('Hospital search is taking longer than expected. Please try again.');
        } else {
            alert('Failed to fetch nearby hospitals. Please try again.');
        }
        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('infoSection').classList.remove('hidden');
    }
}

// --------------------------------------------------
// DISPLAY HOSPITALS ON MAP
// --------------------------------------------------
function displayHospitalsOnMap(hospitals) {
    hospitalMarkers.forEach(marker => map.removeLayer(marker));
    hospitalMarkers = [];
    
    hospitals.forEach((hospital, index) => {
        const icon = L.divIcon({
            html: `<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: 3px solid white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 16px;">
                     ${index + 1}
                   </div>`,
            iconSize: [40, 40],
            className: 'hospital-marker'
        });
        
        const marker = L.marker(
            [hospital.latitude, hospital.longitude],
            { icon: icon }
        ).addTo(map);
        
        const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}`;
        
        const popupContent = `
            <div class="hospital-popup">
                <h3>${hospital.name}</h3>
                <div class="info-row">
                    <span>📍</span>
                    <span class="distance">${hospital.distance_km} km away</span>
                </div>
                <div class="info-row">
                    <span>🏥</span>
                    <span>${hospital.specialty || 'General Hospital'}</span>
                </div>
                ${hospital.phone ? `
                <div class="info-row">
                    <span>📞</span>
                    <a href="tel:${hospital.phone}" style="color: #0369a1; text-decoration: none; font-weight: 600;">${hospital.phone}</a>
                </div>
                ` : ''}
                <div class="actions">
                    <a href="${googleMapsUrl}" target="_blank" class="btn btn-directions">🗺️ Directions</a>
                    <button onclick="sendCaseToHospital(${index})" class="btn btn-send-case">📤 Send Case</button>
                </div>
            </div>
        `;
        
        marker.bindPopup(popupContent, {
            minWidth: 300,
            className: 'hospital-popup-wrapper'
        });
        
        marker.on('click', function() { marker.openPopup(); });
        hospitalMarkers.push(marker);
    });
    
    if (hospitalMarkers.length > 0 && userMarker) {
        const group = new L.featureGroup([userMarker, ...hospitalMarkers]);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// --------------------------------------------------
// RENDER HOSPITAL LIST (Side Panel)
// --------------------------------------------------
function renderHospitalList(hospitals, specialty) {
    const listContainer = document.getElementById('hospitalList');
    if (!listContainer) return;
    
    const hasCaseData = pendingCaseData !== null;
    
    let html = '';
    
    if (specialty) {
        html += `<div class="filter-badge">
            <span>Filtered by: <strong>${specialty}</strong></span>
        </div>`;
    }

    if (!hasCaseData) {
        html += `<div class="no-case-warning">
            <p>⚠️ No AI analysis data found. Please analyze your symptoms first from the dashboard, then come back here.</p>
            <a href="/patient" class="btn-back-sm">← Go to Dashboard</a>
        </div>`;
    }
    
    hospitals.forEach((hospital, index) => {
        const scoreLabel = hospital.specialty_score >= 32 ? 'Best Match' : 
                          hospital.specialty_score >= 20 ? 'Good Match' : 
                          'General';
        const scoreClass = hospital.specialty_score >= 32 ? 'match-best' : 
                          hospital.specialty_score >= 20 ? 'match-good' : 
                          'match-general';
        
        html += `
            <div class="hospital-card" onclick="focusOnHospital(${index})" id="hospital-card-${index}">
                <div class="hospital-card-header">
                    <div class="hospital-number">${index + 1}</div>
                    <div class="hospital-card-info">
                        <h3>${hospital.name}</h3>
                        <span class="hospital-distance">📍 ${hospital.distance_km} km away</span>
                    </div>
                </div>
                <div class="hospital-card-tags">
                    <span class="tag tag-specialty">${hospital.specialty || 'General'}</span>
                    <span class="tag ${scoreClass}">${scoreLabel}</span>
                </div>
                ${hospital.phone ? `<p class="hospital-phone">📞 ${hospital.phone}</p>` : ''}
                ${hasCaseData ? `
                <button class="btn-send-case-card" onclick="event.stopPropagation(); sendCaseToHospital(${index})">
                    📤 Send Case to This Hospital
                </button>
                ` : ''}
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
}

// --------------------------------------------------
// SEND CASE TO HOSPITAL (THE KEY ACTION)
// --------------------------------------------------
async function sendCaseToHospital(index) {
    const hospital = hospitalsData[index];
    if (!hospital) {
        showErrorToast('Hospital not found');
        return;
    }
    
    if (!pendingCaseData) {
        showErrorToast('No medical analysis data found. Please go back and analyze your symptoms first.');
        return;
    }
    
    // Get button reference
    const btn = document.querySelector(`#hospital-card-${index} .btn-send-case-card`);
    
    // Prevent duplicate clicks
    if (btn && btn.disabled) return;
    
    // Confirm
    const confirmed = confirm(`Send your case to "${hospital.name}"?\n\nThe hospital will receive your symptoms and AI analysis for review.`);
    if (!confirmed) return;
    
    // Set loading state
    if (btn) {
        btn.disabled = true;
        btn.classList.add('loading');
        btn.innerHTML = '<span style="display: inline-block; animation: spin 1s linear infinite;">⏳</span> Sending...';
    }
    
    try {
        const response = await fetch('/api/cases/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symptoms: pendingCaseData.symptoms || 'Not specified',
                ai_summary: pendingCaseData.ai_summary || 'AI analysis completed',
                urgency: pendingCaseData.urgency || 'Medium',
                suggested_department: pendingCaseData.suggested_department || 'General Medicine',
                hospital_id: `osm_${hospital.name.replace(/\s+/g, '_').toLowerCase()}`,
                hospital_name: hospital.name,
                source: pendingCaseData.source || 'text'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccessToast(hospital.name);
            // Clear pending data after successful send
            sessionStorage.removeItem('pendingCaseData');
            pendingCaseData = null;
            
            // Update the list to reflect sent state
            if (btn) {
                btn.textContent = '✅ Case Sent!';
                btn.classList.remove('loading');
                btn.classList.add('sent');
            }
        } else {
            showErrorToast('Failed to send case. Please try again.');
            // Reset button on error
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('loading');
                btn.innerHTML = '📤 Send Case to This Hospital';
            }
        }
    } catch (error) {
        console.error('Error sending case:', error);
        showErrorToast('Network error. Please try again.');
        // Reset button on error
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('loading');
            btn.innerHTML = '📤 Send Case to This Hospital';
        }
    }
}

// --------------------------------------------------
// SUCCESS TOAST
// --------------------------------------------------
function showSuccessToast(hospitalName) {
    // Remove existing toasts
    const existing = document.getElementById('successToast');
    if (existing) existing.remove();
    const errorExisting = document.getElementById('errorToast');
    if (errorExisting) errorExisting.remove();
    
    const toast = document.createElement('div');
    toast.id = 'successToast';
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">✅</span>
            <div>
                <strong>Case Sent Successfully!</strong>
                <p>Your case has been sent to <strong>${hospitalName}</strong> for review.</p>
            </div>
        </div>
    `;
    toast.className = 'success-toast';
    document.body.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => toast.classList.add('show'));
    
    // Auto-remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

// --------------------------------------------------
// ERROR TOAST
// --------------------------------------------------
function showErrorToast(message) {
    // Remove existing error toast
    const existing = document.getElementById('errorToast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.id = 'errorToast';
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">❌</span>
            <div>
                <strong>Error</strong>
                <p>${message}</p>
            </div>
        </div>
    `;
    toast.className = 'error-toast';
    document.body.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => toast.classList.add('show'));
    
    // Auto-remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 6000);
}

// --------------------------------------------------
// FOCUS ON HOSPITAL (map + list sync)
// --------------------------------------------------
function focusOnHospital(index) {
    if (hospitalMarkers[index]) {
        const marker = hospitalMarkers[index];
        map.setView(marker.getLatLng(), 16);
        marker.openPopup();
    }
    
    // Highlight card
    document.querySelectorAll('.hospital-card').forEach(c => c.classList.remove('active'));
    const card = document.getElementById(`hospital-card-${index}`);
    if (card) card.classList.add('active');
}

function highlightHospital(index) { focusOnHospital(index); }
function callHospital(phone) { window.location.href = `tel:${phone}`; }

function showEmptyState() {
    document.getElementById('emptyState').classList.remove('hidden');
}

// --------------------------------------------------
// EXPORTS
// --------------------------------------------------
window.requestLocationAndSearch = requestLocationAndSearch;
window.focusOnHospital = focusOnHospital;
window.highlightHospital = highlightHospital;
window.callHospital = callHospital;
window.sendCaseToHospital = sendCaseToHospital;
