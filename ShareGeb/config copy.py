import os
from dotenv import load_dotenv

DATABASE_CONFIG = {
    "host": "localhost",  # insert your localhost to your_host
    "user": "root",  # inser your user to your_user
    "password": "MinhDZ3009",  # insert your password to your_password
    "port": "3306",
    "database": "ShareGeb_booking",  # insert your database to your_database
}

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or 'YOUR_GOOGLE_MAPS_API_KEY'