from flask import Blueprint, jsonify, g, request
from backend.firebase.db_manager import db_manager
from backend.routes.auth import token_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/analytics", methods=["GET"])
@token_required
def get_analytics():
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin authorization required!"}), 403
        
    orders = db_manager.get_all_orders()
    
    total_sales = 0.0
    total_orders = len(orders)
    paid_orders = 0
    pending_orders = 0
    revenue = 0.0
    
    brand_sales = {"CUSTOM WEAR": 0.0, "CRADANCE": 0.0}
    category_sales = {}
    
    for order in orders:
        grand_total = order["pricing"]["grand_total"]
        status = order.get("status", "Ordered")
        pay_status = order.get("payment_status", "Pending")
        
        if pay_status == "Paid":
            paid_orders += 1
            revenue += grand_total
            
            # Brand & Category stats
            for item in order.get("items", []):
                qty = int(item.get("quantity", 1))
                prod_id = item.get("product_id")
                prod = db_manager.get_product(prod_id)
                if prod:
                    brand = prod.get("brand", "CUSTOM WEAR")
                    cat = prod.get("category", "General")
                    
                    price = prod["prices"]["plain"]
                    if item.get("print_style", "plain").lower() == "printed":
                        price = prod["prices"]["printed"]
                        
                    total_item_val = price * qty
                    brand_sales[brand] = brand_sales.get(brand, 0.0) + total_item_val
                    category_sales[cat] = category_sales.get(cat, 0.0) + total_item_val
        else:
            pending_orders += 1
            
    avg_order_value = revenue / paid_orders if paid_orders > 0 else 0.0
    
    return jsonify({
        "revenue": round(revenue, 2),
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,
        "average_order_value": round(avg_order_value, 2),
        "brand_sales": brand_sales,
        "category_sales": category_sales,
        "sales_report": [
            {
                "order_id": o["id"],
                "customer": o["user_name"],
                "total": o["pricing"]["grand_total"],
                "payment": o["payment_status"],
                "shipping": o["status"],
                "date": o.get("created_at", "")[:10]
            }
            for o in orders
        ]
    })

@admin_bp.route("/inventory", methods=["GET"])
@token_required
def get_inventory():
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin authorization required!"}), 403
        
    products = db_manager.get_products()
    inventory_list = [
        {
            "id": p["id"],
            "name": p["name"],
            "brand": p["brand"],
            "category": p["category"],
            "stock": p.get("stock", 0),
            "price": p["prices"]["plain"]
        }
        for p in products
    ]
    return jsonify(inventory_list)

@admin_bp.route("/customers", methods=["GET"])
@token_required
def get_customers():
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin authorization required!"}), 403
        
    # Read users directly from local DB
    if db_manager.firebase_enabled:
        docs = db_manager.db.collection("users").stream()
        customers = [doc.to_dict() for doc in docs]
    else:
        db = db_manager._load_local_db()
        customers = list(db.get("users", {}).values())
        
    # Clean passwords before return
    for c in customers:
        c.pop("password", None)
        
    return jsonify(customers)

@admin_bp.route("/messages", methods=["GET"])
@token_required
def get_messages():
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin authorization required!"}), 403
        
    messages = db_manager.get_messages()
    return jsonify(messages)

@admin_bp.route("/messages", methods=["POST"])
def send_contact_message():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone", "")
    message = data.get("message")
    
    if not name or not email or not message:
        return jsonify({"message": "Name, email, and message are required fields!"}), 400
        
    message_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "message": message
    }
    
    saved_msg = db_manager.send_message(message_data)
    return jsonify({
        "message": "Message sent successfully! We will get back to you shortly.",
        "data": saved_msg
    }), 201
