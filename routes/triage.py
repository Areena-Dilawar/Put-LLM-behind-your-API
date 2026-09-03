import json

from fastapi import APIRouter, HTTPException

from llm.client import generate_response
from prompts.triage import TRIAGE_PROMPT
from src.schemas import TriageRequest, TriageResult

router = APIRouter()


@router.post("/triage", response_model=TriageResult)
def triage(request: TriageRequest):
    prompt = TRIAGE_PROMPT.format(message=request.text)

    raw_response = generate_response(prompt)

    try:
        data = json.loads(raw_response)
        return TriageResult.model_validate(data)

    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Invalid LLM output",
        )