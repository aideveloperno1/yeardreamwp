import json
from pathlib import Path
from getpass import getpass
from opik import Opik

# 기존 5문항 데이터 읽기
source_path = Path(__file__).resolve().parent / "cases_5.json"
cases = json.loads(source_path.read_text(encoding="utf-8"))

expected_ids = {
    "LAW-001", "LAW-003", "LAW-005", "LAW-011", "LAW-024"
}

if len(cases) != 5 or {c["case_id"] for c in cases} != expected_ids:
    raise ValueError("등록할 개발용 5문항을 확인해주세요.")

# Dataset에 올릴 문제와 채점 기준
items = []

for case in cases:
    items.append({
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
        "split": "development",
    })

print("등록할 문항:", [item["case_id"] for item in items])

# 교육용 LLM 키가 아닌 Opik 키 입력
api_key = getpass("Opik API 키: ").strip()
workspace = input("Opik Workspace 이름: ").strip()

if not api_key or not workspace:
    raise ValueError("Opik API 키와 Workspace가 필요합니다.")

PROJECT = "industrial-safety-answer-evaluation"
DATASET = "industrial-safety-dev-5-v1"

client = Opik(
    api_key=api_key,
    workspace=workspace,
    project_name=PROJECT,
    host="https://www.comet.com/opik/api",
)

dataset = client.get_or_create_dataset(
    name=DATASET,
    description="검수된 산업안전보건 법령 개발용 질문 5개와 평가 기준",
    project_name=PROJECT,
)

dataset.insert(items)

print("\nDataset 등록 요청 완료")
print("프로젝트:", PROJECT)
print("Dataset:", DATASET)
print("Opik 화면에서 문항 5개가 등록됐는지 확인해주세요.")