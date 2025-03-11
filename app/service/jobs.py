from app.data import data
from app.models import models
from app.utils.database import get_db
from sqlalchemy.orm import Session


def add_job(db:Session,data):
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

def sync_job_data(data:dict,db:Session):
    list_of_jobs = []
    print(data["data"] , "data")
    for job in data["data"]:
        list_of_jobs.append(job["jobId"])
    print(list_of_jobs , "list_of_jobs")
    db.query(models.Job_details).filter(models.Job_details.jobId.in_(list_of_jobs)).delete(synchronize_session=False)
    skills = data["skills"]
    for job in data["data"]:
        combined_skills = f"{job['skills']},{job['secondarySkills']}"
        skill_ids = [
            int(skill_id) for skill_id in combined_skills.split(",") if skill_id.strip().isdigit()
        ]
        matched_skills = [skill["label"] for skill in skills if skill["id"] in skill_ids]
        new_job = models.Job_details(
            jobId=job["jobId"],
            job_title=job["title"],
            job_description=job["description"],
            skills=",".join(matched_skills)  # Convert list to comma-separated string
        )
        db.add(new_job)

    db.commit()
    return {"message": "Job data synced successfully"}