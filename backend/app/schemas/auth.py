from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: int
    username: str
    email: str | None
    role: str
    message: str = "Login successful"


class SetupStatusResponse(BaseModel):
    setup_required: bool
    top_admin_exists: bool


class TopAdminSetupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: str | None = Field(default=None, max_length=120)
