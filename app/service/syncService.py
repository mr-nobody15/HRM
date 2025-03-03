import os
import requests
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.routes.resume_routes import resume_parser
from app.service.resume import add_resume 
import asyncio

router = APIRouter()

RECRUITPRO_API = "https://localhost:3001/resume/getresumes"  # Update with actual API
RESUME_FOLDER = "resumes"

def download_zip():
    """Download resumes ZIP from RecruitPro API."""
    try:
        response = requests.get(RECRUITPRO_API, stream=True , verify=False)
        if response.status_code != 200:
            raise Exception("Failed to fetch resumes ZIP")

        zip_path = "resumes.zip"
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)

        return zip_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading ZIP: {str(e)}")

def extract_zip(zip_path):
    """Extract ZIP file."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(RESUME_FOLDER)
        os.remove(zip_path)  # Clean up ZIP after extraction
        return RESUME_FOLDER
    except zipfile.BadZipFile:
        raise HTTPException(status_code=500, detail="Invalid or corrupt ZIP file")

async def parse_and_store_resumes(db: Session):
    """Parse extracted resumes and store metadata in DB."""
    files = os.listdir(RESUME_FOLDER)
    for file in files:
        file_path = os.path.join(RESUME_FOLDER, file)
        # Read file bytes and pass to resume_parser API
        with open(file_path, "rb") as resume_file:
            print(resume_file.name , "resume_file")
            print(resume_file , "resume_file")
            resume_data = await resume_parser(resume_file,db)
            print(resume_data , "resume_data")  # Call existing parser
            # if resume_data:
            #     add_resume(resume_data,db)  # Store parsed resume in DB

@router.get("/sync-resumes")
def sync_resumes(db: Session = Depends(get_db)):
    """Fetch resumes from RecruitPro, extract, parse, and store."""
    # zip_path = download_zip()
    # extract_zip(zip_path)
    asyncio.run(parse_and_store_resumes(db))
    return {"message": "Resumes synced and parsed successfully"}