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
    try:
        list_of_jobs = []

        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
            
        for job in data:
            # Handle both dictionary and object-style access
            if isinstance(job, dict):
                job_id = job.get("jobId") or job.get("id")
                if not job_id:
                    print(f"Warning: Job entry missing ID: {job}")
                    continue
                list_of_jobs.append(str(job_id))
            else:
                job_id = getattr(job, "jobId", None) or getattr(job, "id", None)
                if not job_id:
                    print(f"Warning: Job entry missing ID: {job}")
                    continue
                list_of_jobs.append(str(job_id))
                
        print(list_of_jobs, "list_of_jobs")
        # Delete existing jobs with matching IDs
        if list_of_jobs:
            db.query(models.Job_details).filter(models.Job_details.jobId.in_(list_of_jobs)).delete(synchronize_session=False)
        
        print(data[0].keys() , "data")
        # Add new jobs
        for job in data:
            try:
                if isinstance(job, dict):
                    new_job = models.Job_details(
                        jobId=str(job.get("jobId") or job.get("id")),
                        tenant_id=str(job.get("tenantId")),  # Directly use tenantId from the API response
                        job_title=str(job.get("title") or job.get("job_title")),
                        job_description=str(job.get("description") or job.get("job_description") or job.get("plainText")),  # Added plainText as fallback
                        skills=str(job.get("skills") or job.get("secondarySkills"))  # Added secondarySkills as fallback
                    )
                else:
                    new_job = models.Job_details(
                        jobId=str(getattr(job, "jobId", None) or getattr(job, "id", None)),
                        tenant_id=str(getattr(job, "tenantId", None)),  # Directly use tenantId from the API response
                        job_title=str(getattr(job, "title", None) or getattr(job, "job_title", None)),
                        job_description=str(getattr(job, "description", None) or getattr(job, "job_description", None) or getattr(job, "plainText", None)),
                        skills=str(getattr(job, "skills", None) or getattr(job, "secondarySkills", None))
                    )
                db.add(new_job)
            except Exception as e:
                print(f"Error processing job entry: {job}, Error: {str(e)}")
                continue

        db.commit()
        return {"message": "Job data synced successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error in sync_job_data: {str(e)}")
        raise