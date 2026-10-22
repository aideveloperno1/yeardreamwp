from service.rag_service import search_obj
from analysis.retrieval.load_eval_data import load_eval_data

questions = load_eval_data()

retriever = search_obj("산업안전보건기준에 관한 규칙")

results = []

for item in questions:
    docs = retriever.invoke(item["question"])
    gold_articles = item["gold_articles"]

    articles = [
        doc.metadata.get("article_number")
        for doc in docs
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

    results.append((item["id"], hit1, hit3, hit5, rr))

    print(f"\n[{item['id']}]")
    print("정답 조문:", gold_articles)
    print("검색 조문:", articles)
    print("정답 순위:", rank if rank else "Top-5 밖")
    print(f"Hit@1={hit1}, Hit@3={hit3}, Hit@5={hit5}, RR={rr:.4f}")

print("\n===== 전체 평균 =====")

for index, name in enumerate(["Hit@1", "Hit@3", "Hit@5", "MRR"], start=1):
    average = sum(row[index] for row in results) / len(results)
    print(f"{name}: {average:.4f}")