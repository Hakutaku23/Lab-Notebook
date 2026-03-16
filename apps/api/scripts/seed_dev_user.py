from sqlalchemy import select
from passlib.context import CryptContext

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    db = SessionLocal()
    try:
        existing = db.scalar(
            select(User).where(User.username == "admin")
        )
        if existing:
            print("开发用户已存在：admin / admin123456")
            return

        user = User(
            username="admin",
            email="admin@example.com",
            full_name="Development Admin",
            hashed_password=pwd_context.hash("admin123456"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        print("开发用户创建完成：admin / admin123456")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()