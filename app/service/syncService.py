import os
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.routes.resume_routes import resume_parser
from app.service.resume import add_resume 
import asyncio
from io import BytesIO
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Initialize S3 client with error handling
try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    # Test the connection
    s3_client.head_bucket(Bucket=AWS_BUCKET_NAME)
    logger.info(f"Successfully connected to S3 bucket: {AWS_BUCKET_NAME}")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        logger.error(f"Bucket {AWS_BUCKET_NAME} does not exist")
    elif error_code == '403':
        logger.error(f"Access denied to bucket {AWS_BUCKET_NAME}")
    else:
        logger.error(f"Error connecting to S3: {str(e)}")
    raise HTTPException(status_code=500, detail="Failed to connect to S3")

async def fetch_and_parse_resume(user_id: str, attachment_key: str, db: Session):
    """Fetch resume from S3 and parse it."""
    try:
        # Check if file exists in S3
        try:
            s3_client.head_object(Bucket=AWS_BUCKET_NAME, Key=attachment_key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise HTTPException(status_code=404, detail=f"Resume not found in S3: {attachment_key}")
            raise

        # Get the file from S3
        response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=attachment_key)
        file_content = response['Body'].read()
        
        # Get file metadata
        content_type = response.get('ContentType', '')
        file_size = response.get('ContentLength', 0)
        
        logger.info(f"Retrieved file from S3: {attachment_key} (Size: {file_size} bytes, Type: {content_type})")
        
        # Create a BytesIO object from the file content
        file_obj = BytesIO(file_content)
        file_obj.name = attachment_key.split('/')[-1]  # Set filename for parser
        
        # Parse the resume
        resume_data = await resume_parser(user_id, file_obj, db)
        return resume_data
    except ClientError as e:
        logger.error(f"S3 error for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing resume for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    
@router.post("/sync-resumes")
async def sync_resumes(resume_data: dict, db: Session = Depends(get_db)):
    """
    Sync resumes from S3.
    Expected input format:
    {
        "user_id": "user123",
        "attachment_key": "resumes/user123/resume.pdf"
    }
    """
    try:
        user_id = resume_data.get("user_id")
        attachment_key = resume_data.get("attachment_key")
        
        if not user_id or not attachment_key:
            raise HTTPException(status_code=400, detail="Missing user_id or attachment_key")
        
        # Process the resume
        result = await fetch_and_parse_resume(user_id, attachment_key, db)
        
        return {
            "message": "Resume synced and parsed successfully",
            "user_id": user_id,
            "result": result
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in sync_resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error syncing resume: {str(e)}")