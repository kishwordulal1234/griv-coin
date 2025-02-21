from datetime import datetime
from app import db
from app.models.user import User
from config import Config

class MiningSystem:
    def __init__(self, base_rate=10, min_rate=1):
        self.base_rate = base_rate
        self.min_rate = min_rate
        self.max_gada = Config.MAX_GADA
        
    def calculate_mining_rate(self, active_users):
        if active_users == 0:
            return self.base_rate
        return max(self.min_rate, self.base_rate / active_users)
    
    def get_active_users_count(self):
        return User.query.filter_by(is_active=True).count()
    
    def update_user_balance(self, user_id, mining_rate):
        user = User.query.get(user_id)
        if user and user.is_mining:
            # Calculate new balance
            new_balance = user.balance + (mining_rate * user.mining_power / 60)
            
            # Check if new balance would exceed max
            if new_balance <= self.max_gada:
                user.balance = new_balance
                user.last_seen = datetime.utcnow()
                try:
                    db.session.commit()
                    return True
                except:
                    db.session.rollback()
                    return False
            else:
                # Stop mining if max reached
                user.balance = self.max_gada
                user.is_mining = False
                try:
                    db.session.commit()
                    return False
                except:
                    db.session.rollback()
                    return False
        return False

mining_system = MiningSystem() 