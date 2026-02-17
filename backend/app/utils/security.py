"""安全工具"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def encrypt_api_key(plain_text: str) -> str:
    """加密API密钥（简化版，生产环境应使用更强的加密）"""
    from cryptography.fernet import Fernet
    key = settings.ENCRYPTION_KEY.encode()[:32]
    f = Fernet(key)
    return f.encrypt(plain_text.encode()).decode()


def decrypt_api_key(encrypted_text: str) -> str:
    """解密API密钥"""
    from cryptography.fernet import Fernet
    key = settings.ENCRYPTION_KEY.encode()[:32]
    f = Fernet(key)
    return f.decrypt(encrypted_text.encode()).decode()
