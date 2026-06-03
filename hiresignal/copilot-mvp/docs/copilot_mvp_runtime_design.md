# Copilot MVP Runtime Design

생성: 2026-06-03

## 목적

회사별 취업 코파일럿 MVP가 현재 쌓은 백데이터를 프로그램에서 어떻게 활용할지 정의한다.

전제:

- 1단계에서는 RAG를 구성하지 않는다.
- 회사별 `copilot_kb.json`을 정적 지식 베이스로 로딩한다.
- 기존 유튜브 기반 `product_dataset_v2_public.json`은 보조 규칙/면접 표현/경험 변환 신호로 쓴다.
- 합격 자소서, 면접 후기, 최신 공고는 추후 같은 구조의 `evidence pack`으로 추가한다.

## 현재 데이터 자산

### 1. 회사별 Knowledge Base

위치:

- `companies/sk-hynix/copilot_kb.json`
- `companies/samsung-electronics/copilot_kb.json`
- `companies/hyundai-kia/copilot_kb.json`
- `companies/finance/copilot_kb.json`

용도:

- 회사별 직무 taxonomy
- 직무별 경험 번역 규칙
- 자소서 체크리스트
- 면접 질문 생성 기준
- 산업/기술 동향을 직무에 연결하는 규칙
- 회사별로 피해야 할 범용 조언 방지 규칙

### 2. 유튜브 기반 Product Dataset

위치:

- `product_dataset_v2_public.json`

용도:

- 실제 취준생/현직자 표현
- 면접 유형 신호
- 자소서/면접에서 자주 나오는 평가 기준
- 경험을 직무 언어로 바꾸는 예시
- 회사별 부족 데이터 탐지

주의:

- 일부 질문 추출은 패턴 기반이라 품질이 균일하지 않다.
- `company`, `role` 라벨은 오분류 가능성이 있으므로 주 키로 쓰지 않는다.
- `domain`, `job_tasks`, `evaluation_criteria`, `resume_checks`, `experience_translation_rules`를 우선 사용한다.

### 3. 회사별 Judgment

위치:

- `companies/{company}/judgment.md`

용도:

- 데이터 품질 판단
- 계속 쌓을 가치가 있는 자료와 archive할 자료 구분
- 다음 수집 우선순위 결정

## MVP 런타임 구조

```text
User Input
  |
  v
Intent Classifier
  - company
  - role / role unknown
  - task: resume, interview, role_recommendation, PT, spec_plan
  - user experience cards
  |
  v
Company KB Loader
  - load companies/{company}/copilot_kb.json
  - normalize role_knowledge shape
  |
  v
Context Builder
  - select matching role rules
  - select industry context only if role-relevant
  - select youtube/product signals by domain/company/role
  - select task-specific instruction pack
  |
  v
Prompt Composer
  - system rules
  - company facts
  - role checks
  - user experience
  - output format
  |
  v
LLM
  |
  v
Post Processor
  - missing info questions
  - checklist
  - interview follow-ups
  - risk flags
```

## 핵심 원칙

### 1. 회사부터 묻는다

회사별 코파일럿이 셀링 포인트이므로 회사가 없으면 상세 조언을 시작하지 않는다.

필수 입력:

- 목표 회사
- 지원 직무 또는 관심 직무
- 작업 목적: 자소서, 면접, PT, 직무추천, 스펙관리
- 사용자의 경험 카드

예외:

- 사용자가 직무를 모르면 `role_recommendation_rules`로 후보를 추천한다.

### 2. 직무별 질문지가 달라야 한다

같은 경험도 회사/직무별로 다르게 번역한다.

예:

- SK하이닉스 양산기술: 수율, 공정 조건, 안정 양산
- 삼성전자 DS 평가 및 분석: Product Engineering, 불량 검출, 검증 방법론
- 현대차 신차 품질: 고객 인도 전 품질 책임, 재발 방지, 협업
- 금융권 개인금융: 고객 니즈, 신뢰, 설명, 정확성

### 3. 산업 동향은 직무에 연결될 때만 쓴다

나쁜 사용:

- “HBM4가 중요하므로 지원동기에 넣으세요”
- “SDV가 중요하므로 현대차 지원동기에 넣으세요”
- “디지털금융이 중요하므로 은행 지원동기에 넣으세요”

좋은 사용:

- HBM4 + 패키지개발: 열/전기/기계 신뢰성
- SDV + 차량 SW: OTA, 차량 OS, 제어기 통합
- 디지털금융 + IT: 보안, 장애 대응, 지급결제 안정성

### 4. RAG 없이도 context packet을 작게 만든다

MVP에서는 전체 KB를 통째로 넣지 않는다.

컨텍스트는 다음 정도로 제한한다.

- 회사 공통 규칙 5개 이하
- 직무 규칙 1~2개
- 산업/기술 맥락 1~2개
- 자소서/면접 체크리스트 5~8개
- 유튜브 기반 표현/면접 신호 3~5개

## 데이터 정규화 계층

현재 회사별 JSON 구조가 완전히 같지는 않다.

- SK하이닉스: `role_knowledge`가 객체 형태
- 삼성/현대/금융: `role_knowledge`가 배열 형태

따라서 런타임에서 `normalizeCompanyKb()`가 필요하다.

```ts
type NormalizedCompanyKb = {
  companyId: string;
  companyName: string;
  roles: NormalizedRole[];
  industries: NormalizedIndustry[];
  recommendationRules: RecommendationRule[];
  copilotRules: {
    do: string[];
    avoid: string[];
  };
  sources: string[];
};

type NormalizedRole = {
  roleId: string;
  displayName: string;
  aliases: string[];
  focus: string[];
  resumeChecks: string[];
  interviewQuestions: string[];
  experienceTranslations: string[];
};
```

정규화 규칙:

```ts
function normalizeRoles(kb: any): NormalizedRole[] {
  if (Array.isArray(kb.role_knowledge)) {
    return kb.role_knowledge.map(role => ({
      roleId: slug(role.korean_role || role.role),
      displayName: role.korean_role || role.role,
      aliases: [role.role, role.korean_role].filter(Boolean),
      focus: role.copilot_focus || [],
      resumeChecks: role.resume_checks || [],
      interviewQuestions: role.interview_questions || [],
      experienceTranslations: role.experience_translation
        ? [role.experience_translation]
        : role.experience_translation_rules || role.experience_translation || []
    }));
  }

  return Object.entries(kb.role_knowledge || {}).map(([name, role]: [string, any]) => ({
    roleId: slug(name),
    displayName: name,
    aliases: [name],
    focus: role.core_work || [],
    resumeChecks: role.resume_checks || [],
    interviewQuestions: role.interview_questions || [],
    experienceTranslations: role.experience_translation ? [role.experience_translation] : []
  }));
}
```

## Context Builder 로직

```ts
type CopilotTask =
  | "role_recommendation"
  | "resume_review"
  | "interview_practice"
  | "pt_builder"
  | "spec_plan";

type UserProfile = {
  targetCompany?: string;
  targetRole?: string;
  task: CopilotTask;
  experiences: ExperienceCard[];
  constraints?: {
    beginner?: boolean;
    nonMajor?: boolean;
    applyingSoon?: boolean;
  };
};

type ExperienceCard = {
  title: string;
  situation?: string;
  action?: string;
  result?: string;
  keywords: string[];
  metrics?: string[];
};
```

### 1. 회사 선택

```ts
function resolveCompany(input: UserProfile): CompanyId | "need_question" {
  if (!input.targetCompany) return "need_question";
  return matchCompanyAlias(input.targetCompany);
}
```

### 2. 직무 선택

```ts
function resolveRole(profile: UserProfile, kb: NormalizedCompanyKb) {
  if (profile.targetRole) {
    return fuzzyMatchRole(profile.targetRole, kb.roles);
  }

  return recommendRolesFromExperience(profile.experiences, kb.recommendationRules);
}
```

### 3. 컨텍스트 패킷 생성

```ts
function buildContextPacket(profile: UserProfile, kb: NormalizedCompanyKb) {
  const role = resolveRole(profile, kb);
  const taskPack = getTaskPack(profile.task);
  const productSignals = selectProductSignals({
    company: kb.companyName,
    role,
    task: profile.task,
    experiences: profile.experiences
  });

  return {
    company: kb.companyName,
    role,
    task: profile.task,
    rules: {
      do: kb.copilotRules.do.slice(0, 5),
      avoid: kb.copilotRules.avoid.slice(0, 5)
    },
    roleChecks: role.resumeChecks.slice(0, 8),
    experienceTranslations: role.experienceTranslations.slice(0, 5),
    industryContext: selectIndustryContext(kb.industries, role, profile.experiences),
    productSignals,
    taskInstructions: taskPack
  };
}
```

## Task Pack 설계

### 1. 직무 추천

입력:

- 경험 카드
- 전공/스킬
- 관심 회사

출력:

- 추천 직무 2~3개
- 추천 근거
- 각 직무에 맞게 경험을 바꾸는 방식
- 부족한 근거

### 2. 자소서 첨삭

체크 순서:

1. 목표 회사/직무에 맞는 경험인가
2. 회사별 직무 언어가 들어갔는가
3. 경험이 과장되지 않았는가
4. 면접 꼬리질문을 버틸 수 있는가
5. 산업 동향을 직무와 연결했는가

출력:

- 문제 진단
- 수정 방향
- 문장 개선안
- 꼬리질문 3개
- 추가로 필요한 경험/근거

### 3. 면접 훈련

체크 순서:

1. 회사별 질문 유형 선택
2. 직무 질문 생성
3. 경험 검증 꼬리질문 생성
4. 산업/회사 동향 질문 생성
5. 답변 평가

출력:

- 예상 질문
- 모범 답변 구조
- 사용자가 준비해야 할 근거
- 답변 리스크

### 4. 현대차/기아 PT Builder

현대차/기아는 별도 task pack이 필요하다.

입력:

- 필살기 경험 2개
- 지원 직무

출력:

- PT 제목
- 슬라이드별 한 문장 메시지
- 문제/행동/결과/직무 연결
- 예상 꼬리질문

### 5. 금융권 준비 진단

금융권은 별도 task pack이 필요하다.

입력:

- 목표 은행
- 고객 응대 경험
- 필기 준비 상태
- 면접 유형

출력:

- 준비 상태 점수
- 자소서 관심 증거 점검
- NCS/금융상식 루틴
- 은행별 PT/BEI/세일즈 대비 질문

## 프롬프트 조립 예시

```text
너는 회사별 취업 코파일럿이다.

목표 회사: 삼성전자 DS
목표 직무: 평가 및 분석
작업: 자소서 첨삭

회사별 금지:
- 삼성전자 이름만 넣은 일반 반도체 조언 금지
- HBM4를 모든 직무에 억지로 연결 금지
- DX/모바일/가전 맥락과 DS 반도체 맥락 혼합 금지

직무 기준:
- Product Engineering, 불량 검출, 신뢰성, Data Science, 고객/응용 검증
- 평가 데이터, 원인 가설, 검증 방법, 품질/신뢰성 개선을 확인

사용자 경험:
...

출력:
1. 현재 문장의 문제
2. 직무 언어로 바꿀 포인트
3. 수정 예시
4. 면접 꼬리질문
5. 추가로 필요한 근거
```

## MVP 구현 순서

### Step 1. 정적 KB Loader

- `companies/*/copilot_kb.json` 로드
- 회사 alias 매핑
- `normalizeCompanyKb()` 구현

### Step 2. Context Builder

- 회사 선택
- 직무 선택/추천
- task pack 선택
- context packet 생성

### Step 3. Prompt Composer

- task별 출력 포맷 고정
- 회사별 금지 규칙 주입
- 직무 체크리스트 주입

### Step 4. Product Dataset 연결

- `product_dataset_v2_public.json` 로드
- `domain`, `sub_role`, `job_tasks`, `evaluation_criteria` 기준으로 관련 신호 선택
- 자막 원문이 아니라 구조화된 체크/규칙만 사용

### Step 5. User Feedback 저장

RAG 전 단계라도 다음은 저장한다.

- 사용자가 선택한 회사/직무
- 코파일럿이 추천한 직무
- 사용자가 채택한 문장
- 추가 질문
- 부족하다고 표시한 정보

이 로그가 다음 데이터 수집 우선순위가 된다.

## 1단계 MVP에서 하지 않을 것

- 벡터 DB/RAG
- 원문 자막 전체 검색
- 대량 합격 자소서 무분별 수집
- 회사 뉴스 자동 요약만 제공하는 기능
- 일반 취업 조언 챗봇화

## 판단

현재 백데이터는 RAG 없이도 MVP에 바로 쓸 수 있다.

이유:

- 회사별 직무 taxonomy가 생겼다.
- 회사별 금지 규칙이 생겼다.
- 경험 번역 규칙이 생겼다.
- 유튜브 데이터가 면접/자소서 표현을 보강한다.
- 금융권/현대차처럼 산업군별 다른 제품 로직이 보인다.

따라서 다음 구현은 데이터 추가 수집보다 `Context Builder`와 `Task Pack`을 먼저 만드는 것이 맞다.
