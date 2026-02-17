"""用户API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.schemas.response import APIResponse
from app.utils.security import verify_password, get_password_hash

router = APIRouter()


@router.get("/me", response_model=APIResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return APIResponse(
        code=200,
        data=UserResponse.from_orm(current_user).dict()
    )


@router.put("/me", response_model=APIResponse)
def update_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.phone is not None:
        current_user.phone = user_data.phone

    db.commit()
    db.refresh(current_user)

    return APIResponse(
        code=200,
        message="更新成功",
        data=UserResponse.from_orm(current_user).dict()
    )


@router.post("/me/password", response_model=APIResponse)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return APIResponse(
        code=200,
        message="密码修改成功"
    )
