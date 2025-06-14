from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6)

class UserLogin(BaseModel): 
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CurrentUser(BaseModel):
    username: str
    email: EmailStr
    id: str # Represents the ObjectId as a string