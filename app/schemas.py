from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    category_name: str
    seniority_name: str
    location_city: str | None = None


class UserSkillInput(BaseModel):
    skill_name: str
    skill_level: int = Field(default=1, ge=1, le=5)


class UserSkillsUpdateRequest(BaseModel):
    skills: list[UserSkillInput]


class UserProfileUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=100)
    category_name: str | None = None
    seniority_name: str | None = None
    location_city: str | None = None


class UserSkillLevelUpdateRequest(BaseModel):
    skill_level: int = Field(ge=1, le=5)