import os
import json
import uuid
import re
from datetime import datetime

# Get absolute paths to ensure it works regardless of where script is run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_DIR = os.path.join(BASE_DIR, "leads")
LEADS_FILE = os.path.join(LEADS_DIR, "leads.json")

def validate_lead(name: str, email: str, phone: str) -> tuple[bool, str]:
    """
    Validates lead information based on simple business rules.
    Returns (True, "") if valid, (False, "error message") otherwise.
    """
    name = str(name).strip()
    email = str(email).strip()
    phone = str(phone).strip()

    if len(name) < 2:
        return False, "Name must be at least 2 characters long."
        
    # Basic email structure check
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Please provide a valid email address."
        
    # Count digits in the phone number
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10:
        return False, "Phone number must contain at least 10 digits."
        
    return True, ""

def save_lead(name: str, email: str, phone: str, message: str = "") -> bool:
    """
    Validates and saves a lead to a JSON file safely, simulating a CRM entry.
    """
    is_valid, error_msg = validate_lead(name, email, phone)
    if not is_valid:
        print(f"Validation Error: {error_msg}")
        return False
        
    # Ensure leads directory exists
    os.makedirs(LEADS_DIR, exist_ok=True)
    
    # Safely load existing leads
    leads = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    leads = json.loads(content)
        except json.JSONDecodeError:
            print("Warning: leads.json is corrupt or malformed. Overwriting with new data.")
            leads = []
        except Exception as e:
            print(f"System Error reading leads file: {e}")
            return False

    # Create new lead dictionary
    new_lead = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "name": name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "message": message.strip(),
        "source": "website_chatbot",
        "status": "new"
    }
    
    leads.append(new_lead)
    
    # Save back to JSON
    try:
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=4)
    except Exception as e:
        print(f"System Error writing to leads file: {e}")
        return False
        
    # Print success messages exactly as requested
    print("Lead saved successfully")
    print(f"[MOCK CRM] Lead submitted -> {new_lead['name']} ({new_lead['email']})")
    
    return True

def get_all_leads() -> list:
    """
    Retrieves all stored leads from the JSON file.
    """
    if not os.path.exists(LEADS_FILE):
        return []
        
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
            return []
    except Exception:
        return []

if __name__ == "__main__":
    print("--- Testing Lead Validation ---")
    valid, msg = validate_lead("A", "test@test.com", "1234567890")
    print(f"Short name test: Valid={valid}, Msg={msg}")
    
    valid, msg = validate_lead("John", "bademail", "1234567890")
    print(f"Bad email test: Valid={valid}, Msg={msg}")
    
    valid, msg = validate_lead("John", "john@example.com", "123")
    print(f"Short phone test: Valid={valid}, Msg={msg}")
    
    print("\n--- Testing Lead Saving ---")
    save_lead("Sarah Jenkins", "sarah.j@example.com", "+1 800 555-0199", "I'd like to consult about a wellness vanity.")
    
    print("\n--- Retrieving All Leads ---")
    saved_leads = get_all_leads()
    print(json.dumps(saved_leads, indent=2))
