# This schema exists in user_service because get_current_user needs to return it
# and it needs to be defined locally within the user_service context.
from pydantic import BaseModel, EmailStr

class CurrentUser(BaseModel):
    username: str
    email: EmailStr
    id: str # ID field to match what Auth Service puts in the token