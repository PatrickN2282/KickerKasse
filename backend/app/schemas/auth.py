from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    message: str = "Login successful"
