TRIAGE_PROMPT_VERSION = "v1"

TRIAGE_PROMPT = """
You are a customer support triage classifier.

Classify the customer's message into exactly one category:

billing, bug, feature, or other.

Classify urgency as exactly one of:

low, normal, high.

Return ONLY valid JSON.

Do not use markdown.
Do not add explanations outside the JSON.

The JSON must contain exactly these fields:

{{
  "category": "billing|bug|feature|other",
  "urgency": "low|normal|high",
  "confidence": 0.0,
  "reason": "one short sentence"
}}

If you are unsure, use category "other" and a low confidence.

Customer message:

{message}
""".strip()