import streamlit as st
import io
import re

st.set_page_config(page_title="웰파인 AI 회의실", page_icon="🤖", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f0ede8; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background-color: #e8e4df; }
</style>
""", unsafe_allow_html=True)

PROVIDERS = {
    "🟠 Claude (Anthropic)": {
        "key": "anthropic",
        "models": {"Sonnet (기본)": "claude-sonnet-4-6", "Opus (고성능)": "claude-opus-4-8", "Haiku (빠름)": "claude-haiku-4-5-20251001"}
    },
    "🟢 ChatGPT (OpenAI)": {
        "key": "openai",
        "models": {"GPT-4o (권장)": "gpt-4o", "GPT-4o mini (빠름)": "gpt-4o-mini"}
    },
    "🔵 Gemini (Google)": {
        "key": "gemini",
        "models": {"Gemini 2.5 Flash (무료/빠름)": "gemini-2.5-flash", "Gemini 2.5 Pro": "gemini-2.5-pro", "Gemini 1.5 Flash": "gemini-1.5-flash"}
    },
}

BOTS = [
    {"name": "노무봇", "emoji": "⚖️", "system": """당신은 웰파인(강원도 횡성 건강기능식품 OEM/ODM) 인사총무팀의 노무 전문 AI입니다.
성격: 보수적이고 까다롭습니다.
- 법 조문 근거 없이는 절대 "괜찮다"고 말하지 마세요
- 애매하면 반드시 "전문가 확인 필요"라고 명시하세요
- 근로기준법, 노동관련 법령 관점으로 검토하세요
- 핵심 포인트를 번호 목록으로 제시하세요"""},
    {"name": "HRM봇", "emoji": "📋", "system": """당신은 웰파인 인사총무팀의 HRM 전문 AI입니다.
성격: 원칙주의자입니다.
- 사내 규정, 취업규칙과의 일치 여부를 체크하세요
- 규정과 실제 운영 간의 괴리를 찾아내세요
- 형평성을 체크하세요
- 핵심 포인트를 번호 목록으로 제시하세요"""},
    {"name": "채용봇", "emoji": "🤝", "system": """당신은 웰파인 인사총무팀의 채용 전문 AI입니다.
성격: 현실주의자입니다.
- 강원도 횡성 지역의 지원자 풀이 제한적임을 감안하세요
- JD의 모호한 표현이나 차별적 표현을 찾아내세요
- 채용 과정에서의 법적 문제를 체크하세요
- 핵심 포인트를 번호 목록으로 제시하세요"""},
    {"name": "계약봇", "emoji": "📝", "system": """당신은 웰파인 인사총무팀의 계약 전문 AI입니다.
성격: 의심 많은 변호사 스타일입니다.
- 계약서 조항을 꼼꼼하게 분석하세요
- 불리한 조항이나 모호한 표현을 찾아내세요
- 해지/갱신 조항의 리스크를 집중 체크하세요
- 핵심 포인트를 번호 목록으로 제시하세요"""},
    {"name": "총무봇", "emoji": "🏢", "system": """당신은 웰파인 인사총무팀의 총무 전문 AI입니다.
성격: 꼼꼼한 살림꾼입니다.
- 비용 처리, 시설, 물품 관련 규정 준수 여부를 체크하세요
- 세무적으로 문제없는지 검토하세요
- 내부 결재/승인 프로세스를 확인하세요
- 핵심 포인트를 번호 목록으로 제시하세요"""},
    {"name": "급여봇", "emoji": "💰", "system": """당신은 웰파인 인사총무팀의 급여/4대보험 전문 AI입니다.
성격: 숫자에 목숨 거는 스타일입니다.
- 급여 계산과 공제 항목의 정확성을 체크하세요
- 4대보험 요율과 신고 기한을 확인하세요
- E-9 비자 외국인 근로자의 특수한 처리를 체크하세요
- 핵심 포인트를 번호 목록으로 제시하세요"""},
    {"name": "교육봇", "emoji": "📚", "system": """당신은 웰파인 인사총무팀의 교육/OJT 전문 AI입니다.
성격: 실용주의 교육자입니다.
- 교육 내용이 실제 업무와 연결되는지 체크하세요
- OJT/수습평가 설계의 공정성을 확인하세요
- 외국인 근로자 교육 시 언어/문화 차이를 고려하세요
- 핵심 포인트를 번호 목록으로 제시하세요"""},
]

FACTCHECK_SYSTEM = """당신은 웰파인 인사총무팀의 팩트체크 AI입니다.
성격: 감정 없는 검사 스타일입니다.
- 근거 없는 주장, 틀린 정보를 모두 지적하세요
- 맞으면 맞다, 틀리면 틀리다고 냉정하게 판단하세요
- 각 봇 의견별로 검증 결과를 정리해 주세요"""

FIELD_SYSTEM = """당신은 웰파인 인사총무팀의 실무 전문 AI입니다.
성격: 현장 경험 많은 선배 스타일입니다.
- "이론은 맞는데 실제로 가능해?" 라는 관점으로 접근하세요
- 직원 입장에서 이 결정을 받아들일 수 있는지 시뮬레이션하세요
- 강원도 횡성 제조업 현장 특성을 감안하세요
- 현실적으로 실행 가능한 방향을 제시하세요"""

FINAL_SYSTEM = """당신은 웰파인 인사총무팀 AI 회의의 최종 정리 AI입니다.
성격: 냉철한 회의 진행자입니다.
- 모든 봇들의 의견을 종합해 결론을 도출하세요
- 의견이 충돌한 부분은 양쪽 모두 명시하세요
- 구체적인 액션 아이템을 우선순위 순서로 제시하세요
- 전문가 확인이 반드시 필요한 사항을 명시하세요

다음 형식으로 작성하세요:
## 핵심 결론
## 주요 리스크
## 액션 아이템 (우선순위 순)
## 전문가 확인 필요 사항"""


def call_bot(provider_key, api_key, model, system, content, max_tokens=700):
    combined = system + "\n\n" + content
    if provider_key == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": content}]
        )
        return resp.content[0].text
    elif provider_key == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model, max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": content}]
        )
        return resp.choices[0].message.content
    elif provider_key == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model)
        resp = m.generate_content(combined)
        return resp.text
    return "지원하지 않는 제공자입니다."


def extract_text(uploaded_file):
    if not uploaded_file:
        return ""
    ext = uploaded_file.name.split(".")[-1].lower()
    try:
        if ext == "txt":
            return uploaded_file.read().decode("utf-8", errors="ignore")
        elif ext == "pdf":
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        elif ext in ("docx", "doc"):
            from docx import Document
            doc = Document(io.BytesIO(uploaded_file.read()))
            return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[파일 읽기 오류: {e}]"
    return ""


def build_content(doc_text, question, case_notes):
    parts = []
    if case_notes.strip():
        parts.append(f"[웰파인 누적 케이스]\n{case_notes.strip()}")
    if doc_text.strip():
        parts.append(f"[문서 내용]\n{doc_text[:3000]}")
    if question.strip():
        parts.append(f"[질문/검토 요청]\n{question.strip()}")
    return "\n\n".join(parts)


# ── 사이드바 ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 설정")
    selected_provider_label = st.selectbox("AI 제공자", list(PROVIDERS.keys()), label_visibility="collapsed")
    provider = PROVIDERS[selected_provider_label]
    provider_key = provider["key"]

    api_key_input = st.text_input("API 키", type="password",
        placeholder={"anthropic":"sk-ant-...","openai":"sk-...","gemini":"AIza..."}.get(provider_key,""),
        label_visibility="collapsed")
    secret_map = {"anthropic":"ANTHROPIC_API_KEY","openai":"OPENAI_API_KEY","gemini":"GEMINI_API_KEY"}
    secret_val = st.secrets.get(secret_map.get(provider_key,""), "") if hasattr(st, "secrets") else ""
    api_key = api_key_input or secret_val

    selected_model_label = st.selectbox("모델", list(provider["models"].keys()), label_visibility="collapsed")
    selected_model = provider["models"][selected_model_label]

    st.divider()
    st.markdown("### 봇 프롬프트 편집")
    if "bot_prompts" not in st.session_state:
        st.session_state.bot_prompts = {b["name"]: b["system"] for b in BOTS}
        st.session_state.bot_prompts["팩트체크봇"] = FACTCHECK_SYSTEM
        st.session_state.bot_prompts["실무봇"] = FIELD_SYSTEM
        st.session_state.bot_prompts["최종정리봇"] = FINAL_SYSTEM
    bot_to_edit = st.selectbox("봇 선택", [b["name"] for b in BOTS]+["팩트체크봇","실무봇","최종정리봇"], label_visibility="collapsed")
    edited = st.text_area("프롬프트", value=st.session_state.bot_prompts[bot_to_edit], height=180, label_visibility="collapsed")
    if st.button("저장", use_container_width=True):
        st.session_state.bot_prompts[bot_to_edit] = edited
        st.success("저장됨!")

    st.divider()
    st.markdown("### 누적 케이스")
    if "case_notes" not in st.session_state:
        st.session_state.case_notes = ""
    case_input = st.text_area("케이스", value=st.session_state.case_notes, height=130,
        placeholder="예: 수습 불합격 시 2회 이상 면담 기록 필요\nE-9 근로자 계약서 이중언어 사용...",
        label_visibility="collapsed")
    if st.button("케이스 저장", use_container_width=True):
        st.session_state.case_notes = case_input
        st.success("저장됨!")


# ── 메인 화면 ────────────────────────────────────────────
st.markdown("## 웰파인 인사총무 AI 회의실")
st.caption(f"현재: {selected_provider_label} · {selected_model_label}")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("##### 문서 업로드")
    uploaded_file = st.file_uploader("파일", type=["pdf","docx","txt"], label_visibility="collapsed")
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name}")
with col2:
    st.markdown("##### 질문 / 검토 요청")
    user_question = st.text_area("질문", height=120, label_visibility="collapsed",
        placeholder="예: 이 근로계약서 수습기간 조항이 법적으로 문제없는지 봐줘")

start = st.button("🚀 회의 시작", type="primary", use_container_width=True)

if start:
    if not api_key:
        st.error("왼쪽에서 API 키를 입력해주세요.")
        st.stop()
    if not uploaded_file and not user_question.strip():
        st.error("문서를 업로드하거나 질문을 입력해주세요.")
        st.stop()

    doc_text = ""
    if uploaded_file:
        with st.spinner("문서 읽는 중..."):
            doc_text = extract_text(uploaded_file)

    full_content = build_content(doc_text, user_question, st.session_state.get("case_notes",""))

    st.divider()
    st.markdown("### 1️⃣ 전문 봇 의견")
    bot_results = {}
    for bot in BOTS:
        system = st.session_state.bot_prompts.get(bot["name"], bot["system"])
        with st.spinner(f'{bot["emoji"]} {bot["name"]} 검토 중...'):
            try:
                result = call_bot(provider_key, api_key, selected_model, system, full_content, 700)
            except Exception as e:
                result = f"오류: {e}"
            bot_results[bot["name"]] = result
        with st.expander(f'{bot["emoji"]} **{bot["name"]}**', expanded=False):
            st.markdown(result)

    st.markdown("### 2️⃣ 팩트체크")
    fc_input = full_content + "\n\n[전문 봇들의 의견]\n" + "\n".join(f"\n{n}:\n{o}" for n,o in bot_results.items())
    with st.spinner("🔍 팩트체크봇 검증 중..."):
        try:
            fc_result = call_bot(provider_key, api_key, selected_model,
                st.session_state.bot_prompts.get("팩트체크봇", FACTCHECK_SYSTEM), fc_input, 900)
        except Exception as e:
            fc_result = f"오류: {e}"
    with st.expander("🔍 **팩트체크봇**", expanded=True):
        st.markdown(fc_result)

    st.markdown("### 3️⃣ 실무 검토")
    field_input = fc_input + f"\n\n팩트체크봇:\n{fc_result}"
    with st.spinner("🔧 실무봇 검토 중..."):
        try:
            field_result = call_bot(provider_key, api_key, selected_model,
                st.session_state.bot_prompts.get("실무봇", FIELD_SYSTEM), field_input, 700)
        except Exception as e:
            field_result = f"오류: {e}"
    with st.expander("🔧 **실무봇**", expanded=True):
        st.markdown(field_result)

    st.divider()
    st.markdown("### 🎯 최종 결론")
    final_input = field_input + f"\n\n실무봇:\n{field_result}"
    with st.spinner("🎯 최종정리봇 정리 중..."):
        try:
            final_result = call_bot(provider_key, api_key, selected_model,
                st.session_state.bot_prompts.get("최종정리봇", FINAL_SYSTEM), final_input, 1500)
        except Exception as e:
            final_result = f"오류: {e}"
    st.markdown(final_result)
    st.success("✅ 회의 완료!")
