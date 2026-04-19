import requests
import json
import time
import re
from math import radians, cos, sin, asin, sqrt

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------
OVERPASS_API_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Lightweight in-memory cache to reduce repeated Overpass latency
HOSPITAL_CACHE = {}
CACHE_TTL_SECONDS = 300

# Medical specialties mapping for hospitals
SPECIALTY_KEYWORDS = {
    "Radiology": ["radiology", "imaging", "xray", "x-ray", "diagnostic", "diagnostics", "diagnostic center", "ct scan", "ct", "ultrasound", "mri", "sonography"],
    "Pulmonology": ["pulmonology", "pulmonary", "lung", "respiratory", "chest"],
    "Cardiology": ["cardiology", "heart", "cardiac", "chest pain"],
    "Orthopedics": ["orthopedics", "bone", "fracture", "joint", "spine"],
    "Pediatrics": ["pediatrics", "children", "child", "infant"],
    "Gynecology": ["gynecology", "obstetrics", "maternity", "women"],
    "Neurology": ["neurology", "brain", "seizure", "stroke", "neurological"],
    "Oncology": ["oncology", "cancer", "tumor"],
    "Emergency": ["emergency", "trauma", "accident"],
    "General": ["general", "internal medicine"],
}


def normalize_requested_specialty(suggested_department):
    """Normalize free-text specialty into canonical key for reliable matching."""
    if not suggested_department:
        return ""

    raw = str(suggested_department).strip()
    clean = re.sub(r"\(.*?\)", "", raw)
    clean = re.sub(r"\[.*?\]", "", clean)
    clean = clean.strip().lower()

    for specialty, keywords in SPECIALTY_KEYWORDS.items():
        if specialty.lower() in clean:
            return specialty
        if any(keyword in clean for keyword in keywords):
            return specialty

    return raw

# --------------------------------------------------
# UTILITY: CALCULATE DISTANCE
# --------------------------------------------------
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


# --------------------------------------------------
# QUERY NEARBY HOSPITALS FROM OVERPASS API
# --------------------------------------------------
def find_nearby_hospitals(latitude, longitude, radius_km=5):
    """
    Query Overpass API for nearby hospitals
    
    Args:
        latitude: User's latitude
        longitude: User's longitude
        radius_km: Search radius in kilometers
    
    Returns:
        List of hospitals with details
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        radius_km = float(radius_km)

        cache_key = (round(lat, 3), round(lon, 3), int(radius_km))
        cached = HOSPITAL_CACHE.get(cache_key)
        now = time.time()
        if cached and (now - cached["timestamp"] < CACHE_TTL_SECONDS):
            return cached["hospitals"]

        # Query by radius in meters (faster + more precise than bbox for this use-case)
        radius_m = max(1000, int(radius_km * 1000))
        query = f"""
        [out:json][timeout:15];
        (
          node(around:{radius_m},{lat},{lon})["amenity"~"hospital|clinic|doctors"];
          way(around:{radius_m},{lat},{lon})["amenity"~"hospital|clinic|doctors"];
          relation(around:{radius_m},{lat},{lon})["amenity"~"hospital|clinic|doctors"];
        );
        out center;
        """

        data = None
        for url in OVERPASS_API_URLS:
            try:
                response = requests.post(
                    url,
                    data=query,
                    timeout=(4, 14)
                )
                if response.status_code == 200:
                    data = response.json()
                    break
                print(f"Overpass API non-200 from {url}: {response.status_code}")
            except requests.RequestException as req_err:
                print(f"Overpass API request failed for {url}: {req_err}")

        if not data:
            return []

        hospitals = []
        
        for element in data.get('elements', []):
            # Get coordinates
            if 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
            elif 'lat' in element:
                lat = element['lat']
                lon = element['lon']
            else:
                continue
            
            # Get name and details
            tags = element.get('tags', {})
            name = tags.get('name', 'Unknown Hospital')
            amenity = tags.get('amenity', 'hospital')
            phone = tags.get('phone', '')
            website = tags.get('website', '')
            opening_hours = tags.get('opening_hours', '')
            healthcare = tags.get('healthcare', '')
            healthcare_speciality = tags.get('healthcare:speciality', '') or tags.get('healthcare:specialty', '')
            description = tags.get('description', '')
            
            # Calculate distance
            distance_km = haversine(longitude, latitude, lon, lat)
            
            hospital = {
                'name': name,
                'latitude': lat,
                'longitude': lon,
                'distance_km': round(distance_km, 2),
                'amenity': amenity,
                'phone': phone,
                'website': website,
                'opening_hours': opening_hours,
                'healthcare': healthcare,
                'healthcare_speciality': healthcare_speciality,
                'description': description,
                'specialty': 'General Hospital'  # Default
            }
            
            hospitals.append(hospital)
        
        # Sort by distance and return top 10
        hospitals.sort(key=lambda x: x['distance_km'])
        top = hospitals[:12]
        HOSPITAL_CACHE[cache_key] = {
            "timestamp": now,
            "hospitals": top,
        }
        return top
        
    except Exception as e:
        print(f"Error querying Overpass API: {str(e)}")
        return []


# --------------------------------------------------
# MATCH HOSPITALS TO MEDICAL SPECIALTIES (IMPROVED)
# --------------------------------------------------
def match_hospitals_to_specialty(hospitals, suggested_department):
    """
    Score hospitals based on relevance to suggested medical department.
    Prioritizes hospitals by name relevance and type.
    
    Args:
        hospitals: List of hospital dicts
        suggested_department: Department suggested by AI (e.g., "Radiology", "Cardiology")
    
    Returns:
        Sorted list of hospitals with specialty match scores
    """
    normalized_dept = normalize_requested_specialty(suggested_department)
    dept_lower = normalized_dept.lower() if normalized_dept else ""
    target_keywords = SPECIALTY_KEYWORDS.get(normalized_dept, [])
    
    for hospital in hospitals:
        score = 0
        hospital_name_lower = hospital['name'].lower()
        amenity_type = hospital.get('amenity', '').lower()
        medical_blob = " ".join([
            hospital_name_lower,
            str(hospital.get('healthcare', '')).lower(),
            str(hospital.get('healthcare_speciality', '')).lower(),
            str(hospital.get('description', '')).lower(),
        ])
        
        # Hospitals (main care centers) get base score
        if amenity_type == 'hospital':
            score += 10
        elif amenity_type == 'clinic':
            score += 5
        else:
            score += 3
        
        # Check if hospital name contains major hospital keywords (quality indicators)
        quality_keywords = ['medical center', 'multispeciality', 'multi-specialty', 'institute', 
                           'hospital', 'health', 'care center', 'care', 'nursing home']
        for kw in quality_keywords:
            if kw in hospital_name_lower:
                score += 2
                break
        
        # Check for specialty-specific keywords in hospital name
        specialty_found = None
        for specialty, keywords in SPECIALTY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in medical_blob:
                    specialty_found = specialty
                    # Exact match with suggested department = high score
                    if specialty.lower() == dept_lower:
                        score += 24
                    else:
                        score += 4
                    break
            if specialty_found:
                break

        # Extra boost for strong direct match with target specialty keywords
        if target_keywords and any(keyword in medical_blob for keyword in target_keywords):
            score += 18
        
        # If suggested department matches specialty directly
        if dept_lower and not specialty_found:
            if dept_lower in medical_blob:
                score += 15
                specialty_found = normalized_dept

        # Radiology/X-ray specific boost
        if dept_lower == "radiology":
            radiology_terms = ["xray", "x-ray", "radiology", "imaging", "diagnostic", "ct", "mri", "scan", "sonography", "ultrasound"]
            if any(term in medical_blob for term in radiology_terms):
                score += 22
        
        hospital['specialty_score'] = score
        hospital['specialty'] = specialty_found if specialty_found else "General Hospital"
    
    return hospitals


# --------------------------------------------------
# GET NEARBY HOSPITALS WITH SPECIALTY FILTERING
# --------------------------------------------------
def get_nearby_hospitals(latitude, longitude, suggested_department=None, radius_km=5, limit=5):
    """
    Main function to get nearby hospitals with specialty matching
    
    Args:
        latitude: User's latitude
        longitude: User's longitude
        suggested_department: Medical department to filter by (e.g., "Radiology")
        radius_km: Search radius in kilometers
        limit: Maximum number of hospitals to return
    
    Returns:
        Dict with hospitals and metadata
    """
    # Get hospitals within radius (expand if needed)
    hospitals = find_nearby_hospitals(latitude, longitude, radius_km)
    
    # If no hospitals found in current radius, try larger radius
    if not hospitals and radius_km < 15:
        hospitals = find_nearby_hospitals(latitude, longitude, radius_km + 5)
    
    if not hospitals:
        return {
            'success': False,
            'message': 'No hospitals found in your area',
            'hospitals': []
        }
    
    normalized_specialty = normalize_requested_specialty(suggested_department)

    # Match to specialty if provided
    if normalized_specialty:
        hospitals = match_hospitals_to_specialty(hospitals, normalized_specialty)
        # Sort by: specialty score (higher first), then by distance
        hospitals.sort(key=lambda x: (-x.get('specialty_score', 0), x['distance_km']))

        # Prefer strong specialty matches when available (especially for X-ray/Radiology)
        strong_matches = [h for h in hospitals if h.get('specialty_score', 0) >= 32]
        if len(strong_matches) >= 2:
            hospitals = strong_matches + [h for h in hospitals if h not in strong_matches]
    else:
        hospitals = match_hospitals_to_specialty(hospitals, None)
        # Sort by distance only
        hospitals.sort(key=lambda x: x['distance_km'])
    
    # Return limited results, but include specialty info
    result_hospitals = hospitals[:limit]
    
    return {
        'success': True,
        'hospitals': result_hospitals,
        'total_found': len(hospitals),
        'search_location': {
            'latitude': latitude,
            'longitude': longitude
        },
        'search_specialty': normalized_specialty
    }


# --------------------------------------------------
# EXTRACT SPECIALTY FROM AI ANALYSIS
# --------------------------------------------------
def extract_specialty_from_analysis(analysis_result):
    """
    Extract medical specialty from AI analysis result
    
    Args:
        analysis_result: Dict from Gemini AI analysis
    
    Returns:
        Specialty string (e.g., "Radiology", "Cardiology")
    """
    if not isinstance(analysis_result, dict):
        return None
    
    # Prefer suggested_specialties first
    specialties = analysis_result.get('suggested_specialties', [])
    if isinstance(specialties, list) and specialties:
        return normalize_requested_specialty(specialties[0])

    # Get suggested_department from AI response
    suggested_dept = analysis_result.get('suggested_department', '')
    
    # Extract specialty keywords
    for specialty in SPECIALTY_KEYWORDS.keys():
        if specialty.lower() in suggested_dept.lower():
            return specialty
    
    return normalize_requested_specialty(suggested_dept) if suggested_dept else None
