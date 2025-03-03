from sqlalchemy import Column,Integer,String,Boolean, ForeignKey,JSON,Text
from sqlalchemy.orm import relationship
from app.utils.database import Base


class Resume(Base):
    __tablename__ = "resume"

    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(String(255),index=True)
    name = Column(String(255),index=True)
    email = Column(String(255),index=True)
    skills = Column(Text)
    experiences = Column(JSON)
    education = Column(JSON)
    projects = Column(JSON)

    def __repr__(self):
        return f"Resume(id={self.id}, user_id={self.user_id}, name={self.name}, email={self.email}, skills={self.skills}, experiences={self.experiences}, education={self.education}, projects={self.projects})"

class Job_details(Base):
    __tablename__ = "job_details"
    jobId = Column(String(255),primary_key=True,index=True)
    job_title = Column(String(255))
    job_description = Column(Text)
    skills = Column(Text)

    def __repr__(self):
        return f"Job_details(jobId={self.jobId}, job_title={self.job_title}, job_description={self.job_description}, skills={self.skills})"




# class resume_analysis(Base):
#     __tablename__ = "resume_analysis"
#     id = Column(Integer,primary_key=True,index=True)
#     resume_id = Column(Integer,ForeignKey("resume.id"))
#     score = Column(Integer,index=True)
#     analysis = Column(Text,index=True)
    
