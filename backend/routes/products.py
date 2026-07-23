from flask import Blueprint, request, jsonify, g
from backend.firebase.db_manager import db_manager
from backend.routes.auth import token_required

products_bp = Blueprint("products", __name__)

@products_bp.route("", methods=["GET"])
def get_products():
    brand = request.args.get("brand")
    category = request.args.get("category")
    gender = request.args.get("gender")
    search = request.args.get("search", "").lower()
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_rating = request.args.get("min_rating", type=float)
    color = request.args.get("color")
    size = request.args.get("size")
    sort_by = request.args.get("sort_by", "popularity") # popularity, newest, price_asc, price_desc, rating
    
    # Load all products from DB manager (supports filters at the query level where possible)
    products = db_manager.get_products(brand=brand, category=category, gender=gender)
    
    # Client-side style filtering for complex queries
    filtered_products = []
    for p in products:
        # Search match
        if search:
            name_match = search in p.get("name", "").lower()
            desc_match = search in p.get("description", "").lower()
            cat_match = search in p.get("category", "").lower()
            if not (name_match or desc_match or cat_match):
                continue
                
        # Price match
        plain_price = p.get("prices", {}).get("plain", 0)
        if min_price is not None and plain_price < min_price:
            continue
        if max_price is not None and plain_price > max_price:
            continue
            
        # Rating match
        if min_rating is not None and p.get("rating", 0) < min_rating:
            continue
            
        # Color match
        if color:
            colors = [c.get("name", "").lower() for c in p.get("colors", [])]
            if color.lower() not in colors:
                continue
                
        # Size match
        if size:
            sizes = [s.lower() for s in p.get("sizes", [])]
            if size.lower() not in sizes:
                continue
                
        filtered_products.append(p)
        
    # Sorting
    if sort_by == "newest":
        # Since we might not have timestamps on all products, we use their IDs or reverse list
        filtered_products.reverse()
    elif sort_by == "price_asc":
        filtered_products.sort(key=lambda x: x.get("prices", {}).get("plain", 0))
    elif sort_by == "price_desc":
        filtered_products.sort(key=lambda x: x.get("prices", {}).get("plain", 0), reverse=True)
    elif sort_by == "rating":
        filtered_products.sort(key=lambda x: x.get("rating", 0), reverse=True)
    else: # popularity / stock
        filtered_products.sort(key=lambda x: x.get("stock", 0), reverse=True)
        
    return jsonify(filtered_products)

@products_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    product = db_manager.get_product(product_id)
    if not product:
        return jsonify({"message": "Product not found!"}), 404
    return jsonify(product)

@products_bp.route("/<product_id>/reviews", methods=["GET"])
def get_reviews(product_id):
    reviews = db_manager.get_reviews(product_id)
    return jsonify(reviews)

@products_bp.route("/<product_id>/reviews", methods=["POST"])
@token_required
def add_review(product_id):
    user = g.current_user
    data = request.get_json() or {}
    rating = data.get("rating", 5)
    comment = (data.get("comment", "") or "").strip()
    if not comment:
        return jsonify({"message": "Comment is required!"}), 400
        
    # Basic XSS sanitization
    sanitized_comment = comment.replace("<", "&lt;").replace(">", "&gt;")
    rating_val = max(1.0, min(float(rating), 5.0))
        
    product = db_manager.get_product(product_id)
    if not product:
        return jsonify({"message": "Product not found!"}), 404
        
    review_data = {
        "product_id": product_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "rating": rating_val,
        "comment": sanitized_comment
    }
    
    review = db_manager.add_review(review_data)
    return jsonify({
        "message": "Review added successfully!",
        "review": review
    }), 201

# Admin CRUD APIs
@products_bp.route("", methods=["POST"])
@token_required
def create_product():
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin access required!"}), 403
        
    data = request.get_json() or {}
    name = data.get("name")
    brand = data.get("brand", "CUSTOM WEAR")
    prices = data.get("prices", {"plain": 0, "printed": 0})
    
    if not name or not prices.get("plain"):
        return jsonify({"message": "Product name and plain price are required!"}), 400
        
    product_data = {
        "id": data.get("id"),
        "name": name,
        "brand": brand,
        "gender": data.get("gender", "Men"),
        "category": data.get("category", name),
        "prices": prices,
        "colors": data.get("colors", []),
        "sizes": data.get("sizes", ["XS", "S", "M", "L", "XL", "2XL"]),
        "cover_image": data.get("cover_image", ""),
        "specifications": data.get("specifications", {
            "Material": "100% Cotton",
            "GSM": "180",
            "Made in India": "Yes",
            "Printing Type": "Screen",
            "Fabric": "Biowashed",
            "Bio Washed": "Yes",
            "Eco Friendly": "Yes",
            "Side Seam": "Yes",
            "Fit Type": "Regular Fit"
        }),
        "description": data.get("description", ""),
        "rating": 5.0,
        "stock": data.get("stock", 100)
    }
    
    product = db_manager.create_product(product_data)
    return jsonify({
        "message": "Product created successfully!",
        "product": product
    }), 201

@products_bp.route("/<product_id>", methods=["PUT"])
@token_required
def update_product(product_id):
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin access required!"}), 403
        
    data = request.get_json() or {}
    product = db_manager.update_product(product_id, data)
    if not product:
        return jsonify({"message": "Product not found or update failed!"}), 404
        
    return jsonify({
        "message": "Product updated successfully!",
        "product": product
    })

@products_bp.route("/<product_id>", methods=["DELETE"])
@token_required
def delete_product(product_id):
    if g.current_user.get("role") != "admin":
        return jsonify({"message": "Admin access required!"}), 403
        
    success = db_manager.delete_product(product_id)
    if not success:
        return jsonify({"message": "Product not found!"}), 404
        
    return jsonify({"message": "Product deleted successfully!"})
