/* Shared mockup rules. No model calls, real scoring or network requests. */
import M from "./mockData.js";
const KEY = "mockup.evaluation.v1";
const VERSION = 1;
const clone = (v) => JSON.parse(JSON.stringify(v));
const metrics = { accuracy: "정확성", faithfulness: "근거 충실성" };
const statusLabels = {
  pending: "대기",
  running: "실행 중",
  completed: "완료",
  failed: "실패",
  excluded: "제외",
};
const batchLabels = {
  running: "실행 중",
  completed: "완료",
  partial: "일부 실패",
  interrupted: "중단",
};
const dataset = "자체 예시 6문항 · v1";
const judge = "목업 채점 기준 v1 (실제 Opik 명세 아님)";
function settings(type, variant) {
  return {
    prompt:
      type === "prompt" && variant === "B"
        ? "v2 · 조건·예외 보존 안내 추가 (예시)"
        : "v1 · 기본 안내 (예시)",
    gen: "생성 모델 A (예시)",
    emb: "임베딩 모델 B (예시)",
    k: 5,
    method:
      type === "retrieval" && variant === "B"
        ? "벡터 + BM25 (예시)"
        : "벡터 검색 (예시)",
    filter: "법령명",
    judge,
  };
}
function create(type, variant, fail) {
  if (!["prompt", "retrieval"].includes(type) || !["A", "B"].includes(variant))
    throw new Error("Unknown evaluation setting");
  const id =
    "EV-" +
    Date.now().toString(36) +
    "-" +
    Math.random().toString(36).slice(2, 8);
  return {
    id,
    type,
    variant,
    dataset,
    settings: settings(type, variant),
    state: "running",
    at: new Date().toISOString(),
    fail: !!fail,
    items: M.evalCases.map((c) => ({
      id: c.id,
      state: c.id === "EX-06" ? "excluded" : "pending",
      reason:
        c.id === "EX-06" ? "근거 확인 필요 · 이번 모의 실행에서 제외" : "",
      answer: null,
      scores: { accuracy: null, faithfulness: null },
      metricNotes: {},
      judgments: null,
      runId: null,
    })),
  };
}
const answers = {
  "EX-01": [
    "안전난간 상부 난간대는 90cm 이상입니다. (예시 요약 답변 · 조건/예외 보완 필요)",
    "안전난간 상부 난간대는 90cm 이상입니다. 중간 난간대 위치는 높이에 따라 달라지며, 발끝막이판 적용 예외도 함께 확인해야 합니다. (개선 예시 · PDF 대조 필요)",
  ],
  "EX-02": [
    "안전난간을 어디에 설치하시나요?",
    "계단 측면인지 작업발판 끝인지 알려 주세요. 장소에 따른 조건을 확인하겠습니다.",
  ],
  "EX-03": [
    "안전난간의 구조 기준을 확인해 주세요. (질문에 대한 보류 안내 미흡 예시)",
    "해당 예시 조문에는 색상 기준이 없어 색상을 특정할 수 없습니다. (보류 예시)",
  ],
  "EX-04": [
    "연차휴가는 이 목업의 지원 범위 밖입니다.",
    "연차휴가는 이 목업의 지원 범위 밖입니다.",
  ],
  "EX-05": [
    "계단 측면에는 중간 난간대 기준을 확인해야 합니다. (조건 누락 예시)",
    "계단의 개방된 측면은 난간기둥 간격 등 단서 조건을 함께 확인해야 합니다. (예시 · PDF 대조 필요)",
  ],
};
function finishItem(batch, id) {
  const item = batch.items.find((x) => x.id === id);
  if (
    batch.state !== "running" ||
    !item ||
    !["pending", "running"].includes(item.state)
  )
    return false;
  if (batch.fail && id === "EX-03") {
    item.state = "failed";
    item.reason = "검토 도구로 지정한 모의 평가 실패";
    return true;
  }
  const b = batch.variant === "B";
  const ix = Number(id.slice(-2)) - 1;
  item.state = "completed";
  item.answer = answers[id][b ? 1 : 0];
  item.scores.accuracy = [b ? 0.9 : 0.7, 0.9, b ? 0.9 : 0.3, 1, b ? 0.9 : 0.4][
    ix
  ];
  item.scores.faithfulness =
    ix === 1 || ix === 3
      ? null
      : [b ? 0.9 : 0.65, null, b ? 0.95 : 0.4, null, b ? 0.9 : 0.5][ix];
  item.metricNotes.faithfulness =
    ix === 1 || ix === 3 ? "해당 없음 · 추가 질문/범위 밖 안내" : "";
  item.reason =
    "화면 동작 검토를 위해 미리 작성한 예시 답변·점수입니다. 실제 채점 결과가 아닙니다.";
  item.judgments = clone(M.evalResults[batch.variant][id]);
  if (batch.type === "prompt" && ix === 0 && b)
    item.judgments = ["o", "o", "o", "-"];
  item.runId = id === "EX-01" ? batch.id + "-" + id : null;
  return true;
}
function counts(batch) {
  const out = {
    total: batch.items.length,
    scheduled: 0,
    pending: 0,
    running: 0,
    completed: 0,
    failed: 0,
    excluded: 0,
  };
  batch.items.forEach((i) => {
    out[i.state]++;
    if (i.state !== "excluded") out.scheduled++;
  });
  return out;
}
const validScore = (v) =>
  typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= 1;
function aggregate(batch, metric) {
  const values = batch.items
    .filter((i) => i.state === "completed" && validScore(i.scores[metric]))
    .map((i) => i.scores[metric]);
  return {
    n: values.length,
    mean: values.length
      ? values.reduce((a, b) => a + b, 0) / values.length
      : null,
  };
}
function compatible(a, b) {
  return !!(
    a &&
    b &&
    a.variant === "A" &&
    b.variant === "B" &&
    a.type === b.type &&
    a.dataset === b.dataset &&
    a.settings.judge === b.settings.judge &&
    a.settings.gen === b.settings.gen &&
    a.settings.emb === b.settings.emb &&
    a.settings.k === b.settings.k &&
    a.settings.filter === b.settings.filter &&
    (a.type === "prompt"
      ? a.settings.method === b.settings.method
      : a.settings.prompt === b.settings.prompt)
  );
}
function compare(a, b, metric) {
  if (
    !compatible(a, b) ||
    [a, b].some((v) => ["running", "interrupted"].includes(v.state))
  )
    return null;
  const pairs = a.items
    .filter((i) => i.state === "completed" && validScore(i.scores[metric]))
    .map((i) => [i, b.items.find((j) => j.id === i.id)])
    .filter(
      ([, j]) => j && j.state === "completed" && validScore(j.scores[metric]),
    );
  if (!pairs.length) return { n: 0, a: null, b: null, delta: null };
  const av = pairs.reduce((s, [i]) => s + i.scores[metric], 0) / pairs.length;
  const bv = pairs.reduce((s, [, i]) => s + i.scores[metric], 0) / pairs.length;
  return { n: pairs.length, a: av, b: bv, delta: bv - av };
}
function blank() {
  return {
    version: VERSION,
    selection: { type: "prompt", variant: "A" },
    batches: {},
  };
}
function isBatch(b, key) {
  if (
    !b ||
    !["prompt:A", "prompt:B", "retrieval:A", "retrieval:B"].includes(key) ||
    key !== b.type + ":" + b.variant ||
    !Object.hasOwn(batchLabels, b.state) ||
    typeof b.id !== "string" ||
    !b.id.startsWith("EV-") ||
    b.dataset !== dataset ||
    !b.settings ||
    JSON.stringify(b.settings) !==
      JSON.stringify(settings(b.type, b.variant)) ||
    !Array.isArray(b.items) ||
    b.items.length !== 6 ||
    !Number.isFinite(Date.parse(b.at))
  )
    return false;
  const expected = M.evalCases.map((c) => c.id);
  return b.items.every(
    (i, n) =>
      i &&
      i.id === expected[n] &&
      Object.hasOwn(statusLabels, i.state) &&
      i.scores &&
      Object.keys(metrics).every(
        (m) => i.scores[m] === null || validScore(i.scores[m]),
      ) &&
      (i.answer === null || typeof i.answer === "string") &&
      (i.runId === null ||
        (i.id === "EX-01" && i.runId === b.id + "-" + i.id)) &&
      i.metricNotes &&
      typeof i.metricNotes === "object" &&
      typeof i.reason === "string" &&
      (i.judgments === null ||
        (Array.isArray(i.judgments) &&
          i.judgments.length === 4 &&
          i.judgments.every((v) => ["o", "x", "-"].includes(v)))) &&
      (i.state === "completed" ||
        (i.answer === null &&
          i.runId === null &&
          Object.values(i.scores).every((v) => v === null))),
  );
}
function load(storage) {
  try {
    const raw = storage.getItem(KEY);
    if (!raw) return { data: blank(), warning: "" };
    const data = JSON.parse(raw);
    if (
      data.version !== VERSION ||
      !data.selection ||
      !["prompt", "retrieval"].includes(data.selection.type) ||
      !["A", "B"].includes(data.selection.variant) ||
      !data.batches ||
      Array.isArray(data.batches) ||
      !Object.entries(data.batches).every(([k, b]) => isBatch(b, k))
    )
      throw new Error("format");
    Object.values(data.batches).forEach((b) => {
      if (b.state === "running") {
        b.state = "interrupted";
        b.items.forEach((i) => {
          if (i.state === "running") i.state = "pending";
        });
      }
    });
    return { data, warning: "" };
  } catch {
    return {
      data: blank(),
      warning:
        "저장 자료를 읽을 수 없습니다. 현재 화면에서 새 모의 실행을 할 수 있습니다.",
    };
  }
}
function save(storage, data) {
  try {
    storage.setItem(KEY, JSON.stringify(data));
    return "";
  } catch {
    return "결과 저장이 차단됐습니다. 현재 화면에서만 확인 가능하며 이동 후 추적 기록을 조회할 수 없습니다.";
  }
}
function traces(data) {
  return Object.values(data.batches).flatMap((b) =>
    b.items
      .filter((i) => i.state === "completed" && i.runId)
      .map((i) => ({
        id: i.runId,
        sessionId: b.id,
        at: b.at,
        question: M.evalCases.find((c) => c.id === i.id).q,
        status: "answer",
        topic: "guardrail",
        source: "evaluation",
        evaluation: true,
        answer: i.answer,
        bodyVersion: 2,
        settings: b.settings,
        evaluationId: b.id,
        comparison: b.type,
        variant: b.variant,
        scores: i.scores,
        reason: i.reason,
      })),
  );
}
function context(text, pending, lastTopic, classify, has, out, nodata) {
  const topic = classify(text);
  if (!topic && has(text, out))
    return {
      topic: null,
      ctx: text,
      pending: false,
      standalone: "out",
      inherited: false,
    };
  if (!topic && has(text, nodata))
    return {
      topic: null,
      ctx: text,
      pending: false,
      standalone: "nodata",
      inherited: false,
    };
  if (pending && (!topic || topic === pending.topic))
    return {
      topic: pending.topic,
      ctx: pending.original + " " + text,
      pending: true,
      inherited: false,
    };
  return {
    topic: topic || lastTopic,
    ctx: text,
    pending: false,
    inherited: !topic && !!lastTopic,
  };
}
function answerText(r) {
  if (r.status === "answer") {
    const lines = [
      r.conclusion && "결론: " + r.conclusion,
      r.summary,
      r.explain,
      r.contextNote,
      r.situation,
      ...(r.brief || []),
    ];
    for (const [key, label] of [
      ["conditions", "적용 조건"],
      ["exceptions", "예외"],
      ["actions", "안전조치"],
    ])
      if (r[key]?.length)
        lines.push(
          label +
            "\n" +
            r[key]
              .map(([t, ref]) => "- " + t + (ref ? " (" + ref + ")" : ""))
              .join("\n"),
        );
    if (r.limits) lines.push("판단 한계: " + r.limits);
    return lines.filter(Boolean).join("\n\n");
  }
  if (r.status === "clarify")
    return [
      "추가 질문: " + r.question,
      r.need +
        "에 따라 적용 기준이 달라져요. 골라 주시거나 직접 입력해 주세요.",
      ...(r.options || []),
    ].join("\n");
  if (r.status === "hold")
    return (
      "확인된 근거가 없어 답변을 보류합니다.\n" +
      r.reason +
      "\n확인하지 못한 내용은 단정해서 안내하지 않습니다. 장소·설비·궁금한 기준을 더 구체적으로 적어 다시 물어봐 주세요."
    );
  if (r.status === "error")
    return (
      "요청을 처리하지 못했습니다.\n" +
      (r.kind === "llm"
        ? "답변을 만드는 중 응답 시간이 초과되었습니다.\nE504 · LLM_TIMEOUT"
        : "법령 검색 서버에 연결하지 못했습니다. 검색 결과가 없는 것이 아니라 검색 자체가 실패했습니다.\nE503 · SEARCH_UNAVAILABLE") +
      "\n이번 상담 실행은 종료되었고, 질문은 그대로 보관되어 있어요.\n실행 ID " +
      r.runId
    );
  return (
    {
      out: "이 챗봇이 안내하지 않는 질문입니다.\n이 챗봇은 산업안전보건기준에 관한 규칙에 따른 작업장 안전기준(통로·계단·안전난간·사다리·추락 방지·보호구 등)을 안내합니다. 근로조건·임금·휴가 등은 정확한 답변을 드릴 수 없어요.",
      unclassified:
        "어떤 작업장 안전기준에 대한 질문인지 판단하기 어려워요.\n어디에서 어떤 작업을 하는지, 무엇이 궁금한지 함께 적어 주세요.",
      nodata:
        "지원 범위 안의 질문이지만, 이 목업에는 예시 답변이 없어요.\n실제 서비스에서는 관련 조문을 검색해 다른 주제와 같은 형식(결론·조건·예외·안전조치·근거)으로 답변합니다.\n목업에는 안전난간·사다리·추락 방지·개구부 예시만 들어 있습니다. 검토 도구의 예시 질문을 사용해 보세요.",
    }[r.status] || ""
  );
}
const C = {
  KEY,
  VERSION,
  metrics,
  statusLabels,
  batchLabels,
  dataset,
  judge,
  settings,
  create,
  finishItem,
  counts,
  aggregate,
  compatible,
  compare,
  blank,
  load,
  save,
  traces,
  context,
  answerText,
  validScore,
  isBatch,
};

export default C;
