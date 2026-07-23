import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.routes.auth import auth_bp
from backend.routes.products import products_bp
from backend.routes.orders import orders_bp
from backend.routes.admin import admin_bp

# Resolve paths relative to THIS file, regardless of where the server is launched from
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_FRONTEND_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", "frontend"))

app = Flask(__name__, static_folder=_FRONTEND_DIR)
CORS(app)

app.config.from_object(Config)

# Register API blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(products_bp, url_prefix="/api/products")
app.register_blueprint(orders_bp, url_prefix="/api/orders")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

# Security Headers Middleware
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Global Exception Handler
@app.errorhandler(404)
def not_found(e):
    return jsonify({"message": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"message": "An internal server error occurred"}), 500

# Route custom prints uploads and invoices
@app.route("/static/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

# Serve the homepage
@app.route("/")
def index():
    return send_from_directory(_FRONTEND_DIR, "index.html")

# Serve any other frontend file by exact name (CSS, JS, HTML, images…)
@app.route("/<path:filename>")
def serve_frontend_files(filename):
    full_path = os.path.join(_FRONTEND_DIR, filename)
    if os.path.isfile(full_path):
        return send_from_directory(_FRONTEND_DIR, filename)
    # SPA fallback — serve index.html for unknown routes
    return send_from_directory(_FRONTEND_DIR, "index.html")

if __name__ == "__main__":
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    print(f"CUSTOM WEAR & CRADANCE Server launching at http://localhost:{port}/")
    app.run(host="0.0.0.0", port=port, debug=True)

