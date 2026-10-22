# 검색 분석

담당: 분석가 1

법령 검수 기록, 검색 평가 코드와 결과를 둡니다. 공동 근거 조문 목록은 `evaluation/evidence.json`에서 관리할 예정입니다.
___


## RAG 검색 품질 평가

법령 검색 시스템의 Retrieval 성능을 평가합니다.

### 평가 환경

- 법령: 산업안전보건기준에 관한 규칙
- 임베딩 모델: nomic-embed-text, bge-m3
- Vector DB: ChromaDB
- 비교 검색 방식: Dense Search, BM25
- 평가 지표: Hit@1, Hit@3, Hit@5, MRR@5
- 평가 데이터: 개발용 질문 5개

### 평가 코드

| 파일 | 설명 |
|---|---|
| `evaluate_retrieval.py` | nomic-embed-text 검색 성능 평가 |
| `compare_bm25.py` | BM25 검색 성능 평가 |
| `evaluate_bge.py` | bge-m3 검색 성능 평가 |
| `build_bge_db.py` | bge-m3 전용 ChromaDB 구축 |

### 실행 준비

프로젝트 루트에서 Python 가상환경을 활성화하고 필요한 패키지를 설치합니다.

```powershell
pip install -r requirements.txt
pip install rank-bm25
```

Ollama에 임베딩 모델을 설치합니다.

```powershell
ollama pull nomic-embed-text
ollama pull bge-m3
```

법령 PDF는 프로젝트 루트의 `upload/` 폴더에 준비합니다.

기존 nomic-embed-text DB는 `store/`, bge-m3 DB는 `store_bge/`를 사용합니다.

### 실행 방법

프로젝트 최상위 폴더에서 실행합니다.

**bge-m3 DB 구축**

```powershell
python -m analysis.retrieval.build_bge_db
```

**검색 성능 평가**

```powershell
python -m analysis.retrieval.evaluate_retrieval
python -m analysis.retrieval.compare_bm25
python -m analysis.retrieval.evaluate_bge
```

### 개발용 5문항 평가 결과

| 지표 | nomic-embed-text | BM25 | bge-m3 |
|---|---:|---:|---:|
| Hit@1 | 0.0000 | 0.8000 | 1.0000 |
| Hit@3 | 0.0000 | 1.0000 | 1.0000 |
| Hit@5 | 0.0000 | 1.0000 | 1.0000 |
| MRR@5 | 0.0000 | 0.8667 | 1.0000 |

※ 개발용 5문항을 대상으로 측정한 결과입니다. 전체 검색 성능을 의미하지 않습니다.

※ 정답 조문 번호 일치 여부를 평가했으며, 실제 답변 근거의 충분성은 별도 검증이 필요합니다.

### 평가 근거 데이터

질문별 정답 근거 조문은 `evaluation/evidence.json`에서 관리합니다.

현재 5개 개발용 문항의 근거 조문을 등록하고 검수했습니다.

향후 `evaluation/questions.json`이 준비되면 공통 평가 데이터를 읽는 방식으로 코드를 개선할 예정입니다.
