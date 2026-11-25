from sqlalchemy import BigInteger, Integer, Column, DateTime, ForeignKey, Index, String, Text, func
from app.db.session import Base

class TeamFeedPost(Base):
    __tablename__ = 'team_feed_posts'
    __table_args__ = (Index('ix_team_feed_posts_team_created', 'team_id', 'created_at'),)
    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    team_id = Column(BigInteger, ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)
    title = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    play_date = Column(String(10), nullable=True)
    play_time = Column(String(5), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
