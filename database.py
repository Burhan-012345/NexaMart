from models import db, Category, Product
from datetime import datetime

def init_db():
    """Initialize database with sample data"""
    # Create categories
    categories = [
        Category(name="Electronics", description="Latest gadgets and electronics", image_url="/static/section/electronics.jpeg"),
        Category(name="Fashion", description="Trendy clothing and accessories", image_url="/static/section/fashion.jpeg"),
        Category(name="Home & Kitchen", description="Home appliances and kitchenware", image_url="/static/section/home.jpeg"),
        Category(name="Books", description="Books and stationery", image_url="/static/section/books.jpeg"),
        Category(name="Beauty", description="Beauty and personal care", image_url="/static/section/beauty.jpeg"),
        Category(name="Sports", description="Sports equipment and accessories", image_url="/static/section/sports.jpeg"),
        Category(name="Toys", description="Toys and games", image_url="/static/section/toys.jpeg"),
        Category(name="Automotive", description="Automotive parts and accessories", image_url="/static/section/automotive.jpeg"),
        Category(name="Jewelry", description="Fine jewelry and watches", image_url="/static/section/jewelry.jpeg"),
        Category(name="Health", description="Health and wellness products", image_url="/static/section/health.jpeg")
    ]
    for category in categories:
        if not Category.query.filter_by(name=category.name).first():
            db.session.add(category)
    
    db.session.commit()
    
    # Create sample products for each category
    products_data = [
        # Electronics (10 items)
        [
            Product(name="Samsung Galaxy S24", description="Latest Samsung smartphone with advanced features", price=79999.00, discounted_price=74999.00, image_url="/static/images/galaxy_s24.jpg", category_id=1, stock_quantity=50),
            Product(name="iPhone 15 Pro", description="Apple's flagship smartphone with titanium design", price=134900.00, discounted_price=129900.00, image_url="/static/images/iphone15.jpg", category_id=1, stock_quantity=30),
            Product(name="Sony WH-1000XM5", description="Wireless noise-canceling headphones", price=29990.00, discounted_price=27990.00, image_url="/static/images/sony_headphones.jpg", category_id=1, stock_quantity=100),
            Product(name="MacBook Air M2", description="Apple MacBook Air with M2 chip", price=114900.00, discounted_price=109900.00, image_url="/static/images/macbook_air.jpg", category_id=1, stock_quantity=25),
            Product(name="Samsung 4K Smart TV", description="55 inch 4K UHD Smart Television", price=54999.00, discounted_price=49999.00, image_url="/static/images/samsung_tv.jpg", category_id=1, stock_quantity=20),
            Product(name="iPad Air", description="Apple iPad Air with M1 chip", price=59900.00, discounted_price=54900.00, image_url="/static/images/ipad_air.jpg", category_id=1, stock_quantity=40),
            Product(name="Dell XPS 13", description="Dell XPS 13 laptop with Intel i7", price=124990.00, discounted_price=119990.00, image_url="/static/images/dell_xps.jpg", category_id=1, stock_quantity=15),
            Product(name="Apple Watch Series 9", description="Latest Apple Watch with advanced health features", price=41900.00, discounted_price=38900.00, image_url="/static/images/apple_watch.jpg", category_id=1, stock_quantity=60),
            Product(name="Bose SoundLink", description="Portable Bluetooth speaker", price=24990.00, discounted_price=22990.00, image_url="/static/images/bose_speaker.jpg", category_id=1, stock_quantity=75),
            Product(name="Canon EOS R6", description="Mirrorless camera with 20MP sensor", price=189999.00, discounted_price=179999.00, image_url="/static/images/canon_camera.jpg", category_id=1, stock_quantity=10)
        ],
        
        # Fashion (10 items)
        [
            Product(name="Men's Cotton T-Shirt", description="Premium cotton t-shirt for men", price=899.00, discounted_price=699.00, image_url="/static/images/mens_tshirt.jpg", category_id=2, stock_quantity=200),
            Product(name="Women's Summer Dress", description="Elegant summer dress for women", price=2499.00, discounted_price=1999.00, image_url="/static/images/womens_dress.jpg", category_id=2, stock_quantity=150),
            Product(name="Leather Jacket", description="Genuine leather jacket for men", price=8999.00, discounted_price=7999.00, image_url="/static/images/leather_jacket.jpg", category_id=2, stock_quantity=50),
            Product(name="Running Shoes", description="Comfortable running shoes for sports", price=3499.00, discounted_price=2999.00, image_url="/static/images/running_shoes.jpg", category_id=2, stock_quantity=100),
            Product(name="Denim Jeans", description="Classic blue denim jeans", price=1999.00, discounted_price=1599.00, image_url="/static/images/denim_jeans.jpg", category_id=2, stock_quantity=120),
            Product(name="Winter Sweater", description="Warm woolen sweater for winter", price=2999.00, discounted_price=2499.00, image_url="/static/images/winter_sweater.jpg", category_id=2, stock_quantity=80),
            Product(name="Formal Shirt", description="Office wear formal shirt", price=1499.00, discounted_price=1299.00, image_url="/static/images/formal_shirt.jpg", category_id=2, stock_quantity=90),
            Product(name="Sports Shorts", description="Comfortable sports shorts", price=799.00, discounted_price=599.00, image_url="/static/images/sports_shorts.jpg", category_id=2, stock_quantity=150),
            Product(name="Evening Gown", description="Elegant evening gown for special occasions", price=5999.00, discounted_price=4999.00, image_url="/static/images/evening_gown.jpg", category_id=2, stock_quantity=40),
            Product(name="Casual Sneakers", description="Trendy casual sneakers", price=2299.00, discounted_price=1899.00, image_url="/static/images/casual_sneakers.jpg", category_id=2, stock_quantity=110)
        ],
        
        # Home & Kitchen (10 items)
        [
            Product(name="Non-Stick Cookware Set", description="10-piece non-stick cookware set", price=5999.00, discounted_price=4999.00, image_url="/static/images/cookware.jpeg", category_id=3, stock_quantity=60),
            Product(name="Air Fryer", description="Digital air fryer with multiple functions", price=4499.00, discounted_price=3999.00, image_url="/static/images/fryer.jpeg", category_id=3, stock_quantity=45),
            Product(name="Blender", description="High-speed blender for smoothies", price=2999.00, discounted_price=2499.00, image_url="/static/images/blender.jpeg", category_id=3, stock_quantity=70),
            Product(name="Coffee Maker", description="Automatic drip coffee maker", price=3499.00, discounted_price=2999.00, image_url="/static/images/coffee.jpeg", category_id=3, stock_quantity=55),
            Product(name="Dinner Set", description="24-piece ceramic dinner set", price=2999.00, discounted_price=2499.00, image_url="/static/images/dinner.jpeg", category_id=3, stock_quantity=40),
            Product(name="Vacuum Cleaner", description="Bagless vacuum cleaner", price=6999.00, discounted_price=5999.00, image_url="/static/images/cleaner.jpeg", category_id=3, stock_quantity=30),
            Product(name="Microwave Oven", description="Solo microwave oven 20L", price=7999.00, discounted_price=6999.00, image_url="/static/images/oven.jpeg", category_id=3, stock_quantity=35),
            Product(name="Food Processor", description="Multi-functional food processor", price=5499.00, discounted_price=4799.00, image_url="/static/images/processor.jpeg", category_id=3, stock_quantity=25),
            Product(name="Kitchen Knife Set", description="8-piece professional knife set", price=3999.00, discounted_price=3499.00, image_url="/static/images/knife.jpeg", category_id=3, stock_quantity=50),
            Product(name="Pressure Cooker", description="Stainless steel pressure cooker", price=2499.00, discounted_price=1999.00, image_url="/static/images/cooker.jpeg", category_id=3, stock_quantity=65)
        ],
        
        # Books (10 items)
        [
            Product(name="The Psychology of Money", description="Timeless lessons on wealth and happiness", price=499.00, discounted_price=399.00, image_url="/static/images/money.jpeg", category_id=4, stock_quantity=100),
            Product(name="Atomic Habits", description="Tiny changes, remarkable results", price=599.00, discounted_price=499.00, image_url="/static/images/habit.jpeg", category_id=4, stock_quantity=120),
            Product(name="Ikigai", description="The Japanese secret to a long and happy life", price=449.00, discounted_price=349.00, image_url="/static/images/ikigai.jpeg", category_id=4, stock_quantity=90),
            Product(name="The Alchemist", description="A magical story about following your dreams", price=399.00, discounted_price=299.00, image_url="/static/images/alchemist.jpeg", category_id=4, stock_quantity=150),
            Product(name="Think and Grow Rich", description="Classic personal development book", price=349.00, discounted_price=249.00, image_url="/static/images/rich.jpeg", category_id=4, stock_quantity=80),
            Product(name="Rich Dad Poor Dad", description="What the rich teach their kids about money", price=499.00, discounted_price=399.00, image_url="/static/images/rich_dad.jpeg", category_id=4, stock_quantity=110),
            Product(name="The Power of Now", description="A guide to spiritual enlightenment", price=549.00, discounted_price=449.00, image_url="/static/images/power.jpeg", category_id=4, stock_quantity=70),
            Product(name="Sapiens", description="A brief history of humankind", price=699.00, discounted_price=599.00, image_url="/static/images/sapiens.jpeg", category_id=4, stock_quantity=95),
            Product(name="The Subtle Art of Not Giving a F*ck", description="A counterintuitive approach to living a good life", price=599.00, discounted_price=499.00, image_url="/static/images/art.jpeg", category_id=4, stock_quantity=130),
            Product(name="Deep Work", description="Rules for focused success in a distracted world", price=549.00, discounted_price=449.00, image_url="/static/images/deep_work.jpeg", category_id=4, stock_quantity=85)
        ],
        
        # Beauty (10 items)
        [
            Product(name="Vitamin C Serum", description="Brightening and anti-aging serum", price=1299.00, discounted_price=999.00, image_url="/static/images/serum.jpeg", category_id=5, stock_quantity=200),
            Product(name="Hair Dryer", description="Professional hair dryer with diffuser", price=2499.00, discounted_price=1999.00, image_url="/static/images/dryer.jpeg", category_id=5, stock_quantity=60),
            Product(name="Face Moisturizer", description="Hydrating face cream for all skin types", price=899.00, discounted_price=699.00, image_url="/static/images/moisturizer.jpeg", category_id=5, stock_quantity=150),
            Product(name="Makeup Kit", description="Complete makeup kit with brushes", price=1999.00, discounted_price=1599.00, image_url="/static/images/makeup_kit.jpeg", category_id=5, stock_quantity=80),
            Product(name="Perfume", description="Luxury fragrance for men and women", price=2999.00, discounted_price=2499.00, image_url="/static/images/perfume.jpeg", category_id=5, stock_quantity=100),
            Product(name="Hair Straightener", description="Ceramic hair straightening iron", price=1799.00, discounted_price=1499.00, image_url="/static/images/straightener.jpeg", category_id=5, stock_quantity=70),
            Product(name="Sunscreen Lotion", description="SPF 50+ broad spectrum sunscreen", price=699.00, discounted_price=499.00, image_url="/static/images/lotion.jpeg", category_id=5, stock_quantity=180),
            Product(name="Face Mask", description="Sheet masks for glowing skin", price=299.00, discounted_price=199.00, image_url="/static/images/face_mask.jpeg", category_id=5, stock_quantity=250),
            Product(name="Lipstick Set", description="Set of 6 matte lipsticks", price=1499.00, discounted_price=1199.00, image_url="/static/images/lipstick_set.jpeg", category_id=5, stock_quantity=90),
            Product(name="Electric Shaver", description="Men's electric shaver with trimmer", price=3499.00, discounted_price=2999.00, image_url="/static/images/shaver.jpeg", category_id=5, stock_quantity=55)
        ],
        
        # Sports (10 items)
        [
            Product(name="Yoga Mat", description="Non-slip premium yoga mat", price=1499.00, discounted_price=1199.00, image_url="/static/images/yoga_mat.jpeg", category_id=6, stock_quantity=120),
            Product(name="Dumbbell Set", description="Adjustable dumbbell set 10-25kg", price=4999.00, discounted_price=4499.00, image_url="/static/images/dumbbell_set.jpeg", category_id=6, stock_quantity=40),
            Product(name="Running Shoes", description="Professional running shoes", price=3999.00, discounted_price=3499.00, image_url="/static/images/sports_shoes.jpeg", category_id=6, stock_quantity=80),
            Product(name="Football", description="Professional size 5 football", price=1999.00, discounted_price=1599.00, image_url="/static/images/football.jpeg", category_id=6, stock_quantity=60),
            Product(name="Fitness Tracker", description="Smart fitness tracker with heart rate monitor", price=2999.00, discounted_price=2499.00, image_url="/static/images/tracker.jpeg", category_id=6, stock_quantity=95),
            Product(name="Tennis Racket", description="Professional tennis racket", price=4499.00, discounted_price=3999.00, image_url="/static/images/racket.jpeg", category_id=6, stock_quantity=35),
            Product(name="Basketball", description="Official size basketball", price=2499.00, discounted_price=1999.00, image_url="/static/images/basketball.jpeg", category_id=6, stock_quantity=50),
            Product(name="Resistance Bands", description="Set of 5 resistance bands", price=899.00, discounted_price=699.00, image_url="/static/images/band.jpeg", category_id=6, stock_quantity=150),
            Product(name="Cycling Helmet", description="Safety certified cycling helmet", price=1799.00, discounted_price=1499.00, image_url="/static/images/helmet.jpeg", category_id=6, stock_quantity=70),
            Product(name="Badminton Set", description="Complete badminton set with rackets", price=2999.00, discounted_price=2499.00, image_url="/static/images/batminton.jpeg", category_id=6, stock_quantity=45)
        ],
        
        # Toys (10 items)
        [
            Product(name="LEGO Classic Set", description="Creative brick box with 790 pieces", price=2999.00, discounted_price=2499.00, image_url="/static/images/classic_set.jpeg", category_id=7, stock_quantity=85),
            Product(name="Remote Control Car", description="2.4GHz remote control car", price=1999.00, discounted_price=1599.00, image_url="/static/images/remote_car.jpeg", category_id=7, stock_quantity=60),
            Product(name="Barbie Dreamhouse", description="3-story dollhouse with accessories", price=5999.00, discounted_price=4999.00, image_url="/static/images/house.jpeg", category_id=7, stock_quantity=30),
            Product(name="Educational Tablet", description="Kids learning tablet with games", price=3499.00, discounted_price=2999.00, image_url="/static/images/tablet.jpeg", category_id=7, stock_quantity=55),
            Product(name="Puzzle Set", description="1000-piece jigsaw puzzle", price=899.00, discounted_price=699.00, image_url="/static/images/puzzle_set.jpeg", category_id=7, stock_quantity=100),
            Product(name="Action Figure", description="Superhero action figure collection", price=1499.00, discounted_price=1199.00, image_url="/static/images/figure.jpeg", category_id=7, stock_quantity=75),
            Product(name="Building Blocks", description="Magnetic building blocks set", price=2499.00, discounted_price=1999.00, image_url="/static/images/blocks.jpeg", category_id=7, stock_quantity=65),
            Product(name="Drone with Camera", description="HD camera drone for kids", price=4999.00, discounted_price=4499.00, image_url="/static/images/drone.jpeg", category_id=7, stock_quantity=25),
            Product(name="Science Kit", description="Educational science experiment kit", price=1799.00, discounted_price=1499.00, image_url="/static/images/science_kit.jpeg", category_id=7, stock_quantity=40),
            Product(name="Board Game Collection", description="Family board games set", price=2999.00, discounted_price=2499.00, image_url="/static/images/game.jpeg", category_id=7, stock_quantity=50)
        ],
        
        # Automotive (10 items)
        [
            Product(name="Car Vacuum Cleaner", description="Portable car vacuum cleaner", price=1999.00, discounted_price=1599.00, image_url="/static/images/car_cleaner.jpeg", category_id=8, stock_quantity=70),
            Product(name="Car Phone Holder", description="Universal car phone mount", price=499.00, discounted_price=399.00, image_url="/static/images/holder.jpeg", category_id=8, stock_quantity=200),
            Product(name="Car Air Freshener", description="Long-lasting car air freshener", price=299.00, discounted_price=199.00, image_url="/static/images/freshner.jpeg", category_id=8, stock_quantity=300),
            Product(name="Jump Starter", description="Portable car jump starter", price=5999.00, discounted_price=4999.00, image_url="/static/images/starter.jpeg", category_id=8, stock_quantity=35),
            Product(name="Car Cover", description="Universal waterproof car cover", price=2499.00, discounted_price=1999.00, image_url="/static/images/cover.jpeg", category_id=8, stock_quantity=45),
            Product(name="Tyre Inflator", description="Digital tyre inflator with pressure gauge", price=1799.00, discounted_price=1499.00, image_url="/static/images/inflator.jpeg", category_id=8, stock_quantity=60),
            Product(name="Car Seat Covers", description="Premium fabric car seat covers", price=3999.00, discounted_price=3499.00, image_url="/static/images/seat_cover.jpeg", category_id=8, stock_quantity=40),
            Product(name="Car Wash Kit", description="Complete car washing kit", price=1499.00, discounted_price=1199.00, image_url="/static/images/wash_kit.jpeg", category_id=8, stock_quantity=85),
            Product(name="Dash Cam", description="HD dashboard camera with night vision", price=4999.00, discounted_price=4499.00, image_url="/static/images/dash_cam.jpeg", category_id=8, stock_quantity=55),
            Product(name="Car Organizer", description="Backseat car organizer for kids", price=899.00, discounted_price=699.00, image_url="/static/images/organizor.jpeg", category_id=8, stock_quantity=90)
        ],
        
        # Jewelry (10 items)
        [
            Product(name="Gold Plated Necklace", description="Elegant gold plated necklace", price=2999.00, discounted_price=2499.00, image_url="/static/images/necklace.jpeg", category_id=9, stock_quantity=50),
            Product(name="Silver Bracelet", description="Sterling silver bracelet with stones", price=1999.00, discounted_price=1599.00, image_url="/static/images/bracelet.jpeg", category_id=9, stock_quantity=65),
            Product(name="Diamond Earrings", description="Sparkling diamond stud earrings", price=8999.00, discounted_price=7999.00, image_url="/static/images/earring.jpeg", category_id=9, stock_quantity=25),
            Product(name="Smart Watch", description="Fitness tracking smartwatch", price=5999.00, discounted_price=4999.00, image_url="/static/images/smart_watch.jpeg", category_id=9, stock_quantity=80),
            Product(name="Pearl Set", description="Elegant pearl necklace and earrings set", price=4999.00, discounted_price=4499.00, image_url="/static/images/pearl_set.jpeg", category_id=9, stock_quantity=35),
            Product(name="Men's Watch", description="Luxury men's wristwatch", price=6999.00, discounted_price=5999.00, image_url="/static/images/mens_watch.jpeg", category_id=9, stock_quantity=45),
            Product(name="Fashion Rings Set", description="Set of 3 fashion rings", price=1499.00, discounted_price=1199.00, image_url="/static/images/rings_set.jpeg", category_id=9, stock_quantity=70),
            Product(name="Anklet", description="Delicate silver anklet", price=899.00, discounted_price=699.00, image_url="/static/images/anklet.jpeg", category_id=9, stock_quantity=85),
            Product(name="Charm Bracelet", description="Personalized charm bracelet", price=2499.00, discounted_price=1999.00, image_url="/static/images/charm_bracelet.jpeg", category_id=9, stock_quantity=40),
            Product(name="Luxury Watch", description="Automatic mechanical watch", price=12999.00, discounted_price=11999.00, image_url="/static/images/luxury_watch.jpeg", category_id=9, stock_quantity=20)
        ],
        
        # Health (10 items)
        [
            Product(name="Digital Thermometer", description="Fast and accurate digital thermometer", price=699.00, discounted_price=499.00, image_url="/static/images/thermometer.jpeg", category_id=10, stock_quantity=150),
            Product(name="Blood Pressure Monitor", description="Automatic blood pressure machine", price=1999.00, discounted_price=1599.00, image_url="/static/images/monitor.jpeg", category_id=10, stock_quantity=60),
            Product(name="Weighing Scale", description="Digital body weight scale", price=1499.00, discounted_price=1199.00, image_url="/static/images/scale.jpeg", category_id=10, stock_quantity=80),
            Product(name="Protein Powder", description="Whey protein for muscle building", price=2999.00, discounted_price=2499.00, image_url="/static/images/powder.jpeg", category_id=10, stock_quantity=95),
            Product(name="Yoga Accessories Kit", description="Complete yoga accessories set", price=2499.00, discounted_price=1999.00, image_url="/static/images/kit.jpeg", category_id=10, stock_quantity=55),
            Product(name="First Aid Kit", description="Comprehensive first aid kit", price=899.00, discounted_price=699.00, image_url="/static/images/first_aid_kit.jpeg", category_id=10, stock_quantity=120),
            Product(name="Massage Gun", description="Percussion massage therapy gun", price=5999.00, discounted_price=4999.00, image_url="/static/images/gun.jpeg", category_id=10, stock_quantity=35),
            Product(name="Air Purifier", description="HEPA air purifier for home", price=7999.00, discounted_price=6999.00, image_url="/static/images/purifier.jpeg", category_id=10, stock_quantity=25),
            Product(name="Vitamin Supplements", description="Multivitamin supplements pack", price=1499.00, discounted_price=1199.00, image_url="/static/images/suppliments.jpeg", category_id=10, stock_quantity=200),
            Product(name="Foot Massager", description="Electric foot massager machine", price=3499.00, discounted_price=2999.00, image_url="/static/images/massager.jpeg", category_id=10, stock_quantity=40)
        ]
    ]
    
    # Add all products to database
    for category_products in products_data:
        for product in category_products:
            if not Product.query.filter_by(name=product.name).first():
                db.session.add(product)
    
    db.session.commit()
    print("Database initialized with 10 categories and 100 products!")
