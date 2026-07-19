import json
from typing import Any

from app.core.llm import extract_json

_CLAUSE_TYPES = [
    "indemnification", "liability", "termination", "governing_law",
    "confidentiality", "payment", "renewal", "data_protection",
    "intellectual_property", "insurance", "force_majeure", "warranty",
    "sla", "audit", "anti_corruption", "assignment", "subcontracting",
    "non_compete", "non_solicitation", "entire_agreement", "amendments",
    "publicity", "notices", "export_control", "third_party", "waiver",
    "severability", "survival", "independent_contractor", "counterparts",
    "further_assurances", "time_essence", "cumulative_remedies",
    "legal_fees", "set_off", "delivery", "training", "support",
    "disaster_recovery", "transition", "records_retention", "sanctions",
    "diversity", "data_security", "compliance", "right_to_use",
    "benchmarks", "pricing", "scope", "other"
]

_CLAUSE_EXTRACTION_PROMPT = """Break this contract into individual legal clauses. For each clause, identify:
1. The clause type (from the allowed list)
2. The full text of the clause
3. A brief summary

Allowed clause types: {clause_types}

Return JSON format:
{{
  "clauses": [
    {{
      "clause_type": "type",
      "text_content": "full clause text",
      "summary": "brief summary"
    }}
  ]
}}

Important:
- Each clause should be a distinct legal provision
- Include the COMPLETE text of each clause
- Classify by the primary legal subject
- Return ONLY valid JSON

Contract text:
{contract_text}"""


async def extract_clauses(contract_text: str) -> list[dict[str, Any]]:
    """Break contract into classified clauses using LLM."""
    prompt = _CLAUSE_EXTRACTION_PROMPT.format(
        clause_types=", ".join(_CLAUSE_TYPES[:20]),
        contract_text=contract_text[:15000]
    )
    result = await extract_json(
        "You are a legal contract clause extraction system.",
        prompt
    )
    clauses = result.get("clauses", [])
    if not clauses and isinstance(result, dict):
        for key, value in result.items():
            if isinstance(value, list):
                clauses = value
                break
    return clauses
