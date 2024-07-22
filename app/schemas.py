from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str
    
class ExpenseCategory(BaseModel):
    expense: str