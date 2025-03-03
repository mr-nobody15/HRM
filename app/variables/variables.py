from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any

class Experience(BaseModel):
    company: str
    role: str
    years: int
    description: str

class Education(BaseModel):
    institution: str
    degree: str
    year: int

class Project(BaseModel):
    name: str
    description: str

class Resume(BaseModel):
    id: int
    name: str
    email: EmailStr
    skills: str  # List of skills as strings
    experiences: List[Experience]  # json object
    education: List[Education]  # json object
    projects:  List[Project]  # list of projects