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
        message = twilio_client.messages.create(
            body=f'Your NexaMart verification OTP is: {otp}. Valid for 10 minutes.',
            from_=Config.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return False

def send_email_otp(email, otp, purpose='registration'):
    """Send OTP via email"""
    try:
        if purpose == 'registration':
            subject = 'NexaMart - Email Verification OTP'
            body = f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #4169E1, #FFFFFF); padding: 20px; border-radius: 10px;">
                <div style="text-align: center; background: #4169E1; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">NexaMart</h1>
                </div>
                <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #4169E1;">Email Verification</h2>
                    <p>Dear User,</p>
                    <p>Your verification OTP for NexaMart is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #4169E1; letter-spacing: 5px; padding: 15px 25px; border: 2px dashed #4169E1; border-radius: 8px;">
                            {otp}
                        </span>
                    </div>
                    <p>This OTP is valid for 10 minutes. Please do not share it with anyone.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <p>Best regards,<br>NexaMart Team</p>
                </div>
            </div>
            '''
        else:
            subject = 'NexaMart - Password Reset OTP'
            body = f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #4169E1, #FFFFFF); padding: 20px; border-radius: 10px;">
                <div style="text-align: center; background: #4169E1; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">NexaMart</h1>
                </div>
                <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #4169E1;">Password Reset</h2>
                    <p>Dear User,</p>
                    <p>Your OTP for password reset is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #4169E1; letter-spacing: 5px; padding: 15px 25px; border: 2px dashed #4169E1; border-radius: 8px;">
                            {otp}
                        </span>
                    </div>
                    <p>This OTP is valid for 10 minutes. Please do not share it with anyone.</p>
                    <p>If you didn't request a password reset, please ignore this email.</p>
                    <p>Best regards,<br>NexaMart Team</p>
                </div>
            </div>
            '''
        
        msg = Message(subject, recipients=[email])
        msg.html = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def format_currency(amount):
    """Format amount as Indian Rupees"""
    return f'₹{amount:,.2f}'

def generate_order_id():
    """Generate unique order ID"""
    return 'NM' + ''.join(random.choices(string.digits, k=8))

def calculate_totals(cart_items):
    """Calculate cart totals with fixed tax"""
    subtotal = sum(item.product.discounted_price or item.product.price * item.quantity for item in cart_items)
    shipping = 0 if subtotal >= 999 else 50
    tax = 300  # Fixed tax amount as requested
    grand_total = subtotal + shipping + tax
    
    return {
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total
    }