from sqlalchemy.orm import Session
from fastapi import Depends
from app.utils.database import get_db
from fastapi import APIRouter

from fastapi import HTTPException
from app.variables.variables import Analysis
from app.service.analysisService import analysis_service

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"]
)

@router.post("/")
async def analysis(analysis: Analysis, db: Session = Depends(get_db)):
    try:
        return await analysis_service(analysis, db)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





