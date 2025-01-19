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

sample_resume = {{
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
    print(resume_data)
    resume.add_resume(resume_data,db=db)
    return resume_data
    return {"message":"Resume added successfully","resume":resume_data}


def resume_analysis(resume):
    
    prompt_template = """
Heres a prompt for an LLM to analyze resumes based on the factors discussed, ensuring detailed insights and actionable feedback:

Prompt for LLM: Resume Analysis

You are an AI model designed to evaluate resumes and provide insights. Your task is to analyze the provided resume and generate the following outputs:
	1.	Overall Score: A score out of 100 that reflects the quality of the resume.
	2.	Key Strengths: Highlight the strengths of the resume.
	3.	Areas of Improvement: Identify areas where the resume can be improved.
	4.	Detailed Analysis: Provide an in-depth evaluation of the following categories:
	•	Relevance of Skills: How well do the listed skills align with the given job role or industry? Are there any notable gaps?
	•	Experience: Evaluate the candidates work experience for relevance, diversity, and depth. Mention the roles, responsibilities, and any quantifiable achievements.
	•	Education: Assess the educational background, including degrees, certifications, and institution reputation.
	•	Projects: Review the listed projects for complexity, relevance, and outcomes. Highlight key contributions.
	•	Achievements: Analyze awards, recognitions, or notable accomplishments for their significance.
	•	Formatting and Readability: Assess the structure, formatting, grammar, and overall presentation of the resume.
	•	Growth Trajectory: Evaluate evidence of career progression, promotions, or continuous learning.
	•	Network Presence: Check for the presence of professional links (e.g., GitHub, LinkedIn, portfolios) and their relevance.
	5.	Suggestions:
	•	List skills or certifications that the candidate should consider acquiring.
	•	Recommend formatting or content changes to enhance clarity and professionalism.
	•	Suggest ways to make achievements and contributions more quantifiable.

    Please score the following resume with a total score of 100, weighted as follows:
- 35 points for Skills (Relevance and depth of skills).
- 35 points for Experience (Relevance and depth of work experience).
- 25 points for Education (Alignment with the job and any relevant qualifications).
- 5 points for Clarity and Presentation (Ease of reading, structure, and formatting).

Break down the score into these four categories and provide detailed insights on how the candidate can improve in each area.


Input:
{resume}

Sample Input:
Provide the resume in the following format:

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
  ],
}}

Output:
Generate a detailed report including:
	•	Overall Score (0-100):
	•	Key Strengths:
	•	Areas of Improvement:
	•	Detailed Analysis:
	•	Relevance of Skills:
	•	Experience:
	•	Suggestions:

Make the analysis concise, insightful, and actionable.

 """
    


    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    prompt = PromptTemplate(template=prompt_template, input_variables=["resume"])
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"resume": resume})
    print(result)
    return result



@router.post("/resume_analysis")
def resume_analysis_route(resume_id:int,db:Session = Depends(get_db)):
    resume_data =  resume.get_resume_by_id(db=db,resume_id=resume_id)
    return resume_analysis(resume_data)









