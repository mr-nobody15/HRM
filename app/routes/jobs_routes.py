from fastapi import APIRouter
from app.service import jobs , resume
from sqlalchemy.orm import Session
from fastapi import Depends
from app.utils.database import get_db
from fastapi import Query
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
import time
from typing import List
import os
import json
import requests
from app.service.jobs import sync_job_data

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.get("/")
def read_root():
    return {"message": "Welcome to My FastAPI App jobs!"}


class Job(BaseModel):
    """
    Job model for adding job
    """ 
    jobId: str 
    job_title: str
    job_description: str
    skills: str

@router.post("/add_job")
def add_job(data:List[Job], db: Session = Depends(get_db)):  # Accepts list of jobs
    return jobs.add_job(db=db, data=data)

@router.get("/get_job")
def get_job(db:Session = Depends(get_db)):
    return jobs.get_job(db=db)

@router.get("/get_job_by_id")
def get_job_by_id(db:Session = Depends(get_db),job_id:int = Query(...)):
    return jobs.get_job_by_id(db=db,job_id=job_id)



Application_Tracking_Prompt = f"""
    Act as an advanced Applicant Tracking System (ATS) specialized in evaluating resumes for tech roles, particularly Data Science, Machine Learning, and Data Analytics. Analyze the given resume against the provided job description and generate a structured evaluation focusing on key hiring criteria.

 Deliverables:
1. Match Percentage: Calculate a precise match score (%) between the resume and job description based on skills, experience, and role-specific keywords.
2. Missing Keywords: Identify crucial technical and domain-specific keywords missing from the resume that are essential for the job.
3. Key Strengths: Identify the key strengths of the candidate based on the resume and job description in skills .
4. Candidate Profile Summary: Provide a concise summary highlighting relevant strengths and key gaps in alignment with the job.
5. Experience:  Years of experience in the field.
6. projects: list of projects from the resume.
7. Improvement Suggestions: Offer specific recommendations to enhance the candidates competitiveness in the job market, focusing on:
   - Technical Expertise: Proficiency in Python, R, SQL, machine learning frameworks, and statistical methods.
   - Domain Knowledge: Understanding of industry-specific applications, such as finance, healthcare, or e-commerce.
   - Certifications & Courses: Suggested certifications (e.g., AWS, TensorFlow, Google Data Analytics) to boost credibility.
   - Projects & Achievements: Enhancing project descriptions with quantifiable outcomes.
   - Resume Optimization: Structural or content improvements to increase ATS-friendliness.
   - Education: Highest degree and field of study.
 Input:
- Resume:{{text}}
- Job Description: {{jd}}

 Expected Output:
{{format_instructions}}

Ensure that the analysis is data-driven, actionable, and concise, focusing on improving job match accuracy and candidate positioning in a competitive hiring landscape.
    """

def match_job_resume(data):
    resumes = data["resumes"]
    jobs = data["jobs"]
    job_resume_match = []
    for job in jobs:
        for resume in resumes:
            job_resume_match.append({
                "job":{
                    "id":job["jobId"],
                    "title":job["job_title"],
                    "plainText":job["job_description"],
                    "skills":job["skills"]
                },
                "resume":{
                    "id":resume["id"],
                    "name":resume["name"],
                    "skills":resume["skills"],
                    "experiences":resume["experiences"] or [],
                    "education":resume["education"] or [],
                    "projects":resume["projects"] or []
                },
            })
    return job_resume_match

class format_instructions_for_output(BaseModel):
    percentage_match:int
    missing_keywords:list
    key_strengths:list
    Profile_Summary:str
    experience:int
    education:str
    projects: list
    Suggestions_for_improvement:str

@router.post("/analyze-resumes")
async def analyze_resumes(data:dict,db:Session = Depends(get_db)):
    start_time = time.time()
    job_resume_match = match_job_resume(data)
    parser = PydanticOutputParser(pydantic_object=format_instructions_for_output)
    format_instructions = parser.get_format_instructions()
    print(format_instructions , "format instructions")
    llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPENAI_API_KEY"))
    job_resume_match_result = []
    for job_resume in job_resume_match:
        formatted_prompt = Application_Tracking_Prompt.format(text=job_resume["resume"],jd=job_resume["job"],format_instructions=format_instructions)
        response = llm.invoke(formatted_prompt)
        print(response.content,"-----------response----------")
        response_json = json.loads(response.content)
        job_resume_match_result.append(response_json)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return  {"analysis":job_resume_match_result,"job_resume_match":job_resume_match}


class format_instructions_for_output_by_id(BaseModel):
    percentage_match:int
    missing_keywords:list
    Profile_Summary:str


@router.post("/analyze-by-id")
async def analyze_by_id(data:dict,db:Session = Depends(get_db)):
    start_time = time.time()
    resume_data = resume.get_resume_by_user_id(db=db,user_id=data["userId"])
    job_data = jobs.get_job_by_id(db=db,job_id=data["jobId"])
    data = {
        "resumes":[resume_data],
        "jobs":[job_data]
    }
    print(data , "data")
    parser = PydanticOutputParser(pydantic_object=format_instructions_for_output_by_id)
    format_instructions = parser.get_format_instructions()
    print(format_instructions , "format instructions")
    llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPENAI_API_KEY"))
    formatted_prompt = Application_Tracking_Prompt.format(text=data["resumes"][0],jd=data["jobs"][0],format_instructions=format_instructions)
    response = llm.invoke(formatted_prompt)
    print(response.content,"-----------response----------")
    response_json = json.loads(response.content)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return  {"analysis":response_json}


## Cron Job for sync the data from recruitpro  Job data to the database

@router.post("/sync_job_data")
def sync_job_data_from_recruitpro(db:Session = Depends(get_db)):
    url = f"{os.getenv('RECRUITPRO_API_KEY')}/jobs/all"
    response = requests.get(url ,verify=False)
    print(response.json())
    result = response.json()
    result_add = sync_job_data(result , db=db)
    return result_add




# @router.post("/add_resume_Analysis")
# async def add_resume_Analysis(data:dict,db:Session = Depends(get_db)):
