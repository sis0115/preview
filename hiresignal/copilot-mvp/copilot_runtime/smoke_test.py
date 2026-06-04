from __future__ import annotations

from .loader import CopilotDataLoader
from .models import CopilotInput, ExperienceCard
from .prompt_composer import compose_prompt


def main() -> None:
    loader = CopilotDataLoader("copilot-data")
    context = loader.build_context_packet(
        CopilotInput(
            company_text="하이닉스",
            role_text="양산기술",
            task="resume_review",
            question="지원동기와 입사 후 포부를 작성해주세요.",
            draft="저는 SK하이닉스가 세계적인 반도체 회사라 지원했습니다.",
            experience_cards=[
                ExperienceCard(
                    title="박막 증착 실험",
                    keywords=["공정 조건", "재현성", "데이터"],
                    situation="결과 편차가 반복적으로 발생함",
                    action="조건을 나눠 기록하고 비교함",
                    result="결과 편차 원인을 좁힘",
                )
            ],
        )
    )
    prompt = compose_prompt(
        CopilotInput(
            company_text="하이닉스",
            role_text="양산기술",
            task="resume_review",
            question="지원동기와 입사 후 포부를 작성해주세요.",
            draft="저는 SK하이닉스가 세계적인 반도체 회사라 지원했습니다.",
        ),
        context,
    )
    print("company:", context.company["display_name"])
    print("role:", context.role["display_name"] if context.role else None)
    print("patterns:", len(context.accepted_resume_patterns))
    print("interview_questions:", len(context.interview_questions))
    print("system_chars:", len(prompt["system"]))
    print("user_chars:", len(prompt["user"]))


if __name__ == "__main__":
    main()
