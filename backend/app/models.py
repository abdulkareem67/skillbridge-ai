from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    location: str = Field(default="Pakistan", max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be blank")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ManualSkillsRequest(BaseModel):
    skills: list[str] = Field(min_length=1, max_length=50)

    @field_validator("skills")
    @classmethod
    def skills_reasonable_length(cls, v: list[str]) -> list[str]:
        for s in v:
            if len(s) > 80:
                raise ValueError("Each skill must be 80 characters or fewer")
        return v


class TargetRoleRequest(BaseModel):
    role: str = Field(min_length=1, max_length=100)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ProgressUpdateRequest(BaseModel):
    skill_name: str = Field(min_length=1, max_length=80)
    status: str

    @field_validator("status")
    @classmethod
    def status_allowed(cls, v: str) -> str:
        allowed = {"not_started", "in_progress", "completed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v
