
from rank_bm25 import BM25Okapi
from service.rag_service import store

# 1. ChromaDB에서 기존 법령 청크 가져오기
data = store.get(
    where={"subject": "산업안전보건기준에 관한 규칙"},
    include=["documents", "metadatas"]
)

documents = data["documents"]
metadatas = data["metadatas"]

print(f"BM25 검색 대상 청크 수: {len(documents)}")

# 2. 공백 기준으로 단어 분리
tokenized_docs = [doc.split() for doc in documents]

# 3. BM25 검색 모델 준비
bm25 = BM25Okapi(tokenized_docs)

# 4. 기존 평가 질문 5개
questions = [
    ("LAW-001", "작업장 바닥에 물기가 있어 근로자가 미끄러질 위험이 있습니다. 사업주는 바닥을 어떻게 관리해야 하나요?", "제3조"),
    ("LAW-003", "지게차 같은 하역운반기계가 주로 사용하는 작업장 출입구에는 보행자용 출입구도 따로 설치해야 하나요?", "제11조"),
    ("LAW-005", "추락 방지를 위한 안전난간의 상부 난간대를 바닥에서 80cm 높이에 설치하려고 합니다. 높이 기준을 충족하나요?", "제13조"),
    ("LAW-011", "작업장 통로에는 어느 정도의 조명이 필요하나요? 상시 통행하지 않는 지하실에서 휴대용 조명기구를 쓰는 경우도 같나요?", "제21조"),
    ("LAW-024", "작업발판과 추락방호망을 모두 설치하기 곤란합니다. 3개 이상의 버팀대로 안정적으로 세울 수 있는 이동식 사다리라면 어떤 조건에서 작업에 사용할 수 있나요?", "제42조"),
]

results = []

# 5. 질문별 BM25 검색 평가
for eval_id, question, gold in questions:
    scores = bm25.get_scores(question.split())

    # 점수가 높은 순서로 상위 5개 추출
    top_indices = scores.argsort()[::-1][:5]

    articles = [
        metadatas[i]["article_number"]
        for i in top_indices
    ]

    rank = next(
        (i for i, article in enumerate(articles, start=1)
         if article == gold),
        None
    )

    hit1 = int(rank is not None and rank <= 1)
    hit3 = int(rank is not None and rank <= 3)
    hit5 = int(rank is not None and rank <= 5)
    rr = 1 / rank if rank else 0

    results.append((hit1, hit3, hit5, rr))

    print(f"\n[{eval_id}]")
    print("정답 조문:", gold)
    print("검색 조문:", articles)
    print("정답 순위:", rank if rank else "Top-5 밖")
    print(f"Hit@1={hit1}, Hit@3={hit3}, Hit@5={hit5}, RR={rr:.4f}")

# 6. 평균 성능 계산
print("\n===== BM25 전체 평균 =====")

for index, name in enumerate(["Hit@1", "Hit@3", "Hit@5", "MRR@5"]):
    average = sum(row[index] for row in results) / len(results)
    print(f"{name}: {average:.4f}")
