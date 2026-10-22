"""최종 평가용 5문항: 실제 챗봇 답변 수집 → 자동 평가 → Opik 기록."""
import argparse
import csv
import getpass
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
METRICS = {
    "truthfulness": "진실성·정확성",
    "instruction_following": "지시 준수",
    "completeness": "완결성",
    "conciseness": "간결성",
    "format_compliance": "형식 준수",
    "tone_appropriateness": "톤 적절성",
}
VALID = {"통과", "실패", "검토 필요"}
RUBRIC_VERSION = "six-metrics-v2-batch"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def read_cases():
    cases = load_json(BASE / "cases_final_5.json")
    if len(cases) != 5 or len({c["case_id"] for c in cases}) != 5:
        raise ValueError("중복 없는 최종 평가용 5문항이 필요합니다.")
    if any(c["split"] != "final_test" for c in cases):
        raise ValueError("최종 평가용 문항만 사용하세요.")
    return cases


def get_run(args, create=False):
    if args.run_dir:
        run = Path(args.run_dir).resolve()
    elif create:
        run = BASE / "results_final" / ("final_batch_" + stamp())
    else:
        pointer = BASE / "results_final" / "latest_batch.txt"
        if not pointer.exists():
            raise FileNotFoundError("먼저 collect를 실행하세요.")
        run = BASE / "results_final" / pointer.read_text(encoding="utf-8").strip()
    if create:
        run.mkdir(parents=True, exist_ok=False)
        (BASE / "results_final").mkdir(exist_ok=True)
        (BASE / "results_final" / "latest_batch.txt").write_text(run.name, encoding="utf-8")
    elif not (run / "manifest.json").exists():
        raise FileNotFoundError("실행 폴더에 manifest.json이 없습니다.")
    print("[작업 폴더]", run)
    return run


def collect(args):
    cases = read_cases()
    run = get_run(args, create=True)
    # 평가 기준과 데이터의 버전을 해당 실행 폴더에 함께 보존
    write_json(run / "cases.json", cases)
    rubric = (BASE / "judge_rubric.txt").read_text(encoding="utf-8")
    (run / "judge_rubric.txt").write_text(rubric, encoding="utf-8")
    write_json(run / "manifest.json", {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "api_url": args.api_url,
        "subject": args.subject,
        "run_label": args.label,
        "embedding_model_declared": args.embedding_model,
        "configuration_note": "임베딩 모델은 사용자 지정값이며 API로 검증한 값이 아님",
        "rubric_version": RUBRIC_VERSION,
        "rubric_sha256": hashlib.sha256(rubric.encode()).hexdigest(),
        "case_ids": [c["case_id"] for c in cases],
    })
    for case in cases:
        cid = case["case_id"]
        print(f"[{cid}] 답변 생성 중...", flush=True)
        # 챗봇에는 질문과 검색할 법령명만 전송. 기준 답변은 전송하지 않음.
        payload = {"q": case["question"], "subject": args.subject}
        req = Request(args.api_url, data=json.dumps(payload, ensure_ascii=False).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=300) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                answer = response.read().decode("utf-8")
            if "application/json" in content_type.lower():
                raise ValueError("현재 수집기는 text/plain 응답용입니다. API 응답 형식을 확인하세요.")
            if not answer.strip():
                raise ValueError("빈 답변 반환")
            write_json(run / f"{cid}_answer.json", {
                "case_id": cid, "question": case["question"], "subject": args.subject,
                "answer": answer, "status_code": status, "source_type": "team_rag_api",
                "embedding_model_declared": args.embedding_model, "run_label": args.label,
                "retrieved_context": None,
                "context_note": "API가 실제 검색 본문을 반환하지 않아 미확보",
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[{cid}] 저장 완료")
        except Exception as error:
            write_json(run / f"{cid}_collection_error.json", {
                "case_id": cid, "stage": "collection", "error_type": type(error).__name__,
                "note": "실행 오류이며 답변 품질 실패 점수가 아님",
            })
            print(f"[{cid}] 수집 오류: {type(error).__name__} — 서버 터미널 확인")
    print("수집 종료. 다음 명령: evaluate")


def validate_evaluation(evaluation):
    if not isinstance(evaluation, dict):
        raise ValueError("채점 결과가 JSON 객체가 아닙니다.")
    for metric in METRICS:
        item = evaluation.get(metric)
        if not isinstance(item, dict) or item.get("result") not in VALID:
            raise ValueError(f"{metric}: 판정 형식 오류")
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError(f"{metric}: 평가 이유 누락")


def evaluate(args):
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(BASE.parent / ".env")
    run = get_run(args)
    cases = load_json(run / "cases.json")
    manifest = load_json(run / "manifest.json")
    rubric = (run / "judge_rubric.txt").read_text(encoding="utf-8")
    key = os.getenv("ELICE_API_KEY") or getpass.getpass("교육용 LLM API 키: ").strip()
    model = os.getenv("ELICE_MODEL", "claude-haiku-5-5")
    client = OpenAI(api_key=key,
        base_url=os.getenv("ELICE_BASE_URL", "https://mlapi.run/e488b98a-60f2-4db1-9931-49ba1a217dc4/v1"),
        timeout=90.0, max_retries=0)
    for case in cases:
        cid = case["case_id"]
        answer_path = run / f"{cid}_answer.json"
        output = run / f"{cid}_evaluation.json"
        if not answer_path.exists():
            print(f"[{cid}] 수집된 답변 없음 — 미평가")
            continue
        if output.exists():
            print(f"[{cid}] 기존 평가 보존 — 재호출 생략")
            continue
        record = load_json(answer_path)
        print(f"[{cid}] 6개 지표 평가 중...", flush=True)
        try:
            response = client.chat.completions.create(model=model, messages=[
                {"role": "system", "content": rubric},
                {"role": "user", "content": json.dumps({
                    "question": case["question"], "reference_answer": case["expected_output"],
                    "verified_reference_context": case["reference_context"],
                    "required_facts": case["required_facts"],
                    "expected_behavior": case["expected_behavior"],
                    "reviewed_evaluation_criteria": case["reviewed_evaluation_criteria"],
                    "actual_retrieved_context": record.get("retrieved_context"),
                    "generated_answer": record["answer"],
                }, ensure_ascii=False)},
            ])
            raw = (response.choices[0].message.content or "").strip()
            (run / f"{cid}_judge_raw_{stamp()}.txt").write_text(raw, encoding="utf-8")
            if raw.startswith("```") and raw.endswith("```"):
                raw = "\n".join(raw.splitlines()[1:-1]).strip()
            evaluation = json.loads(raw)
            validate_evaluation(evaluation)
            record.update({
                "evaluation": evaluation, "judge_model": model,
                "judge_prompt": rubric, "rubric_version": manifest["rubric_version"],
                "evaluation_reference_answer": case["expected_output"],
                "evaluation_reference_context": case["reference_context"],
                "required_facts": case["required_facts"],
                "human_review_status": "검토 전",
                "source_answer_file": answer_path.name,
            })
            write_json(output, record)
            for metric, label in METRICS.items():
                print(f"  {label}: {evaluation[metric]['result']}")
        except Exception as error:
            write_json(run / f"{cid}_evaluation_error.json", {
                "case_id": cid, "stage": "evaluation", "error_type": type(error).__name__,
                "note": "채점 실행 오류이며 답변 품질 실패 점수가 아님",
            })
            print(f"[{cid}] 평가 오류: {type(error).__name__} — 원문 파일/연결 설정 확인")
    summary(run, cases)


def summary(run, cases):
    headers = ["case_id", "evaluation_status", "human_review_status"]
    for metric in METRICS:
        headers.extend([metric, metric + "_reason"])
    with (run / "summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for case in cases:
            path = run / f"{case['case_id']}_evaluation.json"
            row = {"case_id": case["case_id"], "evaluation_status": "미평가"}
            if path.exists():
                record = load_json(path)
                row.update(evaluation_status="완료", human_review_status=record["human_review_status"])
                for metric in METRICS:
                    item = record["evaluation"][metric]
                    row[metric], row[metric + "_reason"] = item["result"], item["reason"]
            writer.writerow(row)
    print("[엑셀로 열 수 있는 결과표]", run / "summary.csv")


def upload(args):
    from opik import Opik
    run = get_run(args)
    paths = sorted(run.glob("LAW-*_evaluation.json"))
    if not paths:
        raise FileNotFoundError("평가 결과가 없습니다. 먼저 evaluate를 실행하세요.")
    key = os.getenv("OPIK_API_KEY") or getpass.getpass("Opik API 키: ").strip()
    workspace = os.getenv("OPIK_WORKSPACE") or input("Opik Workspace 이름: ").strip()
    if not key or not workspace:
        raise ValueError("Opik 키와 Workspace가 필요합니다.")
    project = "industrial-safety-answer-evaluation"
    client = Opik(api_key=key, workspace=workspace, project_name=project,
                  host="https://www.comet.com/opik/api")
    for path in paths:
        record = load_json(path)
        if record.get("opik_trace_id"):
            print(f"[{record['case_id']}] 이미 기록됨 — 생략")
            continue
        validate_evaluation(record["evaluation"])
        now = datetime.now(timezone.utc)
        trace = client.trace(
            name=f"{record['case_id']}_{record['run_label']}", start_time=now, end_time=now,
            input={"question": record["question"]}, output={"answer": record["answer"]},
            metadata={**record, "batch_id": run.name, "source_file": path.name,
                      "record_type": "imported_saved_evaluation",
                      "timing_note": "등록 시각이며 실제 챗봇 응답 시간은 아님"},
            tags=["final_test", "rubric-v2-batch", record["run_label"]],
        )
        for metric in METRICS:
            item = record["evaluation"][metric]
            if item["result"] in {"통과", "실패"}:
                trace.log_feedback_score(name=metric, value=float(item["result"] == "통과"),
                                         reason=item["reason"])
        if client.flush(timeout=30) is False:
            raise RuntimeError("전송 확인 실패. 재실행 전 Opik에서 중복 기록 여부를 확인하세요.")
        record.update(opik_trace_id=trace.id, opik_project=project)
        write_json(path, record)
        print(f"[{record['case_id']}] Opik 기록 완료")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["collect", "evaluate", "upload"])
    parser.add_argument("--run-dir", help="이전 실행 폴더를 명시할 때 사용")
    parser.add_argument("--api-url", default="http://127.0.0.1:8001/ask/chat")
    parser.add_argument("--subject", default="산업안전보건기준에 관한 규칙")
    parser.add_argument("--embedding-model", default="bge-m3:latest")
    parser.add_argument("--label", default="bge-m3_prompt-fixed-final-test")
    args = parser.parse_args()
    {"collect": collect, "evaluate": evaluate, "upload": upload}[args.mode](args)


if __name__ == "__main__":
    main()
