"""策略API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse, StrategyListResponse
from app.schemas.response import APIResponse
from app.services.strategy_service import StrategyService

router = APIRouter()


@router.post("", response_model=APIResponse, status_code=201)
def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建策略"""
    strategy = StrategyService.create_strategy(db, current_user, strategy_data)
    return APIResponse(
        code=201,
        message="策略创建成功",
        data=StrategyResponse.from_orm(strategy).dict()
    )


@router.get("", response_model=APIResponse)
def get_strategies(
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取策略列表"""
    strategies, total = StrategyService.get_strategies(db, current_user, status, limit, offset)
    return APIResponse(
        code=200,
        data=StrategyListResponse(
            total=total,
            items=[StrategyResponse.from_orm(s) for s in strategies]
        ).dict()
    )


@router.get("/{strategy_id}", response_model=APIResponse)
def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取策略详情"""
    strategy = StrategyService.get_strategy(db, current_user, strategy_id)
    return APIResponse(
        code=200,
        data=StrategyResponse.from_orm(strategy).dict()
    )


@router.put("/{strategy_id}", response_model=APIResponse)
def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新策略配置"""
    strategy = StrategyService.update_strategy(db, current_user, strategy_id, strategy_data)
    return APIResponse(
        code=200,
        message="策略更新成功",
        data=StrategyResponse.from_orm(strategy).dict()
    )


@router.post("/{strategy_id}/start", response_model=APIResponse)
def start_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动策略"""
    strategy = StrategyService.start_strategy(db, current_user, strategy_id)
    return APIResponse(
        code=200,
        message="策略已启动",
        data=StrategyResponse.from_orm(strategy).dict()
    )


@router.post("/{strategy_id}/stop", response_model=APIResponse)
def stop_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停止策略"""
    strategy = StrategyService.stop_strategy(db, current_user, strategy_id)
    return APIResponse(
        code=200,
        message="策略已停止",
        data=StrategyResponse.from_orm(strategy).dict()
    )


@router.delete("/{strategy_id}", response_model=APIResponse)
def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除策略"""
    StrategyService.delete_strategy(db, current_user, strategy_id)
    return APIResponse(
        code=200,
        message="策略已删除"
    )
