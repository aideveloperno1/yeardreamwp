import { describe, expect, it } from "vitest";
import M from "../src/lib/mockData.js";
import C from "../src/lib/evaluation.js";
import { decideMock } from "../src/lib/chatRules.js";
import {
  freshChat,
  keys,
  read,
  restoreChat,
  saveRun,
  validRuns,
  write,
} from "../src/lib/storage.js";
const finish = (b) => {
  b.items.forEach((i) => C.finishItem(b, i.id));
  b.state = b.items.some((i) => i.state === "failed") ? "partial" : "completed";
  return b;
};
describe("evaluation rules preserved from static baseline", () => {
  it("counts failure/exclusion separately and aggregates only valid completed scores", () => {
    const b = finish(C.create("prompt", "A", true));
    const c = C.counts(b);
    expect(c).toMatchObject({
      total: 6,
      scheduled: 5,
      completed: 4,
      failed: 1,
      excluded: 1,
    });
    expect(C.aggregate(b, "faithfulness").n).toBe(2);
    b.items[0].scores.accuracy = 0;
    expect(C.aggregate(b, "accuracy").n).toBe(4);
  });
  it("compares paired valid scores and refuses interrupted/incompatible batches", () => {
    const a = finish(C.create("prompt", "A", true)),
      b = finish(C.create("prompt", "B", false));
    expect(C.compare(a, b, "accuracy").n).toBe(4);
    expect(C.compare(a, b, "faithfulness").n).toBe(2);
    b.state = "interrupted";
    expect(C.compare(a, b, "accuracy")).toBeNull();
    b.state = "completed";
    b.settings.gen = "changed";
    expect(C.compare(a, b, "accuracy")).toBeNull();
  });
  it("restores selection and marks in-progress batch interrupted", () => {
    const d = C.blank();
    d.selection = { type: "retrieval", variant: "B" };
    const b = C.create("retrieval", "B");
    b.items[0].state = "running";
    d.batches["retrieval:B"] = b;
    C.save(sessionStorage, d);
    const r = C.load(sessionStorage);
    expect(r.data.selection).toEqual(d.selection);
    expect(r.data.batches["retrieval:B"].state).toBe("interrupted");
    expect(r.data.batches["retrieval:B"].items[0].state).toBe("pending");
  });
  it("keeps representative trace settings from the actual mock batch", () => {
    const b = finish(C.create("retrieval", "B"));
    const d = C.blank();
    d.batches["retrieval:B"] = b;
    const records = C.traces(d);
    expect(records).toHaveLength(1);
    expect(records[0].settings.method).toContain("BM25");
    expect(records[0].id).toBe(b.id + "-EX-01");
  });
  it("handles blocked, damaged and unsupported evaluation records", () => {
    expect(
      C.load({
        getItem() {
          throw Error();
        },
      }).warning,
    ).not.toBe("");
    sessionStorage.setItem(C.KEY, "{bad");
    expect(C.load(sessionStorage).warning).not.toBe("");
    expect(sessionStorage.getItem(C.KEY)).toBe("{bad");
    expect(
      C.save(
        {
          setItem() {
            throw Error();
          },
        },
        C.blank(),
      ),
    ).not.toBe("");
    sessionStorage.setItem(C.KEY, JSON.stringify({ version: 999 }));
    expect(C.load(sessionStorage).warning).not.toBe("");
  });
});
describe("question decisions and full answer retention", () => {
  it("distinguishes pending supplements, new topics, outside scope and no example", () => {
    const s = freshChat();
    const a = decideMock(s, "안전난간", null);
    expect(a.status).toBe("clarify");
    s.pending = { topic: a.topic, original: a.original };
    expect(decideMock(s, "계단 측면", null).status).toBe("answer");
    expect(decideMock(s, "사다리 위에서 작업", null).sources).toEqual(["f42"]);
    expect(decideMock(s, "연차휴가", null).status).toBe("out");
    expect(decideMock(s, "조도 기준", null).status).toBe("nodata");
  });
  it("preserves conditions, exceptions, actions and judgment limits in saved answer", () => {
    const r = decideMock(freshChat(), "사다리 위에서 작업", null);
    const text = C.answerText(r);
    for (const key of ["적용 조건", "예외", "안전조치", "판단 한계"])
      expect(text).toContain(key);
    expect(text).toContain(r.limits);
    expect(
      C.answerText(decideMock(freshChat(), "안전난간", "error_search")),
    ).toContain("SEARCH_UNAVAILABLE");
  });
});
describe("storage compatibility and isolation", () => {
  it("restores legacy messages and pending without inventing missing records", () => {
    const old = {
      sessionId: "S-OLD",
      messages: [{ role: "user", text: "기존 질문", at: "2026-10-21" }],
      pending: { topic: "guardrail", original: "안전난간" },
    };
    write(keys("mock").chat, old);
    expect(restoreChat("mock").value).toMatchObject(old);
    expect(restoreChat("live").value.messages).toHaveLength(0);
  });
  it("marks old streaming answer interrupted after reload", () => {
    write(keys("live").chat, {
      ...freshChat(),
      messages: [
        {
          role: "ai",
          result: {
            status: "streaming",
            runId: "CLIENT-old",
            mode: "live",
            text: "일부",
          },
        },
      ],
    });
    expect(restoreChat("live").value.messages[0].result).toMatchObject({
      status: "interrupted",
      text: "일부",
    });
  });
  it("retains last 60 records in separate mode keys", () => {
    for (let i = 0; i < 62; i++)
      saveRun({ id: "R" + i, sessionId: "S", question: "q" }, "mock");
    saveRun({ id: "API", sessionId: "S", question: "live" }, "live");
    expect(read(keys("mock").runs, [], validRuns).value).toHaveLength(60);
    expect(read(keys("live").runs, [], validRuns).value[0].id).toBe("API");
  });
  it("keeps damaged storage untouched and reports access failure", () => {
    localStorage.setItem(keys("mock").chat, "{bad");
    expect(restoreChat("mock").blocked).toBe(true);
    expect(localStorage.getItem(keys("mock").chat)).toBe("{bad");
    expect(
      read("x", null, () => true, {
        getItem() {
          throw Error();
        },
      }).blocked,
    ).toBe(true);
  });
  it("preserves all requirements and law source verification metadata", () => {
    expect(M.reqs).toHaveLength(55);
    expect(M.laws.f42.verify).toContain("원문 미수록");
  });
});
