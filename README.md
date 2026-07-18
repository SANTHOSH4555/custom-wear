# CUSTOM WEAR & CRADANCE — Premium E-Commerce Website

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange.svg)](https://firebase.google.com)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-CDN-cyan.svg)](https://tailwindcss.com)

A complete **premium e-commerce clothing website** featuring two distinct brands: **CUSTOM WEAR** ("Wear Your Identity") and **CRADANCE** ("Premium Streetwear Collection").

---

## 🚀 Quick Start

### 1. Start the Server

**Windows (double-click or cmd):**
```bat
start.bat
```

**PowerShell / Terminal:**
```powershell
backend\venv\Scripts\python run.py
```

The site will be live at: **http://localhost:5000/**

---

## 🔐 Default Credentials

| Role  | Email | Password |
|-------|-------|----------|
| Admin | `admin@customwear.io` | `admin123` |
| Customer | Register via Login page | — |

**Test Coupon Codes:**
| Code | Discount |
|------|----------|
| `WELCOME10` | 10% off |
| `PREMIUM20` | 20% off |
| `FESTIVE30` | 30% off |

---

## 📁 Project Structure

```
f:\dress e-commerce website\
├── run.py                        # ← Launch server from here
├── start.bat                     # ← Windows double-click launcher
├── frontend/
│   ├── index.html                # Homepage (Brand Hub)
│   ├── custom-wear.html          # CUSTOM WEAR brand page
│   ├── cradance.html             # CRADANCE brand page
│   ├── products.html             # Product catalog with filters
│   ├── product-details.html      # Product detail + color selector
│   ├── custom-printing.html      # Canvas design studio
│   ├── cart.html                 # Shopping cart + GST + coupons
│   ├── checkout.html             # Delivery details + UPI QR payment
│   ├── dashboard.html            # Customer dashboard + order tracking
│   ├── admin.html                # Admin control panel
│   ├── login.html                # Login / Register / Google auth
│   ├── css/
│   │   └── style.css             # Global Glassmorphism styles
│   ├── js/
│   │   ├── app.js                # API wrapper, cart, auth, toast
│   │   ├── firebase-config.js    # Firebase client auth (optional)
│   │   └── products-data.js      # Local products dataset (auto-seeded)
│   └── assets/
│       └── images/               # All product photos + brand logo
│
└── backend/
    ├── app.py                    # Flask app factory
    ├── config.py                 # JWT + upload path config
    ├── requirements.txt          # Python dependencies
    ├── firebase-key.json         # ← Add your Firebase key here (optional)
    ├── firebase/
    │   └── db_manager.py         # Dual-mode DB (Firebase OR local JSON)
    ├── routes/
    │   ├── auth.py               # Register / Login / Profile / JWT
    │   ├── products.py           # Products CRUD + Reviews + Search
    │   ├── orders.py             # Checkout + UPI QR + Order tracking
    │   └── admin.py              # Analytics + Inventory + Messages
    ├── data/
    │   ├── initial_products.json # Auto-seeded from your product images
    │   └── local_db.json         # Auto-created local JSON database
    ├── static/
    │   └── uploads/              # Custom print uploads + invoices
    └── tests/
        └── verify_backend.py     # Automated API test suite
```

---

## 🔥 Firebase Integration (Optional)

To enable Firebase Firestore and Firebase Storage:

1. Create a Firebase project at https://console.firebase.google.com
2. Generate a service account key (Project Settings → Service Accounts)
3. Save it as `backend/firebase-key.json`
4. Update `frontend/js/firebase-config.js` with your web app credentials

Without a key, the app automatically runs in **Local JSON Mock Mode** — fully functional for development.

---

## 🛍️ Feature Highlights

| Feature | Details |
|---------|---------|
| **Dual Brand Hub** | Split hero panel — CUSTOM WEAR (blue) & CRADANCE (dark luxury) |
| **Product Catalog** | 11 products seeded from your actual images with real pricing |
| **Color Circles** | Click a color → product image swaps instantly |
| **GSM Variants** | Round Neck T-Shirt supports 180 GSM & 220 GSM with dual pricing |
| **Plain vs. Printed** | Toggle updates price live |
| **Canvas Studio** | Upload PNG/SVG/PDF, add text, drag/resize/rotate, 4 print positions |
| **Cart + Coupons** | Quantity adjust, coupon codes, GST 18%, free shipping above ₹1000 |
| **UPI Payment** | Generates real UPI QR code (7708374473) + app simulation links |
| **Order Tracking** | 5-stage visual pipeline: Ordered → Packed → Shipped → Out for Delivery → Delivered |
| **Admin Panel** | Revenue stats, dispatch control, inventory editor, customer log, messages |
| **JWT Auth** | Secure login with token expiry, protected routes |
| **Dark/Light Mode** | Toggle with `localStorage` persistence |
| **AOS Animations** | Fade, zoom, slide-in scroll-triggered animations |
| **Skeleton Loading** | Shimmer placeholders while products load |
| **Mobile First** | Fully responsive Tailwind CSS layout |

---

## 🧪 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create new account |
| POST | `/api/auth/login` | Email/password login → JWT |
| POST | `/api/auth/google-login` | Google OAuth login |
| GET | `/api/auth/profile` | Get profile (auth required) |
| PUT | `/api/auth/profile` | Update name/phone/addresses |
| POST | `/api/auth/forgot-password` | Send password reset |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all (with filters & sort) |
| GET | `/api/products/:id` | Single product detail |
| GET | `/api/products/:id/reviews` | Product reviews |
| POST | `/api/products/:id/reviews` | Add review (auth required) |
| POST | `/api/products` | Create product (admin only) |
| PUT | `/api/products/:id` | Edit product (admin only) |
| DELETE | `/api/products/:id` | Delete product (admin only) |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orders` | Place order (auth required) |
| GET | `/api/orders` | My orders (auth required) |
| GET | `/api/orders/:id` | Order detail |
| POST | `/api/orders/:id/pay` | Get UPI QR / simulate payment |
| PUT | `/api/orders/:id/status` | Update dispatch status (admin) |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/analytics` | Revenue, AOV, sales report |
| GET | `/api/admin/inventory` | Stock levels |
| GET | `/api/admin/customers` | All registered customers |
| GET | `/api/admin/messages` | Contact form inbox |
| POST | `/api/admin/messages` | Submit contact message |

---

## 📦 Product Catalogue (Seeded from your images)

| Product | Plain Price | Printed Price |
|---------|-------------|---------------|
| Men's Round Neck T-Shirt (180 GSM) | ₹320 | ₹420 |
| Men's Round Neck T-Shirt (220 GSM) | ₹380 | ₹470 |
| Men's Long Sleeve T-Shirt | ₹320 | ₹430 |
| Men's 3/4 Oversized T-Shirt | ₹420 | ₹480 |
| Men's Normal Hoodie | ₹620 | ₹730 |
| Men's Oversized Hoodie | ₹680 | ₹780 |
| Men's Bomber Jacket | ₹880 | ₹970 |
| Men's Sweatshirt | ₹500 | ₹550 |
| Women's Crop Top | ₹265 | ₹375 |
| Women's Crop Hoodie | ₹520 | ₹650 |
| Women's Pants/Joggers | ₹550 | ₹550 |
| **CRADANCE Supima Tee** | **₹1700** | **₹1700** |

---

## 📞 Contact & Support

- **WhatsApp:** +91 7708374473
- **Instagram:** @custom_wear_io
- **Business Hours:** Mon–Sat, 9:00 AM – 7:00 PM
