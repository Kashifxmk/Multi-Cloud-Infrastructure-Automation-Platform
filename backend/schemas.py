from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    terms_accepted: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordRequest(BaseModel):
    email: EmailStr


class TokenRequest(BaseModel):
    token: str = Field(min_length=16)


class PasswordResetConfirmRequest(TokenRequest):
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    is_verified: bool
    is_admin: bool
