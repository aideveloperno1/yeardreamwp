# 개발용 5문항 답변 평가

검수된 엑셀의 LAW-001, LAW-003, LAW-005, LAW-011, LAW-024만 사용합니다. 모두 개발용으로 표시된 문항입니다. 원본 질문과 검수된 기준 답변은 변경하지 않았습니다.

## 파일 넣기

압축 안의 파일 5개를 기존 `team-code/evaluation` 폴더에 넣습니다. 기존 collect_answers.py, evaluate_answer.py, upload_to_opik.py는 덮어쓰지 않습니다.

- run_batch_evaluation.py: 수집·평가·Opik 기록
- cases_5.json: 질문별 검수 답변, 근거 조문, 필수 평가 내용
- judge_rubric.txt: 6개 공통 평가 지표
- requirements_eval.txt: 평가용 추가 패키지
- README_batch.md: 이 설명서

## 실행 준비

VS Code 터미널의 위치를 아래 경로로 맞춥니다.

```powershell
cd "C:\Users\roman\OneDrive\바탕 화면\팀플\team-code"
.\.venv\Scripts\python.exe -m pip install -r .\evaluation\requirements_eval.txt
```

루트 `.env`의 ELICE_API_KEY, ELICE_BASE_URL, ELICE_MODEL은 기존 설정을 사용합니다. 평가 단계에서만 읽습니다. API 키를 GitHub에 올리지 마세요.

## 1. 현재 챗봇 답변 5개 수집

기존 챗봇 서버와 Ollama를 켜두고 실행합니다. PDF를 다시 등록할 필요는 없습니다. 현재 제공되는 text/plain 응답의 POST /ask/chat용입니다.

```powershell
.\.venv\Scripts\python.exe .\evaluation\run_batch_evaluation.py collect
```

질문과 subject만 전송합니다. 기준 답변·근거 원문·필수 내용은 챗봇으로 전송하지 않습니다. 질문 5개가 순차 실행되며 실제 생성 모델 API 비용이 발생할 수 있습니다.

매번 새 `evaluation/results/batch_...` 폴더를 만듭니다. 기존 1문항 결과와 다른 실행의 답변을 덮어쓰지 않습니다. 새 실행에는 cases.json, judge_rubric.txt, manifest.json도 복사해 당시의 기준을 보존합니다.

실행 로그에서 각 문항의 저장 완료 여부를 확인하세요. 오류 문항은 별도 오류 파일을 남기며 답변 실패 점수로 취급하지 않습니다. 오류 원인은 서버 터미널을 확인하세요.

## 2. 저장된 답변 자동 평가

```powershell
.\.venv\Scripts\python.exe .\evaluation\run_batch_evaluation.py evaluate
```

가장 최근 batch 폴더의 답변을 읽고 문항별로 6개 지표를 채점합니다. 교육용 API로 질문당 1회 채점 요청하므로 최대 5회 호출합니다. `.env`에 키가 없으면 숨김 입력을 요청합니다.

출력 파일:

- LAW-..._answer.json: 실제 챗봇 질문·답변
- LAW-..._evaluation.json: 자동 판정·이유·평가 기준
- LAW-..._judge_raw_....txt: 채점 모델 원문
- summary.csv: 엑셀로 열 수 있는 5문항 평가표

수집·평가 오류가 난 문항은 summary.csv에 미평가로 나타납니다. 평가가 이미 저장된 문항은 evaluate 재실행 시 재호출하지 않습니다. 오류 원문과 실행 로그를 확인하고 실패 원인을 해결한 뒤 재실행할 수 있습니다.

자동 판정은 사람이 확인해야 합니다. 원래 자동 점수는 보존하고, 사람의 판단·이유는 별도 기록하세요. 수집 원문과 판정이 맞는지도 확인하세요.

## 3. Opik 기록

```powershell
.\.venv\Scripts\python.exe .\evaluation\run_batch_evaluation.py upload
```

Opik API 키와 기존 Workspace 이름을 입력합니다. 교육용 LLM 키와 다릅니다. 기존 `industrial-safety-answer-evaluation` 프로젝트에 문항별 Trace를 만듭니다.

통과=1, 실패=0으로 기록합니다. 검토 필요는 점수로 변환하지 않고 Metadata의 evaluation에 판정·이유를 보관합니다. 같은 로컬 평가 파일에 trace ID가 있으면 중복 전송을 생략합니다. 전송 확인 실패 시 재실행 전에 Opik에서 중복 기록을 확인하세요.

이 방식은 저장된 평가 결과를 Trace에 기록하는 방식입니다. Opik Experiments나 실시간 RAG 단계별 추적을 구현한 것은 아닙니다. 표시 시간은 등록 시각이며 응답 시간·비용을 측정하지 않습니다.

## 개선 후 비교

먼저 개선 전 5문항의 결과와 사람이 확인한 오류를 보관합니다. 생성 프롬프트를 바꾼 다음 서버를 재시작하고 다른 label로 새 결과를 수집합니다.

```powershell
.\.venv\Scripts\python.exe .\evaluation\run_batch_evaluation.py collect --label bge-m3_prompt-after-improvement
.\.venv\Scripts\python.exe .\evaluation\run_batch_evaluation.py evaluate
.\.venv\Scripts\python.exe .\evaluation\run_batch_evaluation.py upload
```

질문·평가 기준·검색 설정·생성 모델은 유지하고 변경한 생성 프롬프트는 별도로 버전을 기록하세요. 현재 API가 프롬프트나 모델 정보를 반환하지 않으므로 서버의 실제 설정도 팀과 확인하세요. 프롬프트 외 설정도 함께 바꾸면 무엇 때문에 달라졌는지 구분하기 어렵습니다.

이전 실행을 명시할 때는 evaluate 또는 upload 뒤에 `--run-dir "실제 batch 폴더의 전체 경로"`를 붙이세요. 생략하면 가장 최근 수집한 batch를 사용합니다.

## 평가의 범위와 제한

- 진실성·정확성 / 지시 준수 / 완결성 / 간결성 / 형식 준수 / 톤 적절성의 6개 지표입니다. 공통 기준은 judge_rubric.txt, 문항별 기준은 cases_5.json에 있습니다.
- 1문항 전용 평가 코드를 여러 문항용으로 일반화하여 버전명을 six-metrics-v2-batch로 분리했습니다. 이전 1문항 점수와 직접 합산하지 말고, 비교 대상 답변에는 같은 기준을 적용하세요.
- reference_context는 첨부 PDF에서 추출한 검증용 조문입니다. 당시 RAG가 실제 검색한 청크가 아닙니다. 반복 머리말만 제거했습니다. PDF의 최신성은 별도로 검증하지 않았습니다.
- 실제 검색 청크는 API에서 반환되지 않아 null입니다. 근거 충실성이나 근거에 따른 보류 적절성을 확정할 수 없습니다. 답변이 스스로 나열한 출처를 실제 검색 결과로 간주하지 않습니다.
- 참고 조문 밖의 추가 주장을 검증할 수 없으면 진실성을 검토 필요로 남깁니다. 기준 답변과 문장이 다르다는 이유만으로 환각 판정하지 않습니다.
- 필수 내용 목록은 검수된 답변·기준을 채점용으로 분리한 것이므로 실행 전에 팀에서 한 번 확인하세요. 특히 LAW-024는 7개 사용 조건과 예외를 모두 확인합니다. 긴 질문은 필요한 설명이 길어도 허용합니다.
- 조건이 이미 질문에 있으면 답변에서 이를 무조건 반복할 필요는 없지만 질문의 전제를 바꾸면 안 됩니다.
- metadata의 embedding_model_declared는 명령행 지정값이며 서버의 실제 모델을 검증한 값이 아닙니다.
- 현재 파이프라인은 정답 안내가 가능한 개발용 5문항용입니다. 범위 밖 질문·보류·추가 질문이 정답인 문항에는 별도 기대 행동과 채점 기준이 필요합니다.
- 5문항 결과만으로 전체 챗봇 성능을 일반화할 수 없습니다. 최종 평가용 문항은 개선에 사용하지 않고 별도로 보관하세요.
- 교육용 API 키와 Opik 키는 파일·결과표에 저장하지 않습니다. 실행 오류 원문에는 민감한 정보가 있을 수 있어 오류 종류만 파일에 남깁니다.
- 로컬 모의 응답으로 수집·채점 저장·Opik 전송 분기를 점검했습니다. 사용자 챗봇과 외부 API에 대한 실제 실행은 사용자 환경에서 확인해야 합니다.
