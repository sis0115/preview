from __future__ import annotations

import json
from dataclasses import asdict

from .models import CopilotContextPacket, CopilotInput


def compose_resume_review_prompt(input_data: CopilotInput, context: CopilotContextPacket) -> dict[str, str]:
    """Create prompt messages for resume review.

    The return value is provider-agnostic. API adapters can map it to OpenAI,
    Anthropic, or another chat format later.
    """

    role = context.role or {}
    system_lines = [
        "너는 회사별 취업 코파일럿이다.",
        "없는 경험을 만들지 않는다.",
        "합격자 예시는 원문이 아니라 비식별 패턴만 사용한다.",
        "산업 동향은 지원 직무와 연결될 때만 사용한다.",
    ]
    system_lines.extend(context.prompt_pack.get("do", []))
    system_lines.extend(f"금지: {rule}" for rule in context.prompt_pack.get("avoid", []))
    system_lines.extend(f"개인정보 처리: {rule}" for rule in context.prompt_pack.get("privacy_rules", []))

    user_payload = {
        "task": input_data.task,
        "company": context.company,
        "role": {
            "role_id": role.get("role_id"),
            "display_name": role.get("display_name"),
            "focus": role.get("focus", []),
            "resume_checks": role.get("resume_checks", []),
            "experience_translation_rules": role.get("experience_translation_rules", []),
        },
        "role_candidates": context.role_candidates,
        "question": input_data.question,
        "draft": input_data.draft,
        "experience_cards": [asdict(card) for card in input_data.experience_cards],
        "industry_topics": context.industry_topics,
        "accepted_resume_patterns": context.accepted_resume_patterns,
        "interview_questions": context.interview_questions,
        "youtube_signals": context.youtube_signals,
        "output_sections": context.task_pack.get("output_sections", []),
        "case_detection": context.task_pack.get("case_detection", []),
    }

    return {
        "system": "\n".join(system_lines),
        "user": json.dumps(user_payload, ensure_ascii=False, indent=2),
    }


def compose_prompt(input_data: CopilotInput, context: CopilotContextPacket) -> dict[str, str]:
    if input_data.task == "resume_review":
        return compose_resume_review_prompt(input_data, context)

    return {
        "system": "\n".join(
            [
                "너는 회사별 취업 코파일럿이다.",
                "없는 경험을 만들지 않는다.",
                "근거 데이터에 없는 내용을 확정적으로 말하지 않는다.",
            ]
        ),
        "user": json.dumps(
            {
                "task": input_data.task,
                "company": context.company,
                "role": context.role,
                "role_candidates": context.role_candidates,
                "task_pack": context.task_pack,
                "industry_topics": context.industry_topics,
                "accepted_resume_patterns": context.accepted_resume_patterns,
                "interview_questions": context.interview_questions,
                "experience_cards": [asdict(card) for card in input_data.experience_cards],
            },
            ensure_ascii=False,
            indent=2,
        ),
    }
