import { Link, useSearchParams } from "react-router";
import { useApp } from "../hooks/AppState.jsx";
import M from "../lib/mockData.js";
import { Page } from "../components/Common.jsx";
import { LawView } from "../components/LawView.jsx";
export default function LawPage() {
  const [params] = useSearchParams();
  const key = params.has("id") ? params.get("id") : Object.keys(M.laws)[0];
  const { mode } = useApp();
  return (
    <Page
      title="조문 상세"
      description="팀 PDF 기준 목업 자료이며 원문·버전 검수가 필요합니다."
    >
      {mode === "live" ? (
        <p className="note">
          실제 조문 조회 API 미지원입니다. 모의 모드에서 예시 조문을 열 수
          있습니다.
        </p>
      ) : (
        <>
          <nav className="law-picker" aria-label="예시 조문 선택">
            {Object.entries(M.laws).map(([id, law]) => (
              <Link
                key={id}
                to={"/law?id=" + id}
                aria-current={id === key ? "page" : undefined}
              >
                {law.article} {law.title}
              </Link>
            ))}
          </nav>
          <LawView lawKey={key} />
        </>
      )}
    </Page>
  );
}
