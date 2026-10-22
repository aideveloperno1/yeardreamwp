from service.rag_service import search_obj

questions = [
    {
        "id": "LAW-001",
        "question": "작업장 바닥에 물기가 있어 근로자가 미끄러질 위험이 있습니다. 사업주는 바닥을 어떻게 관리해야 하나요?",
        "gold": "제3조",
    },
    {
        "id": "LAW-003",
        "question": "지게차 같은 하역운반기계가 주로 사용하는 작업장 출입구에는 보행자용 출입구도 따로 설치해야 하나요?",
        "gold": "제11조",
    },
    {
        "id": "LAW-005",
        "question": "추락 방지를 위한 안전난간의 상부 난간대를 바닥에서 80cm 높이에 설치하려고 합니다. 높이 기준을 충족하나요?",
        "gold": "제13조",
    },
    {
        "id": "LAW-011",
        "question": "작업장 통로에는 어느 정도의 조명이 필요하나요? 상시 통행하지 않는 지하실에서 휴대용 조명기구를 쓰는 경우도 같나요?",
        "gold": "제21조",
    },
    {
        "id": "LAW-024",
        "question": "작업발판과 추락방호망을 모두 설치하기 곤란합니다. 3개 이상의 버팀대로 안정적으로 세울 수 있는 이동식 사다리라면 어떤 조건에서 작업에 사용할 수 있나요?",
        "gold": "제42조",
    },
]

retriever = search_obj("산업안전보건기준에 관한 규칙")

results = []

for item in questions:
    docs = retriever.invoke(item["question"])

    articles = [
        doc.metadata.get("article_number")
        for doc in docs
    ]

    rank = next(
        (i for i, article in enumerate(articles, start=1)
         if article == item["gold"]),
        None
    )

    hit1 = int(rank is not None and rank <= 1)
    hit3 = int(rank is not None and rank <= 3)
    hit5 = int(rank is not None and rank <= 5)
    rr = 1 / rank if rank else 0

    results.append((item["id"], hit1, hit3, hit5, rr))

    print(f"\n[{item['id']}]")
    print("정답 조문:", item["gold"])
    print("검색 조문:", articles)
    print("정답 순위:", rank if rank else "Top-5 밖")
    print(f"Hit@1={hit1}, Hit@3={hit3}, Hit@5={hit5}, RR={rr:.4f}")

print("\n===== 전체 평균 =====")

for index, name in enumerate(["Hit@1", "Hit@3", "Hit@5", "MRR"], start=1):
    average = sum(row[index] for row in results) / len(results)
    print(f"{name}: {average:.4f}")