from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> User:
    normalized_username = username.strip()
    user = db.scalar(select(User).where(User.username == normalized_username))
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误。",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前账号已停用。",
        )
    return user


def register_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    normalized_username = username.strip()
    normalized_email = email.strip().lower()
    normalized_full_name = full_name.strip() if full_name else None

    if not normalized_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名不能为空。")
    if not normalized_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱不能为空。")
    if "@" not in normalized_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入有效的邮箱地址。")

    existing_username = db.scalar(select(User).where(User.username == normalized_username))
    if existing_username is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在，请更换后重试。")

    existing_email = db.scalar(select(User).where(User.email == normalized_email))
    if existing_email is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册，请直接登录或使用其他邮箱。")

    user = User(
        username=normalized_username,
        email=normalized_email,
        full_name=normalized_full_name or None,
        hashed_password=hash_password(password),
        role="researcher",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(subject=str(user.id), extra={"username": user.username, "role": user.role})
