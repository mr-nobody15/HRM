import os
import boto3
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from app.routes.resume_routes import resume_parser
import asyncio
from io import BytesIO
from dotenv import load_dotenv
import logging
import requests
from typing import List, Dict
from fastapi import UploadFile, File

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# API Configuration
RECRUITPRO_API = "https://localhost:3002/resumes/getresumes"

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
S3_RESUME_FOLDER = "candidate-resumes"

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
    raise Exception("Failed to connect to S3")

async def fetch_resume_metadata() -> List[Dict]:
    """Fetch resume metadata from the local API."""
    try:
        print(RECRUITPRO_API, "RECRUITPRO_API")
        response = requests.get(RECRUITPRO_API, verify=False)
        print(response, "response")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching resume metadata: {str(e)}")
        raise Exception(f"Error fetching resume metadata: {str(e)}")

async def fetch_and_parse_resume(user_id: str, attachment: str, db: Session):
    """Fetch resume from S3 and parse it."""
    try:
        # Construct the full S3 key
        s3_key = f"{S3_RESUME_FOLDER}/{attachment}"
        
        # Check if file exists in S3
        try:
            s3_client.head_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise Exception(f"Resume not found in S3: {s3_key}")
            raise
        # Get the file from S3
        response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
        file_content = response['Body'].read()
        # Get file metadata
        content_type = response.get('ContentType', '')
        file_size = response.get('ContentLength', 0)
        
        logger.info(f"Retrieved file from S3: {s3_key} (Size: {file_size} bytes, Type: {content_type})")
        
        # Create a BytesIO object from the file content
        file_obj = BytesIO(file_content)
        
        # Determine file extension from content type
        file_ext = ''
        if content_type == 'application/pdf':
            file_ext = '.pdf'
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            file_ext = '.docx'
        
        # If no extension found in content type, try to get it from the filename
        if not file_ext and '.' in attachment:
            file_ext = os.path.splitext(attachment)[1].lower()
        
        if not file_ext:
            raise Exception(f"Could not determine file type for {attachment}")
        
        # Create filename with proper extension
        filename = f"{user_id}{file_ext}"
        
        # Create an UploadFile object with the correct content type
        upload_file = UploadFile(
            filename=filename,
            file=file_obj,
            headers={"content-type": content_type}
        )
        # Parse the resume
        resume_data = await resume_parser(filename=user_id, attachment=attachment, file=upload_file, db=db)
        return resume_data
    except ClientError as e:
        logger.error(f"S3 error for user {user_id}: {str(e)}")
        raise Exception(f"S3 error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing resume for user {user_id}: {str(e)}")
        raise Exception(f"Error processing resume: {str(e)}")

async def sync_resumes_service(db: Session) -> List[Dict]:
    """
    Service function to sync resumes from local API and S3.
    Returns a list of results for each processed resume.
    """
    try:
        # Fetch resume metadata from local API
        resume_metadata = await fetch_resume_metadata()
        
        results = []
        for resume in resume_metadata:
            try:
                user_id = resume.get("userId")
                attachment = resume.get("attachments")
                
                if not user_id or not attachment:
                    logger.warning(f"Skipping invalid resume metadata: {resume}")
                    continue
                
                # Process the resume
                result = await fetch_and_parse_resume(user_id, attachment, db)
                results.append({
                    "userId": user_id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                logger.error(f"Error processing resume for user {user_id}: {str(e)}")
                results.append({
                    "userId": user_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    except Exception as e:
        logger.error(f"Error in sync_resumes_service: {str(e)}")
        raise