#!/usr/bin/env python3
import json
from pathlib import Path

import build_product_dataset as bpd


STAGES = [
    ("original35", "초기 35건", "results.jsonl"),
    ("merged47", "batch1 이후 47건", "merged_results.jsonl"),
    ("merged51", "finance batch2 이후 51건", "merged_results_51.jsonl"),
    ("merged55", "hyundai batch3 이후 55건", "merged_results_55.jsonl"),
    ("merged67", "popular batch4 이후 67건", "merged_results_67.jsonl"),
    ("merged88", "company batch5 이후 88건", "merged_results_88.jsonl"),
    ("core64", "core-only 64건", "core_results_finance_hyundai_semiconductor.jsonl"),
]


def stats_for(path, cache):
    rows = bpd.read_jsonl(path)
    data = bpd.build_dataset(rows, cache)
    videos = data["videos"]
    kept = sum(1 for row in rows if (row.get("result") or {}).get("keep"))
    no_transcript = sum(1 for row in rows if row.get("status") == "no_transcript")
    processed = sum(1 for row in rows if row.get("status") == "processed")
    task_count = sum(len(v["job_tasks"]) for v in videos)
    criteria_count = sum(len(v["evaluation_criteria"]) for v in videos)
    question_count = sum(len(v["interview_questions"]) for v in videos)
    high = sum(1 for v in videos if v["confidence"] == "high")
    medium = sum(1 for v in videos if v["confidence"] == "medium")
    low = sum(1 for v in videos if v["confidence"] == "low")
    return {
        "rows": len(rows),
        "processed": processed,
        "kept": kept,
        "no_transcript": no_transcript,
        "videos": len(videos),
        "by_domain": data["aggregate"]["by_domain"],
        "avg_tasks": task_count / len(videos) if videos else 0,
        "avg_criteria": criteria_count / len(videos) if videos else 0,
        "avg_questions": question_count / len(videos) if videos else 0,
        "confidence": {"high": high, "medium": medium, "low": low},
        "top_tasks": data["aggregate"]["top_job_tasks"][:8],
        "top_criteria": data["aggregate"]["top_evaluation_criteria"][:8],
    }


def pct(n, d):
    return f"{(n / d * 100):.1f}%" if d else "-"


def main():
    cache = json.loads(Path("transcript_cache.json").read_text(encoding="utf-8"))
    stage_stats = []
    for key, label, path in STAGES:
        if not Path(path).exists():
            continue
        stage_stats.append((key, label, path, stats_for(path, cache)))

    lines = [
        "# 데이터 품질 단계별 리뷰",
        "",
        "질문: 데이터가 많아질수록 좋아졌는가?",
        "",
        "결론: 양은 늘었지만 모든 추가분이 제품 품질을 올리지는 않았다. 회사별/직무별 데이터는 좋아졌고, 일반 고조회수/소비재 데이터는 별도 보관이 맞다.",
        "",
        "## 단계별 지표",
        "| 단계 | rows | videos | keep | no transcript | 도메인 분포 | 평균 task | 평균 criteria | confidence high/med/low |",
        "|---|---:|---:|---:|---:|---|---:|---:|---|",
    ]
    for _, label, _, s in stage_stats:
        domains = ", ".join(f"{k}:{v}" for k, v in s["by_domain"].items())
        conf = f"{s['confidence']['high']}/{s['confidence']['medium']}/{s['confidence']['low']}"
        lines.append(
            f"| {label} | {s['rows']} | {s['videos']} | {s['kept']} ({pct(s['kept'], s['rows'])}) | "
            f"{s['no_transcript']} | {domains} | {s['avg_tasks']:.2f} | {s['avg_criteria']:.2f} | {conf} |"
        )

    lines.extend([
        "",
        "## 무엇이 좋아졌나",
        "",
        "### 1. 초기 35건",
        "- 반도체, 현대차, 금융권의 기본 축이 잡혔다.",
        "- 다만 일부 영상은 회사/직무 특정성이 약했고, 제품 기능으로 바로 쓰기에는 신호가 얇은 구간이 있었다.",
        "",
        "### 2. batch1~3",
        "- SK하이닉스/삼성전자/현대차/금융권이 보강되면서 core 도메인의 반복 신호가 생겼다.",
        "- 이 구간이 실제 품질 향상 폭이 가장 컸다. 이유는 같은 회사군 안에서 직무, 면접, 자소서 신호가 반복되기 때문이다.",
        "",
        "### 3. popular batch4",
        "- 조회수 높은 일반 면접 영상은 사용성 힌트는 줬다.",
        "- 하지만 회사별 차별성은 낮아졌다. 답변 구조, 1분 자기소개, 지원동기 같은 범용 기능에는 좋지만 core 데이터에 섞으면 평균적인 조언이 늘어난다.",
        "",
        "### 4. company batch5",
        "- 반도체/현대차/금융권에는 도움이 됐다. 특히 현직자/공식 채용/전형 설명 데이터가 추가됐다.",
        "- 반면 CJ/아모레/LG생활건강은 별도 도메인 가능성은 있지만 지금 MVP의 핵심 축과 다르다.",
        "",
        "## 데이터가 많아지며 생긴 문제",
        "- 도메인이 넓어지면 코파일럿이 답변할 때 특정 회사 언어보다 범용 취업 조언을 우선할 위험이 있다.",
        "- keep/drop 추출기는 회사 특정 정보를 엄격하게 보려 해서 고조회수 일반 영상이나 공식 채용 영상 일부를 drop한다. 그래서 keep 수만으로 품질을 판단하면 안 된다.",
        "- 소비재/유통을 섞으면 제품 방향이 `반도체/현대차/금융 특화`에서 `모든 취업 준비`로 흐려진다.",
        "",
        "## 지금 쓰기 좋은 데이터",
        "- 주 데이터셋: 금융권, 현대차/기아, SK하이닉스, 삼성전자/반도체 core 64건",
        "- 별도 archive: 일반 면접 고조회수, 소비재/유통, 기타 22개 영상",
        "- 제품 메시지는 `회사/직무별 자소서·면접 코파일럿`으로 잡고, 일반 면접 데이터는 내부 보조 규칙으로만 제한적으로 쓰는 편이 낫다.",
        "",
        "## 다음 판단",
        "- 더 모으기보다 현재 core 64건을 정제하는 단계가 맞다.",
        "- 우선순위는 추가 수집이 아니라 오분류 수정, 회사/직무 라벨 정규화, 질문 추출 품질 개선이다.",
    ])
    Path("data_quality_progression_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote data_quality_progression_review.md")


if __name__ == "__main__":
    main()
