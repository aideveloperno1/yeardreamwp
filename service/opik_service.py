
import os
from collections import defaultdict
from statistics import mean
from dotenv import load_dotenv

load_dotenv()

import opik


# 단일 Opik 실험 평가 결과 조회
def get_opik_results():

    # 1. 환경변수 가져오기
    api_key = os.getenv("OPIK_API_KEY")
    workspace = os.getenv("OPIK_WORKSPACE")
    experiment_id = os.getenv("OPIK_EXPERIMENT_ID")

    if not api_key:
        raise ValueError("OPIK_API_KEY가 없습니다.")

    if not experiment_id:
        raise ValueError("OPIK_EXPERIMENT_ID가 없습니다.")

    # 2. Opik 클라이언트 생성
    client = opik.Opik(
        api_key=api_key,
        workspace=workspace
    )

    # 3. 실험 조회
    experiment = client.get_experiment_by_id(experiment_id)

    # 4. 해당 실험의 평가 데이터 가져오기
    items = experiment.get_items(max_results=1000)

    scores_by_name = defaultdict(list)
    results = []

    for item in items:

        scores = {}

        # 평가 지표별 점수
        for score in item.feedback_scores or []:
            name = score["name"]
            value = score.get("value")

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                scores[name] = value
                scores_by_name[name].append(value)

        # 질문 데이터 추출
        dataset_data = item.dataset_item_data or {}

        question = (
            dataset_data.get("question")
            or dataset_data.get("input")
            or ""
        )

        results.append({
            "question": question,
            "scores": scores
        })

    # 5. 평가 지표별 평균 점수
    averages = {
        name: round(mean(values), 3)
        for name, values in scores_by_name.items()
        if values
    }

    # 6. 결과 반환
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment.name,
        "total": len(items),
        "averages": averages,
        "results": results
    }
