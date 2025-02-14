import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('7894') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///gada.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    MINING_BASE_RATE = 10  # Base mining rate (coins per minute)
    MIN_MINING_RATE = 1    # Minimum mining rate
    MAX_GADA = 1619       # Maximum GADA coins per user 