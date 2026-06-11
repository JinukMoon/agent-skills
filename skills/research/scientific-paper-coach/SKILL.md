---
name: scientific-paper-coach
description: SNU 영어 논문 작성법 강의(모윤숙·이지영·정한별 교수)의 200+항목 체크리스트를 기준으로 과학 논문을 심사하거나 작성을 가이드한다. 두 모드 — (A) Review: 기존 원고(PDF/docx/tex/md)를 주며 "논문 리뷰", "체크리스트로 검사", "작성법 기준으로 봐줘"라고 하면 섹션별 PASS/FAIL 리포트 생성. (B) Write: 논문 섹션을 새로 쓰거나 고칠 때 ("introduction 써줘", "abstract 초안", "이 단락 다듬어줘", cover letter 작성) 체크리스트 기준을 먼저 로드해 그에 맞춰 작성. 영어 과학 논문의 작성·수정·심사 어느 쪽이든 이 skill을 쓴다. 단, 대상은 사용자 본인의 원고다 — 남이 쓴 이미 출판된 논문을 읽고 번역·정독·비평할 때는 paper-reading을 쓴다. /scientific-paper-coach로도 호출.
---

# Scientific Paper Coach

SNU "이공계 학생을 위한 영어 논문 작성법" 강의(모윤숙·이지영·정한별 교수) 1~13차시 + 실시간 세션 전체를 근거로 한다. 같은 폴더의 `checklist.md`(200+항목)가 모든 기준의 단일 출처(single source of truth)다 — 심사할 때도, 작성할 때도 이 파일이 기준이다.

> 이 체크리스트는 수강생이 학습 목적으로 정리한 개인 학습 노트이며, 강의의 공식 자료가 아니다. 가르침의 출처는 위 강의에 있다.

## 모드 판별

- 사용자가 **완성된/작성 중인 원고 파일을 주며 검사·평가를 원하면** → **Mode A (Review)**
- 사용자가 **논문 텍스트를 새로 쓰거나 고쳐 쓰길 원하면** (섹션 초안, 단락 수정, abstract 작성, cover letter 등) → **Mode B (Write)**
- 애매하면 (예: "이 원고 어때?" 후 "고쳐줘") 두 모드를 이어서 쓴다: Review로 문제를 찾고 Write로 고친다. 모드 전환 시 사용자에게 알린다.

---

# Mode A — Review (기존 원고 심사)

## 동작 절차

### ① 원고 읽기
- **PDF**: `Read` 도구에 `pages` 파라미터를 써서 섹션 단위로 읽는다 (10페이지 초과면 pages 지정 필수). 길면 Introduction → Methods → Results → Discussion 순으로 나눠 읽는다.
- **docx**: `docx` skill(또는 document-skills:docx)로 텍스트를 추출한 뒤 읽는다.
- **tex / md / txt**: `Read`로 직접 읽는다. .tex는 본문과 함께 \section, \cite, \begin{figure} 등 구조 명령도 함께 본다.
- 원고의 절대경로를 기록한다. 리포트를 같은 폴더에 저장하기 위함이다.

### ② 체크리스트 로드
- 같은 폴더의 `checklist.md`를 `Read`로 전부 읽는다. 절대 기억에 의존해 항목을 지어내지 말 것 — 항상 파일을 근거로 삼는다.

### ③ 섹션별 검사
- 원고에서 해당 섹션을 식별하고, checklist.md의 그 섹션 항목을 하나씩 검사한다.
- 각 항목에 대해:
  - **PASS / FAIL / N/A** 판정을 내린다.
  - **근거**: 원고에서 해당하는 문장을 짧게 인용한다 (FAIL/PASS 모두). 근거를 못 찾으면 "확인 필요"로 표기한다.
  - **FAIL이면 구체적 수정 제안**을 단다 — 강의 기준에 맞춘 고쳐쓰기 예시나 명확한 지시.
- 판정 원칙:
  - 강의 가르침이 1차 기준이다. **분야 관례와 충돌하면 둘 다 언급**한다 (예: "강의는 numeric+information-prominent를 권장하나, 이 분야는 author-date가 표준일 수 있음 — 저널 확인 필요").
  - 확신이 없으면 단정하지 말고 **"확인 필요"**로 표기한다.
  - **칭찬보다 결함 탐지를 우선**한다. PASS는 간결히, FAIL은 자세히.
  - 원고에 없는 섹션(예: Conclusion 미존재)은 N/A로 두되, 강의 기준상 그 역할이 다른 섹션에 있어야 하면 그 점을 지적한다.

### ④ 리포트 작성
- 원고와 **같은 폴더**에 `review_<원고이름>.md`로 저장한다 (확장자 제외한 원고 파일명 사용).

## 리포트 형식

```markdown
# Review: <원고 제목 또는 파일명>

> 근거: SNU 영어 논문 작성법 강의 체크리스트 (~/.claude/skills/scientific-paper-coach/checklist.md)
> 심사일: <날짜> / 원고: <절대경로>

## 총평 (Summary)
- 전체 통과율: PASS N개 / FAIL N개 / N/A N개 (검사 항목 N개)
- 가장 심각한 문제 3~5개 (우선순위순, 각 1~2줄 + 근거 차시)
  1. ...
  2. ...

## 섹션별 상세 (Section-by-section)

### <섹션명> (예: Introduction)
| 항목 | 판정 | 근거 (원고 인용) | 수정 제안 |
|------|------|------------------|-----------|
| gap 문장이 현재/현재완료 시제인가 (3차시) | FAIL | "...was rarely studied" | "has rarely been studied"로 — 과거형은 현재 무관 함의 |
| ... | PASS | "..." | — |

(섹션마다 표 반복: Title/Keywords·Highlights/Abstract/Introduction/Methodology/Results-시각자료/Results-본문/Discussion/Conclusion/References·Citation/Summarizing·Paraphrasing/문장·문법·구두점/(부록)투고)

## 우선순위 수정 권고 (Action Items)
1. [심각] ... (근거 차시)
2. [중요] ...
3. [권장] ...
```

---

# Mode B — Write (체크리스트 기준 작성 가이드)

새 논문/섹션/단락을 쓰거나 고쳐 쓸 때, 체크리스트를 **사후 검사가 아니라 사전 설계도**로 쓴다.

## 동작 절차

### ① 관련 체크리스트 섹션 로드 (작성 시작 전, 필수)
- `checklist.md`에서 **쓰려는 섹션 + 공통 섹션**을 읽는다:
  - 해당 섹션 항목 (예: Introduction이면 Introduction 18항목)
  - 항상 함께: "문장·문법·구두점" (시제 3원칙, FANBOYS, 병렬구조, 조동사 강도) + "전체 구조"
  - 인용이 들어가면: References·Citation + Summarizing·Paraphrasing
- 이렇게 먼저 읽는 이유: 다 쓰고 나서 고치면 구조적 문제(예: gap 없는 Introduction, narrow하게 시작하는 서론)는 다시 써야 한다. 기준을 알고 쓰면 한 번에 통과한다.

### ② 기준에 맞춰 작성
- 섹션의 구조 규칙을 뼈대로 잡는다 (예: Introduction이면 Stage 1→2→3→4 순서, broad→narrow; Discussion이면 재진술→비교→해석→한계→함의→추후연구).
- 문장 단위 규칙을 적용하며 쓴다: 시제 선택(주제 중요성=현재완료, gap=현재/현재완료, 방법·결과=과거), 조동사 확실성 척도, hedging(fail/ignore 같은 단정어 회피), 병렬구조, FANBOYS 콤마.
- 사용자가 준 내용(데이터, 주장, 인용 문헌)만 쓴다 — 내용을 지어내지 않는다. 빠진 재료(예: gap 문장에 쓸 선행연구 한계)가 있으면 작성 전에 사용자에게 묻는다.
- 사용자의 기존 문체·분야 관례가 체크리스트와 충돌하면 어느 쪽을 따를지 묻거나, 양쪽 버전을 제시한다.

### ③ Self-check 후 전달 (필수)
- 초안 완성 후, ①에서 로드한 항목으로 **스스로 검사**하고 결과를 초안과 함께 보여준다:

```markdown
## 초안
<작성한 텍스트>

## Self-check (체크리스트 대조)
- 통과: 항목 a, b, c ... (간결히)
- 의도적 미적용: <항목> — <이유: 분야 관례/사용자 요청/재료 부족>
- 사용자 확인 필요: <항목> — <무엇을 알려주면 되는지>
```

- "의도적 미적용"과 "확인 필요"가 하나도 없도록 쓰는 것이 목표지만, 숨기는 것보다 드러내는 것이 우선이다.

## Write 모드 적용 범위
- 논문 섹션 (Title, Abstract, Introduction, Methods, Results, Discussion, Conclusion, Highlights, Keywords)
- 투고 관련 글 (cover letter, 에디터 이메일, response to reviewers) — 체크리스트 부록 + 12차시 템플릿 기준
- 단락 단위 수정·다듬기 — 해당 단락이 속한 섹션의 기준 적용

---

# 공통 운영 지침

- **긴 논문**은 섹션별로 나눠 처리한다. 한 번에 다 읽으려 하지 말고, 읽기와 검사(또는 작성)를 섹션 단위로 반복한다. 매우 긴 경우 섹션별 부분 리포트를 작성한 뒤 마지막에 총평을 합친다.
- 체크리스트 항목이 200개가 넘으므로, Review에서 **명백히 N/A인 항목은 생략하지 말고 N/A로 간단히 기록**해 누락이 아님을 보인다. 분량이 과하면 N/A 항목은 섹션 끝에 "N/A: 항목 a, b, c (사유)"로 묶어도 된다.
- 모든 FAIL/수정 제안에는 가능하면 **고쳐쓰기 예시**를 제시한다 (강의 템플릿 활용).
- 분야별 관례 충돌이 잦은 지점: citation 스타일(numeric vs author-date), 인칭대명사 we 사용 여부, Methods 위치, Results/Discussion 통합 여부. 이들은 항상 "저널 Instructions for Authors 확인 필요"를 병기한다.
- Unicode 첨자는 plain text에서 일반 문자(CO2)로 쓴다.
- 리포트·설명은 한국어로 쓰되 핵심 영어 용어를 병기한다. 논문 본문 텍스트는 영어로 쓴다.
