from app.data import data
from app.models import models
from app.utils.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import datetime

# def add_resume(db:Session):
#     for resume in data.sample_Resume_data:
#         new_resume = models.Resume(
#             id=resume["id"],
#             name=resume["name"],
#             email=resume["email"],
#             skills=resume["skills"],
#             experiences=resume["experiences"],
#             education=resume["education"],
#             projects=resume["projects"]
#         )
#         db.add(new_resume)
#     db.commit()


def get_resume(db:Session):
    return db.query(models.Resume).all()

def get_resume_by_id(db:Session,resume_id:int):
    return db.query(models.Resume).filter(models.Resume.id == resume_id).first()


def add_resume(resume_data: dict, user_id: str, attachment:str, db: Session):
    try:
        # Check if resume already exists for this user
        existing_resume = db.query(models.Resume).filter(models.Resume.user_id == user_id).first()
        
        if existing_resume:
            # Update existing resume
            existing_resume.name = resume_data.name
            existing_resume.email = resume_data.email
            existing_resume.skills = resume_data.skills
            existing_resume.experiences = [exp.dict() for exp in resume_data.experiences]
            existing_resume.education = [edu.dict() for edu in resume_data.education]
            existing_resume.projects = [project.dict() for project in resume_data.projects]
            existing_resume.file_name = attachment
            existing_resume.updated_at = datetime.now()
            db.commit()
            return existing_resume
        else:
            # Get the maximum ID and increment by 1
            max_id = db.query(models.Resume).order_by(models.Resume.id.desc()).first()
            new_id = 1 if max_id is None else max_id.id + 1
            
            # Create new resume record
            new_resume = models.Resume(
                id=new_id,
                user_id=user_id,
                name=resume_data.name,
                email=resume_data.email,
                skills=resume_data.skills,
                experiences=[exp.dict() for exp in resume_data.experiences],
                education=[edu.dict() for edu in resume_data.education],
                projects=[project.dict() for project in resume_data.projects],
                file_name=attachment,
                updated_at=datetime.now()
            )
            
            # Add new resume
            db.add(new_resume)
            db.commit()
            return new_resume
    except Exception as e:
        db.rollback()
        raise Exception(f"Error adding resume: {str(e)}")


def get_resume_by_user_id(db:Session,user_id:str):
    resume_data = db.query(models.Resume).filter(models.Resume.user_id == user_id).first()
    print(resume_data , "resume_data")
    return resume_data



