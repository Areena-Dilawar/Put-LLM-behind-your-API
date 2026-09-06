import json
import os
import random
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate",
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama3.2:3b",
)

TIMEOUT_SECONDS = float(
    os.getenv("LLM_TIMEOUT_SECONDS", "30")
)

MAX_RETRIES = int(
    os.getenv("LLM_MAX_RETRIES", "2")
)

LLM_ENABLED = os.getenv(
    "LLM_ENABLED",
    "true",
).lower() == "true"


class LLMTimeoutError(Exception):
    """Raised when the LLM request times out after all retries."""


class LLMProviderError(Exception):
    """Raised when the LLM provider returns a non-retryable error."""


def _retry_after_seconds(response: requests.Response) -> float | None:
    retry_after = response.headers.get("Retry-After")

    if not retry_after:
        return None

    try:
        return max(0.0, float(retry_after))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(retry_after)
            return max(0.0, retry_at.timestamp() - time.time())
        except (TypeError, ValueError, OverflowError):
            return None


def _backoff_seconds(retry_number: int) -> float:
    base_delay = 2 ** (retry_number - 1)
    jitter = random.uniform(0, 0.25)
    return base_delay + jitter


def _write_call_log(
    *,
    prompt_version: str,
    repair_count: int,
    input_tokens: int | None,
    output_tokens: int | None,
    duration_ms: int,
    status_code: int | None = None,
    error: str | None = None,
) -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "prompt_version": prompt_version,
        "model": MODEL_NAME,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "repair_count": repair_count,
    }

    if status_code is not None:
        record["status_code"] = status_code

    if error is not None:
        record["error"] = error

    with open(
        logs_dir / "llm_calls.jsonl",
        "a",
        encoding="utf-8",
    ) as file:
        file.write(json.dumps(record) + "\n")


def generate_response(
    prompt: str,
    *,
    prompt_version: str = "v1",
    repair_count: int = 0,
) -> str:
    if not LLM_ENABLED:
        raise RuntimeError("LLM is disabled.")

    if TIMEOUT_SECONDS > 60:
        raise ValueError(
            "LLM_TIMEOUT_SECONDS must be 60 seconds or less."
        )

    for attempt in range(MAX_RETRIES + 1):
        start_time = time.perf_counter()

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=TIMEOUT_SECONDS,
            )

            duration_ms = int(
                (time.perf_counter() - start_time) * 1000
            )

            status_code = response.status_code

            # Retry only 429 and 5xx.
            if status_code == 429 or 500 <= status_code <= 599:
                if attempt < MAX_RETRIES:
                    retry_after = _retry_after_seconds(response)

                    if retry_after is not None:
                        delay = retry_after
                    else:
                        delay = _backoff_seconds(attempt + 1)

                    time.sleep(delay)
                    continue

                _write_call_log(
                    prompt_version=prompt_version,
                    repair_count=repair_count,
                    input_tokens=None,
                    output_tokens=None,
                    duration_ms=duration_ms,
                    status_code=status_code,
                    error=f"LLM provider returned HTTP {status_code}",
                )

                raise LLMProviderError(
                    f"LLM provider returned HTTP {status_code}."
                )

            # Never retry 400, 401, 403, or other 4xx errors.
            if status_code >= 400:
                _write_call_log(
                    prompt_version=prompt_version,
                    repair_count=repair_count,
                    input_tokens=None,
                    output_tokens=None,
                    duration_ms=duration_ms,
                    status_code=status_code,
                    error=f"LLM provider returned HTTP {status_code}",
                )

                raise LLMProviderError(
                    f"LLM provider returned HTTP {status_code}."
                )

            data = response.json()

            input_tokens = data.get("prompt_eval_count")
            output_tokens = data.get("eval_count")

            _write_call_log(
                prompt_version=prompt_version,
                repair_count=repair_count,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
            )

            return data["response"]

        except requests.Timeout as exc:
            duration_ms = int(
                (time.perf_counter() - start_time) * 1000
            )

            if attempt < MAX_RETRIES:
                time.sleep(_backoff_seconds(attempt + 1))
                continue

            _write_call_log(
                prompt_version=prompt_version,
                repair_count=repair_count,
                input_tokens=None,
                output_tokens=None,
                duration_ms=duration_ms,
                error="LLM request timed out.",
            )

            raise LLMTimeoutError(
                "LLM request timed out."
            ) from exc

        except requests.RequestException as exc:
            duration_ms = int(
                (time.perf_counter() - start_time) * 1000
            )

            _write_call_log(
                prompt_version=prompt_version,
                repair_count=repair_count,
                input_tokens=None,
                output_tokens=None,
                duration_ms=duration_ms,
                error=str(exc),
            )

            raise LLMProviderError(
                "Unable to reach the LLM provider."
            ) from exc