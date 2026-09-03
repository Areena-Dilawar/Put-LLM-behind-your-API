import json

from fastapi import APIRouter, HTTPException

from llm.client import generate_response
from src.schemas import TriageRequest, TriageResult

router = APIRouter()


@router.post("/triage", response_model=TriageResult)
def triage(request: TriageRequest):
    raw_response = generate_response(request.text)

    try:
        return TriageResult.model_validate(json.loads(raw_response))
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Invalid LLM output",
        )