from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Add new columns
    with db.engine.connect() as conn:
        conn.execute('ALTER TABLE user ADD COLUMN is_mining BOOLEAN DEFAULT FALSE')
        conn.execute('ALTER TABLE user ADD COLUMN mining_power FLOAT DEFAULT 0.5')
    db.session.commit() 