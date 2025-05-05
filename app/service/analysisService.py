from app.data import data
from app.models import models
from app.utils.database import get_db
from sqlalchemy.orm import Session
from app.variables.variables import Analysis
from fastapi import HTTPException
from app.service.syncService import fetch_and_parse_resume
from app.routes.jobs_routes import analyze_resumes
from app.variables.variables import AnalyzeRequest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analysis_service(analysis: Analysis, db: Session):
    try:
        # First try to get resume from database
        resume_data = db.query(models.Resume).filter(models.Resume.user_id == analysis.user_id).first()
        
        if analysis.isExisting:
            if not resume_data:
                raise HTTPException(status_code=404, detail=f"Resume not found for user {analysis.user_id}")
        else:
            # If resume not in database or no file name, try to sync from S3
            if not resume_data or not resume_data.file_name:
                try:
                    # Try to sync from S3
                    resume_data = await fetch_and_parse_resume(
                        user_id=analysis.user_id,
                        attachment=analysis.file_name,
                        db=db
                    )
                except Exception as s3_error:
                    logger.error(f"Error syncing from S3: {str(s3_error)}")
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Resume not found in database or S3 for user {analysis.user_id}"
                    )
            else:
                # If we have file name, try to sync from S3
                try:
                    resume_data = await fetch_and_parse_resume(
                        user_id=analysis.user_id,
                        attachment=resume_data.file_name,
                        db=db
                    )
                except Exception as s3_error:
                    logger.error(f"Error syncing from S3: {str(s3_error)}")
                    # If S3 sync fails but we have data in DB, continue with that
                    if not resume_data:
                        raise HTTPException(
                            status_code=404, 
                            detail=f"Resume not found in S3 for user {analysis.user_id}"
                        )
        
        # Create AnalyzeRequest object
        analyze_request = AnalyzeRequest(
            user_id=analysis.user_id,
            job_id=analysis.job_id
        )
        
        # Perform comprehensive resume analysis with job matching
        analysis_result = await analyze_resumes(analyze_request, db)
        
        return {
            "message": "Analysis completed successfully",
            "analysis": analysis_result
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in analysis_service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

