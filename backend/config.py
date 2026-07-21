import os

class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "custom_wear_cradance_secret_key_12345")
    TOKEN_EXPIRATION_HOURS = 87600
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    
    # Ensure upload folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
 