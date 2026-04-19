import sys
import io
import os
import json
import re

# Fix Windows console encoding for emoji/unicode in print() statements
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# --------------------------------------------------
# LOAD ENV VARIABLES
# --------------------------------------------------
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("⚠️ Gemini API key not found")

# --------------------------------------------------
# SYSTEM PROMPT (REAL MEDICAL ASSISTANT)
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a compassionate and knowledgeable AI Medical Assistant, like a helpful healthcare guide who listens carefully to patients and helps them understand what might be happening with their health.

Your goal is to help people understand their symptoms and medical concerns in a way that makes sense to them - using simple language, practical advice, and honest guidance about when they should see a doctor.

IMPORTANT PRINCIPLES:
- Be warm, understanding, and non-judgmental
- Explain things in simple language, as if talking to a friend
- Focus on what the patient can DO about their situation
- Always emphasize when professional medical care is needed
- Take symptoms seriously, but also provide reassurance when appropriate

YOUR RESPONSIBILITIES:

1. LISTEN AND UNDERSTAND
   - Carefully analyze what the patient is describing
   - If an image (X-ray, scan, lab report) is provided, describe what typical features you observe
   - Relate findings back to what the patient might be experiencing

2. EXPLAIN WHAT MIGHT BE HAPPENING
   - Describe possible explanations in everyday language
   - Avoid medical jargon - explain things like you're talking to a friend
   - Mention 2-3 most likely possibilities if multiple are possible
   - Be honest if symptoms could relate to something serious

3. PROVIDE PRACTICAL GUIDANCE
   - Give specific, actionable self-care tips they can start immediately
   - Suggest what medications or remedies might help (over-the-counter options)
   - Explain lifestyle changes or precautions they should take
   - Tell them what activities to avoid

4. ASSESS URGENCY HONESTLY
   - Low urgency: Can wait a few days to see a doctor; manageable with self-care
   - Medium urgency: Should see a doctor within 1-2 days; getting worse is concerning
   - High urgency: Should see a doctor immediately; could be serious

5. GUIDE THEM TO THE RIGHT HELP
   - Tell them which type of doctor to see
   - Also suggest specific medical specialties if relevant (e.g., "Radiology", "Orthopedics", "Cardiology")
   - Explain what kind of tests or follow-ups might be helpful
   - Clarify whether they need an emergency room, urgent care, or regular doctor visit

6. SAFETY FIRST
   - You are NOT a doctor - you cannot diagnose or prescribe medications
   - Your information is for guidance and education only
   - Always encourage professional evaluation
   - Be clear about the limits of what you can assess

RESPONSE FORMAT:

Always respond in valid JSON only. Here's the structure:

{
  "patient_explanation": "A warm, clear explanation of what might be happening. Use simple language. Example: 'Your mild fever and cough could be from a common cold or mild flu. These usually get better on their own in a few days, but we want to make sure it's not something else.'",
  "self_care_guidance": [
    "Specific practical advice - e.g., 'Rest and drink plenty of water to help your body fight the infection'",
    "What over-the-counter helps - e.g., 'Over-the-counter pain relievers like acetaminophen or ibuprofen can help with fever and aches'",
    "What to avoid - e.g., 'Avoid strenuous exercise until you feel better'"
  ],
  "key_observations": [
    "Important details from their symptoms or image findings",
    "Things that stand out or warrant attention"
  ],
  "urgency": "Low | Medium | High",
  "urgency_reasoning": "Why this urgency level. E.g., 'Medium because fever that doesn't improve in 3 days, or gets worse, needs medical evaluation'",
  "suggested_department": "The right place to go - e.g., 'General Medicine / Primary Care Doctor' or 'Emergency Room' or 'Orthopedic Specialist'",
  "suggested_specialties": ["List of relevant medical specialties like", "Radiology, Cardiology, Orthopedics, etc.", "Include 1-3 specialties most relevant to the concern"],
  "recommended_next_steps": [
    "Call your doctor if symptoms worsen",
    "Schedule an appointment within 2-3 days if not improving",
    "Try these self-care steps first"
  ],
  "disclaimer": "Standard medical disclaimer about not replacing professional care"
}

STRICT OUTPUT RULES:
- Return ONLY a valid JSON object. No markdown, no code fences (```), no extra text before or after the JSON.
- The first character of your response MUST be { and the last character MUST be }
- Do NOT wrap the JSON in ```json``` or any other formatting.
- Keep all string values on a single line (no literal newlines inside strings).
- Keep output concise to avoid truncation.
- For suggested_specialties, return only clean specialty names (e.g., "Radiology", "Pulmonology") without explanations in brackets.
- Use 1-3 items max for self_care_guidance, key_observations, suggested_specialties, and recommended_next_steps.
- If you are unsure about any field, use sensible defaults rather than omitting it.

TONE AND STYLE GUIDE:
- Use 'we' and 'you' to feel conversational
- Be encouraging when appropriate
- Don't sound scary or alarmist
- Use examples patients can relate to
- Keep explanations shorter and clearer - break complex ideas into parts
"""

# --------------------------------------------------
# GENERATION CONFIG
# --------------------------------------------------
GENERATION_CONFIG = GenerationConfig(
    temperature=0.2,
    top_p=0.85,
    top_k=30,
    max_output_tokens=2048
)

# --------------------------------------------------
# SAFETY SETTINGS
# --------------------------------------------------
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

# --------------------------------------------------
# MODEL
# --------------------------------------------------
MODEL = genai.GenerativeModel("gemini-2.5-flash")

# --------------------------------------------------
# DEFAULT RESPONSE
# --------------------------------------------------
def get_default_response():
    return {
        "patient_explanation": "Thank you for sharing. Please consult a healthcare professional for guidance.",
        "self_care_guidance": [],
        "key_observations": [],
        "urgency": "Medium",
        "urgency_reasoning": "Professional medical consultation recommended.",
        "suggested_department": "General Medicine",
        "suggested_specialties": [],
        "recommended_next_steps": ["Consult a healthcare professional."],
        "disclaimer": "This is AI assistance, not professional medical advice."
    }

def _ensure_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip(): 
        return [value.strip()]
    return []


def _normalize_specialty_name(value):
    if not isinstance(value, str):
        return ""

    raw = value.strip()
    if not raw:
        return ""

    # Remove bracketed guidance text and keep core specialty
    clean = re.sub(r"\(.*?\)", "", raw)
    clean = re.sub(r"\[.*?\]", "", clean)
    clean = clean.strip().lower()

    specialty_aliases = {
        "Radiology": ["radiology", "xray", "x-ray", "imaging", "ct", "mri", "ultrasound"],
        "Pulmonology": ["pulmonology", "pulmonary", "lung", "respiratory"],
        "Cardiology": ["cardiology", "cardiac", "heart"],
        "Orthopedics": ["orthopedic", "orthopaedic", "bone", "joint", "spine"],
        "Neurology": ["neurology", "neuro", "brain"],
        "Oncology": ["oncology", "cancer", "tumor", "tumour"],
        "Gynecology": ["gynecology", "gynaecology", "obstetrics", "maternity"],
        "Pediatrics": ["pediatrics", "paediatrics", "child", "children"],
        "Emergency": ["emergency", "trauma", "urgent", "er"],
        "General Medicine": ["general medicine", "primary care", "internal medicine", "general physician"],
    }

    for canonical, aliases in specialty_aliases.items():
        if any(alias in clean for alias in aliases):
            return canonical

    return raw.strip()


def _normalize_response(data):
    """Normalize model JSON into the exact frontend contract."""
    base = get_default_response()
    if not isinstance(data, dict):
        return base

    merged = {**base, **data}
    merged["self_care_guidance"] = _ensure_list(merged.get("self_care_guidance"))
    merged["key_observations"] = _ensure_list(merged.get("key_observations"))
    merged["suggested_specialties"] = _ensure_list(merged.get("suggested_specialties"))
    merged["recommended_next_steps"] = _ensure_list(merged.get("recommended_next_steps"))

    # Keep responses concise and stable for UI rendering
    merged["self_care_guidance"] = merged["self_care_guidance"][:3]
    merged["key_observations"] = merged["key_observations"][:3]
    merged["recommended_next_steps"] = merged["recommended_next_steps"][:3]

    urgency = str(merged.get("urgency", "Medium")).strip().capitalize()
    merged["urgency"] = urgency if urgency in {"Low", "Medium", "High"} else "Medium"

    merged["patient_explanation"] = str(merged.get("patient_explanation") or base["patient_explanation"]).strip()
    merged["urgency_reasoning"] = str(merged.get("urgency_reasoning") or base["urgency_reasoning"]).strip()
    merged["suggested_department"] = _normalize_specialty_name(str(merged.get("suggested_department") or base["suggested_department"]).strip())
    merged["disclaimer"] = str(merged.get("disclaimer") or base["disclaimer"]).strip()

    # Normalize and deduplicate specialties while preserving order
    normalized_specialties = []
    for spec in merged["suggested_specialties"]:
        canonical = _normalize_specialty_name(spec)
        if canonical and canonical not in normalized_specialties:
            normalized_specialties.append(canonical)
    merged["suggested_specialties"] = normalized_specialties[:3]

    # Ensure a useful specialty exists when department is specific
    if not merged["suggested_specialties"] and merged["suggested_department"] not in {"", "General Medicine"}:
        merged["suggested_specialties"] = [merged["suggested_department"]]

    # Prevent accidental raw JSON dumps in UI
    if merged["patient_explanation"].startswith("{") or merged["patient_explanation"].startswith("```"):
        merged["patient_explanation"] = base["patient_explanation"]

    return merged


def _extract_json_candidate(raw_text):
    if not raw_text:
        return None

    text = raw_text.strip()

    # 1) Direct JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # 2) JSON fenced in markdown
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)

    # 3) First object in mixed text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start:end + 1]

    return None


def _parse_model_response(raw_text):
    candidate = _extract_json_candidate(raw_text)
    if not candidate:
        return None

    cleaned = candidate.strip()
    # Fix common encoding issues
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    cleaned = cleaned.replace("\u2018", "'").replace("\u2013", "-").replace("\u2014", "-")
    # Remove trailing commas before closing braces/brackets
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    # Fix unescaped newlines inside strings
    cleaned = re.sub(r'(?<!\\)\n', ' ', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try even more aggressive cleanup
        try:
            # Remove control characters
            cleaned2 = re.sub(r'[\x00-\x1f\x7f]', ' ', cleaned)
            return json.loads(cleaned2)
        except json.JSONDecodeError:
            return None


def _generate_and_parse(parts):
    """Call model with retries and robust parsing before fallback."""
    last_raw = ""
    for attempt in range(3):
        try:
            response = MODEL.generate_content(
                parts,
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS
            )

            raw = (getattr(response, "text", "") or "").strip()
            if raw:
                last_raw = raw
            parsed = _parse_model_response(raw)
            if parsed is not None:
                return _normalize_response(parsed)
            # If parsing failed but we got text, retry with stricter JSON prompt
            if attempt == 0 and raw:
                print(f"Gemini attempt {attempt + 1}: JSON parse failed, retrying...")
                continue
        except Exception as exc:
            print(f"Gemini generation attempt {attempt + 1} failed: {exc}")

    # Last resort: try to extract anything useful from raw text
    if last_raw:
        fallback = get_default_response()
        # If the raw text looks like a plain-English response, use it
        if len(last_raw) > 30 and not last_raw.startswith('{'):
            fallback["patient_explanation"] = last_raw[:500]
        else:
            fallback["patient_explanation"] = "Unable to analyze right now. Please try again."
        return fallback

    return get_default_response()

# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def analyze_medical_input(text_input=None, image_bytes=None, mime_type="image/png"):
    if not API_KEY:
        return get_default_response()

    parts = []

    if image_bytes:
        parts.append({
            "mime_type": mime_type,
            "data": image_bytes
        })

    if text_input:
        parts.append(f"{SYSTEM_PROMPT}\n\nPatient Input:\n{text_input}")
    else:
        parts.append(SYSTEM_PROMPT)

    return _generate_and_parse(parts)


# --------------------------------------------------
# FUNCTION WITH CONTEXT (FOR CHAT HISTORY)
# --------------------------------------------------
def analyze_medical_input_with_context(text_input=None, image_bytes=None, previous_messages=None, mime_type="image/png"):
    """Analyze with conversation history"""
    if not API_KEY:
        return get_default_response()

    parts = []

    if image_bytes:
        parts.append({
            "mime_type": mime_type,
            "data": image_bytes
        })

    context_text = ""
    if previous_messages:
        context_text = "\n---\nPrevious conversation context:\n"
        for msg in previous_messages:
            role = "Patient" if msg.get('role') == 'user' else "Assistant"
            content = msg.get('content', '')
            if msg.get('role') == 'assistant':
                try:
                    if isinstance(content, str) and content.startswith('{'):
                        data = json.loads(content)
                        content = data.get('patient_explanation', content)
                except:
                    pass
            context_text += f"{role}: {content}\n"

    full_prompt = SYSTEM_PROMPT
    if context_text:
        full_prompt += context_text
    
    if text_input:
        full_prompt += f"\n\nCurrent Patient Message:\n{text_input}"

    parts.append(full_prompt)

    return _generate_and_parse(parts)
