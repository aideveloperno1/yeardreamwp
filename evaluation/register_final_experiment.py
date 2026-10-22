import os
import json
from pathlib import Path
from datetime import datetime
from getpass import getpass

BASE = Path(__file__).resolve().parent

PROJECT = "industrial-safety-answer-evaluation"
DATASET = "industrial-safety-final-5-v1"

EXPECTED_IDS = {
    "LAW-002", "LAW-004", "LAW-010", "LAW-017", "LAW-023"
}

METRICS = [
    "truthfulness",
    "instruction_following",
    "completeness",
    "conciseness",
    "format_compliance",
    "tone_appropriateness",
]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


# 1. 가장 최근 최종 평가 결과 폴더 확인
results_dir = BASE / "results_final"
pointer = results_dir / "latest_batch.txt"

if not pointer.exists():
    raise FileNotFoundError(
        "최종 평가 결과가 없습니다. 먼저 collect와 evaluate를 실행해주세요."
    )

run_dir = results_dir / pointer.read_text(
    encoding="utf-8"
).strip()

marker = run_dir / "experiment_registered.json"

if marker.exists():
    raise RuntimeError(
        "이 결과는 이미 Experiment에 등록되었습니다. "
        "Opik에서 기존 등록 결과를 확인해주세요."
    )

cases = read_json(run_dir / "cases.json")

if (
    len(cases) != 5
    or {case["case_id"] for case in cases} != EXPECTED_IDS
):
    raise ValueError("최종 평가용 5문항 구성을 확인해주세요.")

if any(case.get("split") != "final_test" for case in cases):
    raise ValueError("최종 평가용 문항인지 확인해주세요.")


# 2. 저장된 답변과 자동 평가 결과 확인
records = {}

for case in cases:
    case_id = case["case_id"]
    path = run_dir / f"{case_id}_evaluation.json"

    if not path.exists():
        raise FileNotFoundError(
            f"{case_id}의 평가 결과가 없습니다. "
            "evaluate를 완료한 후 다시 실행해주세요."
        )

    record = read_json(path)

    if record.get("case_id") != case_id:
        raise ValueError(f"{case_id}: 문항 ID가 일치하지 않습니다.")

    if record["question"] != case["question"]:
        raise ValueError(f"{case_id}: 질문이 일치하지 않습니다.")

    if (
        record["evaluation_reference_answer"]
        != case["expected_output"]
    ):
        raise ValueError(f"{case_id}: 기준 답변이 다릅니다.")

    if (
        record["evaluation_reference_context"]
        != case["reference_context"]
    ):
        raise ValueError(f"{case_id}: 평가용 근거 자료가 다릅니다.")

    if not isinstance(record.get("answer"), str) or not record["answer"].strip():
        raise ValueError(f"{case_id}: 생성 답변이 비어 있습니다.")

    for metric in METRICS:
        item = record["evaluation"][metric]

        if item.get("result") not in {"통과", "실패", "검토 필요"}:
            raise ValueError(f"{case_id}: {metric} 판정 형식 오류")

        reason = item.get("reason")

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"{case_id}: {metric} 평가 이유 누락")

    records[case_id] = record

print("[최종 평가 결과 폴더]", run_dir)
print("[등록할 문항]", sorted(records))


# 3. Opik 연결
# 교육용 LLM API 키가 아닌 Opik API 키 입력
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


# 4. 최종 평가용 Dataset 생성 및 문항 등록
dataset = client.get_or_create_dataset(
    name=DATASET,
    description="프롬프트 고정 후 검증하는 최종 평가용 5문항",
    project_name=PROJECT,
)

dataset.insert([
    {
        "case_id": case["case_id"],
        "question": case["question"],
        "expected_output": case["expected_output"],
        "reference_context": case["reference_context"],
        "reference_clause": case["reference_clause"],
        "required_facts": case["required_facts"],
        "expected_behavior": case["expected_behavior"],
        "reviewed_evaluation_criteria": (
            case["reviewed_evaluation_criteria"]
        ),
        "split": "final_test",
    }
    for case in cases
])

print("[Dataset 등록 처리 완료]", DATASET)


# 5. Dataset 문항에 저장된 챗봇 답변 연결
# 챗봇을 다시 호출하지 않음
def saved_answer_task(dataset_item):
    case_id = dataset_item["case_id"]

    if case_id not in records:
        raise ValueError(f"이번 평가에 없는 문항: {case_id}")

    record = records[case_id]

    if dataset_item["question"] != record["question"]:
        raise ValueError(f"{case_id}: Dataset의 질문이 다릅니다.")

    if (
        dataset_item["expected_output"]
        != record["evaluation_reference_answer"]
    ):
        raise ValueError(f"{case_id}: Dataset의 기준 답변이 다릅니다.")

    return {
        "output": record["answer"],
        "saved_evaluation": record["evaluation"],
        # 별도로 작성한 사람의 검토 결과는 이 코드에서 가져오지 않음
        "human_review_imported": False,
        "source_batch": run_dir.name,
    }


# 6. 저장된 자동 평가 결과를 점수로 변환
class SavedEvaluationMetrics(base_metric.BaseMetric):
    def __init__(self):
        super().__init__(name="saved_evaluation_metrics")

    def score(self, saved_evaluation, **ignored_kwargs):
        scores = []

        for metric in METRICS:
            item = saved_evaluation[metric]

            # 검토 필요는 0점으로 처리하지 않음
            # 판정과 이유는 saved_evaluation에 보존
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


# 7. 최종 평가 Experiment 등록
experiment_name = (
    "bge-m3_prompt-fixed-final-test_saved_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
)

print("\n최종 평가 Experiment 등록 중입니다.")

result = evaluate(
    dataset=dataset,
    task=saved_answer_task,
    scoring_metrics=[SavedEvaluationMetrics()],
    experiment_name=experiment_name,
    task_threads=1,
    experiment_config={
        "split": "final_test",
        "record_type": "saved_answers_and_saved_automatic_scores",
        "source_batch": run_dir.name,
        "generation_rerun": False,
        "judge_rerun": False,
        "human_review_imported": False,
        "timing_note": (
            "등록 처리 시간이며 실제 챗봇 답변 생성 시간은 아님"
        ),
    },
)

if client.flush(timeout=30) is False:
    raise RuntimeError(
        "전송 완료를 확인하지 못했습니다. "
        "재실행 전에 Opik에서 등록 여부를 확인해주세요."
    )


# 8. 중복 등록 방지 기록
marker.write_text(
    json.dumps(
        {
            "dataset_name": DATASET,
            "experiment_name": result.experiment_name,
            "experiment_id": result.experiment_id,
            "source_batch": run_dir.name,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("\n[최종 평가 Experiment 등록 처리 완료]")
print("프로젝트:", PROJECT)
print("Dataset:", DATASET)
print("Experiment:", result.experiment_name)
print("사람의 검토 결과는 아직 가져오지 않았습니다.")
print("Opik에서 문항별 Trace를 열어 사람의 평가를 추가해주세요.")