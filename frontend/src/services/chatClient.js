export class ApiError extends Error {
  constructor(message, status = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}
export async function errorMessage(response) {
  const fallback = [400, 422].includes(response.status)
    ? `요청 형식 확인 필요 (HTTP ${response.status})`
    : `서버 요청 실패 (HTTP ${response.status})`;
  try {
    const json = await response.json();
    if (typeof json?.detail === "string" && json.detail.trim())
      return json.detail;
    if (response.status === 422 && Array.isArray(json?.detail)) {
      const labels = { q: "질문", subject: "DB subject", file: "PDF 파일" };
      const fields = [
        ...new Set(
          json.detail.flatMap((item) => {
            const loc = item?.loc;
            const key = Array.isArray(loc) && loc[0] === "body" ? loc[1] : null;
            return Object.hasOwn(labels, key) ? [labels[key]] : [];
          }),
        ),
      ];
      if (fields.length)
        return `${fields.join("·")} 입력을 확인하세요. (HTTP 422)`;
    }
  } catch {
    // HTML, empty and malformed bodies keep a status-based message.
  }
  return fallback;
}
export async function streamChat({
  q,
  subject,
  signal,
  onText,
  fetcher = fetch,
}) {
  const response = await fetcher("/ask/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q, subject }),
    signal,
  });
  if (!response.ok)
    throw new ApiError(await errorMessage(response), response.status);
  if (
    response.headers
      .get("content-type")
      ?.split(";", 1)[0]
      .trim()
      .toLowerCase() !== "text/plain"
  )
    throw new ApiError(
      "예상한 텍스트 응답 형식이 아닙니다. 서버와 프록시 경로를 확인하세요.",
    );
  if (!response.body) throw new ApiError("응답 본문이 없습니다.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let text = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
      if (done) break;
      text += decoder.decode(value, { stream: true });
      onText(text);
    }
    text += decoder.decode();
    onText(text);
    if (!text.trim()) throw new ApiError("빈 응답을 받았습니다.");
    return text;
  } finally {
    reader.releaseLock();
  }
}
