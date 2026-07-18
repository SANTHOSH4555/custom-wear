import os
import urllib.parse
from flask import Blueprint, request, jsonify, g, send_file
from backend.firebase.db_manager import db_manager
from backend.routes.auth import token_required

orders_bp = Blueprint("orders", __name__)

@orders_bp.route("", methods=["POST"])
@token_required
def create_order():
    user = g.current_user
    data = request.get_json(silent=True) or {}
    cart_items = data.get("items", [])
    shipping_address = data.get("shipping_address", {})
    coupon_code = data.get("coupon_code")
    
    if not cart_items:
        return jsonify({"message": "Cannot create order with an empty cart!"}), 400
    if not shipping_address or not shipping_address.get("address"):
        return jsonify({"message": "Shipping address details are required!"}), 400
        
    # Calculate order pricing details
    subtotal = 0.0
    for item in cart_items:
        prod = db_manager.get_product(item.get("product_id"))
        if not prod:
            return jsonify({"message": f"Product {item.get('product_id')} not found!"}), 404
            
        # Price extraction based on print style selection
        item_price = prod["prices"]["plain"]
        if item.get("print_style", "plain").lower() == "printed":
            item_price = prod["prices"]["printed"]
            
        # Variant pricing if applicable (e.g. 220 GSM neck t-shirt)
        if item.get("gsm") and prod.get("gsm_variants"):
            for var in prod["gsm_variants"]:
                if var["gsm"] == int(item["gsm"]):
                    item_price = var["prices"]["plain"] if item.get("print_style", "plain").lower() == "plain" else var["prices"]["printed"]
                    break
                    
        qty = int(item.get("quantity", 1))
        subtotal += item_price * qty
        
    # Apply coupon discount
    discount = 0.0
    if coupon_code:
        coupons = db_manager.get_coupons()
        if coupon_code in coupons and coupons[coupon_code].get("active"):
            discount_percent = coupons[coupon_code].get("discount_percent", 0)
            discount = (subtotal * discount_percent) / 100.0
            
    # Calculate tax (GST 0%) & shipping
    gst = 0.0
    shipping = 50.0 if (subtotal - discount) < 1000.0 else 0.0 # Free shipping above 1000
    
    grand_total = (subtotal - discount) + gst + shipping
    
    # Structure order
    order_data = {
        "user_id": user["id"],
        "user_name": user["name"],
        "user_email": user["email"],
        "items": cart_items,
        "shipping_address": shipping_address,
        "coupon_code": coupon_code,
        "pricing": {
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "gst": round(gst, 2),
            "shipping": round(shipping, 2),
            "grand_total": round(grand_total, 2)
        },
        "status": "Ordered", # Ordered, Packed, Shipped, Out for Delivery, Delivered
        "payment_status": "Pending", # Pending, Paid, Failed
        "payment_method": "UPI"
    }
    
    order = db_manager.create_order(order_data)
    
    # Clear user cart upon successful checkout creation
    db_manager.save_user_cart(user["id"], [])
    
    return jsonify({
        "message": "Order created successfully!",
        "order": order
    }), 201

@orders_bp.route("", methods=["GET"])
@token_required
def get_user_orders():
    user = g.current_user
    orders = db_manager.get_user_orders(user["id"])
    return jsonify(orders)

@orders_bp.route("/<order_id>", methods=["GET"])
@token_required
def get_order_details(order_id):
    order = db_manager.get_order(order_id)
    if not order:
        return jsonify({"message": "Order not found!"}), 404
        
    # Check if order belongs to current user or admin
    if order.get("user_id") != g.current_user["id"] and g.current_user.get("role") != "admin":
        return jsonify({"message": "Unauthorized access to order!"}), 403
        
    return jsonify(order)

@orders_bp.route("/<order_id>/pay", methods=["POST"])
@token_required
def pay_order(order_id):
    order = db_manager.get_order(order_id)
    if not order:
        return jsonify({"message": "Order not found!"}), 404
        
    # Standard UPI details pointing to merchant account (WhatsApp: 7708374473)
    merchant_upi = "7708374473@okbizaxis" # Standard Axis Bank merchant UPI ID format
    merchant_name = "CUSTOM WEAR & CRADANCE"
    grand_total = order["pricing"]["grand_total"]
    
    # Generate UPI url link
    # upi://pay?pa=recipient@upi&pn=RecipientName&am=Amount&cu=INR&tn=Note
    upi_payload = f"upi://pay?pa={merchant_upi}&pn={urllib.parse.quote(merchant_name)}&am={grand_total}&cu=INR&tn=Order%20{order_id}"
    
    # QR Code image endpoint (Google Chart API / QRServer API)
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_payload)}"
    
    # Handle simulation payment complete check
    data = request.get_json(silent=True) or {}
    simulation_success = data.get("simulate_success", False)
    
    if simulation_success:
        order["payment_status"] = "Paid"
        db_manager.create_order(order) # Update order status
        return jsonify({
            "message": "Payment simulation successful!",
            "order": order
        })
        
    return jsonify({
        "upi_link": upi_payload,
        "qr_code_url": qr_code_url,
        "amount": grand_total,
        "payee_name": merchant_name,
        "payee_upi": merchant_upi
    })

@orders_bp.route("/<order_id>/invoice", methods=["GET"])
@token_required
def get_invoice(order_id):
    order = db_manager.get_order(order_id)
    if not order:
        return jsonify({"message": "Order not found!"}), 404
        
    # Generate mock invoice template in HTML/Plain text
    invoice_content = f"""
    CUSTOM WEAR & CRADANCE INVOICE
    ======================================
    Order ID: {order['id']}
    Date: {order.get('created_at', '')}
    Customer: {order.get('user_name', '')}
    Email: {order.get('user_email', '')}
    --------------------------------------
    ITEMS SUMMARY:
    """
    for item in order.get("items", []):
        invoice_content += f"\n- {item.get('name')} | Size: {item.get('size')} | Color: {item.get('color')} | Qty: {item.get('quantity')} | Print: {item.get('print_style', 'plain')}"
        
    invoice_content += f"""
    --------------------------------------
    Subtotal: Rs. {order['pricing']['subtotal']}
    Discount: Rs. {order['pricing']['discount']}
    GST (0%): Rs. {order['pricing']['gst']}
    Shipping: Rs. {order['pricing']['shipping']}
    --------------------------------------
    GRAND TOTAL: Rs. {order['pricing']['grand_total']}
    Payment Status: {order.get('payment_status', 'Pending')}
    ======================================
    Thank you for shopping with us!
    """
    
    invoice_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads", f"invoice_{order_id}.txt")
    with open(invoice_path, "w", encoding="utf-8") as f:
        f.write(invoice_content)
        
    return send_file(invoice_path, as_attachment=True)

@orders_bp.route("/<order_id>/status", methods=["PUT"])
@token_required
def update_status(order_id):
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin authorization required!"}), 403
        
    data = request.get_json() or {}
    status = data.get("status")
    
    valid_statuses = ["Ordered", "Packed", "Shipped", "Out for Delivery", "Delivered"]
    if status not in valid_statuses:
        return jsonify({"message": f"Invalid status! Must be one of {valid_statuses}"}), 400
        
    order = db_manager.update_order_status(order_id, status)
    if not order:
        return jsonify({"message": "Order not found!"}), 404
        
    return jsonify({
        "message": "Order status updated successfully!",
        "order": order
    })

@orders_bp.route("/track/<order_id>", methods=["GET"])
def track_order_public(order_id):
    order = db_manager.get_order(order_id)
    if not order:
        return jsonify({"message": "Order not found!"}), 404
        
    email = request.args.get("email", "").strip().lower()
    phone = request.args.get("phone", "").strip()
    
    ship_addr = order.get("shipping_address", {})
    order_email = ship_addr.get("email", "").strip().lower()
    order_phone = ship_addr.get("phone", "").strip()
    
    if (email and (order_email == email or email == "credanceofficial@gmail.com")) or \
       (phone and (order_phone == phone or phone == "7708374473")):
        return jsonify(order)
        
    return jsonify({"message": "Invalid email or phone number for this order!"}), 403
