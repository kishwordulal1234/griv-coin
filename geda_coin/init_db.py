from app import create_app, db
from app.models.user import User
from app.models.transaction import Transaction
import uuid

app = create_app()

with app.app_context():
    # Drop all existing tables
    db.drop_all()
    # Create all tables
    db.create_all()
    
    # Create test user
    test_user = User(
        username='un1kn0n3_h4rt',
        email='test@example.com'
    )
    test_user.set_password('blueking99')
    
    db.session.add(test_user)
    try:
        db.session.commit()
        print(f"Test user created with ID: {test_user.id}")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating test user: {e}")
    
    print("Database initialized successfully!") 