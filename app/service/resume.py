from app.data import data
from app.models import models
from app.utils.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

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


def add_resume(resume:models.Resume,db:Session):
    id = db.query(models.Resume).count() + 1
    new_resume = models.Resume(
            id=id,
            name=resume.name,
            email=resume.email,
            skills=resume.skills,
            experiences = [exp.dict() for exp in resume.experiences],  # Convert list of Experience objects to dicts
            education = [edu.dict() for edu in resume.education],
            projects=resume.projects
        )
    db.add(new_resume)
    db.commit()

