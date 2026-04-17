from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os, re, logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)
app.secret_key = 'a-very-secure-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif'}
app.permanent_session_lifetime = timedelta(minutes=30)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------- Helpers ---------------- #
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Login required")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_counts():
    cart = session.get('cart', {})
    wishlist = session.get('wishlist', [])

    # cart is DICT → sum quantities
    cart_count = sum(cart.values()) if isinstance(cart, dict) else 0
    wishlist_count = len(wishlist)

    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count
    }



# ---------------- Database ---------------- #
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1234',
    'database': 'pua_market'
}

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn if conn.is_connected() else None
    except Error as e:
        logging.error(e)
        return None

# ---------------- Auth ---------------- #
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        name = request.form['name']

        if not re.match(r'^[\w\.-]+@pua\.edu\.eg$', email):
            flash("Only PUA emails allowed")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                           (name,email,hashed))
            conn.commit()
            session['user_id'] = cursor.lastrowid
            session['email'] = email
            session.permanent = True
            return redirect(url_for('product'))
        except:
            flash("Email already exists")
        finally:
            cursor.close(); conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close(); conn.close()
        if not user or not check_password_hash(user['password'], password):
            flash("Invalid credentials")
            return redirect(url_for('login'))
        session['user_id'] = user['id']
        session['email'] = user['email']
        session.permanent = True
        return redirect(url_for('product'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ---------------- Pages ---------------- #
@app.route('/')
def home():
    return render_template('index.html')

# -------------- Products -------------- #
@app.route('/product')
@login_required
def product():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, price, image, user_id as seller_id FROM products ORDER BY created_at DESC")
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    wishlist = session.get('wishlist', [])  # List of product IDs in wishlist

    return render_template(
        'product.html',
        products=products,
        cart_count=sum(session.get('cart', {}).values()),  # total cart quantity
        wishlist_count=len(wishlist),
        wishlist_items=wishlist
    )


@app.route('/product/<int:product_id>')
@login_required
def product_details(product_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, price, image, user_id as seller_id FROM products WHERE id=%s", (product_id,))
    product = cursor.fetchone()
    cursor.close(); conn.close()
    if not product:
        flash("Product not found")
        return redirect(url_for('product'))
    return render_template('product_details.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    # Delete only if current user is the seller
    cursor.execute("DELETE FROM products WHERE id=%s AND user_id=%s", (product_id, session['user_id']))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    if affected:
        return jsonify({'success': True})
    return jsonify({'success': False})
# -------------- Post Item -------------- #
@app.route('/post', methods=['GET','POST'])
@login_required
def post():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        image = request.files.get('image')
        filename = ''
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products(name,price,image,user_id) VALUES(%s,%s,%s,%s)",
                       (name,price,filename,session['user_id']))
        conn.commit()
        cursor.close(); conn.close()
        return redirect(url_for('product'))
    return render_template('post.html')

@app.route('/profile')
@login_required
def profile():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, email, created_at FROM users WHERE id=%s",
        (session['user_id'],)
    )
    user = cursor.fetchone()
    cursor.close(); conn.close()
    return render_template('profile.html', user=user)

@app.route('/checkout')
@login_required
def checkout():
    return render_template('checkout.html')

# ---------------- CART ---------------- #
@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})

    # Make sure cart is a dict
    if isinstance(cart, list):
        cart = {}
        session['cart'] = cart

    if not cart:
        return render_template("cart.html", items=[], subtotal=0)

    ids = list(cart.keys())
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(ids))
    cursor.execute(f"SELECT id, name, price, image FROM products WHERE id IN ({format_strings})", tuple(ids))
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    items = []
    subtotal = 0
    for p in products:
        qty = cart.get(str(p['id']), 1)
        p['quantity'] = qty
        subtotal += p['price'] * qty
        items.append(p)

    return render_template("cart.html", items=items, subtotal=subtotal)
@app.route('/cart/update', methods=['POST'])
@login_required
def cart_update():
    data = request.get_json()
    pid = str(data['product_id'])
    qty = int(data['quantity'])

    cart = session.get('cart', {})

    if qty <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = qty

    session['cart'] = cart
    return jsonify(success=True)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    cart = session.get("cart", {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    return jsonify(count=sum(cart.values()))


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def cart_remove(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return jsonify(success=True)
@app.route('/cart/mini')
@login_required
def cart_mini():
    cart = session.get('cart', {})
    if isinstance(cart, list):
        cart = {}
        session['cart'] = cart

    if not cart:
        return "<p>Your cart is empty 🛒</p>"

    ids = list(cart.keys())
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(ids))
    cursor.execute(
        f"SELECT id, name, price, image FROM products WHERE id IN ({format_strings})",
        tuple(ids)
    )
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    html = ""
    for p in products:
        qty = cart.get(str(p['id']), 1)
        html += f"""
        <div class="cart-item" data-id="{p['id']}">
          <img src="{url_for('static', filename='uploads/' + p['image'])}" width="50" height="50">
          <div>
            <strong>{p['name']}</strong>
            <p>EGP {p['price']}</p>
            <p>Qty: {qty}</p>
          </div>
        </div>
        """
    return html

# ---------------- WISHLIST ---------------- #
@app.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    wishlist = session.get('wishlist', [])

    if product_id in wishlist:
        wishlist.remove(product_id)
        in_wishlist = False
    else:
        wishlist.append(product_id)
        in_wishlist = True

    session['wishlist'] = wishlist
    session.modified = True

    return jsonify({'count': len(wishlist), 'in_wishlist': in_wishlist})
@app.route('/wishlist/mini')
@login_required
def wishlist_mini():
    wishlist_ids = session.get('wishlist', [])
    if not wishlist_ids:
        return "<p>Your wishlist is empty ❤️</p>"

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    format_ids = ",".join(str(i) for i in wishlist_ids)
    cursor.execute(f"SELECT id, name, price, image FROM products WHERE id IN ({format_ids})")
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    html = ""
    for p in products:
        html += f"""
        <div class="wishlist-item">
            <img src="{url_for('static', filename='uploads/' + p['image'])}" width="50">
            <span>{p['name']}</span>
            <span>EGP {p['price']}</span>
            <button onclick="moveToCart({p['id']})">Move to Cart</button>
        </div>
        """
    return html
# ---------------- CHAT ---------------- #
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    messages = session.get('chat_messages', [])
    if request.method == 'POST':
        msg = request.form.get('message')
        if msg:
            messages.append({'from': 'user', 'text': msg})
            messages.append({'from': 'bot', 'text': bot_reply(msg)})
            session['chat_messages'] = messages
    return render_template('chat.html', messages=messages)

def bot_reply(msg):
    msg = msg.lower()
    if 'hi' in msg or 'hello' in msg:
        return "Heyyy , how can I help you?"
    if 'price' in msg:
        return "All prices are listed on the product cards "
    if 'delivery' in msg:
        return "keep your number to contact"
    if 'bye' in msg:
        return "Byee "
    return "seller will contact you soon"

from flask import abort

@app.route('/chat_seller/<int:seller_id>/<int:product_id>', methods=['GET', 'POST'])
@login_required
def chat_seller(seller_id, product_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # SECURITY: ensure seller owns the product
    cursor.execute("SELECT user_id, name FROM products WHERE id=%s", (product_id,))
    product = cursor.fetchone()

    if not product or product['user_id'] != seller_id:
        cursor.close()
        conn.close()
        abort(403)

    chat_key = f"chat_{session['user_id']}_{seller_id}_{product_id}"
    messages = session.get(chat_key, [])

    if request.method == 'POST':
        msg = request.form.get('message')
        if msg:
            messages.append({'from': 'user', 'text': msg})
            messages.append({'from': 'seller', 'text': bot_reply(msg)})
            session[chat_key] = messages

    cursor.close()
    conn.close()

    return render_template(
        'chat.html',
        messages=messages,
        product_id=product_id,
        seller_id=seller_id
    )
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    return f"<pre>{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)