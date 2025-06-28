from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import Optional
from uuid import UUID

from ..models.db import User
from ..models.schemas import UserCreate, UserUpdate

class UserCRUD:
    @staticmethod
    def get_by_hh_id(db: Session, hh_user_id: str) -> Optional[User]:
        return db.query(User).filter(User.hh_user_id == hh_user_id).first()
    
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create(db: Session, user: UserCreate) -> User:
        db_user = User(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update(db: Session, user_id: UUID, user: UserUpdate) -> Optional[User]:
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**user.dict(exclude_unset=True))
        )
        db.commit()
        return UserCRUD.get_by_id(db, user_id)
    
    @staticmethod
    def update_credits(db: Session, user_id: UUID, credits: int) -> Optional[User]:
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits=credits)
        )
        db.commit()
        return UserCRUD.get_by_id(db, user_id)
    
    @staticmethod
    def decrement_credits(db: Session, user_id: UUID) -> bool:
        user = UserCRUD.get_by_id(db, user_id)
        if not user or user.credits <= 0:
            return False
        
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits=User.credits - 1)
        )
        db.commit()
        return True
    
    @staticmethod
    def add_credits(db: Session, user_id: UUID, credits: int) -> Optional[User]:
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits=User.credits + credits)
        )
        db.commit()
        return UserCRUD.get_by_id(db, user_id)