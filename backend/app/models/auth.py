from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSummary(BaseModel):
    id: int
    public_id: UUID
    username: str
    email: str


class LoginLocalRequest(BaseModel):
    username: str
    password: str


class LoginGoogleRequest(BaseModel):
    id_token: str


class LoginResponse(BaseModel):
    msg: str
    user: UserSummary


class RegisterLocalRequest(BaseModel):
    username: str
    email: str
    password: str


class RegisterGoogleRequest(BaseModel):
    id_token: str


class RegisterResponse(BaseModel):
    msg: str
    user: UserSummary


class PasswordForgotRequest(BaseModel):
    email: EmailStr

class PasswordForgotResponse(BaseModel):
    msg: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class PasswordResetResponse(BaseModel):
    msg: str
