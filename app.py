from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json

from config import Config
from models import ProductQuestion, ProductReview, Wishlist, db, User, OTPVerification, Category, Product, Cart, Order, OrderItem
from utils import mail, generate_otp, send_sms_otp, send_email_otp, format_currency, generate_order_id
from database import init_db
import random
from sqlalchemy import desc, func
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask import send_file
import qrcode
import io

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def utility_processor():
    return dict(format_currency=format_currency)

@app.route('/')
def index():
    categories = Category.query.limit(6).all()
    
    # Featured products - could be based on sales, views, or manual selection
    featured_products = Product.query.filter_by(is_active=True).order_by(desc(Product.id)).limit(8).all()
    
    # Personalized recommendations for logged-in users
    recommended_products = []
    if current_user.is_authenticated:
        # Simple recommendation based on user's previous orders
        user_orders = Order.query.filter_by(user_id=current_user.id).all()
        ordered_category_ids = set()
        for order in user_orders:
            for item in order.items:
                ordered_category_ids.add(item.product.category_id)
        
        if ordered_category_ids:
            recommended_products = Product.query.filter(
                Product.category_id.in_(ordered_category_ids),
                Product.is_active == True
            ).limit(4).all()
        else:
            # Fallback to random products if no order history
            recommended_products = Product.query.filter_by(is_active=True).order_by(func.random()).limit(4).all()
    
    # Recently viewed products (simplified - you might want to store this in session or database)
    recently_viewed = []
    if current_user.is_authenticated:
        recently_viewed = Product.query.filter_by(is_active=True).order_by(func.random()).limit(4).all()
    
    return render_template('main/index.html', 
                         categories=categories, 
                         featured_products=featured_products,
                         recommended_products=recommended_products,
                         recently_viewed=recently_viewed)

# Add API endpoints for search suggestions and trending products
@app.route('/api/search-suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'products': []})
    
    # Search in product names and descriptions
    products = Product.query.filter(
        Product.is_active == True,
        (Product.name.ilike(f'%{query}%') | Product.description.ilike(f'%{query}%'))
    ).limit(5).all()
    
    suggestions = []
    for product in products:
        suggestions.append({
            'id': product.id,
            'name': product.name,
            'price': format_currency(product.current_price),
            'image_url': product.image_url or '/static/images/placeholder.jpg'
        })
    
    return jsonify({'products': suggestions})

@app.route('/api/trending-products')
def trending_products():
    # This could be based on actual sales data, views, etc.
    # For now, return random products as trending
    trending = Product.query.filter_by(is_active=True).order_by(func.random()).limit(8).all()
    
    products = []
    for product in trending:
        products.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'discounted_price': product.discounted_price,
            'image_url': product.image_url or '/static/images/placeholder.jpg'
        })
    
    return jsonify({'products': products})

# Update the add_to_cart route to support AJAX requests
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = current_user.get_cart_count()
        return jsonify({
            'success': True,
            'message': 'Product added to cart!',
            'cart_count': cart_count
        })
    
    flash('Product added to cart!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/categories')
def categories():
    categories = Category.query.all()
    
    # Calculate additional statistics
    total_products = Product.query.filter_by(is_active=True).count()
    active_categories = Category.query.filter_by(is_active=True).count()
    featured_products_count = Product.query.filter_by(is_active=True).count()  # You can modify this logic
    
    # Add product count to each category
    for category in categories:
        category.product_count = Product.query.filter_by(
            category_id=category.id, 
            is_active=True
        ).count()
        category.active_products = category.product_count
    
    return render_template('main/categories.html', 
                         categories=categories,
                         total_products=total_products,
                         active_categories=active_categories,
                         featured_products_count=featured_products_count)

# Update the category_products route
@app.route('/category/<int:category_id>')
def category_products(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category_id, is_active=True).all()
    
    # Add additional product data for filtering
    for product in products:
        # Simulate average rating and review count (you'd typically have this in your database)
        product.average_rating = round(random.uniform(3.5, 5.0), 1)
        product.review_count = random.randint(10, 500)
        product.in_wishlist = False  # You'd check if current user has this in wishlist
    
    return render_template('main/category_products.html', category=category, products=products)

# Add wishlist routes
@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Product already in wishlist'})
    
    wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
    db.session.add(wishlist_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Product added to wishlist'})

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product removed from wishlist'})
    
    return jsonify({'success': False, 'message': 'Product not in wishlist'})

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Add sample data for demonstration
    if not product.average_rating:
        product.average_rating = round(random.uniform(3.5, 5.0), 1)
    if not product.review_count:
        product.review_count = random.randint(50, 500)
    
    return render_template('main/product_detail.html', product=product)

# Add API routes for reviews and questions
@app.route('/api/product/<int:product_id>/reviews')
def get_product_reviews(product_id):
    reviews = ProductReview.query.filter_by(product_id=product_id).order_by(ProductReview.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': review.id,
        'user_name': review.user.full_name or 'Anonymous',
        'rating': review.rating,
        'title': review.title,
        'comment': review.comment,
        'helpful': review.helpful,
        'date': review.created_at.strftime('%b %d, %Y')
    } for review in reviews])

@app.route('/api/product/<int:product_id>/questions')
def get_product_questions(product_id):
    questions = ProductQuestion.query.filter_by(product_id=product_id).order_by(ProductQuestion.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': question.id,
        'user_name': question.user.full_name or 'Anonymous',
        'question': question.question,
        'answer': question.answer,
        'answered_by': question.answered_by,
        'date': question.created_at.strftime('%b %d, %Y'),
        'answer_date': question.answered_at.strftime('%b %d, %Y') if question.answered_at else None
    } for question in questions])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        otp = request.form.get('otp')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('auth/register.html', email=email, phone=phone)
        
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already registered!', 'danger')
            return render_template('auth/register.html', email=email, phone=phone)
        
        # Debug: Check session and OTP record
        print(f"DEBUG: Session register_otp_sent = {session.get('register_otp_sent')}")
        print(f"DEBUG: Session register_email = {session.get('register_email')}")
        print(f"DEBUG: Form email = {email}")
        print(f"DEBUG: OTP entered = {otp}")
        
        if session.get('register_otp_sent') and session.get('register_email') == email:
            # Find the most recent OTP record for this email and purpose
            otp_record = OTPVerification.query.filter_by(
                email=email, 
                purpose='register',
                verified=False
            ).order_by(OTPVerification.created_at.desc()).first()
            
            print(f"DEBUG: OTP record found = {otp_record is not None}")
            if otp_record:
                print(f"DEBUG: OTP expected = {otp_record.otp}")
                print(f"DEBUG: OTP expires at = {otp_record.expires_at}")
                print(f"DEBUG: Current time = {datetime.utcnow()}")
                print(f"DEBUG: Is OTP valid? = {datetime.utcnow() < otp_record.expires_at}")
            
            if otp_record and otp_record.otp == otp and datetime.utcnow() < otp_record.expires_at:
                # OTP verified, create user
                hashed_password = generate_password_hash(password)
                user = User(email=email, phone=phone, password=hashed_password)
                db.session.add(user)
                otp_record.verified = True
                db.session.commit()
                
                flash('Registration successful! Please login.', 'success')
                session.pop('register_otp_sent', None)
                session.pop('register_email', None)
                return redirect(url_for('login'))
            else:
                if not otp_record:
                    flash('No OTP record found. Please request a new OTP!', 'danger')
                elif otp_record.otp != otp:
                    flash('Invalid OTP! Please check and try again.', 'danger')
                else:
                    flash('OTP has expired! Please request a new OTP.', 'danger')
        else:
            flash('Please request OTP first!', 'danger')
        
        return render_template('auth/register.html', email=email, phone=phone)
    
    return render_template('auth/register.html')

@app.route('/send_register_otp', methods=['POST'])
def send_register_otp():
    email = request.json.get('email')
    phone = request.json.get('phone')
    
    if not email or not phone:
        return jsonify({'success': False, 'message': 'Email and phone are required!'})
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered!'})
    
    if User.query.filter_by(phone=phone).first():
        return jsonify({'success': False, 'message': 'Phone number already registered!'})
    
    # Generate and send OTP
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Mark any existing OTPs as expired for this email/purpose
    existing_otps = OTPVerification.query.filter_by(
        email=email, 
        purpose='register',
        verified=False
    ).all()
    
    for existing_otp in existing_otps:
        existing_otp.expires_at = datetime.utcnow()  # Expire immediately
    
    # Save new OTP to database
    otp_record = OTPVerification(
        email=email,
        phone=phone,
        otp=otp,
        purpose='register',
        expires_at=expires_at
    )
    db.session.add(otp_record)
    db.session.commit()
    
    # Send SMS OTP
    sms_sent = send_sms_otp(phone, otp)
    
    # Send Email OTP
    email_sent = send_email_otp(email, otp, 'registration')
    
    if sms_sent or email_sent:
        session['register_otp_sent'] = True
        session['register_email'] = email
        return jsonify({'success': True, 'message': 'OTP sent successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send OTP. Please try again.'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login failed. Check email and password!', 'danger')
    
    return render_template('auth/login.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        otp = request.form.get('otp')
        new_password = request.form.get('new_password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Email not found!', 'danger')
            return render_template('auth/reset_password.html', email=email)
        
        if 'reset_otp_sent' in session and session.get('reset_email') == email:
            if otp and not new_password:
                # Verify OTP
                otp_record = OTPVerification.query.filter_by(
                    email=email,
                    purpose='reset_password',
                    verified=False
                ).first()
                
                if otp_record and otp_record.otp == otp and datetime.utcnow() < otp_record.expires_at:
                    otp_record.verified = True
                    db.session.commit()
                    session['reset_otp_verified'] = True
                    flash('OTP verified! Please set new password.', 'success')
                else:
                    flash('Invalid or expired OTP!', 'danger')
            elif new_password and session.get('reset_otp_verified'):
                # Set new password
                user.password = generate_password_hash(new_password)
                db.session.commit()
                
                session.pop('reset_otp_sent', None)
                session.pop('reset_email', None)
                session.pop('reset_otp_verified', None)
                
                flash('Password reset successful! Please login.', 'success')
                return redirect(url_for('login'))
        else:
            flash('Please request OTP first!', 'danger')
        
        return render_template('auth/reset_password.html', email=email)
    
    return render_template('auth/reset_password.html')

@app.route('/send_reset_otp', methods=['POST'])
def send_reset_otp():
    email = request.json.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required!'})
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'Email not found!'})
    
    # Generate and send OTP
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp_record = OTPVerification(
        email=email,
        otp=otp,
        purpose='reset_password',
        expires_at=expires_at
    )
    db.session.add(otp_record)
    db.session.commit()
    
    # Send Email OTP
    if send_email_otp(email, otp, 'reset'):
        session['reset_otp_sent'] = True
        session['reset_email'] = email
        return jsonify({'success': True, 'message': 'OTP sent to your email!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send OTP. Please try again.'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    try:
        # Get user's orders
        user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
        
        # Get wishlist count
        wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
        
        addresses = []  

        payment_methods = []  
        
        return render_template('main/profile.html', 
                             orders=user_orders,
                             wishlist_count=wishlist_count,
                             addresses=addresses,
                             payment_methods=payment_methods)
        
    except Exception as e:
        app.logger.error(f"Profile error: {str(e)}")
        return f"Error loading profile: {str(e)}", 500

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.full_name = request.form.get('full_name')
    current_user.address = request.form.get('address')
    current_user.city = request.form.get('city')
    current_user.state = request.form.get('state')
    current_user.pincode = request.form.get('pincode')
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if cart_items:
        totals = calculate_totals(cart_items)
        return render_template('main/cart.html', cart_items=cart_items, **totals)
    else:
        return render_template('main/cart.html', cart_items=[], subtotal=0, shipping=0, tax=0, grand_total=0)
    
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))
    
    totals = calculate_totals(cart_items)
    
    if request.method == 'POST':
        # Create order
        order_id = generate_order_id()
        shipping_address = f"{current_user.full_name}\n{current_user.address}\n{current_user.city}, {current_user.state} - {current_user.pincode}"
        
        payment_method = request.form.get('payment_method', 'card')
        
        # Set payment status based on payment method
        if payment_method == 'cod':
            payment_status = 'pending'  # For COD, payment is pending until delivery
        else:
            payment_status = 'completed'  # For card/UPI, assume payment is completed
        
        order = Order(
            order_id=order_id,
            user_id=current_user.id,
            total_amount=totals['grand_total'],
            shipping_address=shipping_address,
            payment_method=payment_method,
            payment_status=payment_status  # Set the correct payment status
        )
        db.session.add(order)
        
        # Add order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.discounted_price or cart_item.product.price
            )
            db.session.add(order_item)
        
        # Clear cart
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    return render_template('main/checkout.html', cart_items=cart_items, **totals)

@app.route('/update_cart/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    print(f"🔍 UPDATE_CART ROUTE CALLED: cart_id={cart_id}, user_id={current_user.id}")
    
    try:
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            print(f"❌ Cart item {cart_id} not found")
            return jsonify({'success': False, 'message': 'Cart item not found'}), 404

        # Check ownership
        if cart_item.user_id != current_user.id:
            print(f"❌ User {current_user.id} doesn't own cart item {cart_id}")
            return jsonify({'success': False, 'message': 'Unauthorized!'}), 403

        action = request.form.get('action')
        print(f"🔍 Action: {action}")

        if action == 'remove':
            print(f"🗑️ Removing cart item {cart_id}")
            db.session.delete(cart_item)
            db.session.commit()
            
            cart_count = Cart.query.filter_by(user_id=current_user.id).count()
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            totals = calculate_totals(cart_items)
            
            print(f"✅ Successfully removed cart item {cart_id}")
            return jsonify({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': cart_count,
                'totals': totals
            })
        
        elif action == 'move_to_wishlist':
            product_id = request.form.get('product_id')
            print(f"❤️ Moving cart item {cart_id} to wishlist, product_id: {product_id}")
            
            # Check if already in wishlist
            existing_wishlist = Wishlist.query.filter_by(
                user_id=current_user.id, 
                product_id=product_id
            ).first()
            
            if not existing_wishlist:
                # Add to wishlist
                wishlist_item = Wishlist(
                    user_id=current_user.id, 
                    product_id=product_id
                )
                db.session.add(wishlist_item)
            
            # Remove from cart
            db.session.delete(cart_item)
            db.session.commit()
            
            cart_count = Cart.query.filter_by(user_id=current_user.id).count()
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            totals = calculate_totals(cart_items)
            
            print(f"✅ Successfully moved cart item {cart_id} to wishlist")
            return jsonify({
                'success': True,
                'message': 'Item moved to wishlist',
                'cart_count': cart_count,
                'totals': totals
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR in update_cart: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check if user owns the order
    if order.user_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Unauthorized!'}), 403
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    
    # Check if order can be cancelled
    if not order.can_cancel():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'This order cannot be cancelled.'})
        flash('This order cannot be cancelled.', 'warning')
        return redirect(url_for('profile'))
    
    # Cancel the order
    if order.cancel_order():
        db.session.commit()  # Ensure changes are saved
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Order cancelled successfully!'})
        flash('Order cancelled successfully!', 'success')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Failed to cancel order.'})
        flash('Failed to cancel order.', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/track_order', methods=['GET', 'POST'])
def track_order():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        order = Order.query.filter_by(order_id=order_id).first()
        
        if order:
            return render_template('main/track_order.html', order=order, searched=True)
        else:
            flash('Order not found!', 'danger')
    
    return render_template('main/track_order.html', searched=False)

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Display order confirmation page"""
    order = Order.query.get_or_404(order_id)
    
    # Check if user owns the order
    if order.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    
    # Calculate estimated delivery date
    estimated_delivery = datetime.now() + timedelta(days=3)
    
    return render_template('main/order_confirmation.html', 
                         order=order, 
                         estimated_delivery=estimated_delivery)

@app.route('/api/recommended-products')
@login_required
def recommended_products():
    """Get recommended products based on current order"""
    order_id = request.args.get('order_id')
    
    # Get current order categories
    if order_id:
        order = Order.query.get(order_id)
        if order and order.user_id == current_user.id:
            # Get categories from ordered products
            category_ids = [item.product.category_id for item in order.items if item.product]
            
            if category_ids:
                # Get products from same categories
                recommended = Product.query.filter(
                    Product.category_id.in_(category_ids),
                    Product.is_active == True,
                    Product.id.notin_([item.product_id for item in order.items])
                ).limit(4).all()
                
                products = []
                for product in recommended:
                    products.append({
                        'id': product.id,
                        'name': product.name,
                        'price': format_currency(product.discounted_price or product.price),
                        'image_url': product.image_url or url_for('static', filename='images/placeholder.jpg')
                    })
                
                return jsonify(products)
    
    # Fallback to random products
    fallback_products = Product.query.filter_by(is_active=True).order_by(func.random()).limit(4).all()
    products = []
    for product in fallback_products:
        products.append({
            'id': product.id,
            'name': product.name,
            'price': format_currency(product.discounted_price or product.price),
            'image_url': product.image_url or url_for('static', filename='images/placeholder.jpg')
        })
    
    return jsonify(products)

@app.route('/print_receipt/<int:order_id>')
@login_required
def print_receipt(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    
    return render_template('receipts/receipt.html', order=order)

def calculate_totals(cart_items):
    """Calculate cart totals with fixed tax"""
    subtotal = sum((item.product.discounted_price or item.product.price) * item.quantity for item in cart_items)
    shipping = 0 if subtotal >= 999 else 50
    tax = 300  # Fixed tax amount as requested
    grand_total = subtotal + shipping + tax
    
    return {
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total
    }

@app.route('/orders')
@login_required
def orders():
    """Display all orders for the current user"""
    user_orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('main/orders.html', orders=user_orders)

@app.route('/api/wishlist')
@login_required
def get_wishlist():
    """Get user's wishlist items"""
    try:
        wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
        
        products = []
        for item in wishlist_items:
            if item.product and item.product.is_active:
                products.append({
                    'id': item.product.id,
                    'name': item.product.name,
                    'price': format_currency(item.product.discounted_price or item.product.price),
                    'image_url': item.product.image_url or url_for('static', filename='images/placeholder.jpg'),
                    'original_price': format_currency(item.product.price) if item.product.discounted_price else None,
                    'discount_percentage': item.product.discount_percentage,
                    'in_stock': item.product.stock_quantity > 0
                })
        
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })
        
    except Exception as e:
        print(f"Error fetching wishlist: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load wishlist',
            'products': [],
            'count': 0
        }), 500

@app.route('/api/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist_api(product_id):
    """Remove item from wishlist via API"""
    try:
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id, 
            product_id=product_id
        ).first()
        
        if wishlist_item:
            db.session.delete(wishlist_item)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Product removed from wishlist'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Product not found in wishlist'
            }), 404
            
    except Exception as e:
        db.session.rollback()
        print(f"Error removing from wishlist: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to remove from wishlist'
        }), 500

@app.route('/download_invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    """Generate and download invoice as PDF"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order
        if order.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized!'}), 403
        
        # Create PDF in memory
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        
        # Set up PDF content
        pdf.setTitle(f"Invoice-{order.order_id}")
        
        # Header
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(100, 750, "NexaMart")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(100, 730, "INVOICE")
        
        # Order Information
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(100, 700, f"Order ID: {order.order_id}")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(100, 685, f"Order Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}")
        pdf.drawString(100, 670, f"Status: {order.get_status_display()}")
        
        # Customer Information
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(100, 640, "Bill To:")
        pdf.setFont("Helvetica", 10)
        y_position = 625
        if current_user.full_name:
            pdf.drawString(100, y_position, current_user.full_name)
            y_position -= 15
        pdf.drawString(100, y_position, current_user.email)
        y_position -= 15
        if current_user.address:
            pdf.drawString(100, y_position, current_user.address)
            y_position -= 15
            pdf.drawString(100, y_position, f"{current_user.city}, {current_user.state} - {current_user.pincode}")
        
        # Items Table Header
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(100, 550, "Item")
        pdf.drawString(300, 550, "Quantity")
        pdf.drawString(400, 550, "Price")
        pdf.drawString(500, 550, "Total")
        
        # Items
        pdf.setFont("Helvetica", 10)
        y_position = 530
        for item in order.items:
            product_name = item.product.name if item.product else "Product"
            # Wrap long product names
            if len(product_name) > 30:
                product_name = product_name[:27] + "..."
            
            pdf.drawString(100, y_position, product_name)
            pdf.drawString(300, y_position, str(item.quantity))
            pdf.drawString(400, y_position, format_currency(item.price))
            pdf.drawString(500, y_position, format_currency(item.subtotal))
            y_position -= 20
            
            # Add new page if running out of space
            if y_position < 100:
                pdf.showPage()
                y_position = 750
                pdf.setFont("Helvetica", 10)
        
        # Totals
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(400, y_position - 40, f"Total: {format_currency(order.total_amount)}")
        pdf.drawString(400, y_position - 60, f"Payment Method: {order.payment_method.upper()}")
        pdf.drawString(400, y_position - 80, f"Payment Status: {order.payment_status.upper()}")
        
        # Footer
        pdf.setFont("Helvetica-Oblique", 8)
        pdf.drawString(100, 50, "Thank you for shopping with NexaMart!")
        pdf.drawString(100, 40, "For any queries, contact: support@nexamart.com")
        
        pdf.save()
        
        # Get PDF data from buffer
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=invoice-{order.order_id}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generating invoice: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Error generating invoice'}), 500
        flash('Error generating invoice', 'danger')
        return redirect(url_for('orders'))

@app.route('/api/generate-qr/<int:order_id>')
@login_required
def generate_qr_code(order_id):
    """Generate QR code for order details"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order
        if order.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized!'}), 403
        
        # Create QR code data
        qr_data = {
            "merchant": "NexaMart",
            "order_id": order.order_id,
            "amount": float(order.total_amount),
            "currency": "INR",
            "date": order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "status": order.status,
            "payment_method": order.payment_method,
            "customer_email": current_user.email,
            "verification_url": f"{request.host_url}verify-order/{order.order_id}"
        }
        
        # Convert to JSON string
        qr_text = json.dumps(qr_data, indent=2)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="#001f3f", back_color="white")
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return send_file(buffer, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        print(f"QR Generation Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to generate QR code'}), 500

@app.route('/api/qr-data/<int:order_id>')
@login_required
def get_qr_data(order_id):
    """Get QR code data for JavaScript generation"""
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized!'}), 403
        
        qr_data = {
            "merchant": "NexaMart",
            "order_id": order.order_id,
            "amount": float(order.total_amount),
            "currency": "INR",
            "date": order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "status": order.status,
            "payment_method": order.payment_method,
            "customer_email": current_user.email,
            "items": [
                {
                    "name": item.product.name if item.product else "Product",
                    "quantity": item.quantity,
                    "price": float(item.price)
                } for item in order.items
            ],
            "verification_url": f"{request.host_url}verify-order/{order.order_id}"
        }
        
        return jsonify({'success': True, 'qr_data': qr_data})
        
    except Exception as e:
        print(f"QR Data Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to get QR data'}), 500

@app.route('/verify-order/<order_id>')
def verify_order(order_id):
    """Public endpoint to verify order using QR code"""
    order = Order.query.filter_by(order_id=order_id).first()
    
    if not order:
        return render_template('errors/order_not_found.html'), 404
    
    return render_template('main/order_verification.html', order=order)

@app.route('/api/download-qr/<int:order_id>')
@login_required
def download_qr_code(order_id):
    """Download QR code as PNG file"""
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized!'}), 403
        
        # Generate QR code
        qr_data = {
            "order_id": order.order_id,
            "amount": float(order.total_amount),
            "date": order.created_at.strftime('%Y-%m-%d'),
            "status": order.status
        }
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#001f3f", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'nexamart-order-{order.order_id}-qrcode.png'
        )
        
    except Exception as e:
        print(f"Download QR Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to download QR code'}), 500
    
@app.route('/debug_cart')
@login_required
def debug_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'cart_count': len(cart_items),
        'items': [{
            'id': item.id,
            'product_name': item.product.name,
            'quantity': item.quantity
        } for item in cart_items]
    })

@app.route('/test_cart_route/<int:cart_id>', methods=['POST'])
@login_required
def test_cart_route(cart_id):
    """Test route to verify cart routes are working"""
    print(f"✅ TEST: test_cart_route called with cart_id: {cart_id}")
    return jsonify({
        'success': True,
        'message': f'Test route working for cart_id: {cart_id}',
        'cart_id': cart_id
    })

@app.route('/debug_routes')
def debug_routes():
    """Debug route to check all available routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify({'routes': routes})

@app.route('/test_update_cart/<int:cart_id>', methods=['POST', 'GET'])
@login_required
def test_update_cart(cart_id):
    """Test route to verify cart update functionality"""
    print(f"✅ TEST ROUTE: test_update_cart called with cart_id: {cart_id}")
    return jsonify({
        'success': True,
        'message': f'Test route working for cart_id: {cart_id}',
        'cart_id': cart_id,
        'current_user': current_user.id
    })

def get_delivery_date(days_to_add=3):
    """Calculate estimated delivery date"""
    delivery_date = datetime.now() + timedelta(days=days_to_add)
    return delivery_date.strftime("%b %d, %Y")

# Add to context processor
@app.context_processor
def utility_processor():
    return dict(
        format_currency=format_currency,
        get_delivery_date=get_delivery_date
    )
# Initialize database
with app.app_context():
    db.create_all()
    init_db()

if __name__ == '__main__':
    app.run(debug=True)