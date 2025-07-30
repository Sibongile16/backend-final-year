from pydantic import BaseModel

class TeacherResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
