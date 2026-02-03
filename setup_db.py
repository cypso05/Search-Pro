# setup_db.py
"""
Database setup script for JobSearch Pro
Run: python setup_db.py
"""

import os
import sys
from app import create_app, db
from models.user import User
from models.job import Job, SavedJob
from models.search import SearchHistory

def setup_database():
    """Initialize the database with tables and admin user"""
    app = create_app('production')
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Create admin user if not exists
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@jobsearch.com')
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                email=admin_email,
                username=admin_username,
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            admin.password = admin_password
            
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: {admin_email}")
        else:
            print("Admin user already exists")
        
        print("Database setup complete!")

if __name__ == '__main__':
    setup_database()
    
    