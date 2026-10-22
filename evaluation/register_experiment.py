import os
import json
from pathlib import Path
from datetime import datetime
from getpass import getpass

BASE = Path(__file__).resolve().parent
PROJECT = "industrial-safety-answer-evaluation"
DATASET = "industrial-safety-dev-5-v1"

METRICS = [
    "truthfulness",
    "instruction_following",
    "completeness",
    "conciseness",
    "format_compliance",
    "tone_appropriateness",
]

# 1. 가장 최근에 수집한 5문항의 실행 폴더 확인
pointer = BASE / "results" / "latest_batch.txt"

if not pointer.exists():
    raise FileNotFoundError("먼저 5문항 답변 수집을 실행해주세요.")

run_dir = BASE / "results" / pointer.read_text(
    encoding="utf-8"
).strip()

marker = run_dir / "experiment_registered.json"

if marker.exists():
    raise RuntimeError(
        "이 실행 결과는 이미 Experiment에 등록되었습니다."
    )

cases = json.loads(
    (run_dir / "cases.json").read_text(encoding="utf-8")
)

expected_ids = {
    "LAW-001", "LAW-003", "LAW-005", "LAW-011", "LAW-024"
}

if len(cases) != 5 or {c["case_id"] for c in cases} != expected_ids:
    raise ValueError("개발용 5문항 구성을 확인해주세요.")

# 2. 문항별 저장된 답변과 자동 평가 결과 불러오기
records = {}

for case in cases:
    case_id = case["case_id"]
    path = run_dir / f"{case_id}_evaluation.json"

    if not path.exists():
        raise FileNotFoundError(
            f"{case_id}의 평가 결과 파일이 없습니다."
        )

    record = json.loads(path.read_text(encoding="utf-8"))

    if record["question"] != case["question"]:
        raise ValueError(f"{case_id}: 질문이 일치하지 않습니다.")

    if (
        record["evaluation_reference_answer"]
        != case["expected_output"]
    ):
        raise ValueError(
            f"{case_id}: 기준 답변이 일치하지 않습니다."
        )

    for metric in METRICS:
        item = record["evaluation"][metric]

        if item["result"] not in {"통과", "실패", "검토 필요"}:
            raise ValueError(
                f"{case_id}: {metric}의 판정 형식을 확인해주세요."
            )

        if not isinstance(item.get("reason"), str):
            raise ValueError(
                f"{case_id}: {metric}의 평가 이유를 확인해주세요."
            )

    records[case_id] = record

print("[사용할 결과 폴더]", run_dir)
print("[등록할 문항]", list(records))

# 3. Opik 연결 설정
# evaluate()에서도 같은 접속 정보를 사용하도록 환경변수에 설정
# 입력한 키는 코드 파일이나 결과 파일에 저장하지 않음
os.environ["OPIK_API_KEY"] = getpass("Opik API 키: ").strip()
os.environ["OPIK_WORKSPACE"] = input(
    "Opik Workspace 이름: "
).strip()
os.environ["OPIK_URL_OVERRIDE"] = "https://www.comet.com/opik/api"
os.environ["OPIK_PROJECT_NAME"] = PROJECT

if (
    not os.environ["OPIK_API_KEY"]
    or not os.environ["OPIK_WORKSPACE"]
):
    raise ValueError("Opik API 키와 Workspace 이름이 필요합니다.")

from opik import Opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import base_metric, score_result

client = Opik()

# 새 Dataset을 만들지 않고, 등록된 Dataset 불러오기
dataset = client.get_dataset(
    name=DATASET,
    project_name=PROJECT,
)

# 4. Dataset의 각 문항에 저장된 답변 연결
def saved_answer_task(dataset_item):
    case_id = dataset_item["case_id"]

    if case_id not in records:
        raise ValueError(f"저장된 평가 결과가 없는 문항: {case_id}")

    record = records[case_id]

    if dataset_item["question"] != record["question"]:
        raise ValueError(
            f"{case_id}: Dataset과 저장 파일의 질문이 다릅니다."
        )

    if (
        dataset_item["expected_output"]
        != record["evaluation_reference_answer"]
    ):
        raise ValueError(
            f"{case_id}: Dataset과 저장 파일의 기준 답변이 다릅니다."
        )

    return {
        "output": record["answer"],
        "saved_evaluation": record["evaluation"],
        "human_review_status": record.get(
            "human_review_status", "검토 전"
        ),
        "source_batch": run_dir.name,
    }

# 5. 저장된 자동 판정을 Experiment의 점수로 변환
class SavedEvaluationMetrics(base_metric.BaseMetric):
    def __init__(self):
        super().__init__(name="saved_evaluation_metrics")

    def score(self, saved_evaluation, **ignored_kwargs):
        scores = []

        for metric in METRICS:
            item = saved_evaluation[metric]

            # 검토 필요를 실패인 0점으로 처리하지 않음
            # 판정과 이유는 saved_evaluation에 그대로 남음
            if item["result"] == "검토 필요":
                continue

            scores.append(
                score_result.ScoreResult(
                    name=metric,
                    value=1.0 if item["result"] == "통과" else 0.0,
                    reason=item["reason"],
                )
            )

        return scores

# 6. 첫 Experiment 생성
experiment_name = (
    "bge-m3_prompt-after-improvement-v2_saved_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
)

print("\nExperiment 등록 중입니다.")

result = evaluate(
    dataset=dataset,
    task=saved_answer_task,
    scoring_metrics=[SavedEvaluationMetrics()],
    experiment_name=experiment_name,
    task_threads=1,
    experiment_config={
        "record_type": "saved_answers_and_saved_automatic_scores",
        "source_batch": run_dir.name,
        "generation_rerun": False,
        "judge_rerun": False,
        "human_review_imported": False,
        "timing_note": (
            "이번 등록 처리의 시간이며 "
            "실제 챗봇 답변 생성 시간은 아님"
        ),
    },
)

# 7. 전송 처리 확인
if client.flush(timeout=30) is False:
    raise RuntimeError(
        "전송 완료를 확인하지 못했습니다. "
        "재실행 전에 Opik에서 등록 여부를 확인해주세요."
    )

# 같은 결과의 중복 등록 방지를 위한 기록
marker.write_text(
    json.dumps(
        {
            "experiment_name": result.experiment_name,
            "experiment_id": result.experiment_id,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("\n[Experiment 등록 처리 완료]")
print("프로젝트:", PROJECT)
print("Experiment:", result.experiment_name)
print("Opik의 Experiments에서 문항별 답변과 점수를 확인해주세요.")