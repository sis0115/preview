# Copilot Data Folder and Loader Design

생성: 2026-06-04

## 목적

지금까지 쌓은 회사별 코파일럿 데이터를 프로그램이 안정적으로 가져올 수 있도록 새 데이터 폴더 구조와 loader 설계를 정의한다.

중요:

- 이 문서는 설계안이다.
- 아직 실제 파일 이동/복사는 하지 않는다.
- 사용자와 검토 후 migration을 진행한다.

## 현재 문제

현재 `companies/` 폴더는 사람이 검토하기에는 좋지만, 프로그램 런타임에서 바로 쓰기에는 몇 가지 문제가 있다.

1. 회사별 JSON 스키마가 완전히 같지 않다.
   - SK하이닉스: `role_knowledge`가 객체
   - 삼성/현대/금융: `role_knowledge`가 배열
2. 사람이 읽는 문서와 제품 주입용 JSON이 같은 위치에 섞여 있다.
3. `collections/`, `sources/`, `raw/`가 분석 근거로는 좋지만 런타임에서 필요한 파일은 일부뿐이다.
4. 자소서/면접/PT/직무추천 task별 prompt pack이 아직 분리되어 있지 않다.
5. 합격 자소서, 면접 후기, 최신 JD가 들어오면 현재 구조만으로는 확장이 복잡해질 수 있다.

## 설계 원칙

### 1. 사람이 보는 폴더와 프로그램이 읽는 폴더를 분리한다

현재 `companies/`는 source/research 폴더로 유지한다.

새로 `copilot-data/`를 만든다.

```text
companies/       # 사람이 검토하는 리서치/근거 폴더
copilot-data/    # 프로그램이 읽는 runtime 데이터 폴더
```

### 2. 런타임 데이터는 정규화된 스키마를 따른다

프로그램은 회사별 원본 JSON을 직접 해석하지 않는다.

항상 다음 순서로 처리한다.

```text
companies/{company}/copilot_kb.json
  -> migration/normalizer
  -> copilot-data/companies/{company}/company_profile.json
  -> loader
```

### 3. task별 prompt와 evidence를 분리한다

자소서, 면접, 직무추천, PT는 같은 회사 KB를 공유하지만 사용하는 evidence가 다르다.

따라서 데이터는 아래처럼 분리한다.

- prompt pack: 코파일럿 행동 규칙
- role taxonomy: 직무별 기준
- evidence pack: 합격 자소서, 면접 후기, JD, 유튜브 신호
- task pack: 자소서/면접/PT/직무추천별 출력 로직

## 제안 폴더 구조

```text
copilot-data/
  README.md
  manifest.json

  companies/
    sk-hynix/
      company_profile.json
      prompt_pack.json
      roles.json
      industry_context.json
      task_packs/
        resume_review.json
        interview_practice.json
        role_recommendation.json
        spec_gap.json
      evidence/
        accepted_resumes/
          README.md
          patterns.json
        interview_reviews/
          README.md
          questions.json
        job_postings/
          README.md
          postings.json
        official_sources/
          sources.json
        youtube_signals/
          signals.json
      examples/
        resume_review_cases.json

    samsung-electronics/
      company_profile.json
      prompt_pack.json
      roles.json
      industry_context.json
      task_packs/
      evidence/
      examples/

    hyundai-kia/
      company_profile.json
      prompt_pack.json
      roles.json
      industry_context.json
      task_packs/
      evidence/
      examples/

    finance/
      company_profile.json
      prompt_pack.json
      roles.json
      industry_context.json
      banks/
        ibk/
          bank_profile.json
          prompt_pack.json
          evidence/
        woori/
        hana/
        kb/
        shinhan/
        nh/

  shared/
    task_schemas/
      resume_review.schema.json
      interview_practice.schema.json
      evidence_pack.schema.json
    company_aliases.json
    role_aliases.json
    output_formats.json
```

## 파일 역할

### manifest.json

런타임에서 사용 가능한 회사와 데이터 버전을 선언한다.

```json
{
  "schema": "copilot-data-manifest-v1",
  "generated_at": "2026-06-04",
  "companies": [
    {
      "company_id": "sk-hynix",
      "display_name": "SK하이닉스",
      "industry": "semiconductor",
      "status": "active",
      "path": "companies/sk-hynix"
    },
    {
      "company_id": "samsung-electronics",
      "display_name": "삼성전자 DS",
      "industry": "semiconductor",
      "status": "active",
      "path": "companies/samsung-electronics"
    },
    {
      "company_id": "hyundai-kia",
      "display_name": "현대차/기아",
      "industry": "mobility",
      "status": "active",
      "path": "companies/hyundai-kia"
    },
    {
      "company_id": "finance",
      "display_name": "금융권",
      "industry": "finance",
      "status": "skeleton",
      "path": "companies/finance"
    }
  ]
}
```

### company_profile.json

회사 기본 정보와 코파일럿 적용 범위를 담는다.

```json
{
  "company_id": "sk-hynix",
  "display_name": "SK하이닉스",
  "industry": "semiconductor",
  "scope": "memory semiconductor recruitment copilot",
  "primary_tasks": [
    "resume_review",
    "interview_practice",
    "role_recommendation",
    "spec_gap"
  ],
  "status": "active",
  "source_company_kb": "companies/sk-hynix/copilot_kb.json"
}
```

### prompt_pack.json

AI 코파일럿의 행동 규칙이다. 자소서/면접이 모두 공유한다.

```json
{
  "company_id": "sk-hynix",
  "do": [
    "목표 직무를 먼저 확인한다",
    "경험을 SK하이닉스 직무 언어로 번역한다",
    "없는 경험은 만들지 않는다",
    "산업 동향은 직무와 연결될 때만 사용한다",
    "합격자 예시는 비식별 패턴만 보여준다"
  ],
  "avoid": [
    "회사명만 넣은 범용 자소서 첨삭",
    "HBM 키워드 과다 삽입",
    "학부 경험을 양산 성과처럼 과장",
    "합격 자소서 원문 노출"
  ],
  "privacy_rules": [
    "학교, 실명, 연구실명, 고객사명, 프로젝트 고유명은 일반화한다",
    "정확한 수치가 개인/기관을 특정할 수 있으면 범위형 표현으로 바꾼다"
  ]
}
```

### roles.json

직무 taxonomy와 직무별 체크리스트를 담는다.

```json
{
  "company_id": "sk-hynix",
  "roles": [
    {
      "role_id": "manufacturing-technology",
      "display_name": "양산기술",
      "aliases": ["양산", "양산기술", "공정 양산"],
      "focus": ["안정 양산", "공정 조건", "수율", "품질", "산포"],
      "resume_checks": [
        "공정 조건과 결과의 관계를 설명하는가",
        "수율/품질/산포/재현성 중 하나 이상의 근거가 있는가"
      ],
      "interview_question_seeds": [
        "공정 조건 중 어떤 변수가 결과에 가장 큰 영향을 줬나요?",
        "실험실 조건과 양산 현장의 차이는 무엇이라고 생각하나요?"
      ],
      "experience_translation_rules": [
        "실험 경험을 공정 조건 -> 결과 편차 -> 원인 가설 -> 개선 행동 -> 안정 생산 관점으로 재작성"
      ]
    }
  ]
}
```

### industry_context.json

산업/기술 동향과 직무 연결 규칙만 담는다.

```json
{
  "company_id": "sk-hynix",
  "topics": [
    {
      "topic_id": "hbm4",
      "name": "HBM4",
      "use_when_roles": ["양산기술", "Product Engineering", "품질보증", "양산기술(P&T)"],
      "role_connections": {
        "양산기술": "고성능 메모리 수요 확대는 안정 양산과 수율 개선 역량을 중요하게 만든다",
        "품질보증": "개발, 인증, 양산, 고객 품질까지 이어지는 품질 시스템이 중요하다"
      },
      "avoid": [
        "HBM 구조를 부정확하게 길게 설명하지 않는다",
        "직무 연결 없이 AI/HBM 키워드만 넣지 않는다"
      ]
    }
  ]
}
```

### task_packs/resume_review.json

자소서 첨삭 task의 출력과 판단 로직이다.

```json
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
    "추가로 필요한 근거"
  ],
  "case_detection": [
    "experience_missing",
    "company_news_only",
    "role_unclear",
    "overclaiming",
    "wrong_question_intent",
    "privacy_risk"
  ]
}
```

### evidence/accepted_resumes/patterns.json

합격 자소서 원문이 아니라 비식별 패턴만 저장한다.

```json
{
  "company_id": "sk-hynix",
  "patterns": [
    {
      "pattern_id": "sk-hynix-mfg-pattern-001",
      "role_id": "manufacturing-technology",
      "source_type": "accepted_cover_letter",
      "privacy_level": "deidentified_pattern",
      "show_raw_text": false,
      "experience_type": "공정 실험",
      "problem": "결과 산포/재현성 저하",
      "actions": ["조건 분리", "기록", "원인 가설", "관리 인자 도출"],
      "result_type": "재현성 향상/기준 수립",
      "role_connection": "공정 조건 관리와 수율/품질 개선",
      "safe_example_sentence": "실험 결과가 반복적으로 흔들리는 원인을 찾기 위해 공정 조건을 항목별로 분리해 기록했고, 결과에 영향을 주는 관리 인자를 좁혀 재현성을 높였습니다."
    }
  ]
}
```

### evidence/interview_reviews/questions.json

면접 후기 원문이 아니라 질문/의도/꼬리질문 패턴을 저장한다.

```json
{
  "company_id": "sk-hynix",
  "questions": [
    {
      "question_id": "sk-hynix-mfg-interview-001",
      "role_id": "manufacturing-technology",
      "source_type": "interview_review",
      "year": 2026,
      "interview_stage": "직무면접",
      "question": "공정 조건 중 어떤 변수가 결과에 가장 큰 영향을 줬나요?",
      "intent": "원인 분석 과정과 데이터 기반 판단을 확인",
      "followups": [
        "그 판단을 데이터로 어떻게 확인했나요?",
        "다른 변수를 배제한 근거는 무엇인가요?"
      ],
      "answer_risk": [
        "그냥 여러 번 해봤다고 답하면 약함",
        "수율이라는 단어를 쓰면서 정의하지 못하면 위험"
      ]
    }
  ]
}
```

## Loader 설계

### TypeScript 인터페이스

```ts
export type CopilotTask =
  | "resume_review"
  | "interview_practice"
  | "role_recommendation"
  | "spec_gap"
  | "pt_builder";

export type CopilotInput = {
  companyId?: string;
  companyText?: string;
  roleId?: string;
  roleText?: string;
  task: CopilotTask;
  question?: string;
  draft?: string;
  experienceCards?: ExperienceCard[];
  bankId?: string;
};

export type ExperienceCard = {
  title: string;
  keywords: string[];
  situation?: string;
  action?: string;
  result?: string;
  metrics?: string[];
};

export type CopilotContextPacket = {
  company: CompanyProfile;
  promptPack: PromptPack;
  role?: RoleProfile;
  industryTopics: IndustryTopic[];
  taskPack: TaskPack;
  acceptedResumePatterns: AcceptedResumePattern[];
  interviewQuestions: InterviewQuestion[];
  jobPostings: JobPostingEvidence[];
  youtubeSignals: YoutubeSignal[];
};
```

### Loader API

```ts
class CopilotDataLoader {
  constructor(private rootDir: string) {}

  async loadManifest(): Promise<CopilotManifest> {}

  async resolveCompany(input: {
    companyId?: string;
    companyText?: string;
  }): Promise<CompanyProfile | null> {}

  async loadCompany(companyId: string): Promise<CompanyBundle> {}

  async resolveRole(bundle: CompanyBundle, input: {
    roleId?: string;
    roleText?: string;
    experienceCards?: ExperienceCard[];
  }): Promise<RoleProfile | RoleRecommendation[]> {}

  async buildContextPacket(input: CopilotInput): Promise<CopilotContextPacket> {}
}
```

### buildContextPacket 흐름

```ts
async function buildContextPacket(input: CopilotInput) {
  const company = await loader.resolveCompany(input);
  if (!company) {
    return askForCompany();
  }

  const bundle = await loader.loadCompany(company.companyId);
  const role = await loader.resolveRole(bundle, input);
  const taskPack = bundle.taskPacks[input.task];

  const industryTopics = selectIndustryTopics({
    role,
    experiences: input.experienceCards,
    topics: bundle.industryContext.topics
  });

  const acceptedResumePatterns = selectAcceptedResumePatterns({
    role,
    task: input.task,
    patterns: bundle.evidence.acceptedResumes
  });

  const interviewQuestions = selectInterviewQuestions({
    role,
    task: input.task,
    questions: bundle.evidence.interviewReviews
  });

  return {
    company,
    promptPack: bundle.promptPack,
    role,
    industryTopics,
    taskPack,
    acceptedResumePatterns,
    interviewQuestions,
    jobPostings: [],
    youtubeSignals: []
  };
}
```

## Prompt 조립 설계

프로그램은 context packet을 LLM prompt로 바꾼다.

```ts
function composeResumeReviewPrompt(input: CopilotInput, context: CopilotContextPacket) {
  return {
    system: [
      "너는 회사별 취업 코파일럿이다.",
      "없는 경험을 만들지 않는다.",
      "합격자 예시는 비식별 패턴만 사용한다.",
      ...context.promptPack.do,
      ...context.promptPack.avoid.map(rule => `금지: ${rule}`)
    ].join("\n"),
    user: JSON.stringify({
      task: input.task,
      company: context.company.displayName,
      role: context.role?.displayName,
      question: input.question,
      draft: input.draft,
      role_checks: context.role?.resumeChecks,
      accepted_patterns: context.acceptedResumePatterns,
      interview_questions: context.interviewQuestions,
      output_sections: context.taskPack.outputSections
    })
  };
}
```

## Migration 설계

실제 실행은 나중에 한다.

### Step 1. 새 폴더 생성

```text
copilot-data/
```

### Step 2. 기존 KB를 정규화 파일로 변환

입력:

- `companies/{company}/copilot_kb.json`

출력:

- `copilot-data/companies/{company}/company_profile.json`
- `prompt_pack.json`
- `roles.json`
- `industry_context.json`

### Step 3. 기존 데모/판단 문서에서 evidence seed 생성

입력:

- `docs/sk_hynix_resume_review_demo.md`
- `companies/*/collections/*`
- `product_dataset_v2_public.json`

출력:

- `evidence/accepted_resumes/patterns.json`
- `evidence/interview_reviews/questions.json`
- `evidence/youtube_signals/signals.json`
- `examples/resume_review_cases.json`

### Step 4. Loader 구현

위치 제안:

```text
src/copilot-data/
  loader.ts
  normalize.ts
  selectors.ts
  promptComposer.ts
```

현재 repo가 Python 중심이라면 우선 Python으로 시작해도 된다.

```text
copilot_runtime/
  loader.py
  normalize.py
  selectors.py
  prompt_composer.py
```

## 검토 포인트

실제 진행 전에 결정해야 할 것:

1. 런타임 구현 언어: TypeScript vs Python
2. `companies/`를 source로 유지하고 `copilot-data/`를 생성할지
3. 합격 자소서 패턴을 언제부터 넣을지
4. 면접 후기 질문을 어떤 신뢰도 기준으로 넣을지
5. 첫 화면을 회사 선택형으로 할지, 자소서 붙여넣기 후 회사/직무 추론형으로 할지

## 추천 결정

내 추천은 다음이다.

1. `companies/`는 그대로 둔다.
2. 새 runtime 폴더는 `copilot-data/`로 만든다.
3. 첫 migration 대상은 SK하이닉스만 한다.
4. SK하이닉스에서 loader/context/prompt가 잘 동작하면 삼성전자 DS, 현대차/기아로 확장한다.
5. 금융권은 bank skeleton만 유지하고 runtime active 상태는 `skeleton`으로 둔다.

이 방식이 좋은 이유:

- 기존 리서치 자료를 망가뜨리지 않는다.
- 프로그램은 정규화된 JSON만 읽는다.
- 회사별 코파일럿 셀링 포인트를 유지한다.
- 자소서와 면접 데이터를 분리하면서도 화면은 통합할 수 있다.
- 나중에 RAG로 넘어갈 때도 evidence pack 구조를 그대로 쓸 수 있다.
