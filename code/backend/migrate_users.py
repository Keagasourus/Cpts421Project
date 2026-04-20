import os
import sys
from sqlalchemy import text
from passlib.context import CryptContext

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import SessionLocal, engine
from src.models import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run_migration():
    print("Checking if users table exists...")
    # Base.metadata.create_all(bind=engine) will create the 'users' table if it doesn't exist
    Base.metadata.create_all(bind=engine)

    # Seed admins
    admins_to_seed = [
        {
            "email": "Hallie.Meredith@lincoln.oxon.org",
            "username": "halliemeredith",
            "password": "T@g^s,arE;fOUr379!PvrPle"
        },
        {
            "email": "asaf.kedar1@gmail.com",
            "username": "asafKedar",
            "password": "-EgX6nsEMfsAZW"
        }
    ]

    db = SessionLocal()
    try:
        from src.models import User
        for admin_data in admins_to_seed:
            existing_user = db.query(User).filter(User.email == admin_data["email"]).first()
            if not existing_user:
                hashed_password = pwd_context.hash(admin_data["password"])
                new_admin = User(
                    email=admin_data["email"],
                    username=admin_data["username"],
                    password_hash=hashed_password,
                    is_admin=True
                )
                db.add(new_admin)
                print(f"Added admin user: {admin_data['username']}")
            else:
                print(f"Admin {admin_data['username']} already exists.")
        db.commit()
    except Exception as e:
        print(f"Error seeding admins: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("Migration and seeding complete.")

if __name__ == "__main__":
    run_migration()
