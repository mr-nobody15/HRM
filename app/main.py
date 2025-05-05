from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.utils.database import engine 
from app.models import models
from dotenv import load_dotenv
import os
from sqlalchemy import text
from app.routes.resume_routes import router as resume_router
from app.routes.jobs_routes import router as jobs_router
from app.routes.sync_routes import router as sync_router
from app.routes.analysis_route import router as analysis_router
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import tiktoken
from pydantic import BaseModel
import schedule
import time
import requests
import threading




load_dotenv()

# Initialize model from LangChain
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

model = ChatOpenAI(model="gpt-3.5-turbo",api_key=os.getenv("OPENAI_API_KEY"))
parser = StrOutputParser()

app = FastAPI(title="My FastAPI App", version="1.0.0")

app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(sync_router)
app.include_router(analysis_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to My FastAPI App!"}


def generate_query_from_question(question):
    """
    Generate SQL query dynamically based on a general question.
    This function will return a single SQL query for a general question based on the provided schema.
    """
    prompt = ChatPromptTemplate.from_template("""
    Generate a SQL query to retrieve specific information from the database.

    The database schema includes a table:
    - `resume`: Contains user details (id,name,email, skills, experience, education,projects).
                                              
    The `skills` column contains a comma-separated list of skills, and you should:
    1. Search for complete words, not substrings (e.g., "Java" should not match "JavaScript").
    2. Handle cases where skills may have spaces after commas (e.g., "Python, Java" should be treated as separate skills).
    3. Write the query to match **exactly** the skill or other field in the question.
    4. Avoid partial matching.
                                              
    sample query:
    question: "give me the resume of the person who has java in skills"
    query: "SELECT *  FROM resume WHERE CONCAT(',', REPLACE(skills, ' ', ''), ',') LIKE '%,java,%';"
                                              
    sample questions : "give me suitable candidates job id 1" ,
                        "give me the candidates suitable for job id 1",
                        "candidates for job id 1 ",
                        "suitable candidates for job id 1",
    query: "SELECT 
            r.id AS resume_id,
            r.name AS resume_name,
            r.skills AS resume_skills,
            jd.skills AS job_skills,
            (
                SELECT COUNT(*) 
                FROM (
                    SELECT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(jd.skills, ',', numbers.n), ',', -1)) AS skill
                    FROM (
                        SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
                    ) numbers
                    WHERE n <= 1 + LENGTH(jd.skills) - LENGTH(REPLACE(jd.skills, ',', ''))
                ) job_skills_table
                WHERE FIND_IN_SET(skill, REPLACE(r.skills, ' ', ''))
            ) AS matched_skills_count
        FROM 
            resume r
        CROSS JOIN 
            job_details jd
        WHERE 
            jd.id = 1
        HAVING 
            matched_skills_count > 0
        ORDER BY 
            matched_skills_count DESC 
        LIMIT 10;
    "                                     
    The question is:
    "{question}"
    Please write an SQL query that retrieves the required information based on the provided schema, using **exact matching** in the `skills` column and handling commas and spaces properly.
    The SQL query should be in plain text with no markdown formatting.Check for substrings and not to consider unless entire word is present.
    """)
    chain = prompt | model | parser
    # Invoke the chain with the provided question and enhanced prompt
    query = chain.invoke({"question": question, "prompt": prompt})
    token = encoding.encode(str(prompt))
    print("token length *************",len(token))
    return query


import json
def check_query(query):
    print(query,"query")
    try:
# Execute the query directly with engine.connect()
        with engine.connect() as connection:
            result = connection.execute(query)
        # Check if we get a valid result and it's iterable
            rows = result.fetchall()
            print(rows,"rows")
            print("--------------------------------")
            result_list = []
            for row in rows:
                row_dict = dict(row._mapping)  # Convert row to dictionary
                # Deserialize JSON fields
                if "experiences" in row_dict:
                    row_dict["experiences"] = json.loads(row_dict["experiences"])
                if "education" in row_dict:
                    row_dict["education"] = json.loads(row_dict["education"])
                result_list.append(row_dict)
            return result_list

    except Exception as e:
        print(f"Error executing query: {e}")
        return "Error"
    
class QueryRequest(BaseModel):
    question: str
@app.post("/query")
def query(query_request:QueryRequest):
    query = generate_query_from_question(query_request.question)
    print(query)
    result = check_query(text(query))
    print(result)
    return result

API_URL = os.environ.get("API_URL") + "/jobs/sync_job_data"
def sync_job_data():
    try:
        response = requests.post(API_URL, verify=False)
        print(f"Sync Response: {response}, {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

# Schedule job to run every 3 hours
schedule.every(3).hours.do(sync_job_data)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Start scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)