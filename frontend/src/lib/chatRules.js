import M from "./mockData.js";
import C from "./evaluation.js";
export function decideMock(state, text, forced) {
  const SOURCES = M.laws;
  const TOPICS = {
    guardrail: "안전난간",
    ladder: "사다리",
    fall: "추락 방지",
    opening: "개구부",
  };

  /* ───────── 주제 분류 · 정보 충족 판단 (목업용 규칙) ───────── */
  const has = (t, words) => words.some((w) => t.includes(w));
  function classify(t) {
    if (has(t, ["안전난간", "난간", "발끝막이"])) return "guardrail";
    if (has(t, ["사다리"])) return "ladder";
    if (
      has(t, ["개구부", "작업발판 끝", "작업발판의 끝", "통로 끝", "통로의 끝"])
    )
      return "opening";
    if (has(t, ["추락", "떨어", "작업발판", "높은 곳", "고소"])) return "fall";
    return null;
  }
  const SAFETY_WORDS = [
    "안전",
    "작업",
    "현장",
    "설치",
    "기준",
    "법령",
    "규칙",
    "산업",
    "근로자",
    "위험",
    "설비",
    "공장",
    "창고",
  ];
  const OUT_WORDS = [
    "연차",
    "휴가",
    "임금",
    "월급",
    "급여",
    "퇴직",
    "해고",
    "근로계약",
    "주휴",
    "야근수당",
    "4대보험",
    "세금",
    "날씨",
  ];
  // 지원 범위 안이지만 목업에 예시 데이터가 없는 주제 (검토용 표시)
  const NODATA_WORDS = [
    "바닥",
    "조도",
    "조명",
    "럭스",
    "출입구",
    "출입문",
    "방화문",
    "낙하물",
    "방호선반",
    "경보",
    "가설통로",
    "계단참",
    "계단의 폭",
    "계단 폭",
    "보호구",
    "안전모",
    "풍속",
    "강풍",
    "크레인",
    "지붕",
    "채광창",
    "용접",
    "환기",
  ];
  // 구체적인 요소·수치를 물으면 되묻지 않고 바로 답함
  const GUARD_SPECIFIC = [
    "높이",
    "하중",
    "발끝막이",
    "중간 난간대",
    "상부 난간대",
    "난간기둥",
    "난간대",
    "cm",
    "센티",
    "kg",
    "지름",
    "간격",
  ];
  function guardPlace(t) {
    if (has(t, ["계단"])) return "stairs";
    if (has(t, ["작업발판", "발판 끝", "단부", "가장자리", "비계"]))
      return "edge";
    if (has(t, ["개구부"])) return "opening";
    if (
      has(t, [
        "통로",
        "옥상",
        "창고",
        "경사로",
        "바닥",
        "층",
        "현장",
        "공장",
        "높이",
      ])
    )
      return "general";
    return null;
  }
  function ladderUse(t) {
    if (has(t, ["사다리식 통로"])) return "passage";
    if (
      has(t, [
        "사다리 위",
        "위에서 작업",
        "올라가서 작업",
        "작업용",
        "작업할",
        "작업하",
        "작업에",
        "이동식 사다리",
        "이동식사다리",
      ])
    )
      return "work";
    if (has(t, ["통로", "오르내", "올라가", "내려가", "출입"]))
      return "passage";
    return null;
  }
  function fallPlace(t) {
    if (has(t, ["개구부", "작업발판 끝", "작업발판의 끝", "통로 끝", "단부"]))
      return "excluded";
    if (has(t, ["기계", "설비", "선박", "지붕", "높은", "고소", "2미터", "2m"]))
      return "covered";
    return null;
  }

  /* ───────── 상담 결과 (구조화) ───────── */
  function build(status, extra) {
    state.run += 1;
    return Object.assign(
      {
        status,
        at: new Date(),
        runId:
          "RUN-" +
          state.sessionId.slice(-4) +
          "-" +
          String(state.run).padStart(3, "0"),
      },
      extra,
    );
  }

  const GUARD_SITUATION = {
    stairs: [
      "계단 측면",
      "계단 측면은 난간기둥 간격이 25cm 이하이면 중간 난간대를 생략할 수 있어요.",
    ],
    edge: [
      "작업발판 끝",
      "작업발판 끝이라면 발끝막이판(10cm 이상)도 함께 설치하세요.",
    ],
    opening: [
      "개구부 주변",
      "개구부 방호 조치는 별도 조문이 있어 원문을 함께 확인하세요.",
    ],
    general: ["일반 장소", ""],
  };

  function answerFor(topic, ctx, contextNote, askText) {
    if (topic === "guardrail") {
      const p = guardPlace(ctx),
        sit = GUARD_SITUATION[p];
      return build("answer", {
        topic,
        contextNote,
        askText,
        placeTag: sit ? sit[0] : "장소 미지정",
        conclusion: "상부 난간대 90cm 이상 · 발끝막이판 10cm 이상",
        summary: "상부 난간대는 바닥면에서 90cm 이상 높이에 설치해야 합니다.",
        explain:
          "안전난간은 상부 난간대·중간 난간대·발끝막이판·난간기둥으로 구성하고, 가장 약한 지점에서도 100kg 이상의 하중을 견뎌야 합니다.",
        situation: sit
          ? sit[1]
          : "장소를 알려주시면 해당 장소의 예외까지 좁혀서 안내할게요.",
        brief: [
          "상부 난간대 높이(120cm 기준)에 따라 중간 난간대 위치와 단수가 달라져요.",
          "계단 측면·발끝막이판에는 조건부 예외가 있어요.",
          "난간 전체를 바닥과 평행하게, 100kg 이상 하중을 견디게 설치해요.",
        ],
        conditions: [
          [
            "상부 난간대를 120cm 이하에 설치하면 중간 난간대는 상부 난간대와 바닥면의 중간에 설치",
            "제2호",
          ],
          [
            "120cm 이상에 설치하면 중간 난간대를 2단 이상 균등하게 설치하고 상하 간격은 60cm 이하",
            "제2호",
          ],
          ["발끝막이판은 바닥면에서 10cm 이상 높이 유지", "제3호"],
          [
            "난간대는 지름 2.7cm 이상의 금속제 파이프나 그 이상의 강도가 있는 재료",
            "제6호",
          ],
        ],
        exceptions: [
          [
            "계단의 개방된 측면에서 난간기둥 간격이 25cm 이하이면 중간 난간대를 설치하지 않을 수 있음",
            "제2호 단서",
          ],
          [
            "물체가 떨어지거나 날아올 위험이 없거나 망 설치 등 예방 조치를 한 장소는 발끝막이판 기준 제외",
            "제3호 단서",
          ],
          [
            "중간 난간대·발끝막이판·난간기둥은 비슷한 구조와 성능을 가진 것으로 대체 가능",
            "제1호 단서",
          ],
        ],
        actions: [
          [
            "상부·중간 난간대는 난간 전체 길이에 걸쳐 바닥면과 평행 유지",
            "제5호",
          ],
          ["난간기둥은 난간대를 견고하게 받치도록 적정 간격 유지", "제4호"],
          ["가장 취약한 지점·방향에서 100kg 이상 하중을 견디는 구조", "제7호"],
        ],
        sources: ["g13"],
        followups: [
          "계단 측면에 설치하면 달라지나요?",
          "발끝막이판은 꼭 있어야 하나요?",
        ],
      });
    }
    if (topic === "ladder" && ladderUse(ctx) === "work") {
      return build("answer", {
        topic,
        contextNote,
        askText,
        placeTag: "사다리 위 작업",
        conditional: true,
        conclusion: "조건부로 가능 — 아래 조건을 모두 지킬 때만",
        summary:
          "작업발판·추락방호망 설치가 곤란한 경우에만, 정해진 사용 조건을 모두 지켜 이동식 사다리에서 작업할 수 있습니다.",
        explain:
          "버팀대가 3개 이상이고 지면에 안정적으로 세울 수 있는 이동식 사다리가 대상입니다.",
        situation: "",
        brief: [
          "평탄·견고하고 미끄럽지 않은 바닥에 세우고, 바닥면에서 3.5m 이하 높이에서만 작업해요.",
          "최상부 발판·그 아래 디딤대 작업은 금지지만, 높이 1m 이하 사다리는 예외예요.",
          "안전모를 쓰고, 작업 높이가 2m 이상이면 안전대도 함께 착용해요.",
        ],
        limits:
          "조건 중 하나라도 지키지 못하면 이 방식의 사다리 작업은 허용되지 않습니다. 작업발판이나 추락방호망을 설치할 수 있는 현장이라면 그쪽이 먼저입니다.",
        conditions: [
          [
            "작업발판과 추락방호망을 설치하기 곤란한 경우에만 해당",
            "제42조제4항",
          ],
          [
            "버팀대 3개 이상, 지면에 안정적으로 세울 수 있는 이동식 사다리",
            "제42조제4항",
          ],
          ["평탄·견고하고 미끄럽지 않은 바닥에 설치", "제42조제4항"],
          ["제조사가 표시한 최대사용하중 이내에서 사용", "제42조제4항"],
          ["바닥면에서 높이 3.5m 이하의 장소에서만 작업", "제42조제4항"],
        ],
        exceptions: [
          [
            "최상부 발판과 그 하단 디딤대에서의 작업 금지 — 높이 1m 이하 사다리는 예외",
            "제42조제4항",
          ],
        ],
        actions: [
          ["시설물 고정·아웃트리거 설치 등으로 넘어짐 방지", "제42조제4항"],
          ["안전모 착용, 작업 높이 2m 이상이면 안전대도 착용", "제42조제4항"],
          ["사용 전 변형·이상 유무 점검", "제42조제4항"],
        ],
        sources: ["f42"],
        followups: [
          "사다리를 통로로 쓸 때 기준은요?",
          "추락방호망은 언제 설치해요?",
        ],
      });
    }
    if (topic === "ladder") {
      return build("answer", {
        topic,
        contextNote,
        askText,
        placeTag: "통로로 사용",
        conclusion: "폭 30cm 이상 · 상단은 걸친 지점보다 60cm 이상",
        summary:
          "사다리를 통로로 쓰면 폭 30cm 이상, 상단은 걸친 지점보다 60cm 이상 올라가야 합니다.",
        explain:
          "오르내리는 용도라면 ‘사다리식 통로’ 기준이 적용됩니다. 발판 간격은 일정하게, 발판과 벽 사이는 15cm 이상 띄워야 해요.",
        situation: "",
        brief: [
          "길이 10m 이상이면 5m 이내마다 계단참이 필요해요.",
          "잠함 내부, 건조·수리 중 선박의 구명줄이 설치된 사다리식 통로는 일부 기준(제5~10호)이 적용되지 않아요.",
          "넘어지거나 미끄러지지 않게 하는 조치가 필요해요.",
        ],
        limits:
          "사다리 위에서 작업한다면 사다리식 통로 기준이 아니라 이동식 사다리 사용 조건(제42조제4항)을 확인해야 해요.",
        conditions: [
          [
            "사다리식 통로 길이가 10m 이상이면 5m 이내마다 계단참 설치",
            "제1항제8호",
          ],
          [
            "기울기 75도 이하 (고정식은 90도 이하, 높이 7m 이상이면 바닥에서 2.5m 지점부터 등받이울)",
            "제1항제9호",
          ],
          [
            "접이식 사다리는 사용 중 접히거나 펼쳐지지 않게 철물 등으로 고정",
            "제1항제10호",
          ],
        ],
        exceptions: [
          [
            "잠함 내 사다리식 통로와 건조·수리 중인 선박의 구명줄이 설치된 사다리식 통로는 제1항제5호~제10호 적용 제외",
            "제2항",
          ],
        ],
        actions: [
          ["견고한 구조, 심한 손상·부식이 없는 재료 사용", "제1항제1·2호"],
          ["사다리가 넘어지거나 미끄러지지 않도록 방지 조치", "제1항제6호"],
          ["상단을 걸쳐놓은 지점에서 60cm 이상 올라가게 설치", "제1항제7호"],
        ],
        sources: ["l24"],
        followups: [
          "길이가 12m면 계단참이 필요해요?",
          "사다리 위에서 작업해도 되나요?",
        ],
      });
    }
    if (topic === "opening") {
      return build("answer", {
        topic,
        contextNote,
        askText,
        placeTag: "끝 부분·개구부",
        conclusion: "난간·울타리·덮개 등 방호 조치 설치 + 개구부 표시",
        summary:
          "추락 위험이 있는 작업발판·통로의 끝이나 개구부에는 안전난간·울타리·수직형 추락방망·덮개 등 방호 조치를 튼튼하게 설치해야 합니다.",
        explain:
          "덮개를 쓴다면 뒤집히거나 떨어지지 않게 설치하고, 어두운 곳에서도 개구부임을 알아볼 수 있게 표시해야 해요.",
        situation: "",
        brief: [
          "작업발판·통로의 끝이나 개구부로서 근로자가 추락할 위험이 있는 장소에 적용돼요.",
          "난간 등 설치가 매우 곤란하거나 작업상 임시 해체가 필요하면 추락방호망으로, 그것도 곤란하면 안전대 착용 등으로 대신해요.",
          "충분한 강도의 구조로 튼튼하게 설치하고, 개구부임을 표시해요.",
        ],
        conditions: [
          [
            "작업발판 및 통로의 끝이나 개구부로서 근로자가 추락할 위험이 있는 장소",
            "제1항",
          ],
        ],
        exceptions: [
          [
            "난간등 설치가 매우 곤란하거나 작업상 임시로 해체해야 하면 제42조제2항 기준의 추락방호망 설치",
            "제2항",
          ],
          [
            "추락방호망 설치도 곤란하면 안전대 착용 등 추락 위험 방지 조치",
            "제2항 단서",
          ],
        ],
        actions: [
          ["충분한 강도를 가진 구조로 튼튼하게 설치", "제1항"],
          ["덮개는 뒤집히거나 떨어지지 않게 설치", "제1항"],
          ["어두운 장소에서도 알아볼 수 있게 개구부임을 표시", "제1항"],
          ["수직형 추락방망은 한국산업표준 성능기준 적합품 사용", "제1항"],
        ],
        sources: ["o43"],
        followups: [
          "안전난간은 어떻게 설치해요?",
          "추락방호망은 언제 설치해요?",
        ],
      });
    }
    return build("answer", {
      topic,
      contextNote,
      askText,
      placeTag: "기계·설비 또는 높은 곳",
      conclusion:
        "작업발판 설치 → 곤란하면 추락방호망 → 그것도 곤란하면 안전대 등",
      summary:
        "추락 위험이 있는 곳에서 작업한다면 비계를 조립하는 등의 방법으로 작업발판을 설치해야 합니다.",
      explain: "기계·설비·선박블록 위에서 작업할 때도 같은 기준이 적용됩니다.",
      situation: "",
      brief: [
        "추락·넘어질 위험 장소나 기계·설비 위에서 작업할 때 적용돼요.",
        "작업발판이 곤란하면 추락방호망, 그것도 곤란하면 안전대 착용 등으로 대신해요. 작업발판의 끝·개구부는 제43조 대상이에요.",
        "비계 조립 등으로 작업발판을 설치해요.",
      ],
      conditions: [
        [
          "근로자가 추락하거나 넘어질 위험이 있는 장소, 또는 기계·설비·선박블록 등에서 작업",
          "제1항",
        ],
        ["작업 중 근로자가 위험해질 우려가 있는 경우", "제1항"],
      ],
      exceptions: [
        ["작업발판을 설치하기 곤란하면 기준에 맞는 추락방호망 설치", "제2항"],
        [
          "추락방호망도 설치하기 곤란하면 안전대 착용 등 필요한 조치",
          "제2항 단서",
        ],
        [
          "작업발판의 끝·개구부 등은 이 조항이 아니라 제43조(개구부 등의 방호 조치) 대상",
          "제1항 괄호",
        ],
      ],
      actions: [
        ["비계를 조립하는 등의 방법으로 작업발판 설치", "제1항"],
        ["추락방호망은 한국산업표준 성능기준 적합품 사용", "제3항"],
      ],
      sources: ["f42"],
      followups: [
        "작업발판 끝은 어떻게 해야 해요?",
        "이동식 사다리 위에서 작업해도 되나요?",
      ],
    });
  }
  function clarifyFor(topic, original) {
    const q = {
      guardrail: [
        "안전난간을 어디에 설치하시나요?",
        ["계단 측면", "작업발판 끝", "창고·건물 통로"],
      ],
      ladder: [
        "사다리를 어떤 용도로 쓰시나요?",
        ["오르내리는 통로로 사용", "사다리 위에서 작업"],
      ],
      fall: [
        "어떤 장소에서 작업하시나요?",
        ["기계·설비 위 작업", "작업발판 끝·개구부 주변", "지붕 등 높은 곳"],
      ],
      opening: [
        "어떤 방호 조치를 생각하고 계신가요?",
        ["덮개", "안전난간", "추락방호망"],
      ],
    }[topic];
    return build("clarify", {
      topic,
      question: q[0],
      options: q[1],
      need: {
        guardrail: "설치 장소",
        ladder: "사다리 용도",
        fall: "작업 장소",
        opening: "방호 조치 종류",
      }[topic],
      original,
    });
  }
  const holdFor = (topic, reason, askText, sources) =>
    build("hold", {
      topic,
      askText,
      sources: sources || null,
      reason:
        reason ||
        "검색된 조문만으로는 이 질문의 조건에 적용할 근거를 확보하지 못했습니다.",
    });
  // 법령이 정하지 않는 내용 (예: 안전난간 색상) — 관련 조문은 찾지만 답할 근거가 없음
  const NO_BASIS = { guardrail: ["무슨 색", "색상", "색깔", "페인트", "칠해"] };

  function decide(text, forced) {
    const selected = C.context(
      text,
      state.pending,
      state.lastTopic,
      classify,
      has,
      OUT_WORDS,
      NODATA_WORDS,
    );
    const pending = selected.pending ? state.pending : null;
    if (selected.standalone && !forced) return build(selected.standalone, {});
    let topic = selected.topic,
      ctx = selected.ctx;
    const contextNote = pending
      ? "‘" + text + "’ 조건을 더해 이어서 답변했어요."
      : selected.inherited
        ? "앞선 주제(" + TOPICS[topic] + ")에 이어서 답변했어요."
        : null;
    const askText = pending ? ctx : text;
    const anyTopic = topic || state.lastTopic || "guardrail";
    switch (forced) {
      case "error_llm":
        return build("error", { kind: "llm", topic, askText });
      case "error_search":
        return build("error", { kind: "search", topic, askText });
      case "out":
        return build("out", {});
      case "unclassified":
        return build("unclassified", {});
      case "hold":
        return holdFor(
          anyTopic,
          "관련 조문을 검색했지만 결과가 없어(재검색 2회) 답변을 보류합니다.",
          askText,
        );
      case "clarify":
        return clarifyFor(anyTopic, pending ? pending.original : text);
      case "answer":
        return answerFor(anyTopic, ctx, contextNote, askText);
      case "nodata":
        return build("nodata", {});
    }
    if (!topic) {
      if (has(text, OUT_WORDS)) return build("out", {});
      if (has(text, NODATA_WORDS)) return build("nodata", {});
      return has(text, SAFETY_WORDS)
        ? build("unclassified", {})
        : build("out", {});
    }
    const lastAi = [...state.messages].reverse().find((m) => m.role === "ai");
    const asked =
      !!pending ||
      (state.lastTopic === topic &&
        lastAi &&
        lastAi.result.status === "answer");
    if (NO_BASIS[topic] && has(ctx, NO_BASIS[topic]))
      return holdFor(
        topic,
        "검색된 조문(" +
          SOURCES.g13.article +
          " " +
          SOURCES.g13.title +
          ")에 이 질문에 관한 기준이 없습니다.",
        askText,
        ["g13"],
      );
    if (topic === "guardrail")
      return !guardPlace(ctx) && !has(ctx, GUARD_SPECIFIC) && !asked
        ? clarifyFor(topic, text)
        : answerFor(topic, ctx, contextNote, askText);
    if (topic === "ladder")
      return !ladderUse(ctx) && !asked
        ? clarifyFor(topic, text)
        : answerFor(topic, ctx, contextNote, askText);
    if (topic === "opening") return answerFor(topic, ctx, contextNote, askText);
    const fp = fallPlace(ctx);
    if (fp === "excluded")
      return answerFor("opening", ctx, contextNote, askText);
    return !fp && !asked
      ? clarifyFor(topic, text)
      : answerFor(topic, ctx, contextNote, askText);
  }

  return decide(text, forced);
}
