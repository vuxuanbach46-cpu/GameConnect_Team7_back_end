import enum
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Enum as SQLEnum,
    DateTime,
    func,
)
from app.db.session import Base


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"


class AuthProvider(str, enum.Enum):
    LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)

    password_hash = Column(String(255), nullable=True)

    google_id = Column(String(255), unique=True, nullable=True, index=True)

    auth_provider = Column(
        SQLEnum(AuthProvider),
        nullable=False,
        default=AuthProvider.LOCAL,
    )

    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    locked_until = Column(DateTime, nullable=True)
    locked_reason = Column(String(500), nullable=True)
    last_seen = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
