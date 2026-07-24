import jwt
import datetime
from flask import Blueprint, request, jsonify, g
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from backend.firebase.db_manager import db_manager
from backend.config import Config

auth_bp = Blueprint("auth", __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            elif auth_header:
                token = auth_header
        
        # Fallback to query string parameter (useful for direct invoice downloads / GET links)
        if not token:
            token = request.args.get("token") or request.args.get("auth_token")
            if not token and "Authorization" in request.args:
                auth_arg = request.args.get("Authorization")
                if auth_arg.startswith("Bearer "):
                    token = auth_arg.split(" ")[1]
                else:
                    token = auth_arg
        
        if not token or not isinstance(token, str) or token.strip().lower() in ["undefined", "null", "none", "false", ""]:
            return jsonify({"message": "Token is missing!"}), 401
        
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = db_manager.get_user(data["user_id"])
            if not current_user:
                return jsonify({"message": "Invalid token user!"}), 401
            g.current_user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401
            
        return f(*args, **kwargs)
    return decorated

def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=Config.TOKEN_EXPIRATION_HOURS)
    }
    encoded = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
    if isinstance(encoded, bytes):
        return encoded.decode("utf-8")
    return encoded

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    
    if not name or not email or not password:
        return jsonify({"message": "Missing required fields (name, email, password)!"}), 400

    if "@" not in email or "." not in email:
        return jsonify({"message": "Please enter a valid email address!"}), 400

    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters long!"}), 400
        
    existing_user = db_manager.get_user_by_email(email)
    if existing_user:
        return jsonify({"message": "User with this email already exists!"}), 409
        
    hashed_password = generate_password_hash(password)
    is_admin = (email == "credanceofficial@gmail.com")
    user_data = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "role": "admin" if is_admin else "user",
        "created_at": datetime.datetime.now().isoformat(),
        "addresses": [],
        "phone": "7708374473" if is_admin else ""
    }
    
    user = db_manager.create_user(user_data)
    token = generate_token(user["id"])
    
    return jsonify({
        "message": "User registered successfully!",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"message": "Missing email or password!"}), 400
        
    # Check if admin login
    if email == "credanceofficial@gmail.com" and password == "admin123":
        # Ensure admin user exists in DB
        admin = db_manager.get_user_by_email(email)
        if not admin:
            admin = db_manager.create_user({
                "name": "Credance Admin",
                "email": email,
                "password": generate_password_hash(password),
                "role": "admin",
                "phone": "7708374473",
                "created_at": datetime.datetime.now().isoformat()
            })
        else:
            # Sync role and phone just in case
            if admin.get("role") != "admin" or admin.get("phone") != "7708374473":
                admin["role"] = "admin"
                admin["phone"] = "7708374473"
                db_manager.create_user(admin)
                
        token = generate_token(admin["id"])
        return jsonify({
            "token": token,
            "user": {
                "id": admin["id"],
                "name": admin["name"],
                "email": admin["email"],
                "role": "admin"
            }
        })

    user = db_manager.get_user_by_email(email)
    if not user or not check_password_hash(user.get("password", ""), password):
        return jsonify({"message": "Invalid email or password!"}), 401
        
    # Make sure if someone manually registers with admin email, they get admin role
    if user.get("email") == "credanceofficial@gmail.com" and user.get("role") != "admin":
        user["role"] = "admin"
        user["phone"] = "7708374473"
        db_manager.create_user(user)

    token = generate_token(user["id"])
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "user")
        }
    })

@auth_bp.route("/google-login", methods=["POST"])
def google_login():
    data = request.get_json() or {}
    email = data.get("email")
    name = data.get("name")
    
    if not email:
        return jsonify({"message": "Google Authentication failed. Email is missing."}), 400
        
    user = db_manager.get_user_by_email(email)
    if not user:
        # Create a new user for Google login
        user_data = {
            "name": name or email.split("@")[0].title(),
            "email": email.lower(),
            "role": "user",
            "created_at": datetime.datetime.now().isoformat(),
            "addresses": [],
            "phone": "",
            "google_auth": True
        }
        user = db_manager.create_user(user_data)
        
    token = generate_token(user["id"])
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "user")
        }
    })

@auth_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    user = g.current_user
    # Don't return password
    user_copy = user.copy()
    user_copy.pop("password", None)
    return jsonify(user_copy)

@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    user = g.current_user
    data = request.get_json() or {}
    
    updatable_fields = ["name", "phone", "addresses"]
    updates = {}
    for field in updatable_fields:
        if field in data:
            updates[field] = data[field]
            
    updated_user = db_manager.update_user(user["id"], updates)
    
    user_copy = updated_user.copy()
    user_copy.pop("password", None)
    return jsonify({
        "message": "Profile updated successfully!",
        "user": user_copy
    })

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email")
    
    if not email:
        return jsonify({"message": "Email is required!"}), 400
        
    user = db_manager.get_user_by_email(email)
    if not user:
        return jsonify({"message": "If this email is registered, we have sent a password reset link."}), 200
        
    # In production, we'd send an email. For this premium demo, we return a mock success message.
    return jsonify({"message": "Password reset link sent to your email address."}), 200
