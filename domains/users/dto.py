from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import Optional
from decimal import Decimal

class UserSignUpDTO(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    bio: Optional[str] = None
    profile_picture: Optional[HttpUrl] = None

class UserLoginDTO(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfileDTO(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    bio: Optional[str] = None
    profile_picture: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: datetime

class AccountDTO(BaseModel):
    id: int
    user_id: int
    balance: Decimal
    last_topup_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class UserWithAccountDTO(UserProfileDTO):
    account: AccountDTO

class TopUpDTO(BaseModel):
    amount: Decimal

class TopUpResponseDTO(BaseModel):
    message: str
    new_balance: Decimal
    amount: Decimal  # 추가된 필드