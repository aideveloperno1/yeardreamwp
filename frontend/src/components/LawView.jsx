import { useEffect, useRef } from "react";
import { Link } from "react-router";
import M from "../lib/mockData.js";
import { Badge, NotFound } from "./Common.jsx";
export function LawView({ lawKey, onOpen, panel = false }) {
  const law = M.laws[lawKey];
  if (!law) return <NotFound what="조문" />;
  return (
    <article className="law-view">
      <p className="law-kicker">{M.LAW} · 목업 예시</p>
      <h2 className="law-title">
        {law.article} {law.title}
      </h2>
      <p className="law-verify">
        <Badge kind="verify" />{" "}
        {law.verify || "기준 PDF 버전과의 일치 검수 필요"}
      </p>
      <dl className="law-meta">
        <dt>법령명</dt>
        <dd>{M.LAW}</dd>
        <dt>조문</dt>
        <dd>
          {law.article} {law.title}
        </dd>
        <dt>시행일</dt>
        <dd>{M.EFFECTIVE}</dd>
        <dt className="dev-only">출처</dt>
        <dd className="dev-only">{law.page}</dd>
        <dt className="dev-only">문서 ID</dt>
        <dd className="dev-only">{law.docId}</dd>
      </dl>
      <h3 className="law-h">조문 전문·발췌</h3>
      <div className="law-body">
        {law.quote.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>
      <h3 className="law-h">참조 조문</h3>
      {law.refs.length ? (
        <ul className="law-list">
          {law.refs.map((r) => (
            <li key={r.key}>
              {onOpen ? (
                <button
                  type="button"
                  className="linkbtn"
                  onClick={() => onOpen(r.key)}
                >
                  {r.label}
                </button>
              ) : (
                <Link to={"/law?id=" + r.key}>{r.label}</Link>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">참조 조문 없음</p>
      )}
      <h3 className="law-h">연결된 별표</h3>
      <p className="muted">
        연결된 별표 없음 · 예시 조문 외 자료는 PDF 확인 후 추가합니다.
      </p>
      <p className="law-link">
        <a href={law.url} target="_blank" rel="noopener noreferrer">
          국가법령정보센터에서 원문 보기 ↗
        </a>
        {panel && (
          <>
            {" "}
            · <Link to={"/law?id=" + lawKey}>조문 상세 페이지로 열기</Link>
          </>
        )}
      </p>
      <p className="muted">{M.LINK_NOTE}</p>
    </article>
  );
}
export function LawPanel({ lawKey, onClose, onOpen }) {
  const close = useRef(null);
  const trigger = useRef(null);
  useEffect(() => {
    trigger.current = document.activeElement;
    close.current?.focus();
    const key = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", key);
    return () => {
      window.removeEventListener("keydown", key);
      if (trigger.current?.isConnected) trigger.current.focus();
    };
  }, []);
  return (
    <aside
      className="law-panel"
      role="dialog"
      aria-modal="false"
      aria-labelledby="law-panel-title"
    >
      <div className="law-panel-head">
        <h2 id="law-panel-title">근거 조문</h2>
        <button ref={close} className="btn" onClick={onClose}>
          닫기
        </button>
      </div>
      <div className="law-panel-body">
        <LawView lawKey={lawKey} onOpen={onOpen} panel />
      </div>
    </aside>
  );
}
