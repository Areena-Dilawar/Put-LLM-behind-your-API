import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from llm.client import generate_response
from prompts.triage import TRIAGE_PROMPT, TRIAGE_PROMPT_VERSION
from src.schemas import TriageRequest, TriageResult

router = APIRouter()


def parse_model_output(raw_response: str) -> TriageResult:
    cleaned = raw_response.strip()

    # Remove markdown code fences if the model added them.
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # Find the JSON object if the model added extra prose.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model output")

    json_text = cleaned[start:end + 1]
    data = json.loads(json_text)

    return TriageResult.model_validate(data)


def quarantine_output(
    input_text: str,
    raw_output: str,
    error: str,
) -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "input": input_text,
        "raw_output": raw_output,
        "error": error,
        "prompt_version": TRIAGE_PROMPT_VERSION,
    }

    with open(logs_dir / "quarantine.jsonl", "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


@router.post("/triage", response_model=TriageResult)
def triage(request: TriageRequest):
    prompt = TRIAGE_PROMPT.format(message=request.text)

    # First model attempt
    raw_response = generate_response(prompt)

    try:
        return parse_model_output(raw_response)
    except (json.JSONDecodeError, ValueError) as first_error:
        validation_error = str(first_error)

    # Exactly one repair attempt
    repair_prompt = f"""
{prompt}

Previous model output:

{raw_response}

Validation error:

{validation_error}

Your previous answer was rejected for this reason. Return only corrected JSON matching the schema.
""".strip()

    repaired_response = generate_response(repair_prompt)

    try:
        return parse_model_output(repaired_response)
    except (json.JSONDecodeError, ValueError) as second_error:
        quarantine_output(
            input_text=request.text,
            raw_output=repaired_response,
            error=str(second_error),
        )

        raise HTTPException(
            status_code=422,
            detail="LLM output could not be validated after one repair attempt.",
        )