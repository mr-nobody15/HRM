from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional

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
    projects:  List[Project] 
    
    
class AnalyzeRequest(BaseModel):
    user_id: str
    job_id: str


class Analysis(BaseModel):
    user_id:str
    job_id:str
    file_name:str
    isExisting:Optional[bool] = False
