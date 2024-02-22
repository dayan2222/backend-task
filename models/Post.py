from pydantic import BaseModel, EmailStr

class Post(BaseModel):
    text: str