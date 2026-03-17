from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import CurrentUserOut, LoginIn, RegisterIn, TokenOut
from app.services.audit import write_audit_log
from app.services.auth import authenticate_user, issue_access_token, register_user
from app.services.serializers import serialize_current_user

router = APIRouter()


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    token = issue_access_token(user)
    write_audit_log(
        db,
        actor=user,
        action="auth.login",
        resource_type="user",
        resource_id=user.id,
        summary=f"用户 {user.username} 登录成功。",
    )
    db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_current_user(user),
    }


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    user = register_user(
        db,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    token = issue_access_token(user)
    write_audit_log(
        db,
        actor=user,
        action="auth.register",
        resource_type="user",
        resource_id=user.id,
        summary=f"用户 {user.username} 完成注册。",
    )
    db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_current_user(user),
    }


@router.get("/me", response_model=CurrentUserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return serialize_current_user(current_user)
