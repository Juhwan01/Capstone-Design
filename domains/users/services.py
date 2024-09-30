from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from domains.users.repositories import UserRepository
from .dto import *
from .models import User
from dependencies.database import get_db
from dependencies.config import get_config

config = get_config()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class UserService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repository = UserRepository(session)

    async def create_user(self, payload: UserSignUpDTO) -> User:
        hashed_password = self._hash_password(payload.password)
        payload.password = hashed_password
        return await self._repository.create_user(payload=payload)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = await self._repository.get_user_by_username(username)
        if not user or not self._verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=config.jwt_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.jwt_secret_key, algorithm=config.jwt_algorithm)
        return encoded_jwt

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = await self._repository.get_user_by_username(username)
        if user is None:
            raise credentials_exception
        return user

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def login(self, login_data: UserLoginDTO) -> Token:
        user = await self.authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = self.create_access_token(data={"sub": user.username})
        return Token(access_token=access_token, token_type="bearer")

    async def get_user_profile(self, user: User) -> UserWithAccountDTO:
        user_with_account = await self._repository.get_user_with_account(user.id)
        
        if not user_with_account or not user_with_account.account:
            raise HTTPException(status_code=404, detail="User or account not found")
        
        account_dto = AccountDTO(
            id=user_with_account.account.id,
            user_id=user_with_account.id,
            balance=user_with_account.account.balance,
            last_topup_at=user_with_account.account.last_topup_at,
            created_at=user_with_account.account.created_at,
            updated_at=user_with_account.account.updated_at
        )
        
        return UserWithAccountDTO(
            id=user_with_account.id,
            username=user_with_account.username,
            email=user_with_account.email,
            full_name=user_with_account.full_name,
            bio=user_with_account.bio,
            profile_picture=user_with_account.profile_picture,
            created_at=user_with_account.created_at,
            updated_at=user_with_account.updated_at,
            account=account_dto
        )

    async def update_user_profile(self, user_id: int, payload: UserProfileDTO) -> User:
        user = await self._repository.update_user(user_id, payload)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def top_up_account(self, user_id: int, top_up_data: TopUpDTO) -> TopUpResponseDTO:
        account = await self._repository.top_up_account(user_id, top_up_data.amount)
        return TopUpResponseDTO(
            message="Top up successful",
            new_balance=account.balance,
            amount=top_up_data.amount
        )

    async def get_current_active_user(self, current_user: User = Depends(get_current_user)):
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user