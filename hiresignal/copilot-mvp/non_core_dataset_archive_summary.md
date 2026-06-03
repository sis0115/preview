# Non-Core Dataset Archive

현재 제품 주 데이터셋에서 제외한 영상 묶음이다.

## 기준
- 주 데이터셋 유지: 금융권, 현대차/기아, SK하이닉스, 삼성전자/반도체
- 별도 보관: 일반 면접 고조회수 영상, CJ/아모레/LG생활건강 등 소비재/유통, 자막 없음/기타

## 수량
- core rows: 64
- archived rows: 24
- archived videos in product archive: 22

## Archive Domain Distribution
- general_interview: 17
- retail_consumer: 5

## 쓰지 않는 이유
- 일반 면접 영상은 사용성 힌트는 좋지만 회사별/직무별 차별성을 흐릴 수 있다.
- 소비재/유통은 별도 도메인으로 가능성은 있지만, 지금 MVP 강점인 금융권/현대차/반도체 축과 다르다.
- 데이터가 많아질수록 범용 조언이 늘어나면 코파일럿 답변이 평균화될 위험이 있다.
