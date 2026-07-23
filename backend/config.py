import os

class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "custom_wear_cradance_secret_key_12345_secure_prod")
    TOKEN_EXPIRATION_HOURS = int(os.environ.get("TOKEN_EXPIRATION_HOURS", 24))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    
    # Ensure upload folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

 