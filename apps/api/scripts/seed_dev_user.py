import os
import sys

from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def main():
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == "admin"))
        if existing:
            changed = False
            if existing.role != "admin":
                existing.role = "admin"
                changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True
            if changed:
                db.commit()
                print("开发用户已更新：admin / admin123456")
            else:
                print("开发用户已存在：admin / admin123456")
            return
        user = User(
            username="admin",
            email="admin@example.com",
            full_name="开发管理员",
            hashed_password=hash_password("admin123456"),
            role="admin",
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
