import os
import secrets

class Config:
    SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///nexamart.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = 'AC24f9c5128dc393b2721b151fb1cef6c4'
    TWILIO_AUTH_TOKEN = '6a221d0e4c581f802afc1e1d845a3ed4'
    TWILIO_PHONE_NUMBER = '+12075063134'
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'contact.nexamart1@gmail.com'
    MAIL_PASSWORD = 'dfly qrhk whnx yeqh'