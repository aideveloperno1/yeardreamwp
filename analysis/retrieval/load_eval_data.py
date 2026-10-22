
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_eval_data():
    cases_path = ROOT / "evaluation" / "cases_5.json"
    evidence_path = ROOT / "evaluation" / "evidence.json"

    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    with open(evidence_path, "r", encoding="utf-8") as f:
        evidence = json.load(f)

    evidence_map = {
        item["id"]: item["gold_articles"]
        for item in evidence
    }

    evaluation_data = []

    for case in cases:
        case_id = case["case_id"]

        if case_id not in evidence_map:
            raise ValueError(
                f"{case_id}: evidence.json에 정답 조문이 없습니다."
            )

        evaluation_data.append({
            "id": case_id,
            "question": case["question"],
            "gold_articles": evidence_map[case_id],
        })

    return evaluation_data


if __name__ == "__main__":
    data = load_eval_data()

    for item in data:
        print(
            item["id"],
            item["gold_articles"]
        )

    print(f"\n총 {len(data)}개 평가 문항 연결 완료")
