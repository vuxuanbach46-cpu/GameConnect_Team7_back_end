from sqlalchemy import Column, BigInteger, String, DateTime, func
from app.db.session import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token_jti = Column(String(36), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
