#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import build_product_dataset as bpd


CORE_DOMAINS = {"semiconductor", "hyundai", "finance"}


def write_jsonl(rows, path):
    Path(path).write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def strip_public(data):
    public = json.loads(json.dumps(data, ensure_ascii=False))
    for video in public["videos"]:
        video.pop("video_claims", None)
        for key in ("job_tasks", "evaluation_criteria"):
            for item in video.get(key, []):
                item.pop("evidence", None)
    return public


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", default="merged_results_88.jsonl")
    parser.add_argument("--cache", default="transcript_cache.json")
    parser.add_argument("--core-out", default="core_results_finance_hyundai_semiconductor.jsonl")
    parser.add_argument("--archive-out", default="non_core_results_archive.jsonl")
    parser.add_argument("--core-json", default="product_dataset_v2.json")
    parser.add_argument("--core-md", default="product_dataset_v2.md")
    parser.add_argument("--core-public-json", default="product_dataset_v2_public.json")
    parser.add_argument("--archive-json", default="product_dataset_non_core_archive.json")
    parser.add_argument("--archive-public-json", default="product_dataset_non_core_archive_public.json")
    parser.add_argument("--archive-md", default="non_core_dataset_archive_summary.md")
    args = parser.parse_args()

    rows = bpd.read_jsonl(args.infile)
    cache = json.loads(Path(args.cache).read_text(encoding="utf-8"))

    core_rows = []
    archive_rows = []
    row_domains = {}
    for row in rows:
        if row.get("status") != "processed":
            archive_rows.append(row)
            continue
        vid = bpd.video_id(row.get("url"))
        transcript = cache.get(vid, "")
        if not transcript:
            archive_rows.append(row)
            continue
        result = row.get("result") or {}
        domain = bpd.detect_domain(row.get("note") or "", result, transcript)
        row_domains[row.get("url")] = domain
        if domain in CORE_DOMAINS:
            core_rows.append(row)
        else:
            archive_rows.append(row)

    write_jsonl(core_rows, args.core_out)
    write_jsonl(archive_rows, args.archive_out)

    core_data = bpd.build_dataset(core_rows, cache)
    Path(args.core_json).write_text(json.dumps(core_data, ensure_ascii=False, indent=2), encoding="utf-8")
    bpd.write_md(core_data, args.core_md)
    Path(args.core_public_json).write_text(
        json.dumps(strip_public(core_data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    archive_data = bpd.build_dataset(archive_rows, cache)
    Path(args.archive_json).write_text(json.dumps(archive_data, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.archive_public_json).write_text(
        json.dumps(strip_public(archive_data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Non-Core Dataset Archive",
        "",
        "현재 제품 주 데이터셋에서 제외한 영상 묶음이다.",
        "",
        "## 기준",
        "- 주 데이터셋 유지: 금융권, 현대차/기아, SK하이닉스, 삼성전자/반도체",
        "- 별도 보관: 일반 면접 고조회수 영상, CJ/아모레/LG생활건강 등 소비재/유통, 자막 없음/기타",
        "",
        "## 수량",
        f"- core rows: {len(core_rows)}",
        f"- archived rows: {len(archive_rows)}",
        f"- archived videos in product archive: {archive_data['aggregate']['video_count']}",
        "",
        "## Archive Domain Distribution",
    ]
    for domain, count in archive_data["aggregate"]["by_domain"].items():
        lines.append(f"- {domain}: {count}")
    lines.extend([
        "",
        "## 쓰지 않는 이유",
        "- 일반 면접 영상은 사용성 힌트는 좋지만 회사별/직무별 차별성을 흐릴 수 있다.",
        "- 소비재/유통은 별도 도메인으로 가능성은 있지만, 지금 MVP 강점인 금융권/현대차/반도체 축과 다르다.",
        "- 데이터가 많아질수록 범용 조언이 늘어나면 코파일럿 답변이 평균화될 위험이 있다.",
    ])
    Path(args.archive_md).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"core rows: {len(core_rows)}")
    print(f"archive rows: {len(archive_rows)}")
    print(f"core videos: {core_data['aggregate']['video_count']}")
    print(f"archive videos: {archive_data['aggregate']['video_count']}")


if __name__ == "__main__":
    main()
