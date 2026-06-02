#!/usr/bin/env python3
import argparse
import json
import re
import ssl
import time
from dataclasses import dataclass, asdict
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import certifi


SEARCH_QUERIES = [
    "취업 면접 자소서 합격 후기",
    "면접왕 이형 자소서 면접",
    "인싸담당자 면접 자소서",
    "삼성전자 면접 후기 취업",
    "SK하이닉스 면접 후기 취업",
    "현대자동차 면접 후기 자소서",
    "은행권 면접 후기 금융권 취업",
    "대기업 면접 1분 자기소개",
    "자소서 첨삭 합격 자기소개서",
    "PT면접 준비 취업",
    "취업 면접 질문 답변",
    "채용 면접 준비 합격 후기",
]


@dataclass
class Candidate:
    video_id: str
    title: str
    channel: str
    url: str
    length_text: str
    length_seconds: int | None
    published_text: str
    upload_date: str | None
    views: int | None
    comments: int | None
    query: str
    reason: str


def fetch(url: str) -> str:
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    with urlopen(req, timeout=40, context=ctx) as res:
        return res.read().decode("utf-8", "ignore")


def find_json_object(text: str, marker: str) -> Any | None:
    start = text.find(marker)
    if start < 0:
        return None
    start = text.find("{", start)
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
    return None


def walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def text_of(node: Any) -> str:
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if "simpleText" in node:
            return node["simpleText"]
        if "runs" in node:
            return "".join(run.get("text", "") for run in node.get("runs", []))
    return ""


def parse_int_text(text: str) -> int | None:
    if not text:
        return None
    s = text.replace(",", "").replace(" ", "")
    m = re.search(r"(\d+(?:\.\d+)?)(천|만|억)?", s)
    if not m:
        return None
    n = float(m.group(1))
    unit = m.group(2)
    mul = {"천": 1_000, "만": 10_000, "억": 100_000_000}.get(unit, 1)
    return int(n * mul)


def parse_length(text: str) -> int | None:
    parts = [int(p) for p in re.findall(r"\d+", text or "")]
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[-3] * 3600 + parts[-2] * 60 + parts[-1]


def existing_video_ids(paths: list[Path]) -> set[str]:
    ids = set()
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        ids.update(re.findall(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", text))
    return ids


def search_videos(query: str) -> list[dict[str, Any]]:
    html = fetch(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
    initial = find_json_object(html, "var ytInitialData")
    if not initial:
        initial = find_json_object(html, "ytInitialData")
    if not initial:
        return []
    return [node["videoRenderer"] for node in walk(initial) if "videoRenderer" in node]


def watch_metadata(video_id: str) -> dict[str, Any]:
    html = fetch(f"https://www.youtube.com/watch?v={video_id}")
    data: dict[str, Any] = {}
    for key in ("viewCount", "uploadDate", "lengthSeconds", "commentCount"):
        m = re.search(rf'"{key}"\s*:\s*"([^"]+)"', html)
        if m:
            data[key] = unescape(m.group(1))
    if "commentCount" not in data:
        m = re.search(r'"commentsCount"\s*:\s*\{"runs":\[\{"text":"([^"]+)"', html)
        if m:
            data["commentCount"] = unescape(m.group(1))
    return data


def candidate_reason(title: str, channel: str, views: int | None) -> str:
    low = f"{title} {channel}".lower()
    tags = []
    for word, label in [
        ("면접", "면접 질문/답변"),
        ("자소서", "자소서"),
        ("삼성", "삼성"),
        ("하이닉스", "SK하이닉스"),
        ("현대", "현대차"),
        ("은행", "금융권"),
        ("pt", "PT면접"),
        ("1분", "1분 자기소개"),
    ]:
        if word in low:
            tags.append(label)
    if views and views >= 100_000:
        tags.append("고조회수")
    return ", ".join(dict.fromkeys(tags)) or "취업 준비 일반"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-json", default="popular_video_candidates.json")
    parser.add_argument("--out-md", default="popular_video_candidates.md")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--sleep", type=float, default=1.2)
    parser.add_argument("--min-seconds", type=int, default=120)
    args = parser.parse_args()

    existing = existing_video_ids(
        [
            Path("urls.txt"),
            Path("urls_additional_batch1.txt"),
            Path("urls_additional_batch2_finance.txt"),
            Path("urls_additional_batch3_hyundai.txt"),
        ]
    )

    by_id: dict[str, Candidate] = {}
    for query in SEARCH_QUERIES:
        for video in search_videos(query):
            video_id = video.get("videoId")
            if not video_id or video_id in existing or video_id in by_id:
                continue
            length_text = text_of(video.get("lengthText"))
            length_seconds = parse_length(length_text)
            if not length_seconds or length_seconds < args.min_seconds:
                continue
            title = text_of(video.get("title"))
            if "shorts" in title.lower() or "#shorts" in title.lower():
                continue
            channel = text_of(video.get("ownerText")) or text_of(video.get("longBylineText"))
            published_text = text_of(video.get("publishedTimeText"))
            views = parse_int_text(text_of(video.get("viewCountText")))
            by_id[video_id] = Candidate(
                video_id=video_id,
                title=title,
                channel=channel,
                url=f"https://www.youtube.com/watch?v={video_id}",
                length_text=length_text,
                length_seconds=length_seconds,
                published_text=published_text,
                upload_date=None,
                views=views,
                comments=None,
                query=query,
                reason=candidate_reason(title, channel, views),
            )
        time.sleep(args.sleep)

    ranked = sorted(by_id.values(), key=lambda c: (c.views or 0, c.length_seconds or 0), reverse=True)[: args.limit]
    for cand in ranked:
        try:
            meta = watch_metadata(cand.video_id)
            if meta.get("viewCount"):
                cand.views = int(re.sub(r"\D", "", meta["viewCount"]))
            cand.upload_date = meta.get("uploadDate")
            if meta.get("lengthSeconds"):
                cand.length_seconds = int(meta["lengthSeconds"])
            if meta.get("commentCount"):
                cand.comments = parse_int_text(meta["commentCount"])
        except Exception as exc:
            print(f"metadata failed {cand.video_id}: {exc}")
        time.sleep(args.sleep)

    ranked = sorted(ranked, key=lambda c: (c.views or 0, c.comments or 0, c.length_seconds or 0), reverse=True)
    Path(args.out_json).write_text(
        json.dumps([asdict(c) for c in ranked], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# 조회수 중심 YouTube 추가 후보",
        "",
        "- 기준: 기존 55건 중복 제외, 쇼츠 제외, 2분 이상 롱폼, 조회수 우선 정렬",
        "- 댓글 수: 공개 watch HTML에서는 안정적으로 노출되지 않아 확인 가능한 경우만 기록",
        "- 목적: 코파일럿 MVP의 자소서/면접/스펙관리 백데이터를 시장 반응이 큰 영상으로 보강",
        "",
        "| 순위 | 영상 | 채널 | 업로드 | 길이 | 조회수 | 댓글 | 선별 이유 |",
        "|---:|---|---|---|---:|---:|---:|---|",
    ]
    for i, cand in enumerate(ranked, 1):
        upload = cand.upload_date or cand.published_text or "-"
        views = f"{cand.views:,}" if cand.views is not None else "-"
        comments = f"{cand.comments:,}" if cand.comments is not None else "-"
        title = cand.title.replace("|", " ")
        channel = cand.channel.replace("|", " ")
        lines.append(
            f"| {i} | [{title}]({cand.url}) | {channel} | {upload} | {cand.length_text} | {views} | {comments} | {cand.reason} |"
        )
    Path(args.out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
