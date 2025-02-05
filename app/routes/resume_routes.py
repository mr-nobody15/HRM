from fastapi import APIRouter
from app.service import resume 
from sqlalchemy.orm import Session
from fastapi import Depends
from app.utils.database import get_db
from PyPDF2 import PdfReader
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from app.variables.variables import Resume
from langchain_core.prompts import PromptTemplate
from fastapi import File, UploadFile
from langchain_core.output_parsers import StrOutputParser


router = APIRouter(
    prefix="/resume",
    tags=["resume"]
)

@router.get("/")
def read_root():
    return {"message": "Welcome to My FastAPI App resume!"}

@router.post("/add_resume")
def add_resume(db:Session = Depends(get_db)):
    return resume.add_resume(db=db)


@router.get("/get_resume")
def get_resume(db:Session = Depends(get_db)):
    return resume.get_resume(db=db)

def load_pdf(file):
    reader = PdfReader(file)
    text = ''.join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

def from_text_to_dict(text):
    """Convert the Text to a dictionary using Google Generative AI"""
    parser = PydanticOutputParser(pydantic_object=Resume)
    # Create the PromptTemplate
    format_instructions = parser.get_format_instructions()
    prompt_template = """
Convert the following resume text into a structured JSON object with the following fields:
    - "name": The name of the person.
    - "email": The email address.
    - "skills": A list of skills mentioned.
    - "education": A list of educational qualifications.
    - "projects": A list of projects mentioned.
    - "phone": The phone number (if available).

sample_Output = {{
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "skills": "Python,SQL,FastAPI,Docker,Machine Learning",
        "experiences": [
            {{"company": "TechCorp", "role": "Software Engineer", "years": 3, "description": "Developed backend APIs using FastAPI."}},
            {{"company": "DataInc", "role": "Data Scientist", "years": 2, "description": "Worked on predictive models using Python and TensorFlow."}}
        ],
        "education": [
            {{"institution": "XYZ University", "degree": "Bachelors in Computer Science", "year": 2018}}
        ],
        "projects": "Personal Blog, AI-driven Recommendation System , AI-driven Chatbot"
        }}
    

Resume Text:
{text}

Please return the result as a valid JSON object without any additional explanation. Example output:
Only use details from the document. Do not generate any additional information.
{format_instructions}
if there is no experience then  include it in the json object as an empty list
"""

    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"], partial_variables={"format_instructions": format_instructions})
    chain = prompt | llm | parser
    result = chain.invoke({"text": text})

    return result


@router.post("/resume_parser")
async def resume_parser(file:UploadFile = File(...),db:Session = Depends(get_db)):
    await file.seek(0)
    text = load_pdf(file.file)
    resume_data = from_text_to_dict(text)
    print(resume_data , "resume_data")
    resume.add_resume(resume_data,db=db)
    return {"message":"Resume added successfully","resume":resume_data}


def resume_analysis(resume):
    
    prompt_template = """
You are an AI Assistant designed to evaluate resumes and provide actionable insights. Your task is to analyze the given resume and generate a structured assessment with the following outputs:

1. Overall Score (0-100): A total score based on the resumes quality, broken down into:
   - Skills (35 points)  Relevance and depth of skills.
   - Experience (35 points)  Relevance, diversity, and impact of work experience.
   - Education (25 points)  Alignment with the job role and relevant qualifications.
   - Clarity & Presentation (5 points)  Readability, formatting, and structure.

2. Key Strengths: Highlight the strongest aspects of the resume.

3. Areas for Improvement: Identify gaps or weaknesses and suggest enhancements.

4. Detailed Analysis: Provide insights into the following categories:
   - Relevance of Skills: Alignment with the job role; identify any skill gaps.
   - Experience: Depth, relevance, and quantifiable impact of work history.
   - Education: Strength of academic background, certifications, and relevance.
   - Projects: Complexity, real-world applicability, and outcomes.
   - Achievements: Significance of awards, recognitions, and milestones.
   - Formatting & Readability: Structure, grammar, and clarity.
   - Growth Trajectory: Evidence of career progression and continuous learning.
   - Network Presence: Professional links (GitHub, LinkedIn, portfolio) and their relevance.

5. Actionable Suggestions:
   - Skill & Certification Recommendations: Suggest relevant skills or certifications to acquire.
   - Resume Improvements: Recommend formatting or content refinements for clarity and professionalism.
   - Quantification of Achievements: Suggest ways to enhance impact through measurable contributions.

Input Format:
Provide the resume as a structured JSON object in the following format:
{{
  "name": "John Doe",
  "email": "johndoe@example.com",
  "skills": ["Python", "SQL", "Machine Learning"],
  "experiences": [
    {{
      "role": "Data Scientist",
      "years": 3,
      "company": "TechCorp",
      "description": "Built predictive models improving sales forecasting accuracy by 25%."
    }},
    {{
      "role": "Data Analyst",
      "years": 2,
      "company": "DataSolutions",
      "description": "Analyzed large datasets to generate insights, contributing to marketing strategy improvements."
    }}
  ],
  "education": [
    {{
      "degree": "B.Sc. in Computer Science",
      "institution": "Top University",
      "year": 2018
    }}
  ],
  "projects": [
    {{
      "title": "Customer Churn Prediction",
      "description": "Developed a machine learning model to predict customer churn with 85 accuracy.",
      "tools": ["Python", "Scikit-learn", "Pandas"]
    }}
  ]
}}

Output Format:
Return the result as a structured JSON object with no additional explanation:
{{
  "overall_score": 85,
  "key_strengths": [
    "Strong skills in Python, SQL, and Machine Learning.",
    "Relevant work experience as a Data Scientist and Data Analyst.",
    "Completed a project on Customer Churn Prediction with high accuracy.",
    "Holds a B.Sc. in Computer Science from a reputable institution."
  ],
  "areas_of_improvement": [
    "Clarity and Presentation: The resume could benefit from a more structured format and improved readability."
  ],
  "detailed_analysis": {{
    "relevance_of_skills": "The listed skills align well with the job role in data science. Consider adding more specialized skills related to the specific job requirements.",
    "experience": "The candidate's work experience as a Data Scientist and Data Analyst demonstrates relevant skills and achievements. It would be beneficial to quantify more achievements and provide more details on responsibilities.",
    "education": "The B.Sc. in Computer Science from a top university is a strong qualification. Consider adding any relevant certifications or courses to enhance the educational background."
  }},
  "suggestions": [
    "Acquire certifications in advanced machine learning techniques or data visualization tools to enhance skill depth.",
    "Improve resume formatting for better readability and structure.",
    "Quantify achievements and contributions in work experience and projects to showcase impact."
  ]
}}
Ensure the analysis is concise, insightful, and actionable.

Resume:
{resume}
"""
    llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")
    prompt = PromptTemplate(template=prompt_template, input_variables=["resume"])
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"resume": resume})
    print(result)
    return result


class ResumeAnalysis(BaseModel):
    resume_id:int



@router.post("/resume_analysis")
def resume_analysis_route(resume_id:ResumeAnalysis,db:Session = Depends(get_db)):
    resume_data =  resume.get_resume_by_id(db=db,resume_id=resume_id.resume_id)
    data = resume_analysis(resume_data)

    return {"analysis":data,"resume":resume_data}









