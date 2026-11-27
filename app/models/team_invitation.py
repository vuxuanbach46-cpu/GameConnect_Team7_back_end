import enum
from sqlalchemy import BigInteger, Integer, Column, DateTime, Enum, ForeignKey, Index, UniqueConstraint, func
from app.db.session import Base

class InvitationStatus(str, enum.Enum):
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'

class TeamInvitation(Base):
    __tablename__ = 'team_invitations'
    __table_args__ = (UniqueConstraint('team_id', 'invitee_id', name='uq_team_invitations_team_invitee'), Index('ix_team_invitations_invitee_status', 'invitee_id', 'status'))
    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    team_id = Column(BigInteger, ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    inviter_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    invitee_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = Column(Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
