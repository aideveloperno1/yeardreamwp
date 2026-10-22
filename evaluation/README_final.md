# 최종 평가용 5문항 실행

## 설치 위치
cases_final_5.json과 run_final_evaluation.py를 기존 team-code/evaluation 폴더에 추가합니다.
기존 cases_5.json, run_batch_evaluation.py, judge_rubric.txt와 개발용 결과를 덮어쓰지 않습니다.
기존 가상환경과 .env를 사용하며, judge_rubric.txt도 현재 평가 기준 그대로 재사용합니다.

## 실행 전
- 문항: LAW-002, LAW-004, LAW-010, LAW-017, LAW-023.
- 이 문항을 이미 프롬프트 개선에 사용했다면 실행 전에 미사용 문항으로 대체해야 합니다.
- 답변 생성 프롬프트·모델·검색 설정·자동 평가 기준을 고정합니다.
- 사람의 간결성 기준은 이전 실험과 동일하게 적용하고 자동 점수와 별도 기록합니다.
- 로컬 FastAPI 서버와 Ollama가 실행 중이고 법령 DB가 준비되어 있어야 합니다.

## 프로젝트 루트의 PowerShell에서
```powershell
.\.venv\Scripts\python.exe .\evaluation\run_final_evaluation.py collect
.\.venv\Scripts\python.exe .\evaluation\run_final_evaluation.py evaluate
```
첫 명령이 완료된 다음 두 번째 명령을 실행합니다. 실행 오류가 있으면 원인을 해결합니다.
evaluate 재실행 시 이미 평가된 문항은 보존하고 미완료 문항을 다시 평가합니다.

## 결과
evaluation/results_final/final_batch_날짜시간/에 답변·평가·summary.csv를 저장합니다.
evaluation/results_final/latest_batch.txt는 최근 최종 평가 폴더를 가리킵니다.
개발용 results/latest_batch.txt에는 영향을 주지 않습니다.

## Opik 주의
기존 register_experiment.py는 개발용 문항 ID와 데이터셋에 고정되어 있으므로
이번 결과 등록용으로 그대로 실행하지 않습니다. 최종 평가 전용 데이터셋과 등록 연결이 별도로 필요합니다.
이 파일의 upload 명령은 Trace 기록만 수행하며 Dataset/Experiment 등록은 아닙니다.

## 해석
챗봇에는 질문과 법령명만 보내며 기준 답변·정답 조문은 보내지 않습니다.
평가 모델에는 기준 답변·조문 원문·평가 기준을 별도로 제공합니다.
API가 검색 본문을 반환하지 않아 실제 검색 청크는 미확보 상태를 유지합니다.
첨부 법령 기준의 5문항 소규모 평가이며 전체 서비스 성능을 대표하지 않습니다.
최종 평가 결과를 보고 프롬프트를 수정하면 이 문항들은 이후 개발용으로 전환해야 합니다.
