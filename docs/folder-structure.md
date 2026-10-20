# Git 저장소 폴더 구조와 담당

저장소: `yeardreamwp`

하나의 저장소에서 담당 폴더를 나누어 관리한다. 모든 경로는 저장소 최상위를 기준으로 한다.

## 1. 담당 폴더

| 폴더 | 담당 | 보관 내용 |
|---|---|---|
| `service/retrieval/` | 개발자 1 | 법령 추출·적재·검색 코드 |
| `service/agent/` | 개발자 1 — 배정 제안 | 주제 분류·상담 흐름 코드 |
| `service/chat/` | 개발자 2 | 답변 생성·API 코드 |
| `frontend/` | 개발자 2 | 채팅 화면 코드 |
| `service/session/` | 개발자 2 — 배정 제안 | 세션·대화 저장 코드 |
| `analysis/retrieval/` | 분석가 1 | 법령 검수 기록·검색 평가 코드와 결과 |
| `analysis/answer/` | 분석가 2 | 평가 데이터 준비·답변 평가 코드와 결과 |

`service/agent/`와 `service/session/`의 담당은 팀 합의 후 확정한다.

## 2. 공통 폴더와 파일

| 위치 | 보관 내용 | 주 담당 |
|---|---|---|
| `evaluation/questions.json` | 공통 평가 질문 | 분석가 2 |
| `evaluation/evidence.json` | 질문별 근거 조문 목록 | 분석가 1 |
| `evaluation/answer_criteria.json` | 답변 평가 기준 | 분석가 2 |
| `service/schemas.py` | 공통 데이터 형식 | 개발자 1·2 |
| `service/chat/prompts/` | 실제 사용 프롬프트 | 분석가 2 초안, 개발자 2 반영 |
| `docs/` | 프로젝트 문서 | 각 담당자 |
| `README.md` | 프로젝트 소개·설치·실행 안내 | 개발자 1 중심 |
| `requirements.txt` | Python 패키지 목록 | 개발자 1 중심 |
| `.env.example` | 비밀값이 없는 환경변수 예시 | 개발자 1 중심 |
| `.gitignore` | Git 추적 제외 설정 | 개발자 1 중심 |
| `main.py` | 공통 실행 파일 | 개발자 2 중심 |

## 3. 폴더 관리 규칙

- 각자 담당 폴더를 중심으로 수정한다.
- 다른 담당자의 폴더나 공통 파일을 수정할 때는 담당자와 먼저 조율한다.
- 폴더 이름이나 경로를 바꿀 때는 해당 경로를 사용하는 팀원에게 공유한다.
- 평가 자료는 `evaluation/`, 평가 코드와 분석 결과는 각자의 `analysis/` 폴더에 둔다.
- 실제 API 키가 담긴 `.env`, 가상환경, 캐시, 생성된 ChromaDB 파일은 Git에서 제외한다.
- 원천 데이터는 공개·재배포 가능 여부를 확인한 뒤 등록한다.
