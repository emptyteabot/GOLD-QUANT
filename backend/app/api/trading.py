"""订单和持仓API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.order import Order
from app.models.position import Position
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse
from app.schemas.position import PositionResponse, PositionListResponse, PositionClose
from app.schemas.response import APIResponse

router = APIRouter()


@router.get("/positions", response_model=APIResponse)
def get_positions(
    symbol: Optional[str] = None,
    status: str = "open",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取持仓列表"""
    query = db.query(Position).filter(Position.user_id == current_user.id)

    if symbol:
        query = query.filter(Position.symbol == symbol)
    if status:
        query = query.filter(Position.status == status)

    positions = query.order_by(Position.opened_at.desc()).all()

    return APIResponse(
        code=200,
        data=PositionListResponse(
            total=len(positions),
            items=[PositionResponse.from_orm(p) for p in positions]
        ).dict()
    )


@router.post("/positions/{position_id}/close", response_model=APIResponse)
def close_position(
    position_id: int,
    close_data: PositionClose,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """平仓"""
    position = db.query(Position).filter(
        Position.id == position_id,
        Position.user_id == current_user.id
    ).first()

    if not position:
        return APIResponse(code=404, message="持仓不存在")

    # 这里应该调用交易所API进行实际平仓
    # 简化实现，直接更新状态
    position.status = "closed"
    from datetime import datetime
    position.closed_at = datetime.utcnow()
    db.commit()

    return APIResponse(
        code=200,
        message="平仓成功"
    )


@router.get("/orders", response_model=APIResponse)
def get_orders(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单列表"""
    query = db.query(Order).filter(Order.user_id == current_user.id)

    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()

    return APIResponse(
        code=200,
        data=OrderListResponse(
            total=total,
            items=[OrderResponse.from_orm(o) for o in orders]
        ).dict()
    )


@router.post("/orders", response_model=APIResponse, status_code=201)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动下单"""
    # 这里应该调用交易所API进行实际下单
    # 简化实现，直接创建订单记录
    import uuid
    order = Order(
        user_id=current_user.id,
        order_id=f"manual-{uuid.uuid4().hex[:12]}",
        symbol=order_data.symbol,
        side=order_data.side,
        order_type=order_data.order_type,
        price=order_data.price,
        quantity=order_data.quantity,
        leverage=order_data.leverage,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return APIResponse(
        code=201,
        message="订单已创建",
        data=OrderResponse.from_orm(order).dict()
    )


@router.delete("/orders/{order_id}", response_model=APIResponse)
def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """撤销订单"""
    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        return APIResponse(code=404, message="订单不存在")

    # 这里应该调用交易所API进行实际撤单
    order.status = "cancelled"
    from datetime import datetime
    order.cancelled_at = datetime.utcnow()
    db.commit()

    return APIResponse(
        code=200,
        message="订单已撤销"
    )
