# 작업장 안전기준 안내 챗봇 API 명세서 초안 v0.2

작성일·재검토일: 2026-10-22. v0.2 검토 보완본. 상태: **팀 검토용 제안, 확정·구현 완료 명세가 아님**.

현재 로컬 코드와 앞서 확인한 GitHub main `65d379de6001bad69322b8f30e9e896a77295a84`를 기준으로 작성했다. 이번 재검토에서는 로컬 main.py·service 세 파일·React API 클라이언트·Vite 설정과 대조했다. 원격 최신 버전은 새로 조회하지 않았다. 실제 DB·모델 실행 검증과 구분한다.

## 1. 목적과 이번 범위

박상진은 화면에 필요한 데이터와 API 초안을 제안하고, 정소미와 현재 service 함수의 반환값·변경 범위를 맞춘다. 상담·검색 근거·PDF 등록을 우선 연결한다. 평가 화면은 후속 협의 항목이다. Agent 판단·추가 질문·재검색·세션·이전 문맥은 이번 구현 범위에서 제외하며 요구사항에서 삭제한 것은 아니다. 질문 주제 분류(REQ-008~011), 의미상 상담 상태·범위 밖 판단(REQ-022/023/048), 별표·참조 자료 연결(REQ-043)도 이 초안만으로 완료되지 않는다. 추가 계약·검증이 필요한 후속 범위로 기록하며, generation_status를 상담 판단 결과로 사용하지 않는다.

```text
React → main.py의 API → 현재 service 함수 → DB·AI
React ← API 응답 ← 답변·검색 자료·등록 결과
```

## 2. API 목록과 현재 상태

| 기능 | 경로 | 현재 상태 | 이번 제안 |
|---|---|---|---|
| 기존 상담 | POST /ask/chat | 구현됨, text/plain 스트림 | 유지. 기본 실호출 시험에 사용 |
| 답변·근거·종료 정보 상담 | POST /ask/chat/stream | **미구현** | SSE 이벤트로 추가. 화면 전환 후에도 기존 경로는 유지 |
| PDF 등록 | POST /upload | 구현됨, 파일명 배열 반환 | 기존 upload 필드를 유지하고 실측 집계 추가 |
| 실제 평가 실행·조회 | 미정 | 현재 service/main에 없음 | 분석 담당 결과 예시 확인 후 별도 확정 |

신규 상담 경로는 현재 Vite /ask 프록시 범위 안에 둔다. 단, 프록시와 서버 라우팅 검증은 구현 후 수행한다. 경로·SSE 채택은 이번 초안의 권고이며 팀 합의 전 확정값이 아니다. JSON 완성 응답으로 합의하면 동일 자료를 한 응답에 담도록 이 명세를 수정하고 두 방식을 중복 구현하지 않는다.

## 3. 공통 실행 기준

- 개발 기본 주소: http://127.0.0.1:8000. 각자 PC에서 실행하며 공동 서버 주소는 배포 시 결정 가능.
- React 개발 주소: http://127.0.0.1:3000 (`npm run dev`). /ask·/upload 상대 경로 요청은 API_PROXY_TARGET(기본 http://127.0.0.1:8000)로 개발 프록시가 전달한다. 현재 `npm run preview`의 4173 포트는 API 연결용이 아니며, 빌드 결과 배포 시에는 별도 서버 라우팅이 필요하다. FastAPI 기본 문서 확인 주소는 http://127.0.0.1:8000/docs 이며 3000/docs는 프록시 대상이 아니다.
- subject: DB 검색 필터 키. 댓글에서 사용된 후보값은 `산업안전보건법에 관한 규칙`. 실제 연결 DB에서 확인한 뒤 확정한다. 화면의 정식 법령명과 구분한다.
- 코드·임베딩 모델·색인·PDF·subject를 같은 기준으로 맞춘다. main의 nomic와 댓글의 bge-m3·100개 배치 변경 중 무엇을 채택할지는 별도 확인한다.
- 외부 생성 AI 설정·키는 백엔드 환경에서 관리한다. 프런트에 비밀값을 보내지 않는다.
- 코드의 ./store와 ./upload는 서버 작업 디렉터리 기준이다. 실제 절대 경로를 기록하고 시험 업로드는 별도 경로에서 진행한다.
- 기존 상담은 누락/공백을 검사한다. 업로드의 저장 전 검증과 아래 확장 규칙은 구현 제안이다. 확장 응답의 시각은 UTC 오프셋이 있는 ISO 8601, 법령 시행일은 YYYY-MM-DD로 표현한다. elapsed_ms는 요청 검증 후 서버 실행 시작부터 종료/오류까지의 경과를 단조 시계로 측정한 0 이상의 정수 ms이며 네트워크 왕복 시간과 구분한다.

## 4. 기존 상담 — 현재 구현 명세

**POST /ask/chat**

요청 Content-Type: application/json. q와 subject는 필수 문자열이다. 서버는 앞뒤 공백을 제거한다.

```json
{
  "q": "질문 내용",
  "subject": "<실제 DB에서 확인한 키>"
}
```

성공: HTTP 200, Content-Type: text/plain; charset=utf-8, 모델 생성 텍스트를 순차 전달한다. JSON 객체나 SSE가 아니다.

| 상황 | 현재 처리 |
|---|---|
| q/subject 공백 | 400, detail: 질문과 법령명을 입력해주세요. |
| 필드 누락·허용되지 않는 타입 | 기본 HTTP 422, detail 배열. 세부 변환/허용은 설치된 Pydantic 버전에 따라 실제 검증 |
| 검색·생성 실패 | 스트림 시작 뒤 오류 가능. 일반 오류 응답·종료 이유를 보장하지 않음 |
| 스트림 끝 | 프런트 수신 종료. 모델 정상 완결·법령 정답을 보증하지 않음 |

화면은 실제 텍스트 전체와 부분 수신 실패를 표시한다. 고정 근거·점수·주제 분류를 실제 응답에 붙이지 않는다.

## 5. 상담 확장 — 신규 구현 제안

**POST /ask/chat/stream**

요청 Content-Type: application/json. q/subject는 기존과 동일하다. 선택 request_id는 프런트 요청과 서버 실행을 연결하는 공개 식별자다. 제안 형식은 영문·숫자·밑줄·하이픈 1~100자다. 서버는 형식을 검사하고 응답에 그대로 연결한다. 재전송 중복 방지나 실행 재사용을 보장하는 키는 아니다.

```json
{
  "q": "질문 내용",
  "subject": "<실제 DB에서 확인한 키>",
  "request_id": "client-example-001"
}
```

성공적으로 스트림을 시작하면 HTTP 200, Content-Type: text/event-stream; charset=utf-8. fetch POST 스트림을 사용한다. UTF-8 청크를 누적하고 빈 줄로 구분한 SSE 이벤트 단위로 해석한다. 한 네트워크 청크가 한 이벤트라는 가정은 금지한다.

### 5.1 이벤트

| 이벤트 | 주요 필드 | 순서/조건 |
|---|---|---|
| start | schema_version, request_id, run_id | 스트림 시작 시 한 번 |
| sources | sources | 검색이 정상 완료되면 한 번. 결과 없음은 [] |
| delta | text | 답변 생성 텍스트 조각, 0회 이상 |
| done | run_id, answer_text, generation_status, finish_reason, cited_source_ids, elapsed_ms | 정상 전송 가능한 종료에서 한 번 |
| error | run_id, code, message, stage, partial_answer_text, retryable, elapsed_ms | 실행 실패 시 최종 이벤트 한 번. 이후 done 없음 |

서버는 요청 실행마다 새로운 고유 run_id를 발급한다. request_id가 같아도 재요청에는 새 run_id를 사용한다. request_id는 클라이언트 상관관계용, run_id는 개별 서버 실행용으로 구분하고 서버 로그와 응답에 같은 run_id를 사용한다. 이 필드만으로 서버 영속 저장·Opik 연결·조회 API가 구현됐다고 주장하지 않는다.

sources 이후 delta와 done으로 끝나거나, start 이후 어느 단계든 error로 끝날 수 있다. 검색 실패를 sources: []로 대체하지 않는다. 검색 결과가 없는 경우도 sources: []를 전달하고 기존 근거 부족 안내 원칙을 따른다. 빈 검색 결과만으로 Agent의 보류 상태를 구현한 것으로 간주하지 않는다.

generation_status는 completed 또는 incomplete다. 모델의 확인된 정상 종료 사유가 stop이고 생성 텍스트가 비어 있지 않으면 completed로 제안한다. 길이 제한·알 수 없는 종료·종료 사유 미수신은 incomplete로 표시하고 finish_reason에는 실제 제공된 값 또는 null을 담는다. 완료는 생성 전송 기준이며 법령 정답·인용 검수 합격을 뜻하지 않는다. 최종 누적 텍스트가 없거나 공백뿐이면 EMPTY_RESPONSE 오류로 처리한다.

done.answer_text는 화면에 보존할 전체 텍스트이며 delta를 모두 이어 붙인 값과 일치해야 한다. 오류의 partial_answer_text는 서버가 앞선 delta로 내보낸 텍스트의 누적값이며 첫 delta 전이면 빈 문자열이다. 실제 클라이언트 수신 여부까지 보증하는 값은 아니다. 프런트는 최종 전체 텍스트를 기존 부분 답변 뒤에 덧붙이지 않고 교체하여 중복 표시를 막는다. 연결 단절로 최종 이벤트를 못 받으면 프런트는 수신 결과 미확인/중단으로 표시하며 완료 처리하지 않는다.

### 5.2 검색 자료와 인용

sources는 **그 실행에서 모델에 실제 전달한 검색 자료**다. 생성·화면·추적·평가에 같은 자료를 사용하고 화면용 별도 재검색을 하지 않는다.

| sources 항목 | 형식 | 규칙 |
|---|---|---|
| source_id | string | 실행 내 고유 ID. 예: S1. 영속 문서 ID와 다름 |
| text | string | 실제 전달한 청크 본문. 조문 전문이 아니면 발췌 표시 |
| rank | integer | 검색 순위 1부터 |
| subject | string | 실제 검색 필터 키 |
| filename | string 또는 null | 검색 자료의 파일명 |
| article_number, article_title | string 또는 null | 실제 추출 메타데이터 |
| law_name | string 또는 null | 검수한 표시 법령명. subject 오타를 표시명으로 자동 확정하지 않음 |
| effective_date, source_url | string 또는 null | 검수한 시행일·해당 버전 원문 출처 |
| document_id, document_version, file_sha256 | string 또는 null | 확보한 자료/버전 식별 |
| page_start, page_end | integer 또는 null | PDF 파일의 물리적 페이지를 1부터 센 값. 페이지 범위를 모르면 둘 다 null, 알면 1 ≤ page_start ≤ page_end |

현재 metadata로 확인 가능한 항목부터 제공하고 없는 값은 null로 둔다. 시행일·출처 등 미확인 값이 있으면 화면에 미확인을 표시한다. 이 임시 처리가 REQ-021/037의 전체 충족을 의미하지는 않는다.

cited_source_ids는 실제 인용과 sources의 연결을 검증한 경우에만 ID 배열로 제공한다. 미검증이면 null, 검증했으나 인용 없음이면 []다. 단순 조문 번호 포함 여부는 법령상 인용의 타당성 검증과 다르다. 배열인 경우 중복 없는 해당 실행 sources.source_id의 부분집합이어야 한다. 검증 기준은 별도 확정하며 초기에는 null을 허용한다. 화면은 미검증 검색 자료를 ‘검색 참고자료’로 표시한다.

검색 점수는 REQ-016의 내부 전달 대상으로 별도 유지한다. 추출 시 점수·척도·방향을 기록하되 화면 공개는 필수로 하지 않는다. Dense 거리와 BM25 점수를 같은 신뢰도로 표현하지 않는다.

### 5.3 필드·스트림 해석 규칙 — 신규 제안

- q/subject는 앞뒤 공백 제거 후 비어 있지 않은 문자열이다. request_id는 생략 가능하고 명시적 null도 미제공으로 처리한다. 값이 있으면 앞서 정한 형식을 엄격히 검사한다. start에는 request_id 키를 항상 포함하며 미제공이면 null이다.
- 이벤트 표의 주요 필드는 모두 필수다. schema_version/run_id/code/message/stage는 문자열, retryable은 boolean, elapsed_ms는 0 이상의 정수다. sources는 배열, text/answer_text/partial_answer_text는 문자열이다. finish_reason은 문자열 또는 null, cited_source_ids는 문자열 배열 또는 null이다. sources 항목 표의 키도 모두 포함하고 미확인 메타데이터만 null로 보낸다.
- 스트림 시작 성공 시 start 한 번, 검색 성공 시 sources 한 번을 순서대로 보낸다. 생성 텍스트는 sources 이후 delta로 보내며, done 또는 error 중 하나로만 종료한다. 종료 뒤에는 이벤트를 보내지 않는다. 연결이 끊겨 종료 이벤트를 전달하지 못하는 경우는 별도 실패로 취급한다.
- 서버는 각 이벤트를 event 한 줄과 JSON data 한 줄, 빈 줄로 끝내고 문자열 내부 줄바꿈은 JSON으로 이스케이프한다. 클라이언트는 UTF-8 분할과 LF/CRLF 이벤트 경계를 처리한다. 주석형 유지 신호가 있으면 무시하고, 불완전한 마지막 이벤트를 성공으로 해석하지 않는다.
- POST fetch를 사용하며 자동 재연결·Last-Event-ID 기반 이어받기는 이번 범위에 없다. 수동 재요청은 새 실행이다. SSE 헤더와 프록시 버퍼링 설정, 연결 유지·시간 초과 수치는 실제 실행 환경에서 정하고 검증한다.
- 호환 가능한 추가 JSON 필드는 무시할 수 있다. 지원하지 않는 schema_version, 잘못된 필드 타입/이벤트 순서/JSON은 프로토콜 오류로 표시하고 완료 처리하지 않는다. 초기 schema_version은 draft-0.2이며 계약 확정 시 버전 변경 여부를 합의한다.

### 5.4 SSE 예시 — 가상 자료

```text
event: start
data: {"schema_version":"draft-0.2","request_id":"client-example-001","run_id":"run-example-001"}

event: sources
data: {"sources":[{"source_id":"S1","text":"형식 설명용 발췌문","rank":1,"subject":"example-subject","filename":"example.pdf","article_number":null,"article_title":null,"law_name":null,"effective_date":null,"source_url":null,"document_id":null,"document_version":null,"file_sha256":null,"page_start":null,"page_end":null}]}

event: delta
data: {"text":"형식 설명용 답변"}

event: done
data: {"run_id":"run-example-001","answer_text":"형식 설명용 답변","generation_status":"completed","finish_reason":"stop","cited_source_ids":null,"elapsed_ms":1200}

```

실패 예시는 다음과 같다. 시간·답변은 해당 실행 값으로 채운다.

```text
event: error
data: {"run_id":"run-example-001","code":"GENERATION_FAILED","message":"답변 생성 중 오류가 발생했습니다.","stage":"generation","partial_answer_text":"이미 수신한 부분 답변","retryable":true,"elapsed_ms":1200}

```

스트림 전 입력 오류는 400/422, 실행 단계 의존성 오류는 스트림이 시작됐다면 HTTP 상태를 바꾸지 않고 error 이벤트로 보낸다. 요청 취소 시 외부 생성 스트림을 닫도록 구현·검증한다. 클라이언트 취소가 이미 수행한 외부 계산이나 DB 작업의 롤백을 보장하지는 않는다.

## 6. PDF 등록 — 현재 계약과 확장 제안

**POST /upload**. 요청은 현재와 동일하게 multipart/form-data의 subject, file이다. 브라우저가 boundary를 설정한다. 파일은 PDF 한 개다.

현재 성공 응답은 아래와 같다. 현재 업로드 실패 동작은 다음과 같으며 아래 확장 제안과 구분한다.

| 상황 | 현재 코드 동작 |
|---|---|
| 필수 multipart 필드 누락·검증 실패 | FastAPI 기본 422, detail 배열 |
| 잘못된 파일명·PDF 외 확장자·동명 파일·파일 쓰기 실패 | file_upload가 false를 반환하고 main.py가 400과 문자열 detail 반환 |
| 공백뿐인 subject | 파일을 먼저 저장한 뒤 add_data에서 ValueError 발생. 별도 변환 없이 서버 오류가 되며 파일이 남을 수 있음 |
| PDF 판독·텍스트/조문 추출·임베딩·색인 실패 | 별도 예외 변환 없음. 일반 서버 오류가 될 수 있고 JSON 오류 계약도 보장하지 않음. 저장된 PDF/색인 잔여 상태 확인 필요 |

현재 동명 파일 검사는 subject별이 아니라 공통 ./upload 폴더의 파일명 기준이다. 새 파일로 subject를 교체해도 이전 PDF 원본을 삭제하는 코드는 없으며, 기존 청크 교체와 원본 파일 정리는 별개다.

```json
{"upload":["example.pdf"]}
```

제안 성공 응답: HTTP 200, application/json. 기존 upload 필드를 유지한다. 기존 프런트는 추가 필드를 무시해도 되지만 새 집계 표시는 별도 연결한다.

```json
{
  "schema_version":"draft-0.2",
  "request_id":null,
  "run_id":"upload-example-001",
  "upload":["example.pdf"],
  "subject":"example-subject",
  "status":"completed",
  "article_count":12,
  "chunk_count":18,
  "replaced_chunk_count":7,
  "document_id":null,
  "document_version":null,
  "file_sha256":null,
  "completed_at":"2026-10-22T10:00:00+09:00"
}
```

예시 건수와 시각은 형식 설명용 가상 값이며 실측 결과가 아니다.

| 필드 | 의미·집계 기준 |
|---|---|
| upload | 등록 처리한 파일명 배열. 공백/빈 문자열 불가 |
| subject | 앞뒤 공백 제거한 실제 등록 키 |
| status | completed는 원본·새 색인 저장 및 필요한 기존 청크 삭제가 모두 성공한 경우만 |
| article_count | 저장한 조문 원문의 고유 조문 수. 조문 구분·중복/부칙 처리 검수 전에는 null 허용. 청크 수로 대신하지 않음 |
| chunk_count | 이번 요청으로 저장 성공한 새 청크 수. 성공 응답에서 1 이상의 정수 필수 |
| replaced_chunk_count | 이번 요청에서 삭제 완료를 확인한 기존 청크 수. 최초 등록은 0. 이름의 replaced는 문서/조문 수가 아닌 삭제 청크 수 |
| document_id/document_version/file_sha256 | 확보된 식별값. 초기 미구현은 null |
| completed_at | 서버에서 확인한 완료 시각 |

제안 성공 응답 예시의 모든 키는 필수다. upload는 현재 단일 PDF 요청 기준으로 비어 있지 않은 파일명 문자열 1개를 담는다. article_count는 1 이상의 정수 또는 null, replaced_chunk_count는 0 이상의 정수다. 미확보 식별값은 null이며 나머지는 예시의 자료형을 따른다. request_id는 multipart의 선택 문자열 필드이며 미제공 시 생략하고 응답에는 null로 보낸다. 문자열 "null"은 미제공 표시가 아니다. 제공한 값은 상담과 같은 형식으로 검사한다. run_id는 매 실행 새로 발급하여 등록 실행과 로그를 연결한다.

**초기 정책 제안:** 현재와 같은 subject 전체 교체·동명 파일 거절을 유지하되 명시적으로 안내한다. 이는 최종 문서 ID/버전 중복 방지 요구를 다 구현한 것이 아니므로 후속 변경 대상으로 남긴다. 동일 subject 복수 PDF 누적 지원으로 오해하지 않는다. 새 교체 정책으로 변경하려면 먼저 합의한다.

서버는 공백 subject·잘못된 파일명을 저장 전에 거절한다. 동명 파일은 기존 파일을 덮어쓰지 않는다. 실제 PDF 판독·텍스트 추출·조문 구성 실패는 오류로 반환한다. 새 저장/기존 삭제 중 실패한 경우 completed나 성공 건수를 반환하지 않는다. 등록 중 검색·동시 등록의 일관성 확보 방식을 정소미와 확인하고 구현 전에는 성공을 보장하지 않는다.

통신 오류·시간 초과 뒤 서버 작업이 계속되었을 수 있으므로 자동 재시도하지 않는다. 실패 후 파일/색인 잔여 상태를 기록하고 같은 파일명 재시도 전에 확인한다. 요청 재전송을 위한 임의 파일명 변경을 복구 정책으로 대신하지 않는다.

## 7. 오류 응답 — 확장 제안

기존 /ask/chat의 응답 계약은 유지한다. 신규 상담의 스트림 전 오류 및 확장 /upload는 아래 JSON 형식을 제안한다. FastAPI 기본 422 배열까지 통일하려면 validation handler 보완이 필요하며 현재 구현이라고 가정하지 않는다.

```json
{
  "detail":"법령 등록 처리 중 오류가 발생했습니다. 재시도 전에 서버 상태를 확인하세요.",
  "error":{
    "code":"INDEXING_FAILED",
    "request_id":null,
    "run_id":"upload-example-001",
    "stage":"indexing",
    "retryable":false,
    "state":{"file":"saved","index":"unknown"}
  }
}
```

detail은 사용자 안내, code는 기계 처리용이다. stage는 validation/file/retrieval/indexing/generation/internal 중 발생 단계다. 검증 오류 등 실행 식별 전에는 run_id=null을 허용한다. file 상태는 not_written/saved/cleaned/unknown, index 상태는 unchanged/updated/unknown으로 제안하며 실제 확인하지 못하면 unknown을 사용한다. 상담 오류에서는 state를 생략하거나 null로 둔다. 실패 상태의 updated는 일관된 교체 완료를 확인한 경우에만 사용하며 오류라고 자동 롤백된 것으로 보지 않는다.

| HTTP | 제안 코드 예시 | 상황 |
|---|---|---|
| 400 | INVALID_INPUT | 공백 질문/subject, 잘못된 파일명 |
| 422 | VALIDATION_ERROR, INVALID_PDF, NO_TEXT, NO_ARTICLES | 필수값/타입 오류, 처리 불가능 PDF |
| 409 | FILE_EXISTS | 동명 파일 충돌 |
| 502 | GENERATION_FAILED | 외부 생성 API 오류 |
| 503 | RETRIEVAL_UNAVAILABLE, EMBEDDING_UNAVAILABLE | DB/임베딩 서비스 사용 불가 |
| 504 | TIMEOUT | 설정된 처리 시간 초과 |
| 500 | INDEXING_FAILED, INTERNAL_ERROR | 그 외 적재/내부 오류 |

현재 /upload는 저장 함수 false를 모두 400으로 반환한다. 위 세분화는 **변경할 내용**이다. retryable은 자동 재시도 지시가 아니다. 등록 결과가 불명확하거나 잔여 상태가 있으면 false로 두고 확인 절차를 안내한다. 서버 로그에는 실행 ID·단계·원인을 기록하되 키·입력 검증 객체 전체를 그대로 노출하지 않는다. 유효하지 않은 request_id 입력은 오류 응답에 그대로 반영하지 않고 null로 둔다. EMPTY_RESPONSE는 generation 단계의 502 대응 오류다. 표의 오류 코드는 JSON 오류와 SSE error에 동일하게 쓰며, 스트림 시작 뒤의 실제 HTTP 상태는 200으로 유지된다. 서버·프록시 장애로 이 JSON 형식조차 받지 못할 수 있으므로 프런트는 비JSON·빈 본문 오류도 처리한다.

## 8. service와 API의 연결 지점

아래 함수명은 제안이며 기존 사용처를 확인해 조율한다. 중복 검색·중복 생성은 하지 않는다.

| 파일 | 현재 | 필요한 보완 |
|---|---|---|
| service/file_service.py | file_upload → bool | 실패 원인과 저장/정리 상태를 구분하는 내부 결과. 기존 함수 유지 또는 래퍼 적용 협의 |
| service/rag_service.py | add_data → 반환 없음, search_obj → retriever | 적재 성공 집계/자료 상태 반환. 검색 본문·메타데이터·내부 점수 확보 경로 정리 |
| service/llm_service.py | get_answer가 검색·생성 후 문자열 yield | 같은 docs를 노출·재사용하고 텍스트/종료 사유/오류를 API에 전달. 기존 text 경로 호환 유지 |
| main.py | 두 API 입구 | 신규 상담 SSE 연결, 등록 결과 확장, 입력/오류 응답 변환 |
| frontend/src/services | 기존 두 API 소비 | 합의 후 신규 상담 SSE 파서·등록 집계 해석 연결 |
| frontend 화면 | 답변 텍스트·등록 파일명, 실제 근거 미지원 | 실제 검색 참고자료·검증 인용·건수·미확인·부분 실패 표시 |

추천 분담: 박상진이 명세·main.py·React 연결을 중심으로 진행하고, 정소미와 현재 service 세 파일의 변경을 조율한다. service의 모든 수정을 정소미에게 일괄 배정하거나 기존 작성 이력만으로 최종 소유권을 확정하는 문서가 아니다.

## 9. 평가 화면 — 후속 협의

현재 코드에는 실제 평가 실행 API가 없다. 이번 초안은 평가 API 경로·Opik 점수 체계를 확정하지 않는다. 김민석·김유진의 실행 코드 또는 실제 결과 파일을 받아 입력 질문 ID/분할·당시 검색 본문·답변·실험 ID·지표명/척도/방향·성공/실패/제외·버전·링크를 맞춘다.

처음에는 실제 결과 파일 표시 방식으로 시작할 수 있다. 다만 이미지에서 요구한 평가 실행 버튼까지 완성하려면 실제 실행 경로 연결이 추가로 필요하다. 웹 버튼만 만들고 모의 점수를 실제 평가로 표시하지 않는다. Agent·세션·평가 API가 완료된 명세로 오해하지 않는다.

## 10. 팀 확인 항목과 완료 기준

**먼저 확인할 다섯 가지**

1. 사용할 코드 커밋·임베딩 모델·색인·subject.
2. 신규 상담 경로와 SSE 권고안 채택 여부.
3. sources에 즉시 제공할 수 있는 항목과 미확인 항목, 실제 인용 검증 범위.
4. article_count 집계 정의, subject 교체·동명 파일·실패 복구와 동시 처리 정책, 업로드 용량·질문 길이·실행 제한 시간.
5. service/main.py 수정 분담과 실제 평가 자료 전달 방식.

**구현 후 확인할 동작**

- 기존 /ask/chat과 기존 upload 배열 소비자가 계속 동작한다.
- 한글·LF/CRLF 이벤트 경계 분리 수신, 정상 종료·길이 제한·미확인 종료·검색 실패·중간 생성 실패·공백뿐인 답변·연결 단절·잘못된 이벤트를 구분한다. 같은 request_id 재요청의 run_id가 다르고 최종 답변이 중복 표시되지 않는지 검사한다.
- 생성에 사용한 docs와 화면의 검색 참고자료가 같다. 미검증 인용·시행일·쪽·점수를 꾸며 넣지 않는다.
- 실제 등록 집계가 DB·파일 상태와 맞고 중복/실패가 성공으로 표시되지 않는다. 재시도 전 잔여 상태를 확인한다.
- API 입력·성공·오류를 자동 검사하고 로컬 FastAPI·DB·모델로 개발용 질문을 실호출한다. PDF 시험은 별도 DB·업로드 경로에서 수행한다.

현재 파일을 작성한 것은 API 구현·팀 합의·실제 실행 완료를 뜻하지 않는다. 기존 [현재 상태](</C:/Users/STAR/Desktop/AI_Study/팀프로젝트/이어드림웜업/frontend/docs/current-status.md>) 설명과 함께 구현 결과를 별도로 기록한다.
