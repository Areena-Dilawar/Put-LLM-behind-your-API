# LLM Triage API

## What the endpoint does

This API takes a customer support message and automatically classifies it into one of four categories: billing, bug, feature, or other. It also assigns an urgency level, a confidence score, and a short reason. The API uses an LLM to make the classification and validates the model's response before returning it.

## Try the API

Send a customer message to the `/triage` endpoint:

```bash
curl -X POST "http://127.0.0.1:8000/triage" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"I was charged twice for my subscription.\"}"
```

Response:

```json
{
  "category": "billing",
  "urgency": "high",
  "confidence": 0.9,
  "reason": "Incorrect billing charge"
}
```

The endpoint returns only the validated triage result. Raw model output is never returned to the client.

## Job Card

### Job

Classify customer support messages into:

* `billing`
* `bug`
* `feature`
* `other`

Also return:

* urgency: `low`, `normal`, or `high`
* confidence: `0.0` to `1.0`
* a short reason

### It must never

* Return an invalid category.
* Return an invalid urgency value.
* Return a confidence value outside `0.0` to `1.0`.
* Return raw LLM text to the client.
* Crash when the model returns malformed output.
* Retry client errors such as HTTP 400, 401, or 403.
* Exceed the configured 60-second maximum request timeout.
* Keep retrying forever.
* Return a successful response when the model output cannot be validated after one repair attempt.

## Provider and Model

* Provider: Ollama
* Model: `llama3.2:3b`
* Prompt version: `v1`

The main environment variables used to configure the LLM are:

```text
LLM_ENABLED=true
OLLAMA_URL=http://localhost:11434/api/generate
MODEL_NAME=llama3.2:3b
```

`LLM_ENABLED` is the kill switch. When disabled, the API returns a deterministic fallback instead of calling the LLM.

## Evaluation Result

Evaluation date: September 7, 2026

Prompt version: `v1`

The evaluation contains 8 labelled cases, including an ambiguous case and a case where the model is explicitly expected to be unsure.

```text
Matched: 6/8
Category accuracy: 75.0%
Failed cases:
- other_1: expected=other, actual=feature
- ambiguous_1: expected=other, actual=bug
```

Category accuracy: **75.0% (6/8)**.

## Cost Log

One successful real Ollama call produced:

```json
{
  "prompt_version": "v1",
  "model": "llama3.2:3b",
  "input_tokens": 165,
  "output_tokens": 22,
  "duration_ms": 15299,
  "repair_count": 0
}
```

Because the model is running locally through Ollama, the provider API cost for this call is **$0**. This excludes electricity and local hardware costs.

At 10,000 requests/day, the Ollama API usage cost remains **$0/day**, excluding electricity, hardware, and infrastructure costs.

## What I'd Fix With Another Day

I would improve the evaluation accuracy, especially for ambiguous and general support messages. The current evaluation achieved 75.0%, with the ambiguous case incorrectly classified as `bug` and the support-hours case incorrectly classified as `feature`. I would add more representative examples and tune the prompt based on the observed failures, then rerun the evaluation to verify that the changes improve accuracy without breaking the existing cases.

## Run the Project

Clone the repository, create and activate a virtual environment, install the dependencies, make sure Ollama is running with the configured model, and start the API:

```bash
uvicorn src.main:app --reload
```

Then call:

```bash
curl -X POST "http://127.0.0.1:8000/triage" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"I was charged twice for my subscription.\"}"
```

The repository includes `.env.example` for configuration. `.env` is excluded from Git.

## Evaluation

To run all eight evaluation cases:

```bash
python evals/run_eval.py
```
