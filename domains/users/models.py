from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dependencies.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=False)
    bio = Column(String(255))
    profile_picture = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    chat_penalty = Column(Integer, default=0)
    view_penalty = Column(Integer, default=0)
    
    # Relationships
    clips = relationship("Clip", back_populates="creater", foreign_keys='Clip.creater_id')
    liked = relationship("Like", back_populates="liked_user", foreign_keys='Like.liked_user_id')
    follows = relationship("Follow", back_populates="follow_user", foreign_keys='Follow.follow_user_id')
    bans = relationship("Ban", back_populates="ben_user", foreign_keys='Ban.ben_user_id')
    account = relationship("Account", back_populates="user", uselist=False)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    balance = Column(Numeric(10, 2), nullable=False, default=0)
    last_topup_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="account") 

    

# Clip model
class Clip(Base):
    __tablename__ = 'clips'
    id = Column(Integer, primary_key=True, index=True)
    creater_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    streamer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creater = relationship("User", foreign_keys=[creater_id], back_populates="clips")
    streamer = relationship("User", foreign_keys=[streamer_id])


# Like model
class Like(Base):
    __tablename__ = 'likes'
    id = Column(Integer, primary_key=True, index=True)
    liked_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    liked_streamer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    liked_user = relationship("User", foreign_keys=[liked_user_id])
    liked_streamer = relationship("User", foreign_keys=[liked_streamer_id])


# Follow model
class Follow(Base):
    __tablename__ = 'follows'
    id = Column(Integer, primary_key=True, index=True)
    follow_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    follow_streamer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    follow_user = relationship("User", foreign_keys=[follow_user_id])
    follow_streamer = relationship("User", foreign_keys=[follow_streamer_id])


# Ban model
class Ban(Base):
    __tablename__ = 'bans'
    id = Column(Integer, primary_key=True, index=True)
    ben_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    ben_streamer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reason = Column(Text, nullable=False)
    what = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ben_user = relationship("User", foreign_keys=[ben_user_id])
    ben_streamer = relationship("User", foreign_keys=[ben_streamer_id])