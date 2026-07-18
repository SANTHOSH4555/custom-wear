import os
import json
import uuid
import datetime

class DBManager:
    def __init__(self):
        self.firebase_enabled = False
        self.db = None
        self.local_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "local_db.json")
        self.initial_products_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "initial_products.json")
        self.key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firebase-key.json")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
        
        # Try initializing Firebase
        if os.path.exists(self.key_path):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                
                # Check if already initialized
                if not firebase_admin._apps:
                    cred = credentials.Certificate(self.key_path)
                    firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.firebase_enabled = True
                print("[DBManager] Connected to Firebase Firestore successfully.")
            except Exception as e:
                print(f"[DBManager] Failed to initialize Firebase: {e}. Falling back to Local Mock Mode.")
        else:
            print("[DBManager] firebase-key.json not found. Falling back to Local Mock Mode.")
            
        if not self.firebase_enabled:
            self._init_local_db()

    def _init_local_db(self):
        if not os.path.exists(self.local_db_path):
            # Load initial products if available
            initial_prods = []
            if os.path.exists(self.initial_products_path):
                try:
                    with open(self.initial_products_path, "r", encoding="utf-8") as f:
                        initial_prods = json.load(f)
                except Exception as e:
                    print(f"[DBManager] Error reading initial products: {e}")
            
            # Create default local database structure
            default_db = {
                "users": {},
                "products": {p["id"]: p for p in initial_prods},
                "categories": [
                    {"id": "t-shirt", "name": "T-Shirt"},
                    {"id": "hoodie", "name": "Hoodie"},
                    {"id": "jacket", "name": "Jacket"},
                    {"id": "sweatshirt", "name": "Sweatshirt"},
                    {"id": "joggers", "name": "Joggers"},
                    {"id": "crop-top", "name": "Crop Top"}
                ],
                "orders": {},
                "cart": {},
                "wishlist": {},
                "payments": {},
                "reviews": {},
                "coupons": {
                    "WELCOME10": {"discount_percent": 10, "active": True},
                    "PREMIUM20": {"discount_percent": 20, "active": True},
                    "FESTIVE30": {"discount_percent": 30, "active": True}
                },
                "notifications": {},
                "messages": {}
            }
            self._save_local_db(default_db)
            print("[DBManager] Initialized a new local JSON database.")
        else:
            # Check if database has products, if not seed it
            db = self._load_local_db()
            if not db.get("products") and os.path.exists(self.initial_products_path):
                try:
                    with open(self.initial_products_path, "r", encoding="utf-8") as f:
                        initial_prods = json.load(f)
                        db["products"] = {p["id"]: p for p in initial_prods}
                        self._save_local_db(db)
                        print("[DBManager] Seeded products into existing empty local database.")
                except Exception as e:
                    print(f"[DBManager] Error seeding products: {e}")

    def _load_local_db(self):
        try:
            with open(self.local_db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DBManager] Error loading local DB: {e}")
            return {}

    def _save_local_db(self, data):
        try:
            with open(self.local_db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DBManager] Error saving local DB: {e}")

    # ================= PRODUCTS OPERATIONS =================
    def get_products(self, brand=None, category=None, gender=None):
        if self.firebase_enabled:
            query = self.db.collection("products")
            if brand:
                query = query.where("brand", "==", brand)
            if category:
                query = query.where("category", "==", category)
            if gender:
                query = query.where("gender", "==", gender)
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        else:
            db = self._load_local_db()
            prods = list(db.get("products", {}).values())
            if brand:
                prods = [p for p in prods if p.get("brand", "").lower() == brand.lower()]
            if category:
                prods = [p for p in prods if p.get("category", "").lower() == category.lower()]
            if gender:
                prods = [p for p in prods if p.get("gender", "").lower() == gender.lower()]
            return prods

    def get_product(self, product_id):
        if self.firebase_enabled:
            doc = self.db.collection("products").document(product_id).get()
            return doc.to_dict() if doc.exists else None
        else:
            db = self._load_local_db()
            return db.get("products", {}).get(product_id)

    def create_product(self, product_data):
        if not product_data.get("id"):
            product_data["id"] = str(uuid.uuid4())
        
        if self.firebase_enabled:
            self.db.collection("products").document(product_data["id"]).set(product_data)
        else:
            db = self._load_local_db()
            db["products"][product_data["id"]] = product_data
            self._save_local_db(db)
        return product_data

    def update_product(self, product_id, product_data):
        if self.firebase_enabled:
            self.db.collection("products").document(product_id).update(product_data)
            return self.get_product(product_id)
        else:
            db = self._load_local_db()
            if product_id in db.get("products", {}):
                db["products"][product_id].update(product_data)
                self._save_local_db(db)
                return db["products"][product_id]
            return None

    def delete_product(self, product_id):
        if self.firebase_enabled:
            self.db.collection("products").document(product_id).delete()
            return True
        else:
            db = self._load_local_db()
            if product_id in db.get("products", {}):
                del db["products"][product_id]
                self._save_local_db(db)
                return True
            return False

    # ================= USER OPERATIONS =================
    def get_user(self, user_id):
        if self.firebase_enabled:
            doc = self.db.collection("users").document(user_id).get()
            return doc.to_dict() if doc.exists else None
        else:
            db = self._load_local_db()
            return db.get("users", {}).get(user_id)

    def get_user_by_email(self, email):
        if self.firebase_enabled:
            users_ref = self.db.collection("users").where("email", "==", email.lower()).limit(1).stream()
            for doc in users_ref:
                return doc.to_dict()
            return None
        else:
            db = self._load_local_db()
            for user in db.get("users", {}).values():
                if user.get("email", "").lower() == email.lower():
                    return user
            return None

    def create_user(self, user_data):
        if not user_data.get("id"):
            user_data["id"] = str(uuid.uuid4())
        
        user_data["email"] = user_data["email"].lower()
        
        if self.firebase_enabled:
            self.db.collection("users").document(user_data["id"]).set(user_data)
        else:
            db = self._load_local_db()
            db["users"][user_data["id"]] = user_data
            self._save_local_db(db)
        return user_data

    def update_user(self, user_id, user_data):
        if self.firebase_enabled:
            self.db.collection("users").document(user_id).update(user_data)
            return self.get_user(user_id)
        else:
            db = self._load_local_db()
            if user_id in db.get("users", {}):
                db["users"][user_id].update(user_data)
                self._save_local_db(db)
                return db["users"][user_id]
            return None

    # ================= CART & WISHLIST OPERATIONS =================
    def get_user_cart(self, user_id):
        if self.firebase_enabled:
            doc = self.db.collection("cart").document(user_id).get()
            return doc.to_dict().get("items", []) if doc.exists else []
        else:
            db = self._load_local_db()
            return db.get("cart", {}).get(user_id, {}).get("items", [])

    def save_user_cart(self, user_id, items):
        if self.firebase_enabled:
            self.db.collection("cart").document(user_id).set({"items": items})
        else:
            db = self._load_local_db()
            if "cart" not in db:
                db["cart"] = {}
            db["cart"][user_id] = {"items": items}
            self._save_local_db(db)
        return items

    def get_user_wishlist(self, user_id):
        if self.firebase_enabled:
            doc = self.db.collection("wishlist").document(user_id).get()
            return doc.to_dict().get("product_ids", []) if doc.exists else []
        else:
            db = self._load_local_db()
            return db.get("wishlist", {}).get(user_id, {}).get("product_ids", [])

    def save_user_wishlist(self, user_id, product_ids):
        if self.firebase_enabled:
            self.db.collection("wishlist").document(user_id).set({"product_ids": product_ids})
        else:
            db = self._load_local_db()
            if "wishlist" not in db:
                db["wishlist"] = {}
            db["wishlist"][user_id] = {"product_ids": product_ids}
            self._save_local_db(db)
        return product_ids

    # ================= ORDER OPERATIONS =================
    def create_order(self, order_data):
        if not order_data.get("id"):
            order_data["id"] = "ORD-" + str(uuid.uuid4().hex[:8]).upper()
        
        order_data["created_at"] = datetime.datetime.now().isoformat()
        
        if self.firebase_enabled:
            self.db.collection("orders").document(order_data["id"]).set(order_data)
        else:
            db = self._load_local_db()
            db["orders"][order_data["id"]] = order_data
            self._save_local_db(db)
        return order_data

    def get_order(self, order_id):
        if self.firebase_enabled:
            doc = self.db.collection("orders").document(order_id).get()
            return doc.to_dict() if doc.exists else None
        else:
            db = self._load_local_db()
            return db.get("orders", {}).get(order_id)

    def get_user_orders(self, user_id):
        if self.firebase_enabled:
            orders_ref = self.db.collection("orders").where("user_id", "==", user_id).stream()
            return [doc.to_dict() for doc in orders_ref]
        else:
            db = self._load_local_db()
            orders = list(db.get("orders", {}).values())
            return [o for o in orders if o.get("user_id") == user_id]

    def get_all_orders(self):
        if self.firebase_enabled:
            docs = self.db.collection("orders").stream()
            return [doc.to_dict() for doc in docs]
        else:
            db = self._load_local_db()
            return list(db.get("orders", {}).values())

    def update_order_status(self, order_id, status):
        if self.firebase_enabled:
            self.db.collection("orders").document(order_id).update({"status": status})
            return self.get_order(order_id)
        else:
            db = self._load_local_db()
            if order_id in db.get("orders", {}):
                db["orders"][order_id]["status"] = status
                self._save_local_db(db)
                return db["orders"][order_id]
            return None

    # ================= MOCK REVIEWS & MESSAGES =================
    def get_reviews(self, product_id):
        if self.firebase_enabled:
            docs = self.db.collection("reviews").where("product_id", "==", product_id).stream()
            return [doc.to_dict() for doc in docs]
        else:
            db = self._load_local_db()
            reviews = list(db.get("reviews", {}).values())
            return [r for r in reviews if r.get("product_id") == product_id]

    def add_review(self, review_data):
        if not review_data.get("id"):
            review_data["id"] = str(uuid.uuid4())
        review_data["created_at"] = datetime.datetime.now().isoformat()
        
        if self.firebase_enabled:
            self.db.collection("reviews").document(review_data["id"]).set(review_data)
        else:
            db = self._load_local_db()
            db["reviews"][review_data["id"]] = review_data
            
            # Recalculate average rating of the product
            prod_id = review_data["product_id"]
            if prod_id in db["products"]:
                prod_reviews = [r for r in db["reviews"].values() if r.get("product_id") == prod_id]
                if prod_reviews:
                    avg_rate = sum(r.get("rating", 5) for r in prod_reviews) / len(prod_reviews)
                    db["products"][prod_id]["rating"] = round(avg_rate, 1)
            
            self._save_local_db(db)
        return review_data

    def get_coupons(self):
        if self.firebase_enabled:
            docs = self.db.collection("coupons").stream()
            return {doc.id: doc.to_dict() for doc in docs}
        else:
            db = self._load_local_db()
            return db.get("coupons", {})

    def send_message(self, message_data):
        if not message_data.get("id"):
            message_data["id"] = str(uuid.uuid4())
        message_data["created_at"] = datetime.datetime.now().isoformat()
        
        if self.firebase_enabled:
            self.db.collection("messages").document(message_data["id"]).set(message_data)
        else:
            db = self._load_local_db()
            if "messages" not in db:
                db["messages"] = {}
            db["messages"][message_data["id"]] = message_data
            self._save_local_db(db)
        return message_data

    def get_messages(self):
        if self.firebase_enabled:
            docs = self.db.collection("messages").stream()
            return [doc.to_dict() for doc in docs]
        else:
            db = self._load_local_db()
            return list(db.get("messages", {}).values())

db_manager = DBManager()
