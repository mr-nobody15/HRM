from app.data import data
from app.models import models
from app.utils.database import get_db
from sqlalchemy.orm import Session


def add_job(db:Session ,data):
    print(data,"data")
    for job in data:
        new_job = models.Job_details(
            jobId=job.jobId,
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
    return db.query(models.Job_details).filter(models.Job_details.jobId == job_id).first()