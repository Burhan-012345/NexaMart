from venv import logger
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

# Add this at the top of app.py after imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab not available - PDF features disabled")

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
        
        # Clean phone number for checking
        phone_digits = ''.join(filter(str.isdigit, phone))
        if phone_digits.startswith('91') and len(phone_digits) == 12:
            phone_digits = phone_digits[2:]
        elif len(phone_digits) > 10:
            phone_digits = phone_digits[-10:]
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('auth/register.html', email=email, phone=phone)
        
        if User.query.filter_by(phone=phone_digits).first():
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
                user = User(email=email, phone=phone_digits, password=hashed_password)  # Store cleaned phone
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
    try:
        print("🟡 OTP request received")
        
        # Check if request contains JSON data
        if not request.is_json:
            print("❌ Request is not JSON")
            return jsonify({'success': False, 'message': 'Invalid request format'})
        
        data = request.get_json()
        print(f"📦 Request data: {data}")
            
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        
        print(f"📧 Email: {email}")
        print(f"📱 Original phone: {phone}")
        
        if not email or not phone:
            print("❌ Missing email or phone")
            return jsonify({'success': False, 'message': 'Email and phone are required!'})
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Invalid email format!'})
        
        # Improved phone validation - handle various formats
        phone_digits = ''.join(filter(str.isdigit, phone))

        # Remove country code if present
        if phone_digits.startswith('91') and len(phone_digits) == 12:
            phone_digits = phone_digits[2:]  # Remove '91' prefix
        elif phone_digits.startswith('91') and len(phone_digits) > 12:
            phone_digits = phone_digits[2:12]  # Take next 10 digits after '91'
        elif len(phone_digits) > 10:
            phone_digits = phone_digits[-10:]  # Take last 10 digits

        print(f"📱 Phone digits after cleaning: {phone_digits}")

        if len(phone_digits) != 10:
            return jsonify({
                'success': False, 
                'message': 'Invalid phone number! Please use a 10-digit Indian number (with or without +91). Example: 7019670262 or +917019670262'
            })

        # Format phone for display and storage
        formatted_phone = f"+91{phone_digits}"
        phone_for_storage = phone_digits  # Store without +91 in database
        
        print(f"📱 Formatted phone: {formatted_phone}")
        print(f"📱 Phone for storage: {phone_for_storage}")
        
        # Check if user already exists
        existing_user_email = User.query.filter_by(email=email).first()
        existing_user_phone = User.query.filter_by(phone=phone_for_storage).first()
        
        if existing_user_email:
            print(f"❌ Email already exists: {email}")
            return jsonify({'success': False, 'message': 'Email already registered!'})
        
        if existing_user_phone:
            print(f"❌ Phone already exists: {phone_for_storage}")
            return jsonify({'success': False, 'message': 'Phone number already registered!'})
        
        # Generate OTP
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        print(f"🔐 Generated OTP: {otp}")
        
        # Save OTP to database
        try:
            # Expire any existing OTPs
            existing_otps = OTPVerification.query.filter_by(
                email=email, 
                purpose='register',
                verified=False
            ).all()
            
            for existing_otp in existing_otps:
                existing_otp.expires_at = datetime.utcnow()
            
            # Create new OTP record
            otp_record = OTPVerification(
                email=email,
                phone=phone_for_storage,  # Store without +91
                otp=otp,
                purpose='register',
                expires_at=expires_at
            )
            db.session.add(otp_record)
            db.session.commit()
            print("✅ OTP saved to database")
            
        except Exception as db_error:
            print(f"❌ Database error: {str(db_error)}")
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Database error. Please try again.'})
        
        # Send OTP via SMS and Email
        print("🟡 Attempting to send OTP...")
        
        sms_sent = False
        email_sent = False
        
        try:
            # Use the formatted phone with +91 for SMS
            sms_sent = send_sms_otp(formatted_phone, otp)
            print(f"📱 SMS sent: {sms_sent}")
        except Exception as sms_error:
            print(f"❌ SMS error: {str(sms_error)}")
        
        try:
            email_sent = send_email_otp(email, otp, 'registration')
            print(f"📧 Email sent: {email_sent}")
        except Exception as email_error:
            print(f"❌ Email error: {str(email_error)}")
        
        # Set session variables
        session['register_otp_sent'] = True
        session['register_email'] = email
        session['register_phone'] = phone_for_storage  # Store without +91
        
        # Return appropriate response
        if sms_sent and email_sent:
            message = 'OTP sent to your mobile and email!'
        elif sms_sent:
            message = 'OTP sent to your mobile number!'
        elif email_sent:
            message = 'OTP sent to your email!'
        else:
            message = f'OTP: {otp} (Check terminal for testing)'
        
        print(f"✅ OTP process completed: {message}")
        
        return jsonify({
            'success': True, 
            'message': message,
            'debug_otp': otp  # Remove in production
        })
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR in send_register_otp: {str(e)}")
        import traceback
        traceback.print_exc()  # This will show the full stack trace
        
        return jsonify({
            'success': False, 
            'message': 'Server error. Please try again.'
        })
    
@app.route('/debug/check-db')
def debug_check_db():
    """Check database connection"""
    try:
        user_count = User.query.count()
        otp_count = OTPVerification.query.count()
        return jsonify({
            'success': True,
            'user_count': user_count,
            'otp_count': otp_count,
            'database': 'Connected'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/debug/session')
def debug_session():
    """Check session data"""
    return jsonify(dict(session))

@app.route('/debug/test-otp-flow')
def debug_test_otp_flow():
    """Test complete OTP flow"""
    test_email = "test@example.com"
    test_phone = "9876543210"
    otp = generate_otp()
    
    print(f"🧪 Testing OTP flow:")
    print(f"📧 Email: {test_email}")
    print(f"📱 Phone: {test_phone}") 
    print(f"🔐 OTP: {otp}")
    
    # Test SMS
    sms_result = send_sms_otp(test_phone, otp)
    
    # Test Email
    email_result = send_email_otp(test_email, otp)
    
    return jsonify({
        'sms_result': sms_result,
        'email_result': email_result,
        'otp': otp,
        'message': 'Check terminal for details'
    })

@app.route('/debug/clear-session')
def debug_clear_session():
    """Clear session data"""
    session.clear()
    return jsonify({'success': True, 'message': 'Session cleared'})

@app.route('/debug/users')
def debug_users():
    """List all users"""
    users = User.query.all()
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'email': user.email,
            'phone': user.phone,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({'users': user_list})
    
@app.route('/debug/send_test_email')
def debug_send_test_email():
    """Debug route to test email sending"""
    try:
        test_email = "your-test-email@gmail.com"  # Change this
        otp = generate_otp()
        success = send_email_otp(test_email, otp, 'registration')
        return jsonify({'success': success, 'otp': otp, 'email': test_email})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/debug/send_test_sms')
def debug_send_test_sms():
    """Debug route to test SMS sending"""
    try:
        test_phone = "+91XXXXXXXXXX"  # Change this
        otp = generate_otp()
        success = send_sms_otp(test_phone, otp)
        return jsonify({'success': success, 'otp': otp, 'phone': test_phone})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/test-sms')
def test_sms():
    """Test SMS functionality"""
    test_phone = "+919876543210"  # Replace with your test number
    otp = generate_otp()
    
    print(f"🧪 Testing SMS to: {test_phone}")
    print(f"🔐 Test OTP: {otp}")
    
    success = send_sms_otp(test_phone, otp)
    
    return jsonify({
        'success': success,
        'phone': test_phone,
        'otp': otp,
        'message': 'Check your phone for SMS' if success else 'SMS failed - check terminal'
    })

@app.route('/test-email')
def test_email():
    """Test Email functionality"""
    test_email = "test@example.com"  # Replace with your test email
    otp = generate_otp()
    
    print(f"🧪 Testing Email to: {test_email}")
    print(f"🔐 Test OTP: {otp}")
    
    success = send_email_otp(test_email, otp, 'registration')
    
    return jsonify({
        'success': success,
        'email': test_email,
        'otp': otp,
        'message': 'Check your email' if success else 'Email failed - check terminal'
    })

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
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Unauthorized!'}), 403
            flash('Unauthorized!', 'danger')
            return redirect(url_for('index'))
        
        # Check if reportlab is available
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available - cannot generate PDF invoice")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False, 
                    'message': 'PDF generation is currently unavailable. Please try again later.'
                }), 503
            
            # Fallback: Render HTML invoice that user can print
            return render_template('receipts/invoice_html.html', order=order)
        
        # Create PDF in memory
        buffer = io.BytesIO()
        
        try:
            # Create PDF canvas
            pdf = canvas.Canvas(buffer, pagesize=letter)
            pdf.setTitle(f"Invoice-{order.order_id}")
            
            # Set up colors
            primary_color = (0.255, 0.412, 0.882)  # Royal Blue #4169E1
            secondary_color = (0.2, 0.2, 0.2)      # Dark Gray
            light_gray = (0.9, 0.9, 0.9)           # Light Gray
            
            # Header Section
            pdf.setFillColorRGB(*primary_color)
            pdf.rect(0, 750, 612, 60, fill=1, stroke=0)  # Header background
            
            pdf.setFillColorRGB(1, 1, 1)  # White text
            pdf.setFont("Helvetica-Bold", 24)
            pdf.drawString(50, 770, "NEXAMART")
            
            pdf.setFont("Helvetica", 14)
            pdf.drawString(50, 745, "INVOICE")
            
            # Company Info
            pdf.setFillColorRGB(*secondary_color)
            pdf.setFont("Helvetica", 8)
            pdf.drawString(400, 770, "NexaMart Online Store")
            pdf.drawString(400, 760, "support@nexamart.com")
            pdf.drawString(400, 750, "+91 9876543210")
            
            # Order Information
            y_position = 700
            pdf.setFillColorRGB(*secondary_color)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y_position, "ORDER INFORMATION")
            
            y_position -= 20
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y_position, f"Order ID: {order.order_id}")
            pdf.drawString(300, y_position, f"Order Date: {order.created_at.strftime('%B %d, %Y')}")
            
            y_position -= 15
            pdf.drawString(50, y_position, f"Status: {order.get_status_display()}")
            pdf.drawString(300, y_position, f"Payment: {order.payment_method.upper()}")
            
            # Customer Information
            y_position -= 30
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y_position, "BILL TO")
            
            y_position -= 15
            pdf.setFont("Helvetica", 10)
            if current_user.full_name:
                pdf.drawString(50, y_position, current_user.full_name)
                y_position -= 15
            pdf.drawString(50, y_position, current_user.email)
            y_position -= 15
            if current_user.phone:
                pdf.drawString(50, y_position, current_user.phone)
                y_position -= 15
            if current_user.address:
                # Handle multi-line address
                address_lines = current_user.address.split('\n')
                for line in address_lines[:2]:  # Limit to 2 lines
                    if y_position < 100:
                        pdf.showPage()
                        y_position = 750
                    pdf.drawString(50, y_position, line)
                    y_position -= 15
                
                city_state = f"{current_user.city}, {current_user.state} - {current_user.pincode}"
                if y_position < 100:
                    pdf.showPage()
                    y_position = 750
                pdf.drawString(50, y_position, city_state)
                y_position -= 30
            
            # Items Table Header
            if y_position < 150:
                pdf.showPage()
                y_position = 750
            
            pdf.setFillColorRGB(*light_gray)
            pdf.rect(50, y_position-20, 512, 20, fill=1, stroke=0)
            
            pdf.setFillColorRGB(*secondary_color)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(60, y_position-5, "PRODUCT")
            pdf.drawString(350, y_position-5, "QTY")
            pdf.drawString(400, y_position-5, "PRICE")
            pdf.drawString(480, y_position-5, "TOTAL")
            
            # Draw line under header
            pdf.setStrokeColorRGB(*secondary_color)
            pdf.line(50, y_position-25, 562, y_position-25)
            
            y_position -= 35
            
            # Items List
            pdf.setFont("Helvetica", 9)
            for item in order.items:
                if y_position < 100:
                    pdf.showPage()
                    y_position = 750
                    # Redraw table header on new page
                    pdf.setFillColorRGB(*light_gray)
                    pdf.rect(50, y_position-20, 512, 20, fill=1, stroke=0)
                    pdf.setFillColorRGB(*secondary_color)
                    pdf.setFont("Helvetica-Bold", 10)
                    pdf.drawString(60, y_position-5, "PRODUCT")
                    pdf.drawString(350, y_position-5, "QTY")
                    pdf.drawString(400, y_position-5, "PRICE")
                    pdf.drawString(480, y_position-5, "TOTAL")
                    pdf.setStrokeColorRGB(*secondary_color)
                    pdf.line(50, y_position-25, 562, y_position-25)
                    y_position -= 35
                
                # Product name (truncate if too long)
                product_name = item.product_name or "Product"
                if len(product_name) > 40:
                    product_name = product_name[:37] + "..."
                
                pdf.setFillColorRGB(*secondary_color)
                pdf.drawString(60, y_position, product_name)
                pdf.drawString(350, y_position, str(item.quantity))
                pdf.drawString(400, y_position, format_currency(item.price))
                pdf.drawString(480, y_position, format_currency(item.subtotal))
                
                y_position -= 20
            
            # Totals Section
            if y_position < 150:
                pdf.showPage()
                y_position = 750
            
            y_position -= 30
            pdf.setStrokeColorRGB(*secondary_color)
            pdf.line(350, y_position, 562, y_position)
            y_position -= 20
            
            pdf.setFont("Helvetica", 10)
            pdf.drawString(400, y_position, "Subtotal:")
            pdf.drawString(480, y_position, format_currency(order.get_subtotal()))
            
            y_position -= 15
            pdf.drawString(400, y_position, "Shipping:")
            pdf.drawString(480, y_position, format_currency(order.shipping_cost))
            
            y_position -= 15
            pdf.drawString(400, y_position, "Tax:")
            pdf.drawString(480, y_position, format_currency(order.total_amount - order.get_subtotal() - order.shipping_cost))
            
            y_position -= 15
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(400, y_position, "Grand Total:")
            pdf.drawString(480, y_position, format_currency(order.total_amount))
            
            # Payment Information
            y_position -= 40
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(50, y_position, "PAYMENT INFORMATION")
            
            y_position -= 15
            pdf.setFont("Helvetica", 9)
            pdf.drawString(50, y_position, f"Method: {order.payment_method.upper()}")
            pdf.drawString(200, y_position, f"Status: {order.payment_status.upper()}")
            
            if order.payment_status == 'completed':
                pdf.drawString(350, y_position, f"Paid on: {order.created_at.strftime('%b %d, %Y')}")
            
            # Footer
            y_position -= 50
            pdf.setFont("Helvetica-Oblique", 8)
            pdf.setFillColorRGB(0.5, 0.5, 0.5)
            pdf.drawString(50, y_position, "Thank you for shopping with NexaMart!")
            pdf.drawString(50, y_position-10, "For any queries, contact: support@nexamart.com")
            pdf.drawString(50, y_position-20, "This is a computer-generated invoice.")
            
            # Save PDF
            pdf.save()
            
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {str(pdf_error)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False, 
                    'message': 'Error generating PDF invoice'
                }), 500
            
            # Fallback to HTML invoice
            return render_template('receipts/invoice_html.html', order=order)
        
        # Get PDF data from buffer
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=nexamart-invoice-{order.order_id}.pdf'
        
        logger.info(f"Invoice PDF generated successfully for order {order.order_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in download_invoice route: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False, 
                'message': 'An error occurred while generating the invoice'
            }), 500
        
        flash('Error generating invoice. Please try again.', 'danger')
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
