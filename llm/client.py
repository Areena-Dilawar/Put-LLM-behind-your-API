def generate_response(prompt: str) -> str:
    return """
{
  "category": "billing",
  "urgency": "high",
  "confidence": 0.9,
  "reason": "The customer reports a duplicate payment charge."
}
""".strip()