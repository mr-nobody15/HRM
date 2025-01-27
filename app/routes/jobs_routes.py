from fastapi import APIRouter
from app.service import jobs
from sqlalchemy.orm import Session
from fastapi import Depends
from app.utils.database import get_db
from fastapi import Query

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.get("/")
def read_root():
    return {"message": "Welcome to My FastAPI App jobs!"}

@router.post("/add_job")
def add_job(db:Session = Depends(get_db)):
    return jobs.add_job(db=db)

@router.get("/get_job")
def get_job(db:Session = Depends(get_db)):
    return jobs.get_job(db=db)

@router.get("/get_job_by_id")
def get_job_by_id(db:Session = Depends(get_db),job_id:int = Query(...)):
    return jobs.get_job_by_id(db=db,job_id=job_id)
