"""Rule-based ticket auto-classification (category + priority).

Implements the exact keyword rules from the homework spec deterministically —
no LLM call — which keeps classification fast, free, and fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.models.ticket import TicketCategory, TicketPriority

CATEGORY_KEYWORDS: Dict[TicketCategory, List[str]] = {
    TicketCategory.BUG_REPORT: [
        "steps to reproduce",
        "reproduction steps",
        "reproduce",
        "defect",
        "expected behavior",
        "actual behavior",
        "regression",
    ],
    TicketCategory.ACCOUNT_ACCESS: [
        "login",
        "log in",
        "log-in",
        "password",
        "2fa",
        "two-factor",
        "two factor",
        "authentication",
        "sign in",
        "sign-in",
        "signin",
        "locked out",
        "reset password",
        "username",
        "account access",
    ],
    TicketCategory.BILLING_QUESTION: [
        "payment",
        "invoice",
        "refund",
        "billing",
        "charge",
        "charged",
        "overcharged",
        "subscription",
        "credit card",
        "receipt",
        "pricing",
    ],
    TicketCategory.TECHNICAL_ISSUE: [
        "bug",
        "error",
        "crash",
        "crashes",
        "crashing",
        "broken",
        "glitch",
        "freeze",
        "freezes",
        "hangs",
        "exception",
        "not working",
        "fails",
        "failure",
    ],
    TicketCategory.FEATURE_REQUEST: [
        "feature request",
        "enhancement",
        "suggestion",
        "would be great",
        "please add",
        "improve",
        "add support for",
        "feature",
    ],
}

# Checked in this order; the category with the most keyword matches wins.
# Listed most-specific-first so close ties favor the more informative category.
CATEGORY_PRECEDENCE: List[TicketCategory] = [
    TicketCategory.BUG_REPORT,
    TicketCategory.ACCOUNT_ACCESS,
    TicketCategory.BILLING_QUESTION,
    TicketCategory.TECHNICAL_ISSUE,
    TicketCategory.FEATURE_REQUEST,
]

PRIORITY_KEYWORDS: Dict[TicketPriority, List[str]] = {
    TicketPriority.URGENT: [
        "can't access",
        "cant access",
        "cannot access",
        "critical",
        "production down",
        "security",
    ],
    TicketPriority.HIGH: ["important", "blocking", "asap"],
    TicketPriority.LOW: ["minor", "cosmetic", "suggestion"],
}

# Urgent beats high beats low; medium is the fallback when nothing matches.
PRIORITY_PRECEDENCE: List[TicketPriority] = [
    TicketPriority.URGENT,
    TicketPriority.HIGH,
    TicketPriority.LOW,
]


@dataclass
class ClassificationOutcome:
    category: TicketCategory
    priority: TicketPriority
    confidence: float
    reasoning: str
    keywords_found: List[str]


def _find_matches(text: str, keywords: List[str]) -> List[str]:
    return [keyword for keyword in keywords if keyword in text]


def _weighted_score(matches: List[str]) -> float:
    """Multi-word phrases (e.g. "steps to reproduce") are more specific signals
    than single words (e.g. "bug"), so they're weighted by word count when
    picking the winning category between overlapping keyword sets."""
    return sum(len(keyword.split()) for keyword in matches)


def _classify_category(text: str) -> Tuple[TicketCategory, float, List[str]]:
    best_category = TicketCategory.OTHER
    best_matches: List[str] = []
    best_score = 0.0

    for category in CATEGORY_PRECEDENCE:
        matches = _find_matches(text, CATEGORY_KEYWORDS[category])
        score = _weighted_score(matches)
        if score > best_score:
            best_category, best_matches, best_score = category, matches, score

    if not best_matches:
        return TicketCategory.OTHER, 0.3, []

    confidence = min(1.0, 0.5 + 0.1 * best_score)
    return best_category, round(confidence, 2), best_matches


def _classify_priority(text: str) -> Tuple[TicketPriority, float, List[str]]:
    for priority in PRIORITY_PRECEDENCE:
        matches = _find_matches(text, PRIORITY_KEYWORDS[priority])
        if matches:
            confidence = min(1.0, 0.6 + 0.1 * _weighted_score(matches))
            return priority, round(confidence, 2), matches

    return TicketPriority.MEDIUM, 0.5, []


def classify_ticket(subject: str, description: str) -> ClassificationOutcome:
    """Classify a ticket's category and priority from its subject + description."""
    text = f"{subject} {description}".lower()

    category, category_confidence, category_keywords = _classify_category(text)
    priority, priority_confidence, priority_keywords = _classify_priority(text)

    overall_confidence = round((category_confidence + priority_confidence) / 2, 2)
    keywords_found = list(dict.fromkeys(category_keywords + priority_keywords))

    reasoning_parts = []
    if category_keywords:
        reasoning_parts.append(
            f"Matched category '{category.value}' via keyword(s): {', '.join(category_keywords)}."
        )
    else:
        reasoning_parts.append("No category keywords matched; defaulted to 'other'.")

    if priority_keywords:
        reasoning_parts.append(
            f"Matched priority '{priority.value}' via keyword(s): {', '.join(priority_keywords)}."
        )
    else:
        reasoning_parts.append("No priority keywords matched; defaulted to 'medium'.")

    return ClassificationOutcome(
        category=category,
        priority=priority,
        confidence=overall_confidence,
        reasoning=" ".join(reasoning_parts),
        keywords_found=keywords_found,
    )
