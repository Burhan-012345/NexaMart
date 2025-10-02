import random
import string
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from twilio.rest import Client
from config import Config

mail = Mail()
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

def generate_otp(length=6):
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))

def send_sms_otp(phone_number, otp):
    """Send OTP via SMS using Twilio"""
    try:
        print(f"📱 Starting SMS send to: {phone_number}")
        
        # Clean phone number
        phone_digits = ''.join(filter(str.isdigit, str(phone_number)))
        
        if len(phone_digits) == 10:
            formatted_phone = '+91' + phone_digits
        elif len(phone_digits) == 12 and phone_digits.startswith('91'):
            formatted_phone = '+' + phone_digits
        else:
            formatted_phone = phone_number
        
        print(f"📱 Formatted phone for Twilio: {formatted_phone}")
        print(f"📞 Twilio phone: {Config.TWILIO_PHONE_NUMBER}")
        
        # ACTUAL SMS SENDING - Remove the development mode code
        message = twilio_client.messages.create(
            body=f'Your NexaMart verification OTP is: {otp}. Valid for 10 minutes.',
            from_=Config.TWILIO_PHONE_NUMBER,
            to=formatted_phone
        )
        print(f"✅ SMS sent successfully! SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ SMS sending failed: {str(e)}")
        # Fallback: show OTP in terminal for debugging
        print(f"🔐 OTP for {phone_number}: {otp}")
        return False  # Return False to indicate failure

def send_email_otp(email, otp, purpose='registration'):
    """Send OTP via email with styled HTML"""
    try:
        print(f"📧 Starting email send to: {email}")
        
        if purpose == 'registration':
            subject = 'NexaMart - Email Verification OTP'
            html_body = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        background-color: #f8f9fa;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background-color: #001f3f; /* Navy Blue */
                        color: #ffffff;
                        padding: 30px 20px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 28px;
                        font-weight: bold;
                    }}
                    .content {{
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .otp-display {{
                        background-color: #FFD700; /* Bright Yellow */
                        color: #001f3f; /* Navy Blue */
                        font-size: 42px;
                        font-weight: bold;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 30px 0;
                        letter-spacing: 8px;
                        border: 3px dashed #001f3f;
                    }}
                    .message {{
                        color: #333333;
                        font-size: 16px;
                        line-height: 1.6;
                        margin-bottom: 25px;
                    }}
                    .footer {{
                        background-color: #001f3f; /* Navy Blue */
                        color: #ffffff;
                        padding: 20px;
                        text-align: center;
                        font-size: 14px;
                    }}
                    .highlight {{
                        color: #001f3f;
                        font-weight: bold;
                    }}
                    .warning {{
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #856404;
                        font-size: 14px;
                    }}
                    .brand {{
                        color: #FFD700; /* Bright Yellow */
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Nexa<span class="brand">Mart</span></h1>
                        <p>Your One-Stop Shopping Destination</p>
                    </div>
                    
                    <div class="content">
                        <h2 style="color: #001f3f; margin-bottom: 20px;">Email Verification Required</h2>
                        
                        <p class="message">
                            Thank you for choosing NexaMart! To complete your registration, 
                            please use the following One-Time Password (OTP) to verify your email address.
                        </p>
                        
                        <div class="otp-display">
                            {otp}
                        </div>
                        
                        <p class="message">
                            This OTP is valid for <span class="highlight">10 minutes</span>. 
                            Please do not share this code with anyone.
                        </p>
                        
                        <div class="warning">
                            ⚠️ <strong>Security Alert:</strong> NexaMart will never ask for your OTP, 
                            password, or banking details via email, phone, or SMS.
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            If you didn't request this verification, please ignore this email.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>&copy; 2024 NexaMart. All rights reserved.</p>
                        <p>Delivering Excellence, Every Time</p>
                    </div>
                </div>
            </body>
            </html>
            '''
        else:
            subject = 'NexaMart - Password Reset OTP'
            html_body = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        background-color: #f8f9fa;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background-color: #001f3f; /* Navy Blue */
                        color: #ffffff;
                        padding: 30px 20px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 28px;
                        font-weight: bold;
                    }}
                    .content {{
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .otp-display {{
                        background-color: #FFD700; /* Bright Yellow */
                        color: #001f3f; /* Navy Blue */
                        font-size: 42px;
                        font-weight: bold;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 30px 0;
                        letter-spacing: 8px;
                        border: 3px dashed #001f3f;
                    }}
                    .message {{
                        color: #333333;
                        font-size: 16px;
                        line-height: 1.6;
                        margin-bottom: 25px;
                    }}
                    .footer {{
                        background-color: #001f3f; /* Navy Blue */
                        color: #ffffff;
                        padding: 20px;
                        text-align: center;
                        font-size: 14px;
                    }}
                    .highlight {{
                        color: #001f3f;
                        font-weight: bold;
                    }}
                    .warning {{
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #856404;
                        font-size: 14px;
                    }}
                    .brand {{
                        color: #FFD700; /* Bright Yellow */
                        font-weight: bold;
                    }}
                    .reset-instructions {{
                        background-color: #e8f4fd;
                        border: 1px solid #b3d9ff;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #004085;
                        font-size: 14px;
                        text-align: left;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Nexa<span class="brand">Mart</span></h1>
                        <p>Password Reset Request</p>
                    </div>
                    
                    <div class="content">
                        <h2 style="color: #001f3f; margin-bottom: 20px;">Reset Your Password</h2>
                        
                        <p class="message">
                            We received a request to reset your NexaMart account password. 
                            Use the OTP below to verify your identity and create a new password.
                        </p>
                        
                        <div class="otp-display">
                            {otp}
                        </div>
                        
                        <div class="reset-instructions">
                            <strong>Instructions:</strong><br>
                            1. Enter this OTP on the password reset page<br>
                            2. Create a strong new password<br>
                            3. Log in with your new credentials
                        </div>
                        
                        <p class="message">
                            This OTP will expire in <span class="highlight">10 minutes</span>. 
                            For security reasons, please do not share this code.
                        </p>
                        
                        <div class="warning">
                            🔒 <strong>Important:</strong> If you didn't request a password reset, 
                            please secure your account immediately and contact our support team.
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>&copy; 2024 NexaMart. All rights reserved.</p>
                        <p>Your Security is Our Priority</p>
                    </div>
                </div>
            </body>
            </html>
            '''
        
        # ACTUAL EMAIL SENDING
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            sender=Config.MAIL_USERNAME
        )
        mail.send(msg)
        print(f"✅ Email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        # Fallback: show OTP in terminal for debugging
        print(f"🔐 OTP for {email}: {otp}")
        return False  # Return False to indicate failure

def format_currency(amount):
    """Format amount as Indian Rupees"""
    return f'₹{amount:,.2f}'

def generate_order_id():
    """Generate unique order ID"""
    return 'NM' + ''.join(random.choices(string.digits, k=8))

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

def validate_phone_number(phone_number):
    """Validate and format Indian phone numbers"""
    # Remove any spaces, dashes, etc.
    phone = ''.join(filter(str.isdigit, str(phone_number)))
    
    # Check length
    if len(phone) == 10:
        return '+91' + phone
    elif len(phone) == 12 and phone.startswith('91'):
        return '+' + phone
    elif len(phone) == 13 and phone.startswith('+91'):
        return phone
    else:
        return None
