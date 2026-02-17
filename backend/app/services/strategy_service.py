"""策略服务"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse
from datetime import datetime


class StrategyService:
    """策略服务"""

    @staticmethod
    def create_strategy(db: Session, user: User, strategy_data: StrategyCreate) -> Strategy:
        """创建策略"""
        strategy = Strategy(
            user_id=user.id,
            name=strategy_data.name,
            description=strategy_data.description,
            symbol=strategy_data.symbol,
            timeframe=strategy_data.timeframe,
            config=strategy_data.config,
            status="stopped"
        )

        # 从config中提取参数
        if "max_leverage" in strategy_data.config:
            strategy.max_leverage = strategy_data.config["max_leverage"]
        if "max_position_ratio" in strategy_data.config:
            strategy.max_position_ratio = strategy_data.config["max_position_ratio"]
        if "stop_loss_ratio" in strategy_data.config:
            strategy.stop_loss_ratio = strategy_data.config["stop_loss_ratio"]

        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def get_strategies(
        db: Session,
        user: User,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[Strategy], int]:
        """获取策略列表"""
        query = db.query(Strategy).filter(Strategy.user_id == user.id)

        if status:
            query = query.filter(Strategy.status == status)

        total = query.count()
        strategies = query.order_by(Strategy.created_at.desc()).offset(offset).limit(limit).all()

        return strategies, total

    @staticmethod
    def get_strategy(db: Session, user: User, strategy_id: int) -> Strategy:
        """获取策略详情"""
        strategy = db.query(Strategy).filter(
            Strategy.id == strategy_id,
            Strategy.user_id == user.id
        ).first()

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )

        return strategy

    @staticmethod
    def update_strategy(
        db: Session,
        user: User,
        strategy_id: int,
        strategy_data: StrategyUpdate
    ) -> Strategy:
        """更新策略"""
        strategy = StrategyService.get_strategy(db, user, strategy_id)

        if strategy.status == "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="运行中的策略无法修改，请先停止"
            )

        if strategy_data.name is not None:
            strategy.name = strategy_data.name
        if strategy_data.description is not None:
            strategy.description = strategy_data.description
        if strategy_data.config is not None:
            strategy.config = strategy_data.config

        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def start_strategy(db: Session, user: User, strategy_id: int) -> Strategy:
        """启动策略"""
        strategy = StrategyService.get_strategy(db, user, strategy_id)

        if strategy.status == "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略已在运行中"
            )

        strategy.status = "running"
        strategy.started_at = datetime.utcnow()
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def stop_strategy(db: Session, user: User, strategy_id: int) -> Strategy:
        """停止策略"""
        strategy = StrategyService.get_strategy(db, user, strategy_id)

        if strategy.status != "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略未在运行"
            )

        strategy.status = "stopped"
        strategy.stopped_at = datetime.utcnow()
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def delete_strategy(db: Session, user: User, strategy_id: int) -> None:
        """删除策略"""
        strategy = StrategyService.get_strategy(db, user, strategy_id)

        if strategy.status == "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="运行中的策略无法删除，请先停止"
            )

        db.delete(strategy)
        db.commit()
