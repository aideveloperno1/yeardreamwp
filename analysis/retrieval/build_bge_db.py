
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from service.rag_service import make_article_docs

# 1. 기존 PDF 파일
filename = "산업안전보건기준에 관한 규칙(고용노동부령)(제00450호)(20260302).pdf"
subject = "산업안전보건기준에 관한 규칙"

# 2. bge-m3 전용 DB 경로
db_path = "./store_bge"

# 기존 DB와 혼동하지 않도록 확인
if Path(db_path).exists():
    raise RuntimeError(
        "store_bge 폴더가 이미 존재합니다. "
        "기존 실험 데이터를 확인한 뒤 실행하세요."
    )

# 3. 기존과 동일한 PDF 청킹 함수 사용
docs = make_article_docs(subject, filename)
print(f"생성된 청크 수: {len(docs)}", flush=True)

# 4. bge-m3 임베딩 모델과 별도 ChromaDB 연결
embeddings = OllamaEmbeddings(
    base_url="http://localhost:11434",
    model="bge-m3:latest"
)

client = chromadb.PersistentClient(path=db_path)

store_bge = Chroma(
    client=client,
    collection_name="lecture",
    embedding_function=embeddings
)

# 5. 개발자 1이 공유한 100개 단위 배치 저장
batch_size = 100

for start in range(0, len(docs), batch_size):
    end = min(start + batch_size, len(docs))

    store_bge.add_documents(docs[start:end])

    print(f"저장 완료: {end}/{len(docs)}", flush=True)

print("bge-m3 DB 구축 완료!")
