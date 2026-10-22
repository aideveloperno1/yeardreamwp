import json
from pathlib import Path
from datetime import datetime, timezone
from getpass import getpass
from opik import Opik

# 1. 가장 최근 v2 평가 결과 불러오기
results_dir = Path(__file__).resolve().parent / "results"
paths = sorted(results_dir.glob("evaluated_LAW-001_v2_*.json"))

if not paths:
    raise FileNotFoundError("v2 평가 결과 파일이 없습니다.")

source_path = paths[-1]
record = json.loads(source_path.read_text(encoding="utf-8"))

print("[등록할 파일]", source_path.name)
print("[임베딩 모델]", record.get("embedding_model"))
print("[평가 기준]", record["rubric_version"])

if record.get("opik_trace_id"):
    raise RuntimeError("이미 Opik에 기록한 파일입니다.")

# 2. 평가 결과 확인
metrics = {
    "truthfulness": "진실성·정확성",
    "instruction_following": "지시 준수",
    "completeness": "완결성",
    "conciseness": "간결성",
    "format_compliance": "형식 준수",
    "tone_appropriateness": "톤 적절성",
}

for metric, label in metrics.items():
    item = record["evaluation"][metric]
    if item["result"] not in {"통과", "실패", "검토 필요"}:
        raise ValueError(f"{label}: 판정 형식을 확인해주세요.")
    print(f"{label}: {item['result']}")

# 3. Opik 연결
opik_key = getpass("\nOpik API 키 입력: ").strip()
workspace = input("Opik Workspace 이름 입력: ").strip()

if not opik_key or not workspace:
    raise ValueError("Opik API 키와 Workspace 이름이 필요합니다.")

PROJECT = "industrial-safety-answer-evaluation"

client = Opik(
    api_key=opik_key,
    workspace=workspace,
    project_name=PROJECT,
    host="https://www.comet.com/opik/api",
)

# 4. 질문·답변·평가 정보 기록
# 아래 시간은 실제 답변 생성 시간이 아니라 Opik 등록 시각
now = datetime.now(timezone.utc)

trace = client.trace(
    name=f"{record['case_id']}_bge-m3_rubric-v2",
    start_time=now,
    end_time=now,
    input={
        "question": record["question"],
    },
    output={
        "answer": record["answer"],
    },
    metadata={
        "case_id": record["case_id"],
        "embedding_model": record.get("embedding_model"),
        "run_label": record.get("run_label"),
        "reference_answer": record["evaluation_reference_answer"],
        "verified_reference_context": record.get(
            "evaluation_reference_context"
        ),
        "actual_retrieved_context": record.get("retrieved_context"),
        "evaluation": record["evaluation"],
        "judge_model": record["judge_model"],
        "judge_prompt": record["judge_prompt"],
        "rubric_version": record["rubric_version"],
        "human_review_status": record.get(
            "human_review_status", "검토 전"
        ),
        "source_file": source_path.name,
        "record_type": "imported_saved_evaluation",
        "timing_note": "등록 시각이며 실제 응답 시간은 아님",
    },
    tags=[
        "development",
        "bge-m3",
        "prompt-before-improvement",
        "rubric-v2",
        "saved-evaluation",
    ],
)

# 5. 통과=1, 실패=0 기록
# 검토 필요는 0점 처리하지 않고 metadata에 판정과 이유 보관
score_map = {"통과": 1.0, "실패": 0.0}

for metric in metrics:
    item = record["evaluation"][metric]

    if item["result"] in score_map:
        trace.log_feedback_score(
            name=metric,
            value=score_map[item["result"]],
            reason=item["reason"],
        )

# 6. 전송 처리 확인
sent = client.flush(timeout=30)

if sent is False:
    raise RuntimeError(
        "전송 완료를 확인하지 못했습니다. "
        "재실행 전 Opik 화면에서 기록 여부를 확인해주세요."
    )

record["opik_trace_id"] = trace.id
record["opik_project"] = PROJECT

source_path.write_text(
    json.dumps(record, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("\n[전송 처리 완료]")
print("프로젝트:", PROJECT)
print("Trace ID:", trace.id)
print("Opik 화면에서 질문·답변·평가 점수를 확인해주세요.")