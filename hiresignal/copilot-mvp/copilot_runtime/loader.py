from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CompanyBundle, CopilotContextPacket, CopilotInput


class CopilotDataError(RuntimeError):
    pass


class CopilotDataLoader:
    """Load normalized runtime data from copilot-data/.

    This loader does not call an LLM. It only resolves company/role and builds
    a compact context packet for prompt composition.
    """

    def __init__(self, root_dir: str | Path = "copilot-data") -> None:
        self.root_dir = Path(root_dir)
        self._manifest: dict[str, Any] | None = None
        self._aliases: dict[str, list[str]] | None = None

    def load_manifest(self) -> dict[str, Any]:
        if self._manifest is None:
            self._manifest = self._read_json(self.root_dir / "manifest.json")
        return self._manifest

    def resolve_company_id(self, company_id: str | None = None, company_text: str | None = None) -> str | None:
        if company_id:
            return company_id
        if not company_text:
            return None

        aliases = self._load_company_aliases()
        normalized = company_text.strip().lower()
        for candidate_id, names in aliases.items():
            if normalized == candidate_id.lower():
                return candidate_id
            if any(normalized == name.lower() for name in names):
                return candidate_id
        return None

    def load_company(self, company_id: str) -> CompanyBundle:
        manifest = self.load_manifest()
        company_meta = next((c for c in manifest["companies"] if c["company_id"] == company_id), None)
        if not company_meta:
            raise CopilotDataError(f"Unknown company_id: {company_id}")
        if company_meta.get("status") not in {"active", "skeleton"}:
            raise CopilotDataError(f"Company is not active in runtime data yet: {company_id}")

        company_dir = self.root_dir / company_meta["path"]
        return CompanyBundle(
            company_profile=self._read_json(company_dir / "company_profile.json"),
            prompt_pack=self._read_json(company_dir / "prompt_pack.json"),
            roles=self._read_json(company_dir / "roles.json"),
            industry_context=self._read_json(company_dir / "industry_context.json"),
            task_packs=self._read_task_packs(company_dir / "task_packs"),
            evidence=self._read_evidence(company_dir / "evidence"),
            examples=self._read_examples(company_dir / "examples"),
        )

    def resolve_role(self, bundle: CompanyBundle, role_id: str | None = None, role_text: str | None = None) -> dict[str, Any] | None:
        roles = bundle.roles.get("roles", [])
        if role_id:
            return next((role for role in roles if role.get("role_id") == role_id), None)
        if not role_text:
            return None

        normalized = role_text.strip().lower()
        for role in roles:
            if normalized == role.get("display_name", "").lower():
                return role
            for alias in role.get("aliases", []):
                if normalized == alias.lower():
                    return role
        return None

    def recommend_roles(self, bundle: CompanyBundle, input_data: CopilotInput, limit: int = 3) -> list[dict[str, Any]]:
        keywords = set()
        if input_data.role_text:
            keywords.add(input_data.role_text.lower())
        for card in input_data.experience_cards:
            keywords.update(keyword.lower() for keyword in card.keywords)
            keywords.add(card.title.lower())

        scored: list[tuple[int, dict[str, Any]]] = []
        for role in bundle.roles.get("roles", []):
            score = 0
            haystack = " ".join(
                role.get("aliases", [])
                + role.get("focus", [])
                + role.get("resume_checks", [])
                + role.get("experience_translation_rules", [])
            ).lower()
            for keyword in keywords:
                if keyword and keyword in haystack:
                    score += 1
            if score:
                scored.append((score, role))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [role for _, role in scored[:limit]]

    def build_context_packet(self, input_data: CopilotInput) -> CopilotContextPacket:
        company_id = self.resolve_company_id(input_data.company_id, input_data.company_text)
        if not company_id:
            raise CopilotDataError("company_id or company_text is required")

        bundle = self.load_company(company_id)
        task_pack = bundle.task_packs.get(input_data.task)
        if not task_pack:
            raise CopilotDataError(f"Task is not available for {company_id}: {input_data.task}")

        role = self.resolve_role(bundle, input_data.role_id, input_data.role_text)
        role_candidates = [] if role else self.recommend_roles(bundle, input_data)

        selected_role = role or (role_candidates[0] if role_candidates else None)
        role_id = selected_role.get("role_id") if selected_role else None
        role_name = selected_role.get("display_name") if selected_role else None

        return CopilotContextPacket(
            company=bundle.company_profile,
            prompt_pack=bundle.prompt_pack,
            task_pack=task_pack,
            role=selected_role,
            role_candidates=role_candidates,
            industry_topics=self._select_industry_topics(bundle, role_name),
            accepted_resume_patterns=self._select_patterns(bundle, role_id),
            interview_questions=self._select_interview_questions(bundle, role_id),
            youtube_signals=bundle.evidence.get("youtube_signals", {}).get("signals", []),
            examples=bundle.examples,
        )

    def _load_company_aliases(self) -> dict[str, list[str]]:
        if self._aliases is None:
            data = self._read_json(self.root_dir / "shared" / "company_aliases.json")
            self._aliases = data.get("aliases", {})
        return self._aliases

    def _select_industry_topics(self, bundle: CompanyBundle, role_name: str | None) -> list[dict[str, Any]]:
        topics = bundle.industry_context.get("topics", [])
        if not role_name:
            return topics[:2]
        matched = [topic for topic in topics if role_name in topic.get("use_when_roles", [])]
        return matched or topics[:2]

    def _select_patterns(self, bundle: CompanyBundle, role_id: str | None) -> list[dict[str, Any]]:
        patterns = bundle.evidence.get("accepted_resumes", {}).get("patterns", [])
        if not role_id:
            return patterns[:3]
        matched = [pattern for pattern in patterns if pattern.get("role_id") == role_id]
        return matched or patterns[:3]

    def _select_interview_questions(self, bundle: CompanyBundle, role_id: str | None) -> list[dict[str, Any]]:
        questions = bundle.evidence.get("interview_reviews", {}).get("questions", [])
        if not role_id:
            return questions[:5]
        matched = [question for question in questions if question.get("role_id") == role_id]
        return matched[:8]

    def _read_task_packs(self, task_dir: Path) -> dict[str, dict[str, Any]]:
        if not task_dir.exists():
            return {}
        packs = {}
        for path in task_dir.glob("*.json"):
            data = self._read_json(path)
            packs[data["task"]] = data
        return packs

    def _read_evidence(self, evidence_dir: Path) -> dict[str, Any]:
        if not evidence_dir.exists():
            return {}
        evidence = {}
        mapping = {
            "accepted_resumes": "patterns.json",
            "interview_reviews": "questions.json",
            "official_sources": "sources.json",
            "youtube_signals": "signals.json",
        }
        for key, filename in mapping.items():
            path = evidence_dir / key / filename
            evidence[key] = self._read_json(path) if path.exists() else {}
        return evidence

    def _read_examples(self, examples_dir: Path) -> dict[str, Any]:
        if not examples_dir.exists():
            return {}
        examples = {}
        for path in examples_dir.glob("*.json"):
            examples[path.stem] = self._read_json(path)
        return examples

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise CopilotDataError(f"Missing data file: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
