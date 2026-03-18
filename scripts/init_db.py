#!/usr/bin/env python3
"""Initialize database and seed admin user."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.security import get_password_hash
from backend.app.db.session import _check_db, engine, SessionLocal
from backend.app.db.models import Base, User


def main():
    print("Initializing WebGuard RF database...")
    if not _check_db():
        print("ERROR: Could not connect to database. Check DB_HOST, DB_USER, DB_PASSWORD, DB_NAME in .env")
        return 1
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@webguard.local",
                hashed_password=get_password_hash("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("Created admin user (admin / admin123)")
        else:
            print("Admin user already exists")
    finally:
        db.close()
    print("Setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
