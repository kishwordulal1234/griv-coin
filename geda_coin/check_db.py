from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    print("\nAll Users in Database:")
    print("-" * 50)
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Password Hash: {user.password_hash}")
        print("-" * 50) 