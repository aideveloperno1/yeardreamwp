from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from service.file_service import file_upload
from service.rag_service import add_data,search_obj
from service.llm_service import get_answer


app = FastAPI()


@app.post("/upload")
def upload(
    subject: str = Form(...),
    file: UploadFile = File(...)
):
    # 1. PDF 원본 저장
    success = file_upload(file)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"파일을 저장하지 못했습니다: {file.filename}"
        )

    # 2. 조문별 청킹 및 벡터 DB 등록
    add_data(subject, file.filename)

    # 3. 등록 결과 반환
    return {"upload": [file.filename]}



class ChatRequest(BaseModel):
    q: str
    subject: str


@app.post("/ask/chat")
def ask_chat(info: ChatRequest):
    query = info.q.strip()
    subject = info.subject.strip()

    if not query or not subject:
        raise HTTPException(
            status_code=400,
            detail="질문과 법령명을 입력해주세요."
        )

    search = search_obj(subject)

    return StreamingResponse(
        get_answer(query, search),
        media_type="text/plain"
    )