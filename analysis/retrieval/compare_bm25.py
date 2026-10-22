
from rank_bm25 import BM25Okapi
from service.rag_service import store
from analysis.retrieval.load_eval_data import load_eval_data

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
questions = load_eval_data()

results = []

# 5. 질문별 BM25 검색 평가
for item in questions:
    eval_id = item["id"]
    question = item["question"]
    gold_articles = item["gold_articles"]

    scores = bm25.get_scores(question.split())

    # 점수가 높은 순서로 상위 5개 추출
    top_indices = scores.argsort()[::-1][:5]

    articles = [
        metadatas[i]["article_number"]
        for i in top_indices
    ]

    rank = next(
        (i for i, article in enumerate(articles, start=1)
         if article in gold_articles),
        None
    )

    hit1 = int(rank is not None and rank <= 1)
    hit3 = int(rank is not None and rank <= 3)
    hit5 = int(rank is not None and rank <= 5)
    rr = 1 / rank if rank else 0

    results.append((hit1, hit3, hit5, rr))

    print(f"\n[{eval_id}]")
    print("정답 조문:", gold_articles)
    print("검색 조문:", articles)
    print("정답 순위:", rank if rank else "Top-5 밖")
    print(f"Hit@1={hit1}, Hit@3={hit3}, Hit@5={hit5}, RR={rr:.4f}")

# 6. 평균 성능 계산
print("\n===== BM25 전체 평균 =====")

for index, name in enumerate(["Hit@1", "Hit@3", "Hit@5", "MRR@5"]):
    average = sum(row[index] for row in results) / len(results)
    print(f"{name}: {average:.4f}")
