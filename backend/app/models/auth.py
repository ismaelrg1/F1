from uuid import UUID

from pydantic import BaseModel

class UserSummary(BaseModel):
    id: int
    public_id: UUID
    username: str


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
    password: str


class RegisterGoogleRequest(BaseModel):
    id_token: str


class RegisterResponse(BaseModel):
    msg: str
    user: UserSummary


class PasswordForgotRequest(BaseModel):
    username: str

class PasswordForgotResponse(BaseModel):
    msg: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class PasswordResetResponse(BaseModel):
    msg: str
