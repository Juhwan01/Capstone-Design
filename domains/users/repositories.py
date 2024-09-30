from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from .models import User, Account
from .dto import UserSignUpDTO, UserProfileDTO, TopUpDTO
from datetime import datetime
from decimal import Decimal

class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_user(self, payload: UserSignUpDTO) -> User:
        profile_picture_str = str(payload.profile_picture) if payload.profile_picture else None
        updated_at = datetime.utcnow()

        user_entity = User(
            username=payload.username,
            email=payload.email,
            hashed_password=payload.password,  # Assuming the password is already hashed
            full_name=payload.full_name,
            bio=payload.bio,
            profile_picture=profile_picture_str,
            updated_at=updated_at
        )
        self._session.add(user_entity)
        try:
            await self._session.flush()
            await self._session.refresh(user_entity)
            
            account_entity = Account(user_id=user_entity.id)
            self._session.add(account_entity)
            
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error: " + str(e))
        return user_entity

    async def get_user_by_username(self, username: str) -> User:
        result = await self._session.execute(
            select(User).options(joinedload(User.account)).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self._session.execute(
            select(User).options(joinedload(User.account)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, payload: UserProfileDTO) -> User:
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        
        for key, value in payload.dict(exclude_unset=True).items():
            setattr(user, key, value)
        
        try:
            await self._session.commit()
            await self._session.refresh(user)
        except IntegrityError as e:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error: " + str(e))
        
        return user

    async def top_up_account(self, user_id: int, amount: Decimal) -> Account:
        result = await self._session.execute(select(Account).where(Account.user_id == user_id))
        account = result.scalar_one_or_none()
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")
        
        account.balance += amount
        account.last_topup_at = datetime.utcnow()
        
        try:
            await self._session.commit()
            await self._session.refresh(account)
        except IntegrityError as e:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error: " + str(e))
        
        return account
    
    async def get_user_with_account(self, user_id: int) -> User:
        query = select(User).options(joinedload(User.account)).where(User.id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()