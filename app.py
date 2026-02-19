from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from db import get_db_connection
from mysql.connector import IntegrityError
from decimal import Decimal, ROUND_HALF_UP

app = Flask(__name__)
app.secret_key = "bookflix_secret_key_2025"

@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True
)

def get_page_type(path):
    if path.startswith("/category"):
        return "category"
    if path.startswith("/book-details"):
        return "book"
    if path.startswith("/wishlist"):
        return "wishlist"
    if path.startswith("/cart"):
        return "cart"
    if path.startswith("/home"):
        return "home"
    return path  # fallback


# ========================= LANDING =========================

@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT image_path
        FROM books
        ORDER BY RAND()
        LIMIT 8
    """)
    trending_books = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html", trending_books=trending_books)

# ========================= AUTH PAGES =========================

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

# ========================= AUTH APIs =========================

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (data["email"], data["password"])
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return jsonify({
        "message": "Login successful",
        "userId": user["id"],
        "name": user["name"]
    }), 200

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
            (data["name"], data["email"], data["password"])
        )
        conn.commit()
    except IntegrityError:
        conn.rollback()
        return jsonify({"message": "Email already registered"}), 409
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Registration successful"}), 201

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@app.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    data = request.get_json()

    email = data.get("email")
    new_password = data.get("newPassword")

    if not email or not new_password:
        return jsonify({"message": "Invalid request"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"message": "Email not registered"}), 404

    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (new_password, email)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Password updated successfully"}), 200

# ========================= HOME =========================

@app.route("/home")
def home_page():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            c.id AS category_id,
            c.name AS category_name,
            b.id AS book_id,
            b.title,
            b.image_path
        FROM categories c
        LEFT JOIN books b ON b.category_id = c.id
        ORDER BY c.id, b.title
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    categories = {}
    for row in rows:
        cid = row["category_id"]
        if cid not in categories:
            categories[cid] = {"name": row["category_name"], "books": []}

        if row["book_id"]:
            categories[cid]["books"].append({
                "id": row["book_id"],
                "title": row["title"],
                "image_path": row["image_path"]
            })

    return render_template(
        "home.html",
        username=session.get("user_name"),
        categories=categories.values()
    )

# ========================= CATEGORY =========================

@app.route("/category")
def category_page():
    if "user_id" not in session:
        return redirect("/login")

    category_name = request.args.get("name")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if not category_name:
        cursor.execute("SELECT id, name FROM categories")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("category.html", categories=categories, books=None)

    cursor.execute("""
        SELECT b.id, b.title, b.image_path
        FROM books b
        JOIN categories c ON b.category_id=c.id
        WHERE c.name=%s
    """, (category_name,))
    books = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "category.html",
        categories=None,
        books=books,
        selected_category=category_name
    )

# ========================= SEARCH =========================

@app.route("/search")
def search_page():
    if "user_id" not in session:
        return redirect("/login")

    query = request.args.get("q", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if query:
        cursor.execute("""
            SELECT id, title, image_path
            FROM books
            WHERE title LIKE %s
        """, (f"%{query}%",))
        books = cursor.fetchall()
    else:
        books = []

    cursor.close()
    conn.close()

    return render_template(
        "category.html",
        categories=None,
        books=books,
        selected_category=f"Search results for '{query}'"
    )


# ========================= BOOK DETAILS =========================

@app.route("/book-details")
def book_details_page():
    book_id = request.args.get("book_id")
    if not book_id:
        return redirect("/home")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------- FETCH BOOK ----------
    cursor.execute("""
        SELECT b.*, c.name AS category_name
        FROM books b
        JOIN categories c ON b.category_id = c.id
        WHERE b.id = %s
    """, (book_id,))
    book = cursor.fetchone()

    if not book:
        cursor.close()
        conn.close()
        return redirect("/home")

    # ---------- WISHLIST CHECK ----------
    is_in_wishlist = False
    if "user_id" in session:
        cursor.execute("""
            SELECT 1
            FROM wishlist
            WHERE user_id = %s AND book_id = %s
            LIMIT 1
        """, (session["user_id"], book_id))
        is_in_wishlist = cursor.fetchone() is not None

    # ---------- PRIME CHECK ----------
    is_prime = False
    if "user_id" in session:
        cursor.execute("""
            SELECT 1
            FROM orders
            WHERE user_id = %s
              AND prime_type IN ('monthly','yearly')
              AND status = 'ordered'
            LIMIT 1
        """, (session["user_id"],))
        is_prime = cursor.fetchone() is not None

    # ---------- PRICE CALC ----------
    price = Decimal(book["price"]) if book["price"] else Decimal("0.00")
    discount_rate = Decimal("0.85")  # 15% discount

    discount_price = (price * discount_rate).quantize(Decimal("0.01"))
    discount_amount = (price - discount_price).quantize(Decimal("0.01"))

    book["discount_price"] = discount_price
    book["discount_amount"] = discount_amount
    book["final_price"] = discount_price if is_prime else price

    cursor.close()
    conn.close()

    return render_template(
        "book-details.html",
        book=book,
        category_name=book["category_name"],
        is_in_wishlist=is_in_wishlist,  
        is_prime=is_prime,
        can_read=is_prime,
        can_download=is_prime,
        can_listen=is_prime
    )


# ========================= WISHLIST =========================

@app.route("/add-to-wishlist/<int:book_id>")
def add_to_wishlist(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT IGNORE INTO wishlist (user_id, book_id) VALUES (%s,%s)",
        (session["user_id"], book_id)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(request.referrer or "/home")

@app.route("/wishlist")
def wishlist_page():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.id, b.title, b.image_path
        FROM wishlist w
        JOIN books b ON w.book_id=b.id
        WHERE w.user_id=%s
    """, (session["user_id"],))
    wishlist_books = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("wishlist.html", wishlist_books=wishlist_books)

@app.route("/wishlist/remove/<int:book_id>", methods=["POST"])
def remove_from_wishlist(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM wishlist WHERE user_id=%s AND book_id=%s",
        (session["user_id"], book_id)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/wishlist")

# ========================= CART =========================

@app.route("/add-to-cart/<int:book_id>")
def add_to_cart(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cart (user_id, book_id, quantity)
        VALUES (%s,%s,1)
        ON DUPLICATE KEY UPDATE quantity = quantity + 1
    """, (session["user_id"], book_id))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/cart")


@app.route("/cart")
def cart_page():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------- FETCH CART ----------
    cursor.execute("""
        SELECT
            b.id,
            b.title,
            b.image_path,
            b.price,
            c.quantity
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = %s
    """, (session["user_id"],))
    cart_books = cursor.fetchall()

    # ---------- PRIME CHECK ----------
    cursor.execute("""
        SELECT 1
        FROM orders
        WHERE user_id = %s
          AND prime_type IN ('monthly','yearly')
          AND status = 'ordered'
        LIMIT 1
    """, (session["user_id"],))
    is_prime = cursor.fetchone() is not None

    # ---------- TOTAL CALC ----------
    total_amount = Decimal("0.00")
    discount_rate = Decimal("0.85")

    for item in cart_books:
        unit_price = Decimal(item["price"])

        if is_prime:
            unit_price = (unit_price * discount_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        subtotal = (unit_price * item["quantity"]).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        item["unit_price"] = unit_price
        item["subtotal"] = subtotal
        total_amount += subtotal

    cursor.close()
    conn.close()

    return render_template(
        "cart.html",
        cart_books=cart_books,
        total_amount=total_amount
    )



@app.route("/cart/update/<int:book_id>", methods=["POST"])
def update_cart(book_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    action = data.get("action")
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------- UPDATE QUANTITY ----------
    if action == "increase":
        cursor.execute("""
            UPDATE cart
            SET quantity = quantity + 1
            WHERE user_id = %s AND book_id = %s
        """, (user_id, book_id))

    elif action == "decrease":
        cursor.execute("""
            UPDATE cart
            SET quantity = GREATEST(quantity - 1, 1)
            WHERE user_id = %s AND book_id = %s
        """, (user_id, book_id))

    conn.commit()

    # ---------- FETCH UPDATED CART ----------
    cursor.execute("""
        SELECT c.book_id, c.quantity, b.price
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()

    total_amount = Decimal("0.00")
    updated_item = None

    for item in cart_items:
        price = Decimal(item["price"])
        quantity = item["quantity"]
        subtotal = price * quantity

        total_amount += subtotal

        if item["book_id"] == book_id:
            updated_item = {
                "quantity": quantity,
                "subtotal": float(subtotal)
            }

    cursor.close()
    conn.close()

    return jsonify({
        "item": updated_item,
        "total": float(total_amount)
    })


@app.route("/cart/remove/<int:book_id>", methods=["POST"])
def remove_from_cart(book_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------- DELETE ITEM ----------
    cursor.execute("""
        DELETE FROM cart
        WHERE user_id = %s AND book_id = %s
    """, (user_id, book_id))
    conn.commit()

    # ---------- RECALCULATE TOTAL ----------
    cursor.execute("""
        SELECT c.quantity, b.price
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = %s
    """, (user_id,))
    items = cursor.fetchall()

    total_amount = Decimal("0.00")
    for item in items:
        total_amount += Decimal(item["price"]) * item["quantity"]

    cursor.close()
    conn.close()

    return jsonify({
        "total": float(total_amount)
    })


# ========================= ORDER =========================

@app.route("/payment")
def payment():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ================= USER =================
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # ================= MEMBERSHIP STATUS =================
    is_prime = False
    if user:
        is_prime = bool(
            user.get("is_prime")
            or user.get("prime")
            or user.get("is_member")
            or user.get("membership")
            or False
        )

    # ================= CART ITEMS =================
    cursor.execute("""
        SELECT
            b.id,
            b.title,
            b.image_path,
            b.price,
            c.quantity
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()

    cursor.close()
    conn.close()

    # ================= CART TOTAL =================
    cart_total = 0.0
    for item in cart_items:
        cart_total += float(item["price"]) * item["quantity"]

    cart_total = round(cart_total, 2)

    return render_template(
        "payment.html",
        cart_items=cart_items,
        cart_total=cart_total,      
        has_cart=len(cart_items) > 0,
        is_prime=is_prime            
    )


@app.route("/place-order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    prime = request.form.get("prime", "none")   # monthly / yearly / none
    payment_method = request.form.get("payment_method")

    conn = get_db_connection()
    cursor = conn.cursor()

    # ---------------- FETCH CART ITEMS (REAL PRICE) ----------------
    cursor.execute("""
        SELECT c.book_id, b.price, c.quantity
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()

    # ---------------- FLAGS ----------------
    has_items = len(cart_items) > 0
    has_prime = prime in ("monthly", "yearly")

    # ---------------- CALCULATE TOTAL ----------------
    total_amount = 0

    for book_id, price, qty in cart_items:
        final_price = price

        # 15% extra discount for Prime members
        if has_prime:
            final_price = round(price * 0.85, 2)
            # final_price = (price * Decimal('0.85')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


        total_amount += final_price * qty

    # ---------------- PRIME COST ----------------
    prime_amount = 0
    if prime == "monthly":
        prime_amount = 199
    elif prime == "yearly":
        prime_amount = 1499

    total_amount += prime_amount





    # ---------------- CREATE ORDER ----------------
    cursor.execute("""
        INSERT INTO orders (user_id, total_amount, status, prime_type)
        VALUES (%s, %s, %s, %s)
    """, (
        user_id,
        total_amount,
        "ordered",
        prime
    ))

    order_id = cursor.lastrowid

    # ---------------- INSERT ORDER ITEMS ----------------
    if has_items:
        for book_id, price, qty in cart_items:
            final_price = price
            if has_prime:
                final_price = round(price * 0.85, 2)

            cursor.execute("""
                INSERT INTO order_items (order_id, book_id, price, quantity)
                VALUES (%s, %s, %s, %s)
            """, (
                order_id,
                book_id,
                final_price,
                qty
            ))

        # clear cart ONLY if books were purchased
        cursor.execute(
            "DELETE FROM cart WHERE user_id = %s",
            (user_id,)
        )

    conn.commit()
    cursor.close()
    conn.close()

    # ---------------- SUCCESS PAGE FLAGS ----------------
    session["has_items"] = has_items
    session["has_prime"] = has_prime

    return redirect(f"/order-success/{order_id}")


@app.route("/order-success/<int:order_id>")
def order_success(order_id):
    if "user_id" not in session:
        return redirect("/login")

    has_items = session.pop("has_items", False)
    has_prime = session.pop("has_prime", False)

    return render_template(
        "order_success.html",
        order_id=order_id,
        has_items=has_items,
        has_prime=has_prime
    )


@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # -------- FETCH ORDERS --------
    cursor.execute("""
        SELECT id, total_amount, status, created_at
        FROM orders
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    orders = cursor.fetchall()

    # -------- FETCH ORDER ITEMS --------
    order_items_map = {}

    for order in orders:
        cursor.execute("""
            SELECT 
                b.id AS book_id,
                b.title,
                b.image_path,
                oi.quantity,
                oi.price
            FROM order_items oi
            JOIN books b ON oi.book_id = b.id
            WHERE oi.order_id = %s
        """, (order["id"],))
        order_items_map[order["id"]] = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "orders.html",
        orders=orders,
        order_items_map=order_items_map
    )

@app.route("/order/cancel/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Only cancel user's own active orders
    cursor.execute("""
        UPDATE orders
        SET status = 'cancelled'
        WHERE id = %s AND user_id = %s AND status = 'ordered'
    """, (order_id, session["user_id"]))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/orders")


# ========================= ACCOUNT/PROFILE =========================

@app.route("/account", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    message = None
    error = None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------- FETCH USER ----------
    cursor.execute("""
        SELECT id, name, email, password
        FROM users
        WHERE id = %s
    """, (user_id,))
    user = cursor.fetchone()

    # ---------- PRIME CHECK ----------
    cursor.execute("""
        SELECT 1
        FROM orders
        WHERE user_id = %s
          AND prime_type IN ('monthly','yearly')
          AND status = 'ordered'
        LIMIT 1
    """, (user_id,))
    user["is_prime"] = cursor.fetchone() is not None

    # ---------- HANDLE POST ----------
    if request.method == "POST":
        action = request.form.get("action")

        # EDIT PROFILE (password required)
        if action == "edit_profile":
            password = request.form.get("password", "").strip()
            new_name = request.form.get("name", "").strip()
            new_email = request.form.get("email", "").strip()

            if password != user["password"]:
                error = "Password is incorrect"
            elif not new_name or not new_email:
                error = "Name and email cannot be empty"
            else:
                cursor.execute("""
                    UPDATE users
                    SET name=%s, email=%s
                    WHERE id=%s
                """, (new_name, new_email, user_id))
                conn.commit()
                message = "Profile updated successfully"

                user["name"] = new_name
                user["email"] = new_email

        # CHANGE PASSWORD
        elif action == "change_password":
            old_password = request.form.get("old_password", "").strip()
            new_password = request.form.get("new_password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            if old_password != user["password"]:
                error = "Old password is incorrect"
            elif new_password != confirm_password:
                error = "Passwords do not match"
            else:
                cursor.execute("""
                    UPDATE users
                    SET password=%s
                    WHERE id=%s
                """, (new_password, user_id))
                conn.commit()

                # logout after password change (security)
                session.clear()
                cursor.close()
                conn.close()
                return redirect("/login")

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        user=user,
        message=message,
        error=error
    )

@app.route("/cancel-subscription", methods=["POST"])
def cancel_subscription():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders
        SET prime_type = 'none',
            status = 'cancelled'
        WHERE user_id = %s
          AND prime_type IN ('monthly', 'yearly')
          AND status = 'ordered'
    """, (session["user_id"],))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/account")


# ===== REGISTER AI ROUTES =====
from ai.brain import handle_ai_chat

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    if "user_id" not in session:
        return jsonify({
            "reply": "Please login so I can help you better 😊",
            "book_ids": []
        })

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "reply": "Say something 😊",
            "book_ids": []
        })

    response = handle_ai_chat(
        message=message,
        user_id=session["user_id"]
    )

    # 🔒 SAFETY: always return expected shape
    return jsonify({
        "reply": response.get("reply", ""),
        "book_ids": response.get("book_ids", [])
    })


@app.route("/api/books/by-ids", methods=["POST"])
def get_books_by_ids():
    data = request.get_json()
    ids = data.get("ids", [])

    if not ids:
        return jsonify([])

    placeholders = ",".join(["%s"] * len(ids))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f"""
        SELECT
            b.id,
            b.title,
            b.image_path,
            c.name AS category
        FROM books b
        JOIN categories c ON b.category_id = c.id
        WHERE b.id IN ({placeholders})
    """, tuple(ids))

    books = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(books)


# ========================= RUN =========================

if __name__ == "__main__":
    app.run(debug=True)
