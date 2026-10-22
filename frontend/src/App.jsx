import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";
import { AppProvider } from "./hooks/AppState.jsx";
import { NotFound, Page, Shell } from "./components/Common.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import DocumentsPage from "./pages/DocumentsPage.jsx";
import EvaluationPage from "./pages/EvaluationPage.jsx";
import LawPage from "./pages/LawPage.jsx";
import TracePage from "./pages/TracePage.jsx";
import GuidePage from "./pages/GuidePage.jsx";
function Redirect({ to }) {
  const loc = useLocation();
  return <Navigate replace to={to + loc.search + loc.hash} />;
}
function Titles() {
  const loc = useLocation();
  useEffect(() => {
    const names = {
      chat: "상담",
      documents: "법령 RAG 관리",
      evaluation: "품질 평가",
      law: "조문 상세",
      trace: "실행 추적",
      guide: "목업 안내",
    };
    document.title =
      (names[loc.pathname.slice(1)] || "페이지") +
      " · 작업장 안전기준 안내 챗봇";
  }, [loc.pathname]);
  return null;
}
export default function App() {
  return (
    <AppProvider>
      <Titles />
      <Shell>
        <Routes>
          <Route path="/" element={<Redirect to="/chat" />} />
          <Route path="/index.html" element={<Redirect to="/chat" />} />
          {["documents", "evaluation", "law", "trace", "guide"].map((id) => (
            <Route
              key={id}
              path={"/" + id + ".html"}
              element={<Redirect to={"/" + id} />}
            />
          ))}
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/evaluation" element={<EvaluationPage />} />
          <Route path="/law" element={<LawPage />} />
          <Route path="/trace" element={<TracePage />} />
          <Route path="/guide" element={<GuidePage />} />
          <Route
            path="*"
            element={
              <Page title="페이지 찾기">
                <NotFound />
              </Page>
            }
          />
        </Routes>
      </Shell>
    </AppProvider>
  );
}
