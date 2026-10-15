"""Seed the database with the first admin user."""
from sqlalchemy import select
from app.db.session import SessionLocal, engine
from app.db.base import Base
import app.models  # noqa: F401
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.config import settings


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == settings.FIRST_ADMIN_EMAIL))
        if existing:
            print(f"Admin already exists: {settings.FIRST_ADMIN_EMAIL}")
            return
        admin = User(
            email=settings.FIRST_ADMIN_EMAIL,
            full_name=settings.FIRST_ADMIN_NAME,
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Created admin: {settings.FIRST_ADMIN_EMAIL} / {settings.FIRST_ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
