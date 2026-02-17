"""数据库初始化脚本"""
from app.database import engine, Base
from app.models.user import User
from app.models.api_key import APIKey
from app.models.strategy import Strategy
from app.models.order import Order
from app.models.position import Position


def init_db():
    """初始化数据库表"""
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")


if __name__ == "__main__":
    init_db()
