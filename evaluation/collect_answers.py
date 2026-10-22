import json
from pathlib import Path
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_URL = "http://127.0.0.1:8001/ask/chat"

case_id = "LAW-001"
question = (
    "작업장 바닥에 물기가 있어 근로자가 미끄러질 위험이 있습니다. "
    "사업주는 바닥을 어떻게 관리해야 하나요?"
)
subject = "산업안전보건기준에 관한 규칙"

payload = {"q": question, "subject": subject}

request = Request(
    API_URL,
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("챗봇 답변 생성 중입니다.")

try:
    with urlopen(request, timeout=300) as response:
        answer = response.read().decode("utf-8")
except HTTPError as error:
    print(error.read().decode("utf-8", errors="replace"))
    raise

if not answer.strip():
    raise ValueError("챗봇에서 빈 답변이 반환되었습니다.")

record = {
    "case_id": case_id,
    "question": question,
    "subject": subject,
    "answer": answer,
    "source_type": "team_rag_api",
    "embedding_model": "bge-m3:latest",
    "run_label": "bge-m3_프롬프트개선전",
    "retrieved_context": None,
}

results_dir = Path(__file__).resolve().parent / "results"
results_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
output_path = results_dir / f"{case_id}_bge_m3_{timestamp}.json"

output_path.write_text(
    json.dumps(record, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("\n[질문]")
print(question)
print("\n[생성 답변]")
print(answer)
print("\n[저장 위치]")
print(output_path)