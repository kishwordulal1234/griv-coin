from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
import uuid

class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Float, default=0.0)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    is_mining = db.Column(db.Boolean, default=False)
    mining_power = db.Column(db.Float, default=0.5)
    reset_code = db.Column(db.String(8), unique=True, nullable=True)
    reset_code_timestamp = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        print(f"Setting password for user {self.username}")  # Debug log
        self.password_hash = generate_password_hash(password)
        print(f"Generated password hash: {self.password_hash}")  # Debug log
        
    def check_password(self, password):
        print(f"Checking password for user {self.username}")  # Debug log
        print(f"Stored hash: {self.password_hash}")  # Debug log
        print(f"Input password: {password}")  # Debug log
        result = check_password_hash(self.password_hash, password)
        print(f"Password check result: {result}")  # Debug log
        return result

    def get_id(self):
        return str(self.id) 