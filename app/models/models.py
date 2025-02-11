from sqlalchemy import Column,Integer,String,Boolean, ForeignKey,JSON,Text
from sqlalchemy.orm import relationship
from app.utils.database import Base


class Resume(Base):
    __tablename__ = "resume"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(255),index=True)
    email = Column(String(255),index=True)
    skills = Column(Text)
    experiences = Column(JSON)
    education = Column(JSON)
    projects = Column(Text)

class Job_details(Base):
    __tablename__ = "job_details"
    id = Column(Integer,primary_key=True,index=True)
    job_title = Column(String(255))
    job_description = Column(Text)
    skills = Column(Text)




# class resume_analysis(Base):
#     __tablename__ = "resume_analysis"
#     id = Column(Integer,primary_key=True,index=True)
#     resume_id = Column(Integer,ForeignKey("resume.id"))
#     score = Column(Integer,index=True)
#     analysis = Column(Text,index=True)
    
