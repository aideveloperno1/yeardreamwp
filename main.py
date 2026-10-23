from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from service.file_service import file_upload
from service.rag_service import add_data,search_obj
from service.llm_service import get_answer


app = FastAPI()
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_methods=["*"],allow_headers=["*"])
app.mount("/view", StaticFiles(directory="view"),name="view")

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


@app.post("/ask/chat")
def ask_chat(info: ChatRequest):
    query = info.q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="질문을 입력해주세요."
        )

    # 법령명 고정
    subject = "산업안전보건기준에 관한 규칙"

    search = search_obj(subject)

    return StreamingResponse(
        get_answer(query, search),
        media_type="text/plain; charset=utf-8"
    )