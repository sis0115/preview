from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


CopilotTask = Literal[
    "resume_review",
    "interview_practice",
    "role_recommendation",
    "spec_gap",
    "pt_builder",
]


@dataclass(frozen=True)
class ExperienceCard:
    title: str
    keywords: list[str] = field(default_factory=list)
    situation: str | None = None
    action: str | None = None
    result: str | None = None
    metrics: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CopilotInput:
    task: CopilotTask
    company_id: str | None = None
    company_text: str | None = None
    role_id: str | None = None
    role_text: str | None = None
    question: str | None = None
    draft: str | None = None
    experience_cards: list[ExperienceCard] = field(default_factory=list)
    bank_id: str | None = None


@dataclass(frozen=True)
class CompanyBundle:
    company_profile: dict[str, Any]
    prompt_pack: dict[str, Any]
    roles: dict[str, Any]
    industry_context: dict[str, Any]
    task_packs: dict[str, dict[str, Any]]
    evidence: dict[str, Any]
    examples: dict[str, Any]


@dataclass(frozen=True)
class CopilotContextPacket:
    company: dict[str, Any]
    prompt_pack: dict[str, Any]
    task_pack: dict[str, Any]
    role: dict[str, Any] | None
    role_candidates: list[dict[str, Any]]
    industry_topics: list[dict[str, Any]]
    accepted_resume_patterns: list[dict[str, Any]]
    interview_questions: list[dict[str, Any]]
    youtube_signals: list[dict[str, Any]]
    examples: dict[str, Any]
