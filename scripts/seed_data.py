"""
Database seed script - Initial data for development/testing
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from libs.database.session import SessionLocal, engine
from libs.database.models import Base, User, UserRole
from services.auth_service.app.auth import get_password_hash
from datetime import datetime
import uuid

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")

def seed_users(db: Session):
    """Seed initial users"""
    print("Seeding users...")
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == "admin@analyticaloan.com").first()
    if existing_admin:
        print("✓ Admin user already exists, skipping...")
        return
    
    # Create admin user
    admin_user = User(
        user_id=uuid.uuid4(),
        email="admin@analyticaloan.com",
        password_hash=get_password_hash("admin123"),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        department="IT",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(admin_user)
    
    # Create underwriter user
    underwriter_user = User(
        user_id=uuid.uuid4(),
        email="underwriter@analyticaloan.com",
        password_hash=get_password_hash("underwriter123"),
        full_name="John Underwriter",
        role=UserRole.UNDERWRITER,
        department="Credit",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(underwriter_user)
    
    # Create risk analyst user
    risk_analyst_user = User(
        user_id=uuid.uuid4(),
        email="risk@analyticaloan.com",
        password_hash=get_password_hash("risk123"),
        full_name="Jane Risk Analyst",
        role=UserRole.RISK_ANALYST,
        department="Risk Management",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(risk_analyst_user)
    
    db.commit()
    print(f"✓ Seeded {3} users")
    print("\nDefault Credentials:")
    print("  Admin:")
    print("    Email: admin@analyticaloan.com")
    print("    Password: admin123")
    print("  Underwriter:")
    print("    Email: underwriter@analyticaloan.com")
    print("    Password: underwriter123")
    print("  Risk Analyst:")
    print("    Email: risk@analyticaloan.com")
    print("    Password: risk123")

def main():
    """Main seed function"""
    print("=" * 60)
    print("AnalyticaLoan - Database Seed Script")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create tables
        create_tables()
        
        # Seed data
        seed_users(db)
        
        print("\n" + "=" * 60)
        print("✅ Database seeding completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
