"""
CUSTOM WEAR & CRADANCE - Server Launcher
Run this file from the workspace root: python run.py
"""
import sys
import os

# Ensure workspace root is on sys.path so that `backend` package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app
from backend.config import Config

if __name__ == "__main__":
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    print("=" * 55)
    print("  CUSTOM WEAR & CRADANCE — Premium E-Commerce Server")
    print("=" * 55)
    print(f"  Homepage  : http://localhost:{port}/")
    print(f"  Admin     : http://localhost:{port}/admin.html")
    print(f"  Login     : http://localhost:{port}/login.html")
    print(f"  API Base  : http://localhost:{port}/api/")
    print("=" * 55)
    print("  Admin credentials  : admin@customwear.io / admin123")
    print("  Test coupons       : WELCOME10 | PREMIUM20 | FESTIVE30")
    print("=" * 55)
    app.run(host="0.0.0.0", port=port, debug=True)
