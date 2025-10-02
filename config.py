import os
import secrets

class Config:
    SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///nexamart.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = 'AC98dceb0cce1b4603299ca4de69840f26'
    TWILIO_AUTH_TOKEN = '3839daa01411e1a5cff78169233fb8b4'
    TWILIO_PHONE_NUMBER = '++13134257867'
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'contact.nexamart1@gmail.com'
    MAIL_PASSWORD = 'dfly qrhk whnx yeqh'
