import logging

from app.core.embedding import generate_embeddings
from app.db.models import UserGuideline

logger = logging.getLogger(__name__)

DEFAULT_COMPANY_GUIDELINES = [
    {
        "type": "indemnification",
        "text": "Company requires mutual indemnification for IP infringement and reasonable indemnification for breach of confidentiality obligations, with prompt notice and sole control of defense.",
        "risk_level": "high",
    },
    {
        "type": "liability",
        "text": "Company requires mutual cap on liability at 1x contract value (or $1M, whichever is lower) with no exclusion for breach of confidentiality, data protection obligations, or intentional misconduct.",
        "risk_level": "high",
    },
    {
        "type": "termination",
        "text": "Company requires ability to terminate for convenience with 30 days notice, immediate termination for material breach, and survival of confidentiality and indemnification clauses post-termination.",
        "risk_level": "medium",
    },
    {
        "type": "governing_law",
        "text": "Company requires governing law and exclusive jurisdiction in the State of Delaware, with waiver of jury trial and class action. Entire agreement clause must be included.",
        "risk_level": "medium",
    },
    {
        "type": "confidentiality",
        "text": "Company requires confidentiality obligations to survive termination for 5 years, with exceptions for publicly available information and disclosures required by law. Standard of care must be reasonable.",
        "risk_level": "high",
    },
    {
        "type": "data_protection",
        "text": "Company requires compliance with all applicable data protection laws including GDPR, CCPA, and PIPL. Data processing agreement required if personal data is shared. 72-hour breach notification required.",
        "risk_level": "high",
    },
    {
        "type": "payment",
        "text": "Company requires net-30 payment terms with 1.5% monthly late fee. Payment obligations survive termination. No withholding taxes without prior agreement.",
        "risk_level": "medium",
    },
    {
        "type": "warranty",
        "text": "Company requires warranties of authority, non-infringement, and compliance with laws. Services warranty of professional workmanship for 90 days. EXCEPT for confidentiality/IP, all other warranties are disclaimed.",
        "risk_level": "medium",
    },
    {
        "type": "insurance",
        "text": "Company requires the other party to maintain commercial general liability ($2M), professional liability ($2M), and cyber insurance ($1M). Each party must be named as additional insured on relevant policies.",
        "risk_level": "medium",
    },
    {
        "type": "force_majeure",
        "text": "Company requires force majeure clause covering acts of God, war, terrorism, and public health emergencies. Excused performance must resume promptly. Payment obligations are not excused.",
        "risk_level": "low",
    },
    {
        "type": "anti_corruption",
        "text": "Company requires compliance with all anti-corruption laws including FCPA and UK Bribery Act. No gifts or payments to government officials without prior written consent.",
        "risk_level": "high",
    },
    {
        "type": "assignment",
        "text": "Company requires that neither party may assign the agreement without the other's written consent, not to be unreasonably withheld. Assignment to an affiliate or in connection with a merger is permitted with notice.",
        "risk_level": "medium",
    },
]


async def seed_default_guidelines(user_id: str, session) -> None:
    try:
        texts = [g["text"] for g in DEFAULT_COMPANY_GUIDELINES]
        try:
            embeddings = await generate_embeddings(texts)
        except Exception as e:
            logger.warning("Failed to generate embeddings for seed guidelines: %s", e)
            embeddings = None

        created = []
        for i, guideline in enumerate(DEFAULT_COMPANY_GUIDELINES):
            record = UserGuideline(
                tenant_id=user_id,
                guideline_type=guideline["type"],
                standard_text=guideline["text"],
                risk_level=guideline["risk_level"],
                guideline_scope="company",
                embedding=embeddings[i] if embeddings else None,
            )
            session.add(record)
            created.append(record)

        DEFAULT_USER_GUIDELINES = [
            {
                "type": "indemnification",
                "text": "Client requires indemnification cap at 25% of total contract value, with mutual defense costs covered only for IP claims. No indemnification for indirect losses.",
                "risk_level": "high",
            },
            {
                "type": "liability",
                "text": "Client requires liability cap not to exceed total contract value, with exclusions for fraud, gross negligence, and breach of confidentiality. No punitive damages.",
                "risk_level": "high",
            },
            {
                "type": "confidentiality",
                "text": "Client requires confidentiality obligations to survive termination for 3 years, with standard exceptions for legal disclosures and independently developed information.",
                "risk_level": "medium",
            },
            {
                "type": "termination",
                "text": "Client requires termination for convenience with 60 days notice, right to terminate for material breach with 15 days cure period, and refund of prepaid fees for unperformed services.",
                "risk_level": "medium",
            },
            {
                "type": "governing_law",
                "text": "Client requires governing law of the State of New York with exclusive jurisdiction in New York County courts. Waiver of jury trial preferred.",
                "risk_level": "medium",
            },
            {
                "type": "data_protection",
                "text": "Client requires data processing agreement with UK International Data Transfer Agreement (IDTA) or equivalent. 48-hour breach notification. Data portability on request.",
                "risk_level": "high",
            },
        ]
        for guideline in DEFAULT_USER_GUIDELINES:
            record = UserGuideline(
                tenant_id=user_id,
                guideline_type=guideline["type"],
                standard_text=guideline["text"],
                risk_level=guideline["risk_level"],
                guideline_scope="user",
                embedding=None,
            )
            session.add(record)
            created.append(record)

        await session.commit()
        logger.info("Seeded %d default guidelines for user %s", len(created), user_id)
    except Exception as e:
        logger.error("Failed to seed default guidelines: %s", e)
        await session.rollback()
