"""认证API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, Token
from app.schemas.response import APIResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=APIResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    token = AuthService.register(db, user_data)
    return APIResponse(
        code=201,
        message="注册成功",
        data=token.dict()
    )


@router.post("/login", response_model=APIResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    token = AuthService.login(db, credentials)
    return APIResponse(
        code=200,
        message="登录成功",
        data=token.dict()
    )


@router.post("/logout", response_model=APIResponse)
def logout():
    """用户登出"""
    # JWT是无状态的，客户端删除token即可
    return APIResponse(
        code=200,
        message="登出成功"
    )


@router.post("/refresh", response_model=APIResponse)
def refresh_token():
    """刷新Token"""
    # 简化实现，实际应验证旧token并生成新token
    return APIResponse(
        code=200,
        message="Token刷新成功"
    )
