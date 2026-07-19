import json
from typing import Any

from app.core.llm import extract_json


_DYNAMIC_SCHEMA_PROMPT = """You are an intelligent contract schema generator.
Given the raw text of a contract, you must analyze it and produce a JSON schema
that describes the fields that can be extracted from this type of contract.

Rules:
1. Only include fields that are actually present or implied in the text.
2. For each field include: name, type (string | number | boolean | array | object), description.
3. Include a confidence_score (0.0 to 1.0) for the overall schema coverage.
4. Return ONLY valid JSON with no markdown or explanation."""

_EXTRACTION_PROMPT_TEMPLATE = """You are a contract extraction engine.
Extract structured data from the following contract text using this JSON schema:

{schema_json}

Contract text:
{contract_text}

Return ONLY valid JSON matching the schema. Do not include any markdown or explanation."""


async def generate_schema(contract_text: str, clause_texts: list[str] | None = None) -> dict[str, Any]:
    combined = contract_text
    if clause_texts:
        combined += "\n\n--- Clauses ---\n" + "\n\n".join(clause_texts)

    user_prompt = f"Analyze this contract and generate a JSON schema for extracting its key fields:\n\n{combined[:12000]}"
    result = await extract_json(_DYNAMIC_SCHEMA_PROMPT, user_prompt)
    return result.get("fields", result)


async def extract_fields(contract_text: str, schema: dict[str, Any]) -> dict[str, Any]:
    user_prompt = _EXTRACTION_PROMPT_TEMPLATE.format(
        schema_json=json.dumps(schema, indent=2),
        contract_text=contract_text[:12000],
    )
    result = await extract_json(_DYNAMIC_SCHEMA_PROMPT, user_prompt)
    return result
