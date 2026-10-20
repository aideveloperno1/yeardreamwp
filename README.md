# 작업장 안전기준 안내 챗봇

## 담당 폴더

| 폴더 | 담당 | 보관 내용 |
|---|---|---|
| `service/retrieval/` | 개발자 1 | 법령 추출·적재·검색 코드 |
| `service/agent/` | 개발자 1 — 배정 제안 | 주제 분류·상담 흐름 코드 |
| `service/chat/` | 개발자 2 | 답변 생성·API 코드 |
| `frontend/` | 개발자 2 | 채팅 화면 코드 |
| `service/session/` | 개발자 2 — 배정 제안 | 세션·대화 저장 코드 |
| `analysis/retrieval/` | 분석가 1 | 법령 검수·검색 평가 코드와 결과 |
| `analysis/answer/` | 분석가 2 | 평가 데이터 준비·답변 평가 코드와 결과 |

Agent와 세션 담당은 팀 합의 후 확정합니다.

공통 파일과 폴더 관리 규칙은 [폴더 구조 안내](docs/folder-structure.md)를 참고하세요.

## 기존 파일

`main.py`, `requirements.txt`, `service/file_service.py`, `service/llm_service.py`, `service/rag_service.py`는 기존 위치에 유지합니다. 코드 이동과 공통 데이터 형식은 담당자 협의 후 반영합니다.

## 파일 관리

- 각자 담당 폴더를 중심으로 수정하고 공통 파일 변경은 먼저 조율합니다.
- 실제 API 키, 가상환경, 캐시, 생성된 ChromaDB 파일은 Git에서 제외합니다.
- 이미 추적 중인 파일은 `.gitignore` 추가만으로 제외되지 않습니다. 기존 `.idea/` 정리는 팀 합의 후 별도로 진행합니다.
- 설치·실행 명령은 구현과 검증 후 담당자가 추가합니다.
