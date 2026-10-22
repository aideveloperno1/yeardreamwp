import { ApiError, errorMessage } from "./chatClient.js";
export async function uploadDocument({
  subject,
  file,
  signal,
  fetcher = fetch,
}) {
  const body = new FormData();
  body.append("subject", subject);
  body.append("file", file);
  const response = await fetcher("/upload", { method: "POST", body, signal });
  if (!response.ok)
    throw new ApiError(await errorMessage(response), response.status);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new ApiError(
      "등록 응답을 해석할 수 없습니다. 서버 결과 확인이 필요합니다.",
    );
  }
  if (
    !Array.isArray(data?.upload) ||
    !data.upload.length ||
    data.upload.some((v) => typeof v !== "string" || !v.trim())
  )
    throw new ApiError(
      "등록 응답 형식이 다릅니다. 서버 결과 확인이 필요합니다.",
    );
  return data;
}
