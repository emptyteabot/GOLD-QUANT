"""认证服务"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.config import settings


class AuthService:
    """认证服务"""

    @staticmethod
    def register(db: Session, user_data: UserCreate) -> Token:
        """用户注册"""
        # 检查用户名是否存在
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已存在"
            )

        # 检查邮箱是否存在
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱已被注册"
            )

        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            status="active",
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 生成token
        access_token = create_access_token(data={"sub": user.id})

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )

    @staticmethod
    def login(db: Session, credentials: UserLogin) -> Token:
        """用户登录"""
        user = db.query(User).filter(User.username == credentials.username).first()

        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()

        # 生成token
        access_token = create_access_token(data={"sub": user.id})

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
