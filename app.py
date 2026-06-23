import streamlit as st
import io

st.set_page_config(page_title="웰파인 AI 회의실", page_icon="🤖", layout="wide",
                   initial_sidebar_state="expanded")

CSS = """
<style>
[data-testid="stAppViewContainer"]{background:#f5f1eb;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#ece8e0;}
#MainMenu,footer{visibility:hidden;}

.table-room{
  background:linear-gradient(180deg,#e8e2d6 0%,#dfd9cd 100%);
  border-radius:20px;padding:22px 12px 14px;
  border:1px solid #cec8be;
  box-shadow:inset 0 2px 6px rgba(0,0,0,0.07);
}
.bot-row{display:flex;justify-content:center;align-items:flex-end;gap:8px;}
.top-row{align-items:flex-end;}
.bottom-row{align-items:flex-start;}
.table-middle{display:flex;justify-content:center;align-items:center;gap:8px;margin:2px 0;}

.conf-table{
  flex:0 0 auto;width:300px;height:82px;
  background:linear-gradient(160deg,#6B4423 0%,#8B5E3C 40%,#9B6B45 60%,#6B4423 100%);
  border-radius:10px;border:3px solid #4A2E18;
  box-shadow:0 6px 20px rgba(0,0,0,0.4),
             inset 0 1px 0 rgba(255,255,255,0.12),
             inset 0 -2px 0 rgba(0,0,0,0.2);
  display:flex;align-items:center;justify-content:center;
}
.table-label{color:rgba(255,255,255,0.5);font-size:10px;letter-spacing:2.5px;
  text-transform:uppercase;font-family:Georgia,serif;}

.bot-card{display:flex;flex-direction:column;align-items:center;
  width:66px;position:relative;}
.bot-avatar{font-size:28px;line-height:1;filter:drop-shadow(0 2px 3px rgba(0,0,0,0.2));}
.bot-name{font-size:10px;font-weight:700;color:#3a3530;margin-top:3px;text-align:center;}
.status-dot{width:7px;height:7px;border-radius:50%;margin-top:3px;background:#bbb;}

.status-idle .status-dot{background:#bbb;}
.status-active .status-dot{background:#f5c842;box-shadow:0 0 7px #f5c842;
  animation:blink 0.9s ease-in-out infinite;}
.status-done .status-dot{background:#52c463;box-shadow:0 0 5px #52c463;}
.status-error .status-dot{background:#e05555;}

.speech-bubble{
  position:absolute;bottom:calc(100% + 5px);
  left:50%;transform:translateX(-50%);
  background:#fff9e6;border:1.5px solid #f5c842;
  border-radius:8px;padding:3px 7px;
  font-size:9px;font-weight:800;color:#6B4A00;
  white-space:nowrap;box-shadow:0 3px 8px rgba(0,0,0,0.15);
  animation:float 1.5s ease-in-out infinite;z-index:10;
}
.speech-bubble::after{
  content:'';position:absolute;top:100%;left:50%;
  transform:translateX(-50%);
  border:5px solid transparent;border-top-color:#f5c842;
}

.chairman-area{display:flex;justify-content:center;
  margin-top:10px;padding-top:8px;
  border-top:1px dashed #c0b8ae;}
.chairman-wrap{background:rgba(255,255,255,0.6);border-radius:12px;
  padding:6px 16px;display:inline-flex;align-items:center;gap:10px;
  border:1px solid #d8d0c8;box-shadow:0 2px 6px rgba(0,0,0,0.06);}
.chairman-inner{display:flex;flex-direction:column;align-items:flex-start;}
.chairman-title{font-size:11px;font-weight:700;color:#3a3530;}
.chairman-subtitle{font-size:9px;color:#aaa;font-style:italic;}

@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}
@keyframes float{0%,100%{transform:translateX(-50%) translateY(0);}
  50%{transform:translateX(-50%) translateY(-3px);}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── 데이터 ────────────────────────────────────────────────
PROVIDERS = {
    "🟠 Claude (Anthropic)": {"key": "anthropic", "models": {
        "Claude Sonnet (기본)": "claude-sonnet-4-6",
        "Claude Opus (고성능)": "claude-opus-4-8",
        "Claude Haiku (빠름)": "claude-haiku-4-5-20251001",
    }},
    "🟢 ChatGPT (OpenAI)": {"key": "openai", "models": {
        "GPT-4o (권장)": "gpt-4o",
        "GPT-4o mini (빠름)": "gpt-4o-mini",
    }},
    "🔵 Gemini (Google)": {"key": "gemini", "models": {
        "Gemini 2.5 Flash (무료/빠름)": "gemini-2.5-flash",
        "Gemini 2.5 Pro (고성능)": "gemini-2.5-pro",
        "Gemini 1.5 Flash": "gemini-1.5-flash",
    }},
}

BOTS = [
    {"name": "노무봇",  "emoji": "⚖️",  "system": "웰파인(강원도 횡성 건강기능식품 OEM/ODM) 인사총무팀 노무 전문 AI.\n성격: 보수적이고 까다로운 노무사 스타일.\n- 법 조문 근거 없이 '괜찮다'고 하지 마세요\n- 애매하면 반드시 '전문가 확인 필요' 명시\n- 근로기준법, 노동관련 법령 관점으로 검토\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "HRM봇",  "emoji": "📋",  "system": "웰파인 인사총무팀 HRM 전문 AI.\n성격: 원칙주의자.\n- 사내 규정, 취업규칙과의 일치 여부 체크\n- 규정과 실제 운영 간의 괴리를 찾아내세요\n- 형평성 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "채용봇",  "emoji": "🤝",  "system": "웰파인 인사총무팀 채용 전문 AI.\n성격: 현실주의자.\n- 강원도 횡성 지역의 지원자 풀이 제한적임 감안\n- JD의 모호한/차별적 표현 찾아내세요\n- 채용 과정의 법적 문제 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "계약봇",  "emoji": "📝",  "system": "웰파인 인사총무팀 계약 전문 AI.\n성격: 의심 많은 변호사 스타일.\n- 계약서 조항 꼼꼼하게 분석\n- 불리한 조항/모호한 표현 찾아내세요\n- 해지/갱신 조항 리스크 집중 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "총무봇",  "emoji": "🏢",  "system": "웰파인 인사총무팀 총무 전문 AI.\n성격: 꼼꼼한 살림꾼.\n- 비용 처리, 시설, 물품 관련 규정 준수 체크\n- 세무적으로 문제없는지 검토\n- 내부 결재/승인 프로세스 확인\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "급여봇",  "emoji": "💰",  "system": "웰파인 인사총무팀 급여/4대보험 전문 AI.\n성격: 숫자에 목숨 거는 스타일.\n- 급여 계산과 공제 항목 정확성 체크\n- 4대보험 요율과 신고 기한 확인\n- E-9 비자 외국인 근로자의 특수한 처리 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "교육봇",  "emoji": "📚",  "system": "웰파인 인사총무팀 교육/OJT 전문 AI.\n성격: 실용주의 교육자.\n- 교육 내용이 실제 업무와 연결되는지 체크\n- OJT/수습평가 설계의 공정성 확인\n- 외국인 근로자 교육 시 언어/문화 차이 고려\n- 핵심 포인트 번호 목록으로 제시"},
]

FACTCHECK_SYS = "웰파인 인사총무팀 팩트체크 AI.\n성격: 감정 없는 검사 스타일.\n- 근거 없는 주장, 틀린 정보 모두 지적\n- 맞으면 맞다, 틀리면 틀리다고 냉정하게 판단\n- 각 봇 의견별로 검증 결과 정리"
FIELD_SYS   = "웰파인 인사총무팀 실무 전문 AI.\n성격: 현장 경험 많은 선배.\n- '이론은 맞는데 실제로 가능해?' 관점으로 접근\n- 직원 입장에서 이 결정을 받아들일 수 있는지 시뮬레이션\n- 강원도 횡성 제조업 현장 특성 감안\n- 현실적으로 실행 가능한 방향 제시"
FINAL_SYS   = "웰파인 인사총무팀 AI 회의 최종 정리 AI. 냉철한 회의 진행자.\n- 모든 봇 의견 종합해 결론 도출\n- 의견 충돌한 부분은 양쪽 모두 명시\n- 구체적 액션 아이템을 우선순위 순서로 제시\n- 전문가 확인 반드시 필요한 사항 명시\n\n다음 형식으로 작성:\n## 핵심 결론\n## 주요 리스크\n## 액션 아이템 (우선순위 순)\n## 전문가 확인 필요 사항"

# ── 함수 ────────────────────────────────────────────────
def call_bot(pkey, api_key, model, system, content, max_tokens=700):
    combined = system + "\n\n" + content
    try:
        if pkey == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(model=model, max_tokens=max_tokens,
                system=system, messages=[{"role": "user", "content": content}])
            return resp.content[0].text
        elif pkey == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(model=model, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": content}])
            return resp.choices[0].message.content
        elif pkey == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            resp = genai.GenerativeModel(model).generate_content(combined)
            return resp.text
    except Exception as e:
        return f"오류: {e}"
    return "지원하지 않는 제공자."


def extract_text(f):
    if not f:
        return ""
    ext = f.name.split(".")[-1].lower()
    try:
        if ext == "txt":
            return f.read().decode("utf-8", errors="ignore")
        elif ext == "pdf":
            import pypdf
            r = pypdf.PdfReader(io.BytesIO(f.read()))
            return "\n".join(p.extract_text() or "" for p in r.pages)
        elif ext in ("docx", "doc"):
            from docx import Document
            d = Document(io.BytesIO(f.read()))
            return "\n".join(p.text for p in d.paragraphs)
    except Exception as e:
        return f"[파일 오류: {e}]"
    return ""


def build_content(doc_text, question, case_notes):
    parts = []
    if case_notes.strip():
        parts.append("[웰파인 누적 케이스]\n" + case_notes.strip())
    if doc_text.strip():
        parts.append("[문서]\n" + doc_text[:3000])
    if question.strip():
        parts.append("[질문/검토 요청]\n" + question.strip())
    return "\n\n".join(parts)


def bot_card(name, emoji, status="idle"):
    bubble = '<div class="speech-bubble">💬 발언 중</div>' if status == "active" else ""
    return (
        f'<div class="bot-card status-{status}">'
        f'{bubble}'
        f'<div class="bot-avatar">{emoji}</div>'
        f'<div class="bot-name">{name}</div>'
        f'<div class="status-dot"></div>'
        f'</div>'
    )


def render_table(statuses=None):
    if statuses is None:
        statuses = {}
    s = lambda n: statuses.get(n, "idle")
    ei = {b["name"]: b["emoji"] for b in BOTS}
    ei.update({"팩트체크봇": "🔍", "실무봇": "🔧", "최종정리봇": "🎯"})

    top  = "".join(bot_card(n, ei[n], s(n)) for n in ["노무봇", "HRM봇", "채용봇", "계약봇"])
    bot  = "".join(bot_card(n, ei[n], s(n)) for n in ["총무봇", "급여봇", "교육봇"])

    cs = s("최종정리봇")
    dot_style = {
        "idle":  "background:#bbb",
        "active":"background:#f5c842;box-shadow:0 0 7px #f5c842",
        "done":  "background:#52c463;box-shadow:0 0 5px #52c463",
        "error": "background:#e05555",
    }.get(cs, "background:#bbb")
    chair_bubble = '<div class="speech-bubble">💬 발언 중</div>' if cs == "active" else ""

    return (
        '<div class="table-room">'
        f'<div class="bot-row top-row">{top}</div>'
        '<div class="table-middle">'
        f'{bot_card("팩트체크봇", ei["팩트체크봇"], s("팩트체크봇"))}'
        '<div class="conf-table"><div class="table-label">WELLFINE HR AI</div></div>'
        f'{bot_card("실무봇", ei["실무봇"], s("실무봇"))}'
        '</div>'
        f'<div class="bot-row bottom-row">{bot}</div>'
        '<div class="chairman-area"><div class="chairman-wrap">'
        f'{chair_bubble}'
        '<span style="font-size:22px;">🎯</span>'
        '<div class="chairman-inner">'
        '<div class="chairman-title">최종정리봇</div>'
        '<div class="chairman-subtitle">회의 진행자</div>'
        '</div>'
        f'<div class="status-dot" style="{dot_style};width:7px;height:7px;border-radius:50%;"></div>'
        '</div></div>'
        '</div>'
    )

# ── 세션 초기화 ───────────────────────────────────────────
if "bot_statuses" not in st.session_state:
    st.session_state.bot_statuses = {}
if "case_notes" not in st.session_state:
    st.session_state.case_notes = ""
if "bot_prompts" not in st.session_state:
    bp = {b["name"]: b["system"] for b in BOTS}
    bp["팩트체크봇"] = FACTCHECK_SYS
    bp["실무봇"]    = FIELD_SYS
    bp["최종정리봇"] = FINAL_SYS
    st.session_state.bot_prompts = bp

# ── 사이드바 ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    p_label = st.selectbox("제공자", list(PROVIDERS.keys()), label_visibility="collapsed")
    prov = PROVIDERS[p_label]
    pkey = prov["key"]

    api_in = st.text_input("API 키", type="password", label_visibility="collapsed",
        placeholder={"anthropic":"sk-ant-...","openai":"sk-...","gemini":"AIza..."}.get(pkey, ""))
    try:
        sec = st.secrets.get({"anthropic":"ANTHROPIC_API_KEY","openai":"OPENAI_API_KEY",
                               "gemini":"GEMINI_API_KEY"}[pkey], "")
    except Exception:
        sec = ""
    api_key = api_in or sec

    m_label = st.selectbox("모델", list(prov["models"].keys()), label_visibility="collapsed")
    model   = prov["models"][m_label]
    st.caption(f"**{p_label}** · {m_label}")

    st.divider()
    st.markdown("### 🤖 봇 프롬프트 편집")
    all_names = [b["name"] for b in BOTS] + ["팩트체크봇", "실무봇", "최종정리봇"]
    bot_sel = st.selectbox("봇 선택", all_names, label_visibility="collapsed")
    edited  = st.text_area("프롬프트", value=st.session_state.bot_prompts.get(bot_sel, ""),
                           height=160, label_visibility="collapsed")
    if st.button("💾 저장", use_container_width=True):
        st.session_state.bot_prompts[bot_sel] = edited
        st.success("저장됨!")

    st.divider()
    st.markdown("### 📂 누적 케이스")
    new_notes = st.text_area("케이스", value=st.session_state.case_notes, height=100,
        placeholder="예: 수습 불합격 시 면담 2회 이상 기록 필요\nE-9 계약서 이중언어 작성...",
        label_visibility="collapsed")
    if st.button("💾 케이스 저장", use_container_width=True):
        st.session_state.case_notes = new_notes
        st.success("저장됨!")

# ── 메인 ──────────────────────────────────────────────────
st.markdown("## 🏢 웰파인 인사총무 AI 회의실")
st.divider()

table_slot = st.empty()
table_slot.markdown(render_table(st.session_state.bot_statuses), unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("##### 📄 문서 업로드")
    ufile = st.file_uploader("파일", type=["pdf","docx","txt"], label_visibility="collapsed")
    if ufile:
        st.success(f"✅ {ufile.name}")
with col2:
    st.markdown("##### 💬 질문 / 검토 요청")
    question = st.text_area("질문", height=90, label_visibility="collapsed",
        placeholder="예: 이 근로계약서 수습기간 조항이 법적으로 문제없나요?")

go = st.button("🚀 회의 시작", type="primary", use_container_width=True)

# ── 회의 진행 ─────────────────────────────────────────────
if go:
    if not api_key:
        st.error("왼쪽 사이드바에서 API 키를 입력해주세요.")
        st.stop()
    if not ufile and not question.strip():
        st.error("문서를 업로드하거나 질문을 입력해주세요.")
        st.stop()

    st.session_state.bot_statuses = {}
    doc_text = extract_text(ufile) if ufile else ""
    content  = build_content(doc_text, question, st.session_state.case_notes)
    bp       = st.session_state.bot_prompts

    def upd(name, status):
        st.session_state.bot_statuses[name] = status
        table_slot.markdown(render_table(st.session_state.bot_statuses), unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📋 회의 진행")

    # ── 1라운드: 전문 봇 1차 의견 ──────────────────────────
    st.markdown("**1라운드 — 전문 봇 1차 의견**")
    ops1 = {}
    for b in BOTS:
        upd(b["name"], "active")
        with st.status(f'{b["emoji"]} {b["name"]} 1차 분석 중...', expanded=False) as stat:
            res = call_bot(pkey, api_key, model, bp.get(b["name"], b["system"]), content, 600)
            ops1[b["name"]] = res
            st.markdown(res)
            stat.update(label=f'{b["emoji"]} {b["name"]} ✅', state="complete", expanded=False)
        upd(b["name"], "done")

    # ── 팩트체크 1차 ────────────────────────────────────────
    st.markdown("**팩트체크 1차**")
    fc1_in = content + "\n\n[1차 의견]\n" + "\n\n".join(f"{n}:\n{o}" for n, o in ops1.items())
    upd("팩트체크봇", "active")
    with st.status("🔍 팩트체크봇 1차 검증 중...", expanded=False) as stat:
        fc1 = call_bot(pkey, api_key, model, bp.get("팩트체크봇", FACTCHECK_SYS), fc1_in, 900)
        st.markdown(fc1)
        stat.update(label="🔍 팩트체크봇 1차 ✅", state="complete", expanded=False)
    upd("팩트체크봇", "done")

    # ── 2라운드: 전문 봇 2차 의견 (팩트체크 반영) ───────────
    st.markdown("**2라운드 — 팩트체크 반영 재의견**")
    ops2 = {}
    for b in BOTS:
        upd(b["name"], "active")
        r2_in = (content
            + f"\n\n[팩트체크 결과]\n{fc1}"
            + f"\n\n[내 1차 의견]\n{ops1.get(b['name'], '')}"
            + "\n\n위 팩트체크 결과를 반영해 의견을 보완하거나 수정해주세요. 기존 의견이 맞다면 그 근거를 보강해주세요.")
        with st.status(f'{b["emoji"]} {b["name"]} 2차 검토 중...', expanded=False) as stat:
            res2 = call_bot(pkey, api_key, model, bp.get(b["name"], b["system"]), r2_in, 600)
