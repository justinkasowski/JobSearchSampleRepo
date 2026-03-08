from typing import Any, Dict
import requests
from pydantic import ValidationError

from config import MODEL, OLLAMA_KEEP_ALIVE, OLLAMA_URL, INTEGRATIONS_PROMPT
from integrations.schemas import MessagePlan

def _call_ollama_json(prompt: str, keep_alive: str | None = None) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "keep_alive": keep_alive or OLLAMA_KEEP_ALIVE,
        },
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("response", "").strip()


def _clean_llm_json(raw_text: str) -> str:
    text = raw_text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def _build_prompt(instruction: str) -> str:
    return f"""{INTEGRATIONS_PROMPT}

USER QUESTION:
{instruction}
"""


def llm_plan_message(instruction: str, keep_alive: str | None = None) -> tuple[MessagePlan, str]:
    prompt = _build_prompt(instruction)
    raw_output = _call_ollama_json(prompt, keep_alive=keep_alive)
    cleaned_output = _clean_llm_json(raw_output)

    try:
        plan = MessagePlan.model_validate_json(cleaned_output)
    except ValidationError as e:
        raise ValueError(
            f"LLM returned invalid MessagePlan JSON.\nRaw output:\n{raw_output}\n\nValidation error:\n{e}"
        )

    return plan, prompt