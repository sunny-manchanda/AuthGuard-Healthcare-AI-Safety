from __future__ import annotations

import re
import unicodedata

from .schemas import SafetyAssessment


ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
PII_PATTERNS = [
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("phone", re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)")),
    ("member_id", re.compile(r"\b(?:MBR|MEM|PAT)[-_ ]?\d{4,10}\b", re.I)),
    ("dob", re.compile(r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b")),
]

CATEGORY_PATTERNS = {
    "prompt_injection": [
        r"ignore (?:all |the )?(?:previous|prior|system) (?:instructions|rules|prompt)",
        r"reveal (?:the )?(?:system prompt|hidden instructions)",
        r"you are now (?:an?|the)",
        r"developer mode",
        r"follow my instructions instead",
    ],
    "routing_manipulation": [
        r"classify (?:this|the case) as",
        r"return (?:only )?(?:approval|denial|document collection|clinician review)",
        r"force (?:the )?queue",
    ],
    "social_engineering": [
        r"i am (?:the |your )?(?:medical director|administrator|supervisor|chief)",
        r"(?:urgent|emergency).*(?:bypass|override|skip)",
        r"(?:bypass|override|skip).*(?:review|approval|controls?)",
    ],
    "data_exfiltration": [
        r"(?:show|reveal|list|export).*(?:other patient|all member|another case|database)",
        r"what (?:other|previous) patient",
        r"cross[- ]case",
    ],
    "unauthorized_action": [
        r"(?:approve|deny) (?:the |this )?(?:request|case|service)",
        r"change (?:the )?(?:case )?status",
        r"update (?:the )?(?:payer|production|case) record",
        r"without (?:human )?(?:review|approval|confirmation)",
    ],
    "medical_advice": [
        r"(?:diagnose|prescribe|recommend treatment)",
        r"(?:is|guarantee).*(?:medically necessary|safe for the patient)",
    ],
}

LEET_TRANSLATION = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})


def normalized_for_detection(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", ZERO_WIDTH_RE.sub("", text)).lower()
    normalized = normalized.translate(LEET_TRANSLATION)
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def redact_pii(text: str) -> tuple[str, list[str]]:
    redacted = text
    findings: list[str] = []
    for name, pattern in PII_PATTERNS:
        if pattern.search(redacted):
            findings.append(name)
            redacted = pattern.sub(f"[REDACTED_{name.upper()}]", redacted)
    return redacted, findings


def assess_input(text: str) -> SafetyAssessment:
    normalized = normalized_for_detection(text)
    categories: list[str] = []
    flags: list[str] = []
    score = 0
    for category, patterns in CATEGORY_PATTERNS.items():
        matched = [pattern for pattern in patterns if re.search(pattern, normalized, re.I)]
        if matched:
            categories.append(category)
            flags.append(f"Detected {category.replace('_', ' ')}")
            score += 3 if category in {"prompt_injection", "data_exfiltration", "unauthorized_action"} else 2

    redacted, pii_types = redact_pii(text)
    if pii_types:
        flags.append("Masked synthetic identifiers: " + ", ".join(sorted(set(pii_types))))
        score += 1
    if ZERO_WIDTH_RE.search(text) or normalized != re.sub(r"[^a-z0-9]+", " ", text.lower()).strip():
        if any(char.isdigit() for char in text) and any(token in normalized for token in ("ignore", "override", "bypass")):
            categories.append("obfuscation")
            flags.append("Detected obfuscated control language")
            score += 3
    if len(text) > 5000:
        categories.append("oversized_input")
        flags.append("Input exceeds the prototype review limit")
        score += 2

    risk_level = "High" if score >= 5 else "Medium" if score >= 2 else "Low"
    escalate = score >= 3 or bool(set(categories) & {"medical_advice", "social_engineering"})
    return SafetyAssessment(risk_level, score, flags, categories, escalate, redacted)

