from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel

class UserRole(str, Enum):
    """User roles for RBAC"""
    FINANCE = "finance"
    MARKETING = "marketing"
    HR = "hr"
    ENGINEERING = "engineering"
    EXECUTIVE = "executive"
    EMPLOYEE = "employee"

class User(BaseModel):
    """User model"""
    username: str
    role: UserRole
    name: str
    email: str = ""

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    sources: List[Dict]
    role: str
    token_usage: Dict