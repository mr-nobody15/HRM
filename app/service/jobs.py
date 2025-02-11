from app.data import data
from app.models import models
from app.utils.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from pydantic import BaseModel
from typing import List

class Job(BaseModel):
    """
    Job model for adding job
    """
    id: str  # Change int to str since jobId is a string
    job_title: str
    job_description: str
    skills: str

def add_job(db:Session ,data:List[Job]):
    for job in data:
        new_job = models.Job_details(
            id=job.id,
            job_title=job.job_title,
            job_description=job.job_description,
            skills=job.skills
        )
        db.add(new_job)
    db.commit()
    return {"message": "Job added successfully"}


def get_job(db:Session):
    return db.query(models.Job_details).all()

def get_job_by_id(db:Session,job_id:int):
    return db.query(models.Job_details).filter(models.Job_details.id == job_id).first()