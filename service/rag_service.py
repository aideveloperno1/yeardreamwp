import chromadb
import os
import re
from uuid import uuid4
import pymupdf
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

#임베딩 함수 설정 - 로컬 ollama 이용
embed_fn = OllamaEmbeddings(base_url="http://localhost:11434",model="bge-m3:latest")

client = chromadb.PersistentClient(path="./store")

store = Chroma(client=client,collection_name="law_bge_m3",embedding_function=embed_fn)

# 긴 조문을 추가로 나누기 위한 설정
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len
)

# 조문 제목 찾는 정규표현식
# 줄 시작의 제1조(목적), 제10조의2(제목) 등을 인식
ARTICLE_PATTERN = re.compile(
    r"^[ \t]*"
    r"(?P<number>제[ \t]*\d+[ \t]*조"
    r"(?:[ \t]*의[ \t]*\d+)?)"
    r"[ \t]*\((?P<title>[^()\n]+)\)",
    re.MULTILINE
)

# PDF에서 조문별 청크 생성
def make_article_docs(subject: str, filename: str):
    path = os.path.join("upload", filename)

    page_texts = []

    with pymupdf.open(path) as pdf:
        for page in pdf:
            text = page.get_text("text")
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            page_texts.append(text)

    full_text = "\n".join(page_texts)

    if not full_text.strip():
        raise ValueError("PDF에서 텍스트를 추출하지 못했습니다.")

    # 전체 텍스트에서 조문 제목의 위치 찾기
    matches = list(ARTICLE_PATTERN.finditer(full_text))

    if not matches:
        raise ValueError(
            "조문을 찾지 못했습니다. "
            "PDF에서 '제1조(목적)' 형식으로 추출되는지 확인해주세요."
        )

    docs = []

    for index, match in enumerate(matches):
        # 현재 조문의 시작 위치
        start = match.start()

        # 다음 조문 직전까지가 현재 조문의 내용
        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(full_text)

        article_text = full_text[start:end].strip()

        # 조문 번호에 포함된 공백 제거
        article_number = re.sub(
            r"\s+",
            "",
            match.group("number")
        )
        article_title = match.group("title").strip()

        # 짧은 조문은 유지하고 긴 조문만 추가 분할
        chunks = splitter.split_text(article_text)

        for chunk_index, chunk in enumerate(chunks, start=1):
            # 모든 청크에 법령명과 조문 정보를 붙임
            content = (
                f"법령명: {subject}\n"
                f"조문: {article_number}({article_title})\n\n"
                f"{chunk}"
            )

            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "subject": subject,
                        "filename": filename,
                        "article_number": article_number,
                        "article_title": article_title,
                        "chunk_index": chunk_index
                    }
                )
            )

    return docs


# 데이터 저장 및 같은 법령의 기존 청크 교체
def add_data(subject:str,filename:str):
    subject = subject.strip()

    if not subject:
        raise ValueError("법령명을 입력해주세요.")

    # 새 PDF의 조문별 청크 준비
    docs = make_article_docs(subject, filename)

    if not docs:
        raise ValueError("등록할 청크가 없습니다.")

    # 같은 법령의 기존 청크 ID 조회
    existing = store.get(
        where={"subject": subject}
    )
    existing_ids = existing["ids"]

    # 새 청크에 사용할 고유 ID 생성
    new_ids = [uuid4().hex for _ in docs]

    # 새 청크를 먼저 임베딩하고 > bge-m3로 모델 변경 후 배치처리방식 변경
    try:
        batch_size = 100

        print(f"전체 등록 대상: {len(docs)}개", flush=True)

        for start in range(0, len(docs), batch_size):
            end = min(start + batch_size, len(docs))

            store.add_documents(
                documents=docs[start:end],
                ids=new_ids[start:end]
            )

            print(f"저장 완료: {end}/{len(docs)}", flush=True)

    except Exception:
        # 일부만 저장됐을 가능성에 대비해 새 청크 정리
        try:
            store.delete(ids=new_ids)
        except Exception as cleanup_error:
            print(f"새 청크 정리 실패: {cleanup_error}")

        # 기존 청크는 유지하고 오류 전달
        raise

    # 새 청크 저장 성공 후 기존 청크 삭제
    if existing_ids:
        store.delete(ids=existing_ids)
        print(f"기존 청크 삭제 수: {len(existing_ids)}")

    print(f"법령명: {subject}")
    print(f"등록 파일: {filename}")
    print(f"새로 저장된 청크 수: {len(docs)}")


# 해당 법령의 검색기
def search_obj(subject: str):
    subject = subject.strip()

    if not subject:
        raise ValueError("검색할 법령명을 입력해주세요.")

    return store.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": {"subject": subject}
        }
    )