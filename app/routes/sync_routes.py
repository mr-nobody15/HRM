from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.service.syncService import sync_resumes_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sync",
    tags=["sync"]
)

@router.post("/resumes")
async def sync_resumes(db: Session = Depends(get_db)):
    """
    Sync resumes from local API and S3.
    This endpoint will:
    1. Fetch resume metadata from local API
    2. For each resume, fetch the file from S3 and parse it
    """
    try:
        results = await sync_resumes_service(db)
        return {
            "message": "Resume sync completed",
            "results": results
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in sync_resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error syncing resumes: {str(e)}") 