
import chromadb
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from analysis.retrieval.load_eval_data import load_eval_data

# bge-m3 전용 DB 연결
embedding = OllamaEmbeddings(
    base_url="http://localhost:11434",
    model="bge-m3:latest"
)

client = chromadb.PersistentClient(path="./store_bge")

store = Chroma(
    client=client,
    collection_name="lecture",
    embedding_function=embedding
)

# 기존 평가에 사용한 동일한 5개 질문
questions = load_eval_data()

# 법령명으로 검색 범위 제한
retriever = store.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {"subject": "산업안전보건기준에 관한 규칙"}
    }
)

results = []

for item in questions:
    eval_id = item["id"]
    question = item["question"]
    gold_articles = item["gold_articles"]

    docs = retriever.invoke(question)

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

    results.append((hit1, hit3, hit5, rr))

    print(f"\n[{eval_id}]")
    print("정답 조문:", gold_articles)
    print("검색 조문:", articles)
    print("정답 순위:", rank if rank else "Top-5 밖")
    print(f"Hit@1={hit1}, Hit@3={hit3}, Hit@5={hit5}, RR={rr:.4f}")

print("\n===== bge-m3 전체 평균 =====")

for index, name in enumerate(["Hit@1", "Hit@3", "Hit@5", "MRR@5"]):
    average = sum(row[index] for row in results) / len(results)
    print(f"{name}: {average:.4f}")
