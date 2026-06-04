#!/usr/bin/env python3
"""Build normalized runtime copilot data from research files.

This is intentionally narrow for the first migration: SK hynix only.
The research files under companies/ stay as the editable source of truth;
copilot-data/ is generated runtime data for the application loader.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "copilot-data"
SK_SOURCE = ROOT / "companies" / "sk-hynix" / "copilot_kb.json"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def slug(value: str) -> str:
    mapping = {
        "Product Engineering": "product-engineering",
        "Utility기술": "utility-engineering",
        "품질보증": "quality-assurance",
        "양산기술": "manufacturing-technology",
        "R&D 공정": "r-and-d-process",
        "양산기술(P&T)": "package-and-test",
        "소자": "device",
        "설계": "design",
        "Maintenance": "maintenance",
    }
    return mapping.get(value, value.lower().replace(" ", "-"))


DEFAULT_INTERVIEW_SEEDS = {
    "양산기술": [
        "공정 조건 중 어떤 변수가 결과에 가장 큰 영향을 줬다고 판단했나요?",
        "그 판단을 데이터로 어떻게 확인했나요?",
        "실험실 조건과 양산 현장의 차이는 무엇이라고 생각하나요?",
        "수율과 품질 중 하나가 충돌하면 어떻게 판단하겠나요?",
        "HBM 같은 고성능 메모리에서 양산기술의 역할은 무엇이라고 생각하나요?",
    ],
    "R&D 공정": [
        "실험 변수를 어떻게 통제했고 어떤 기준으로 결과를 비교했나요?",
        "가설이 틀렸을 때 다음 실험 조건은 어떻게 정했나요?",
        "분석 장비 결과를 공정 조건 개선으로 어떻게 연결했나요?",
    ],
    "양산기술(P&T)": [
        "패키징/테스트 공정에서 신뢰성을 확인할 때 어떤 지표를 보겠나요?",
        "불량을 검출했을 때 공정 문제와 제품 문제를 어떻게 구분하겠나요?",
    ],
}


def build_sk_hynix() -> None:
    source = json.loads(SK_SOURCE.read_text(encoding="utf-8"))
    company_dir = OUT / "companies" / "sk-hynix"

    roles = []
    for role_name, role in source["role_knowledge"].items():
        translations = []
        if role.get("experience_translation"):
            translations.append(role["experience_translation"])

        roles.append(
            {
                "role_id": slug(role_name),
                "display_name": role_name,
                "aliases": [role_name],
                "focus": role.get("core_work", []),
                "resume_checks": role.get("resume_checks", []),
                "interview_question_seeds": role.get("interview_questions", []) or DEFAULT_INTERVIEW_SEEDS.get(role_name, []),
                "experience_translation_rules": translations,
            }
        )

    industry_topics = []
    for topic_name, topic in source["industry_knowledge"].items():
        role_connections = topic.get("connect_to_roles", {})
        industry_topics.append(
            {
                "topic_id": slug(topic_name),
                "name": topic_name,
                "why_it_matters": topic.get("why_it_matters", ""),
                "use_when_roles": list(role_connections.keys()),
                "role_connections": role_connections,
                "avoid": [
                    f"{topic_name}를 직무 연결 없이 지원동기에만 넣지 않는다",
                    f"{topic_name}의 세부 기술을 확실하지 않게 과장 설명하지 않는다",
                ],
            }
        )

    write_json(
        OUT / "manifest.json",
        {
            "schema": "copilot-data-manifest-v1",
            "generated_at": "2026-06-04",
            "companies": [
                {
                    "company_id": "sk-hynix",
                    "display_name": "SK하이닉스",
                    "industry": "semiconductor",
                    "status": "active",
                    "path": "companies/sk-hynix",
                },
                {
                    "company_id": "samsung-electronics",
                    "display_name": "삼성전자 DS",
                    "industry": "semiconductor",
                    "status": "planned",
                    "path": "companies/samsung-electronics",
                },
                {
                    "company_id": "hyundai-kia",
                    "display_name": "현대차/기아",
                    "industry": "mobility",
                    "status": "planned",
                    "path": "companies/hyundai-kia",
                },
                {
                    "company_id": "finance",
                    "display_name": "금융권",
                    "industry": "finance",
                    "status": "skeleton",
                    "path": "companies/finance",
                },
            ],
        },
    )

    write_text(
        OUT / "README.md",
        "# Copilot Runtime Data\n\n"
        "프로그램이 읽는 정규화된 코파일럿 데이터 폴더다.\n\n"
        "- `companies/`: 회사별 runtime data\n"
        "- `shared/`: alias, schema, 공통 출력 포맷\n"
        "- 현재 active migration 대상은 `sk-hynix`다.\n"
        "- 원본 리서치 자료는 `companies/` 폴더에 유지한다.\n",
    )

    write_json(
        company_dir / "company_profile.json",
        {
            "company_id": "sk-hynix",
            "display_name": "SK하이닉스",
            "industry": "semiconductor",
            "scope": "memory semiconductor recruitment copilot",
            "primary_tasks": [
                "resume_review",
                "interview_practice",
                "role_recommendation",
                "spec_gap",
            ],
            "status": "active",
            "source_company_kb": "companies/sk-hynix/copilot_kb.json",
        },
    )

    write_json(
        company_dir / "prompt_pack.json",
        {
            "company_id": "sk-hynix",
            "do": source["copilot_rules"].get("do", []),
            "avoid": source["copilot_rules"].get("avoid", []),
            "privacy_rules": [
                "학교, 실명, 연구실명, 고객사명, 프로젝트 고유명은 일반화한다",
                "정확한 수치가 개인/기관을 특정할 수 있으면 범위형 표현으로 바꾼다",
                "합격자 예시는 원문이 아니라 비식별 패턴만 보여준다",
            ],
        },
    )

    write_json(company_dir / "roles.json", {"company_id": "sk-hynix", "roles": roles})
    write_json(company_dir / "industry_context.json", {"company_id": "sk-hynix", "topics": industry_topics})

    write_json(
        company_dir / "task_packs" / "resume_review.json",
        {
            "task": "resume_review",
            "required_inputs": ["company_id", "role_id", "question", "draft"],
            "optional_inputs": ["experience_cards", "target_season", "job_posting_id"],
            "output_sections": [
                "직무 적합도 진단",
                "현재 문장의 문제",
                "합격 패턴 대비 부족한 것",
                "경험을 직무 언어로 바꾸는 방법",
                "수정 예시",
                "비식별 합격자 패턴 예시",
                "면접 꼬리질문",
                "추가로 필요한 근거",
            ],
            "case_detection": [
                "experience_missing",
                "company_news_only",
                "role_unclear",
                "experience_scattered",
                "technical_explanation_only",
                "collaboration_missing",
                "motivation_experience_disconnected",
                "wrong_question_intent",
                "outdated_or_inaccurate_industry_keyword",
                "failure_not_defended",
                "trait_words_only",
                "spec_listing",
                "overclaiming",
                "privacy_risk",
            ],
        },
    )

    write_json(
        company_dir / "task_packs" / "interview_practice.json",
        {
            "task": "interview_practice",
            "required_inputs": ["company_id", "role_id"],
            "optional_inputs": ["draft", "experience_cards", "interview_stage"],
            "output_sections": [
                "예상 질문",
                "질문 의도",
                "답변 구조",
                "꼬리질문",
                "답변 리스크",
                "보강해야 할 근거",
            ],
        },
    )

    write_json(
        company_dir / "task_packs" / "role_recommendation.json",
        {
            "task": "role_recommendation",
            "required_inputs": ["company_id", "experience_cards"],
            "output_sections": [
                "추천 직무",
                "추천 근거",
                "경험 번역 방향",
                "부족한 근거",
                "다음 준비 과제",
            ],
        },
    )

    write_json(
        company_dir / "task_packs" / "spec_gap.json",
        {
            "task": "spec_gap",
            "required_inputs": ["company_id", "role_id", "experience_cards"],
            "output_sections": [
                "현재 강점",
                "직무 대비 부족한 근거",
                "합격 패턴상 필요한 경험",
                "짧은 기간에 보강할 과제",
            ],
        },
    )

    write_text(
        company_dir / "evidence" / "accepted_resumes" / "README.md",
        "# Accepted Resume Patterns\n\n"
        "합격 자소서 원문을 저장하지 않는다. 제품에는 비식별 패턴과 안전 예시 문장만 사용한다.\n",
    )

    write_json(
        company_dir / "evidence" / "accepted_resumes" / "patterns.json",
        {
            "company_id": "sk-hynix",
            "patterns": [
                {
                    "pattern_id": "sk-hynix-mfg-pattern-001",
                    "role_id": "manufacturing-technology",
                    "source_type": "accepted_cover_letter",
                    "privacy_level": "deidentified_pattern",
                    "show_raw_text": False,
                    "experience_type": "공정 실험 또는 제조 프로젝트",
                    "problem": "결과 산포, 불량, 재현성 저하",
                    "actions": ["조건 분리", "기록", "원인 가설", "관리 인자 도출"],
                    "result_type": "재현성 향상/기준 수립",
                    "role_connection": "공정 조건 관리와 수율/품질 개선",
                    "safe_example_sentence": "실험 결과가 반복적으로 흔들리는 원인을 찾기 위해 공정 조건을 항목별로 분리해 기록했고, 결과에 영향을 주는 관리 인자를 좁혀 재현성을 높였습니다.",
                },
                {
                    "pattern_id": "sk-hynix-maintenance-pattern-001",
                    "role_id": "maintenance",
                    "source_type": "accepted_cover_letter",
                    "privacy_level": "deidentified_pattern",
                    "show_raw_text": False,
                    "experience_type": "장비/설비/제어 프로젝트",
                    "problem": "장비 이상, 반복 고장, 성능 저하",
                    "actions": ["현상 관찰", "데이터 확인", "원인 추적", "조치", "재발 방지"],
                    "result_type": "장비 안정화/재발 방지",
                    "role_connection": "라인 안정 가동과 예방 정비",
                    "safe_example_sentence": "장비 이상 현상을 단순 고장으로 처리하지 않고, 발생 조건과 센서 데이터를 함께 확인해 반복 원인을 좁혔습니다.",
                },
                {
                    "pattern_id": "sk-hynix-pe-pattern-001",
                    "role_id": "product-engineering",
                    "source_type": "accepted_cover_letter",
                    "privacy_level": "deidentified_pattern",
                    "show_raw_text": False,
                    "experience_type": "평가/분석/검증 프로젝트",
                    "problem": "제품 성능 또는 품질 기준 미달",
                    "actions": ["평가 지표 설정", "이상 패턴 분석", "개선 방향 제안"],
                    "result_type": "검증 기준 개선/품질 판단 근거 확보",
                    "role_connection": "제품 완성도, 수율, 신뢰성",
                    "safe_example_sentence": "평가 데이터를 단순히 정리하는 데서 끝내지 않고, 기준을 벗어나는 패턴을 분류해 제품 성능에 영향을 주는 요인을 찾았습니다.",
                },
            ],
        },
    )

    write_text(
        company_dir / "evidence" / "interview_reviews" / "README.md",
        "# Interview Review Questions\n\n"
        "면접 후기 원문이 아니라 질문, 의도, 꼬리질문 패턴만 저장한다.\n",
    )

    interview_questions = []
    for role in roles:
        for idx, question in enumerate(role["interview_question_seeds"][:5], start=1):
            interview_questions.append(
                {
                    "question_id": f"sk-hynix-{role['role_id']}-{idx:03d}",
                    "role_id": role["role_id"],
                    "source_type": "role_seed",
                    "question": question,
                    "intent": "직무 이해와 경험 방어 가능성 확인",
                    "followups": [
                        "그 판단을 어떤 근거로 했나요?",
                        "비슷한 상황이 반복되면 무엇을 먼저 확인하겠나요?",
                    ],
                    "answer_risk": [
                        "구체 경험 없이 키워드만 답하면 약함",
                        "직무 범위를 넘어선 성과로 과장하면 위험",
                    ],
                }
            )
    write_json(
        company_dir / "evidence" / "interview_reviews" / "questions.json",
        {"company_id": "sk-hynix", "questions": interview_questions},
    )

    write_json(
        company_dir / "evidence" / "official_sources" / "sources.json",
        {"company_id": "sk-hynix", "sources": source.get("sources", [])},
    )

    write_json(
        company_dir / "evidence" / "youtube_signals" / "signals.json",
        {
            "company_id": "sk-hynix",
            "signals": [
                {
                    "signal_id": "sk-hynix-youtube-role-language",
                    "source_type": "youtube_signal",
                    "usage": "직무 언어, 현직자 표현, 취준생 혼동 지점 파악",
                    "source_policy": source["source_policy"].get("youtube"),
                }
            ],
        },
    )

    write_json(
        company_dir / "examples" / "resume_review_cases.json",
        {
            "company_id": "sk-hynix",
            "cases": [
                "experience_missing",
                "company_news_only",
                "role_unclear",
                "experience_scattered",
                "technical_explanation_only",
                "collaboration_missing",
                "motivation_experience_disconnected",
                "wrong_question_intent",
                "outdated_or_inaccurate_industry_keyword",
                "failure_not_defended",
                "trait_words_only",
                "spec_listing",
                "overclaiming",
                "privacy_risk",
            ],
            "source_doc": "docs/sk_hynix_resume_review_demo.md",
        },
    )

    write_json(
        OUT / "shared" / "company_aliases.json",
        {
            "aliases": {
                "sk-hynix": ["SK하이닉스", "하이닉스", "SK hynix", "sk hynix"],
                "samsung-electronics": ["삼성전자", "삼성전자 DS", "삼성 DS", "Samsung DS"],
                "hyundai-kia": ["현대자동차", "현대차", "현차", "기아", "Kia", "Hyundai"],
                "finance": ["금융권", "은행권", "IBK", "우리은행", "하나은행", "KB", "신한은행", "NH농협"],
            }
        },
    )

    write_json(
        OUT / "shared" / "output_formats.json",
        {
            "resume_review": [
                "직무 적합도 진단",
                "현재 문장의 문제",
                "합격 패턴 대비 부족한 것",
                "경험을 직무 언어로 바꾸는 방법",
                "수정 예시",
                "비식별 합격자 패턴 예시",
                "면접 꼬리질문",
                "추가로 필요한 근거",
            ]
        },
    )


def main() -> None:
    build_sk_hynix()
    print(f"Built copilot runtime data at {OUT}")


if __name__ == "__main__":
    main()
