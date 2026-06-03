#!/usr/bin/env python3
"""
build_product_dataset.py

Cached transcripts/results를 API 없이 재가공해 코파일럿 제품용 백데이터를 만든다.

출력:
  product_dataset_v2.json
  product_dataset_v2.md
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_INFILE = "core_results_finance_hyundai_semiconductor.jsonl"
DEFAULT_CACHE = "transcript_cache.json"
DEFAULT_JSON = "product_dataset_v2.json"
DEFAULT_MD = "product_dataset_v2.md"


DOMAIN_RULES = {
    "semiconductor": {
        "match": ["SK하이닉스", "삼성전자", "반도체", "공정", "설비", "양산", "평가"],
        "tasks": [
            ("공정 상태 모니터링", ["spc", "모니터링", "공정 상태", "데이터 로그"]),
            ("이상 원인 분석", ["원인 분석", "결함", "불량", "이상", "추적"]),
            ("수율/품질 개선", ["수율", "품질", "개선", "최적화"]),
            ("조건 최적화/DOE", ["doe", "조건 최적화", "실험 설계", "레시피"]),
            ("표준화/재발 방지", ["표준화", "재발 방지", "작업 표준", "문서"]),
            ("장비/현장 대응", ["장비", "설비", "메인트", "maintenance", "교대"]),
        ],
        "criteria": [
            ("데이터 기반 문제해결", ["데이터", "분석", "원인", "가설"]),
            ("직무 이해도", ["직무", "역할", "무슨 일을", "업무"]),
            ("산업 이해", ["hbm", "파운드리", "메모리", "업황", "엔비디아"]),
            ("협업/커뮤니케이션", ["협업", "소통", "커뮤니케이션", "팀원"]),
            ("현장 적응", ["현장", "교대", "라인", "플랜트"]),
        ],
        "resume_checks": [
            "공정/설비/양산 중 지원 직무를 명확히 분리했는가",
            "경험에 데이터, 원인 분석, 개선 행동, 결과가 있는가",
            "HBM/수율/공정 같은 산업 키워드를 본인 경험과 연결했는가",
            "직무가 회사 성과에 기여하는 방식을 설명했는가",
        ],
    },
    "finance": {
        "match": ["금융", "은행", "우리은행", "하나은행", "IBK", "기업은행", "PB", "PF"],
        "tasks": [
            ("고객 응대/상담", ["고객", "응대", "상담", "불만"]),
            ("금융상품 설명/세일즈", ["상품", "세일즈", "롤플레잉", "크로스셀"]),
            ("PT/BEI 면접 대응", ["pt", "bei", "하나fit", "실무진"]),
            ("경제/금융 필기 준비", ["ncs", "필기", "경제", "금융상식"]),
            ("기업/중소기업 이해", ["중소기업", "기업금융", "상생", "신용"]),
        ],
        "criteria": [
            ("고객 신뢰", ["신뢰", "정확", "배려", "고객"]),
            ("사람 응대 경험", ["아르바이트", "인턴", "응대", "갈등"]),
            ("은행 관심 증거", ["영업점", "현직자", "인터뷰", "자격증"]),
            ("필기 루틴", ["꾸준", "스터디", "신문", "라디오"]),
            ("과장 없는 답변", ["과장", "꼬리 질문", "진정성"]),
        ],
        "resume_checks": [
            "은행/금융권에 대한 관심 증거가 행동으로 제시됐는가",
            "자격증과 활동을 고객 응대/직무 수행으로 연결했는가",
            "자소서 문장이 꼬리질문을 버틸 수 있는가",
            "NCS/경제/금융상식 준비 상태가 관리되고 있는가",
        ],
    },
    "hyundai": {
        "match": ["현대자동차", "현대차", "모빌리티", "품질", "구매", "파이로트", "SDV"],
        "tasks": [
            ("품질 검증/마지막 점검", ["품질", "검증", "마무리", "고객에게"]),
            ("구매/협력사 조율", ["구매", "협력사", "조율", "균형"]),
            ("파이로트/양산 전 평가", ["파이로트", "시험", "양산", "사전"]),
            ("자기소개 PT", ["pt", "시각화", "자기소개", "발표"]),
            ("R&D/생산제조 협업", ["연구개발", "생산", "제조", "플랜트"]),
            ("SDV/전장/인포테인먼트", ["sdv", "전장", "인포테인먼트", "avp"]),
        ],
        "criteria": [
            ("필살기 경험", ["필살기", "핵심 경험", "프로젝트", "문제 상황"]),
            ("회사-직무 연결", ["왜 현대", "지원 이유", "직무", "현대자동차"]),
            ("PT 구성력", ["한 문장", "시각화", "슬라이드", "가시성"]),
            ("협업/조율", ["협업", "조율", "협력사", "부서"]),
            ("가치관/임원면접", ["가치관", "좌우명", "10년 후", "상사"]),
        ],
        "resume_checks": [
            "필살기 경험 2개가 자소서와 PT에서 일관되게 이어지는가",
            "회사 뉴스보다 본인의 경험이 중심인가",
            "품질/구매/생산/R&D 중 어느 직무 언어로 경험을 번역했는가",
            "PT 각 장에 말하려는 한 문장이 있는가",
        ],
    },
    "retail_consumer": {
        "match": ["CJ", "올리브영", "대한통운", "ENM", "제일제당", "아모레퍼시픽", "LG생활건강", "브랜드", "커머스", "마케팅"],
        "tasks": [
            ("브랜드/상품 기획", ["브랜드", "상품", "제품", "기획", "큐레이션"]),
            ("고객/시장 이해", ["고객", "소비자", "시장", "트렌드", "니즈"]),
            ("유통/물류/커머스 운영", ["유통", "물류", "커머스", "올리브영", "대한통운", "채널"]),
            ("PT/발표/설득", ["pt", "발표", "프레젠테이션", "설득", "스토리"]),
            ("계열사/직무 선택", ["계열사", "직무", "회사", "선택", "지원"]),
        ],
        "criteria": [
            ("회사/브랜드 이해", ["회사", "브랜드", "계열사", "사업", "제품"]),
            ("고객 관점", ["고객", "소비자", "니즈", "경험"]),
            ("콘텐츠/커뮤니케이션", ["콘텐츠", "커뮤니케이션", "소통", "표현"]),
            ("실행력/협업", ["실행", "협업", "결단", "문제해결"]),
            ("직무 적합성", ["직무", "역량", "적합", "경험"]),
        ],
        "resume_checks": [
            "지원 계열사와 직무를 구체적으로 골랐는가",
            "브랜드/상품/고객 경험을 본인의 행동과 연결했는가",
            "마케팅·영업·MD·물류 중 어느 직무 언어로 경험을 번역했는가",
            "PT나 면접에서 고객 관점과 실행 경험이 드러나는가",
        ],
    },
    "general_interview": {
        "match": ["1분 자기소개", "면접", "자기소개"],
        "tasks": [
            ("1분 자기소개 설계", ["1분", "자기소개", "첫인상"]),
            ("경험 2개로 질문 유도", ["경험 두 개", "질문", "필살기"]),
            ("자연형/전략형 답변", ["자연", "편하게", "전략"]),
        ],
        "criteria": [
            ("구체적 경험", ["경험", "성과", "근거"]),
            ("질문 유도", ["질문", "궁금", "물음표"]),
            ("외운 티 감소", ["자연", "솔직", "편하게"]),
        ],
        "resume_checks": [
            "면접관에게 질문받고 싶은 경험 2개가 명확한가",
            "1분 자기소개가 스펙 나열이 아니라 경험 유도 장치인가",
            "외운 멘트가 무너졌을 때 자연형 버전이 있는가",
        ],
    },
}


QUESTION_PATTERNS = [
    r"([가-힣A-Za-z0-9·/ ]{2,45}(?:지원한 이유|지원 이유|선택한 이유)[가-힣A-Za-z0-9·/ ]{0,35})",
    r"([가-힣A-Za-z0-9·/ ]{0,30}(?:왜|무엇|어떻게|어떤|무슨)[가-힣A-Za-z0-9·/ ]{4,45}(?:요|까|냐|니|습니까|나요|인가))",
    r"([가-힣A-Za-z0-9·/ ]{0,30}(?:갈등|협업|도전|창의|지원동기|직무|전공|프로젝트)[가-힣A-Za-z0-9·/ ]{0,45}(?:질문|경험|이유))",
]


def read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def norm(text):
    return re.sub(r"\s+", " ", text or "").strip()


def snippets(text, needles, limit=3, width=95):
    out = []
    low = text.lower()
    for needle in needles:
        idx = low.find(needle.lower())
        if idx < 0:
            continue
        start = max(0, idx - width // 2)
        end = min(len(text), idx + len(needle) + width // 2)
        s = norm(text[start:end])
        if s and s not in out:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def detect_domain(note, result, transcript):
    company = result.get("company") or ""
    role = result.get("role") or ""
    note_text = note or ""
    if company in {"현대자동차"} or "현대차" in note_text or "현대자동차" in note_text:
        return "hyundai"
    if any(k in note_text for k in ["CJ", "올리브영", "대한통운", "ENM", "제일제당", "아모레퍼시픽", "LG생활건강", "LG 생건"]):
        return "retail_consumer"
    if company in {"금융권", "케이뱅크", "DB금융투자"} or any(k in note_text for k in ["금융", "은행", "증권", "케이뱅크", "DB금융"]):
        return "finance"
    if company in {"SK하이닉스", "삼성전자"} or any(k in note_text for k in ["SK하이닉스", "삼성전자", "반도체", "DS", "공정기술", "설비"]):
        return "semiconductor"
    if any(k in note_text for k in ["1분 자기소개", "자기소개"]):
        return "general_interview"

    blob = " ".join([
        note or "",
        company,
        role,
        transcript[:1200],
    ]).lower()
    scores = {}
    for domain, rule in DOMAIN_RULES.items():
        scores[domain] = sum(1 for k in rule["match"] if k.lower() in blob)
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "general_interview"


def extract_pairs(text, pairs):
    found = []
    for label, keys in pairs:
        ev = snippets(text, keys, limit=2)
        if ev:
            found.append({"name": label, "evidence": ev})
    return found


def extract_video_claims(text, limit=7):
    claim_keys = [
        "중요", "핵심", "필요", "준비", "합격", "면접", "자소서",
        "직무", "지원동기", "문제", "데이터", "수율", "고객", "pt",
    ]
    candidates = []
    sentences = re.split(r"(?<=[.!?。])\s+|(?<=다)\s+", text)
    for sent in sentences:
        s = norm(sent)
        if len(s) < 35 or len(s) > 190:
            continue
        score = sum(1 for k in claim_keys if k.lower() in s.lower())
        if score <= 0:
            continue
        if any(bad in s for bad in ["구독", "좋아요", "댓글", "문의", "카카오", "QR"]):
            continue
        candidates.append((score, s))
    candidates.sort(key=lambda x: (-x[0], len(x[1])))
    out = []
    for _, s in candidates:
        if not any(s[:35] in prev for prev in out):
            out.append(s)
        if len(out) >= limit:
            break
    return out


def extract_questions(text, limit=8):
    found = []
    for pat in QUESTION_PATTERNS:
        for m in re.finditer(pat, text):
            q = norm(m.group(1)).strip(" ,.-")
            if len(q) < 10 or len(q) > 90:
                continue
            if any(bad in q for bad in ["여러분", "제가", "댓글", "문의", "영상"]):
                continue
            if q not in found:
                found.append(q)
            if len(found) >= limit:
                return found
    return found


def build_experience_rules(domain, job_tasks, criteria):
    names = {x["name"] for x in job_tasks + criteria}
    rules = []
    if domain == "semiconductor":
        if "수율/품질 개선" in names or "데이터 기반 문제해결" in names:
            rules.append("프로젝트 경험을 문제 상황 -> 데이터 확인 -> 원인 가설 -> 조건 최적화 -> 수율/품질 결과로 재작성")
        if "장비/현장 대응" in names:
            rules.append("현장/설비 경험을 장비 이상 대응, 교대/라인 적응, 유관부서 커뮤니케이션으로 재작성")
    elif domain == "finance":
        if "고객 응대/상담" in names or "사람 응대 경험" in names:
            rules.append("알바/인턴/봉사 경험을 고객 니즈 파악, 설명, 신뢰 회복, 민원 해결로 재작성")
        if "PT/BEI 면접 대응" in names:
            rules.append("경험별 STAR 구조를 만들고 PT/BEI 꼬리질문까지 방어 가능하게 정리")
    elif domain == "hyundai":
        if "자기소개 PT" in names or "PT 구성력" in names:
            rules.append("자소서 필살기 경험을 PT 슬라이드의 한 문장 메시지, 문제, 행동, 결과로 시각화")
        if "품질 검증/마지막 점검" in names or "파이로트/양산 전 평가" in names:
            rules.append("프로젝트 경험을 품질 검증, 사전 문제 발견, 양산 전 개선, 협업 부서 조율로 재작성")
    elif domain == "retail_consumer":
        if "고객/시장 이해" in names or "고객 관점" in names:
            rules.append("대외활동/인턴/프로젝트 경험을 고객 문제, 시장 관찰, 실행 아이디어, 반응 지표로 재작성")
        if "PT/발표/설득" in names or "콘텐츠/커뮤니케이션" in names:
            rules.append("발표 경험을 타깃 고객, 메시지 구조, 설득 근거, 실행 결과 중심으로 재작성")
        if "계열사/직무 선택" in names or "회사/브랜드 이해" in names:
            rules.append("지원 계열사 선택 이유를 브랜드/상품/채널 이해와 본인 경험의 접점으로 재작성")
    else:
        rules.append("1분 자기소개에는 질문받고 싶은 경험 2개만 남기고 스펙 나열을 제거")
    return rules


def build_dataset(rows, cache):
    videos = []
    for row in rows:
        if row.get("status") != "processed":
            continue
        vid = video_id(row.get("url"))
        transcript = cache.get(vid, "")
        if not transcript:
            continue
        result = row.get("result") or {}
        note = row.get("note") or ""
        domain = detect_domain(note, result, transcript)
        rule = DOMAIN_RULES[domain]
        job_tasks = extract_pairs(transcript, rule["tasks"])
        criteria = extract_pairs(transcript, rule["criteria"])
        questions = extract_questions(transcript)
        video = {
            "video_id": vid,
            "url": row.get("url"),
            "title_or_note": note,
            "company": result.get("company"),
            "role": result.get("role"),
            "domain": domain,
            "keep": bool(result.get("keep")),
            "video_claims": extract_video_claims(transcript),
            "job_tasks": job_tasks,
            "evaluation_criteria": criteria,
            "resume_checks": rule["resume_checks"],
            "interview_questions": questions,
            "experience_translation_rules": build_experience_rules(domain, job_tasks, criteria),
            "product_features": product_features_for(domain),
            "confidence": confidence(job_tasks, criteria, questions),
        }
        videos.append(video)
    return {"schema_version": "v2-local-rules-2026-06-03", "videos": videos, "aggregate": aggregate(videos)}


def product_features_for(domain):
    if domain == "semiconductor":
        return ["경험 카드 데이터/수율 필드", "직무별 자소서 번역", "공정·설비·양산 면접 시뮬레이션"]
    if domain == "finance":
        return ["은행 관심 증거 점검", "PT/세일즈/BEI 면접 모드", "필기 루틴 관리"]
    if domain == "hyundai":
        return ["자소서-PT 일관성 검사", "필살기 경험 2개 선별", "품질/구매/R&D 직무 번역"]
    if domain == "retail_consumer":
        return ["브랜드/고객 경험 번역", "계열사·직무 선택 점검", "PT/발표 스토리라인 코칭"]
    return ["1분 자기소개 경험 2개 설계", "자연형 답변 훈련", "꼬리질문 생성"]


def confidence(job_tasks, criteria, questions):
    score = len(job_tasks) + len(criteria) + (1 if questions else 0)
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def aggregate(videos):
    by_domain = Counter(v["domain"] for v in videos)
    by_company_role = Counter((v.get("company") or "미상", v.get("role") or "직무미상") for v in videos if v["keep"])
    task_counts = Counter()
    criteria_counts = Counter()
    feature_counts = Counter()
    for v in videos:
        for item in v["job_tasks"]:
            task_counts[(v["domain"], item["name"])] += 1
        for item in v["evaluation_criteria"]:
            criteria_counts[(v["domain"], item["name"])] += 1
        for item in v["product_features"]:
            feature_counts[item] += 1
    return {
        "video_count": len(videos),
        "by_domain": dict(by_domain),
        "top_company_roles": [
            {"company": c, "role": r, "count": n}
            for (c, r), n in by_company_role.most_common(20)
        ],
        "top_job_tasks": [
            {"domain": d, "task": t, "count": n}
            for (d, t), n in task_counts.most_common(30)
        ],
        "top_evaluation_criteria": [
            {"domain": d, "criterion": t, "count": n}
            for (d, t), n in criteria_counts.most_common(30)
        ],
        "product_feature_counts": dict(feature_counts.most_common()),
    }


def write_md(data, path):
    lines = [
        "# Product Dataset V2",
        "",
        f"스키마: `{data['schema_version']}`",
        f"영상 수: {data['aggregate']['video_count']}",
        "",
        "## Domain Distribution",
    ]
    for domain, n in data["aggregate"]["by_domain"].items():
        lines.append(f"- {domain}: {n}")

    lines.append("\n## Top Company Roles")
    for item in data["aggregate"]["top_company_roles"][:12]:
        lines.append(f"- {item['company']} / {item['role']}: {item['count']}")

    lines.append("\n## Top Job Tasks")
    for item in data["aggregate"]["top_job_tasks"][:18]:
        lines.append(f"- [{item['domain']}] {item['task']}: {item['count']}")

    lines.append("\n## Top Evaluation Criteria")
    for item in data["aggregate"]["top_evaluation_criteria"][:18]:
        lines.append(f"- [{item['domain']}] {item['criterion']}: {item['count']}")

    lines.append("\n## Product Feature Signals")
    for feature, n in data["aggregate"]["product_feature_counts"].items():
        lines.append(f"- {feature}: {n}")

    lines.append("\n## Sample Video Records")
    for v in data["videos"][:18]:
        lines.extend([
            "",
            f"### {v['title_or_note'] or v['video_id']}",
            f"- domain: {v['domain']}",
            f"- company/role: {v.get('company') or '미상'} / {v.get('role') or '직무미상'}",
            f"- confidence: {v['confidence']}",
        ])
        if v["video_claims"]:
            lines.append("- video_claims:")
            for claim in v["video_claims"][:3]:
                lines.append(f"  - {claim}")
        if v["job_tasks"]:
            lines.append("- job_tasks:")
            for task in v["job_tasks"][:4]:
                lines.append(f"  - {task['name']}")
        if v["evaluation_criteria"]:
            lines.append("- evaluation_criteria:")
            for c in v["evaluation_criteria"][:4]:
                lines.append(f"  - {c['name']}")
        if v["experience_translation_rules"]:
            lines.append("- experience_translation_rules:")
            for r in v["experience_translation_rules"][:3]:
                lines.append(f"  - {r}")

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default=DEFAULT_INFILE)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    ap.add_argument("--json-out", default=DEFAULT_JSON)
    ap.add_argument("--md-out", default=DEFAULT_MD)
    args = ap.parse_args()

    rows = read_jsonl(args.infile)
    cache = json.loads(Path(args.cache).read_text(encoding="utf-8"))
    data = build_dataset(rows, cache)
    Path(args.json_out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(data, args.md_out)
    print(f"videos: {data['aggregate']['video_count']}")
    print(f"json: {args.json_out}")
    print(f"md: {args.md_out}")


if __name__ == "__main__":
    main()
