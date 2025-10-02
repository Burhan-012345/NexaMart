from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile fields
    full_name = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    
    # User preferences and settings
    newsletter_subscribed = db.Column(db.Boolean, default=True)
    marketing_emails = db.Column(db.Boolean, default=True)
    profile_image = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    
    # Social media links (for reviews)
    twitter_handle = db.Column(db.String(50))
    instagram_handle = db.Column(db.String(50))
    
    # Relationships
    cart_items = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('ProductReview', backref='user', lazy=True, cascade='all, delete-orphan', foreign_keys='ProductReview.user_id')
    questions = db.relationship('ProductQuestion', backref='user', lazy=True, cascade='all, delete-orphan', foreign_keys='ProductQuestion.user_id')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    recently_viewed = db.relationship('RecentlyViewed', backref='user', lazy=True, cascade='all, delete-orphan')
    moderated_reviews = db.relationship('ProductReview', backref='moderator', lazy=True, foreign_keys='ProductReview.moderated_by')
    answered_questions = db.relationship('ProductQuestion', backref='answerer', lazy=True, foreign_keys='ProductQuestion.answered_by_user_id')
    
    def get_cart_count(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.cart_items)
    
    def get_total_orders(self):
        """Get total number of orders"""
        return len(self.orders)
    
    def get_wishlist_count(self):
        """Get total number of wishlist items"""
        return len(self.wishlist_items)
    
    def get_recently_viewed(self, limit=10):
        """Get recently viewed products"""
        return [rv.product for rv in self.recently_viewed[-limit:]]
    
    def has_purchased_product(self, product_id):
        """Check if user has purchased a specific product"""
        for order in self.orders:
            for item in order.items:
                if item.product_id == product_id:
                    return True
        return False
    
    def can_review_product(self, product_id):
        """Check if user can review a product (has purchased it)"""
        return self.has_purchased_product(product_id)
    
    def __repr__(self):
        return f'<User {self.email}>'

class OTPVerification(db.Model):
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15))
    otp = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # 'register', 'reset_password', 'verify_email'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return datetime.utcnow() < self.expires_at and not self.verified
    
    def mark_verified(self):
        """Mark OTP as verified"""
        self.verified = True

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    banner_image_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    meta_title = db.Column(db.String(100))
    meta_description = db.Column(db.Text)
    
    # SEO fields
    slug = db.Column(db.String(100), unique=True)
    
    # Relationship
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def get_active_products(self):
        """Get only active products in this category"""
        return [product for product in self.products if product.is_active]
    
    def get_product_count(self):
        """Get count of active products"""
        return len([product for product in self.products if product.is_active])
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float)
    image_url = db.Column(db.String(200))
    video_url = db.Column(db.String(200))  # For product videos
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Enhanced product fields
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    sku = db.Column(db.String(50), unique=True)
    weight = db.Column(db.Float)  # in grams
    dimensions = db.Column(db.String(50))  # "LxWxH" in cm
    
    # SEO fields
    meta_title = db.Column(db.String(100))
    meta_description = db.Column(db.Text)
    slug = db.Column(db.String(150), unique=True)
    
    # Rating and review fields
    average_rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    total_views = db.Column(db.Integer, default=0)
    total_sold = db.Column(db.Integer, default=0)
    
    # Additional images (stored as JSON string)
    additional_images = db.Column(db.Text, default='[]')  # JSON array of image URLs
    
    # Product specifications (stored as JSON)
    specifications = db.Column(db.Text, default='{}')  # JSON object for specifications
    
    # Relationships
    in_carts = db.relationship('Cart', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('ProductReview', backref='product', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('ProductQuestion', backref='product', lazy=True, cascade='all, delete-orphan')
    in_wishlists = db.relationship('Wishlist', backref='product', lazy=True, cascade='all, delete-orphan')
    recently_viewed_by = db.relationship('RecentlyViewed', backref='product', lazy=True, cascade='all, delete-orphan')
    
    @property
    def current_price(self):
        """Get the current price (discounted if available)"""
        return self.discounted_price if self.discounted_price else self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if discounted"""
        if self.discounted_price and self.discounted_price < self.price:
            return int(((self.price - self.discounted_price) / self.price) * 100)
        return 0
    
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    def can_add_to_cart(self, quantity=1):
        """Check if product can be added to cart in given quantity"""
        return self.is_active and self.stock_quantity >= quantity
    
    def reduce_stock(self, quantity):
        """Reduce product stock quantity"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.total_sold += quantity
            return True
        return False
    
    def restore_stock(self, quantity):
        """Restore product stock quantity (for cancellations)"""
        self.stock_quantity += quantity
        self.total_sold = max(0, self.total_sold - quantity)
    
    def add_view(self):
        """Increment view count"""
        self.total_views += 1
    
    def update_rating(self, new_rating):
        """Update average rating when new review is added"""
        total_rating = self.average_rating * self.review_count
        self.review_count += 1
        self.average_rating = (total_rating + new_rating) / self.review_count
    
    def get_additional_images_list(self):
        """Get additional images as Python list"""
        try:
            return json.loads(self.additional_images)
        except:
            return []
    
    def get_specifications_dict(self):
        """Get specifications as Python dictionary"""
        try:
            return json.loads(self.specifications)
        except:
            return {}
    
    def get_related_products(self, limit=4):
        """Get related products from same category"""
        return Product.query.filter(
            Product.category_id == self.category_id,
            Product.id != self.id,
            Product.is_active == True
        ).order_by(Product.total_sold.desc()).limit(limit).all()
    
    def get_top_reviews(self, limit=5):
        """Get top reviews sorted by helpful votes"""
        return ProductReview.query.filter_by(
            product_id=self.id
        ).order_by(ProductReview.helpful.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductReview(db.Model):
    __tablename__ = 'product_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(100))
    comment = db.Column(db.Text)
    helpful = db.Column(db.Integer, default=0)
    verified_purchase = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Review images (stored as JSON string)
    review_images = db.Column(db.Text, default='[]')
    
    # Admin moderation
    is_approved = db.Column(db.Boolean, default=True)
    moderated_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin user ID
    moderated_at = db.Column(db.DateTime)
    
    def mark_helpful(self):
        """Mark review as helpful"""
        self.helpful += 1
    
    def get_review_images_list(self):
        """Get review images as Python list"""
        try:
            return json.loads(self.review_images)
        except:
            return []
    
    def can_edit(self, user_id):
        """Check if user can edit this review"""
        return self.user_id == user_id
    
    def __repr__(self):
        return f'<ProductReview {self.id} - Product:{self.product_id} - Rating:{self.rating}>'

class ProductQuestion(db.Model):
    __tablename__ = 'product_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    answered_by = db.Column(db.String(100))  # admin/seller name
    answered_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin user ID
    answered_at = db.Column(db.DateTime)
    helpful = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin moderation
    is_approved = db.Column(db.Boolean, default=True)
    
    def is_answered(self):
        """Check if question has been answered"""
        return self.answer is not None and self.answered_at is not None
    
    def mark_helpful(self):
        """Mark question as helpful"""
        self.helpful += 1
    
    def can_edit(self, user_id):
        """Check if user can edit this question"""
        return self.user_id == user_id
    
    def __repr__(self):
        return f'<ProductQuestion {self.id} - Product:{self.product_id}>'

class Cart(db.Model):
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate cart items
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),)
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.product.current_price * self.quantity
    
    def can_update_quantity(self, new_quantity):
        """Check if quantity can be updated based on stock"""
        return new_quantity <= self.product.stock_quantity
    
    def __repr__(self):
        return f'<Cart User:{self.user_id} Product:{self.product_id} Qty:{self.quantity}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, shipped, delivered, cancelled, returned
    shipping_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(20), default='card')  # card, upi, cod, netbanking
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Tracking information
    tracking_number = db.Column(db.String(50))
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    returned_at = db.Column(db.DateTime)
    
    # Shipping details
    shipping_method = db.Column(db.String(50), default='standard')
    shipping_cost = db.Column(db.Float, default=0.0)
    estimated_delivery = db.Column(db.Date)
    
    # Customer notes
    customer_notes = db.Column(db.Text)
    
    # Relationship
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def can_cancel(self):
        """Check if order can be cancelled (only pending or confirmed orders)"""
        return self.status in ['pending', 'confirmed']
    
    def can_return(self):
        """Check if order can be returned (only delivered orders within return period)"""
        if self.status != 'delivered' or not self.delivered_at:
            return False
        
        # Check if within return period (e.g., 7 days)
        return_period = timedelta(days=7)
        return datetime.utcnow() - self.delivered_at <= return_period
    
    def cancel_order(self):
        """Cancel the order and restore product stock"""
        if not self.can_cancel():
            return False
        
        # Restore product stock for all items
        for item in self.items:
            item.product.restore_stock(item.quantity)
        
        # Update order status and timestamps
        self.status = 'cancelled'
        self.payment_status = 'refunded' if self.payment_status == 'completed' else 'cancelled'
        self.cancelled_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True
    
    def return_order(self):
        """Process order return"""
        if not self.can_return():
            return False
        
        # Restore product stock for all items
        for item in self.items:
            item.product.restore_stock(item.quantity)
        
        # Update order status
        self.status = 'returned'
        self.payment_status = 'refunded'
        self.returned_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True
    
    def mark_as_shipped(self, tracking_number=None):
        """Mark order as shipped"""
        if self.status == 'confirmed':
            self.status = 'shipped'
            self.tracking_number = tracking_number
            self.shipped_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def mark_as_delivered(self):
        """Mark order as delivered"""
        if self.status == 'shipped':
            self.status = 'delivered'
            self.delivered_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def mark_as_confirmed(self):
        """Mark order as confirmed"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class based on order status"""
        status_classes = {
            'pending': 'bg-secondary',
            'confirmed': 'bg-primary',
            'shipped': 'bg-info',
            'delivered': 'bg-success',
            'cancelled': 'bg-danger',
            'returned': 'bg-warning'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_status_display(self):
        """Get human readable status"""
        status_display = {
            'pending': 'Pending',
            'confirmed': 'Confirmed',
            'shipped': 'Shipped',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled',
            'returned': 'Returned'
        }
        return status_display.get(self.status, self.status.title())
    
    def get_items_count(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items)
    
    def get_subtotal(self):
        """Get order subtotal (without shipping)"""
        return sum(item.subtotal for item in self.items)
    
    def __repr__(self):
        return f'<Order {self.order_id} - {self.status}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of order
    
    # Store product details at time of order (for historical accuracy)
    product_name = db.Column(db.String(100))
    product_image = db.Column(db.String(200))
    product_sku = db.Column(db.String(50))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Automatically capture product details when creating order item
        if self.product and not self.product_name:
            self.product_name = self.product.name
            self.product_image = self.product.image_url
            self.product_sku = self.product.sku
    
    @property
    def subtotal(self):
        """Calculate subtotal for this order item"""
        return self.price * self.quantity
    
    def can_review(self):
        """Check if this item can be reviewed (order is delivered)"""
        return self.order.status == 'delivered'
    
    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Product:{self.product_id} Qty:{self.quantity}>'

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notes for wishlist item
    notes = db.Column(db.Text)
    
    # Unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_wishlist_product'),)
    
    def __repr__(self):
        return f'<Wishlist User:{self.user_id} Product:{self.product_id}>'

class RecentlyViewed(db.Model):
    __tablename__ = 'recently_viewed'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Track view count for recommendations
    view_count = db.Column(db.Integer, default=1)
    
    # Unique constraint to prevent duplicates, but allow updating view_count
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_recently_viewed'),)
    
    def increment_view(self):
        """Increment view count and update timestamp"""
        self.view_count += 1
        self.viewed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<RecentlyViewed User:{self.user_id} Product:{self.product_id}>'

class ProductComparison(db.Model):
    __tablename__ = 'product_comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100))  # For guest users
    product_ids = db.Column(db.Text, nullable=False)  # JSON array of product IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('comparisons', lazy=True))
    
    def get_product_ids_list(self):
        """Get product IDs as Python list"""
        try:
            return json.loads(self.product_ids)
        except:
            return []
    
    def add_product(self, product_id):
        """Add product to comparison (max 3 products)"""
        product_ids = self.get_product_ids_list()
        if product_id not in product_ids and len(product_ids) < 3:
            product_ids.append(product_id)
            self.product_ids = json.dumps(product_ids)
            return True
        return False
    
    def remove_product(self, product_id):
        """Remove product from comparison"""
        product_ids = self.get_product_ids_list()
        if product_id in product_ids:
            product_ids.remove(product_id)
            self.product_ids = json.dumps(product_ids)
            return True
        return False
    
    def clear_comparison(self):
        """Clear all products from comparison"""
        self.product_ids = '[]'
    
    def __repr__(self):
        return f'<ProductComparison User:{self.user_id} Products:{self.product_ids}>'

class NewsletterSubscription(db.Model):
    __tablename__ = 'newsletter_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    unsubscribed_at = db.Column(db.DateTime)
    
    # Subscription preferences
    categories = db.Column(db.Text, default='[]')  # JSON array of category IDs
    
    def get_categories_list(self):
        """Get categories as Python list"""
        try:
            return json.loads(self.categories)
        except:
            return []
    
    def unsubscribe(self):
        """Unsubscribe from newsletter"""
        self.is_active = False
        self.unsubscribed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<NewsletterSubscription {self.email}>'

class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get site setting value"""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_setting(cls, key, value):
        """Set site setting value"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
    
    def __repr__(self):
        return f'<SiteSettings {self.key}>'

# Helper function to generate order IDs
def generate_order_id():
    """Generate unique order ID"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_str = secrets.token_hex(3).upper()
    return f'ORD{timestamp}{random_str}'

# Helper function to generate SKU
def generate_sku(product_name, category_id):
    """Generate product SKU"""
    category_code = f'CAT{category_id:03d}'
    name_code = ''.join([word[0].upper() for word in product_name.split()[:3]])
    random_str = secrets.token_hex(2).upper()
    return f'{category_code}{name_code}{random_str}'