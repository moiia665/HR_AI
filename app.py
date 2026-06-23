import streamlit as st
import streamlit.components.v1 as components
import io, os, json
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="웰파인 AI 회의실", page_icon="🤖", layout="wide",
                   initial_sidebar_state="expanded")

CFG_FILE = "wellfine_config.json"
def load_cfg():
    try:
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}
def save_cfg(data):
    try:
        with open(CFG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#f5f1eb;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#ece8e0;}
#MainMenu,footer{visibility:hidden;}
/* 파일 업로더를 테이블 위 문서 트레이처럼 스타일링 */
[data-testid="stFileUploaderDropzone"]{
  background:#c8b89a !important;
  border:2px dashed #8B5E3C !important;
  border-radius:8px !important;
}
[data-testid="stFileUploaderDropzoneInput"]+div{color:#5a3a1a !important;}
.doc-tray-label{
  background:#ddd0bc;border-radius:0 0 12px 12px;
  padding:4px 16px 8px;text-align:center;
  font-size:11px;color:#6B4A1A;font-weight:600;
  border:1px solid #c8b490;border-top:none;
  margin-top:-6px;
}
</style>
""", unsafe_allow_html=True)

PROVIDERS = {
    "\U0001f7e0 Claude (Anthropic)": {"key": "anthropic", "models": {
        "Claude Sonnet (기본)": "claude-sonnet-4-6",
        "Claude Opus (고성능)": "claude-opus-4-8",
        "Claude Haiku (빠름)": "claude-haiku-4-5-20251001",
    }},
    "\U0001f7e2 ChatGPT (OpenAI)": {"key": "openai", "models": {
        "GPT-4o (권장)": "gpt-4o",
        "GPT-4o mini (빠름)": "gpt-4o-mini",
    }},
    "\U0001f535 Gemini (Google)": {"key": "gemini", "models": {
        "Gemini 2.5 Flash (무료/빠름)": "gemini-2.5-flash",
        "Gemini 2.5 Pro (고성능)": "gemini-2.5-pro",
        "Gemini 1.5 Flash": "gemini-1.5-flash",
    }},
}

BOTS = [
    {"name": "노무봇",  "system": "웰파인(강원도 횡성 건강기능식품 OEM/ODM) 인사총무팀 노무 전문 AI.\n성격: 보수적이고 까다로운 노무사 스타일.\n- 법 조문 근거 없이 '괜찮다'고 하지 마세요\n- 애매하면 반드시 '전문가 확인 필요' 명시\n- 근로기준법, 노동관련 법령 관점으로 검토\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "HRM봇",  "system": "웰파인 인사총무팀 HRM 전문 AI.\n성격: 원칙주의자.\n- 사내 규정, 취업규칙과의 일치 여부 체크\n- 규정과 실제 운영 간의 괴리를 찾아내세요\n- 형평성 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "채용봇",  "system": "웰파인 인사총무팀 채용 전문 AI.\n성격: 현실주의자.\n- 강원도 횡성 지역의 지원자 풀이 제한적임 감안\n- JD의 모호한/차별적 표현 찾아내세요\n- 채용 과정의 법적 문제 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "계약봇",  "system": "웰파인 인사총무팀 계약 전문 AI.\n성격: 의심 많은 변호사 스타일.\n- 계약서 조항 꼼꼼하게 분석\n- 불리한 조항/모호한 표현 찾아내세요\n- 해지/갱신 조항 리스크 집중 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "총무봇",  "system": "웰파인 인사총무팀 총무 전문 AI.\n성격: 꼼꼼한 살림꾼.\n- 비용 처리, 시설, 물품 관련 규정 준수 체크\n- 세무적으로 문제없는지 검토\n- 내부 결재/승인 프로세스 확인\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "급여봇",  "system": "웰파인 인사총무팀 급여/4대보험 전문 AI.\n성격: 숫자에 목숨 거는 스타일.\n- 급여 계산과 공제 항목 정확성 체크\n- 4대보험 요율과 신고 기한 확인\n- E-9 비자 외국인 근로자의 특수한 처리 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "교육봇",  "system": "웰파인 인사총무팀 교육/OJT 전문 AI.\n성격: 실용주의 교육자.\n- 교육 내용이 실제 업무와 연결되는지 체크\n- OJT/수습평가 설계의 공정성 확인\n- 외국인 근로자 교육 시 언어/문화 차이 고려\n- 핵심 포인트 번호 목록으로 제시"},
]

FACTCHECK_SYS = """웰파인 인사총무팀 팩트체크 AI. 감정 없는 검사 스타일.

반드시 아래 실제 법령/규정 기준으로 검증하세요:
- 근로기준법 (근로시간, 수습, 해고, 휴가, 임금 관련)
- 최저임금법 (매년 최저임금 기준 적용)
- 근로자퇴직급여보장법 (퇴직금/퇴직연금)
- 고용보험법 / 산재보험법 / 국민연금법 / 국민건강보험법 (4대보험 요율·신고기한)
- 남녀고용평등과 일·가정 양립 지원에 관한 법률 (육아휴직, 출산휴가)
- 외국인근로자의 고용 등에 관한 법률 (E-9 비자 규정, 고용허가제)
- 채용절차의 공정화에 관한 법률
- 개인정보 보호법 (채용·인사 서류 관련)
- 업로드된 문서(취업규칙, 사내규정, 계약서 등)가 있으면 해당 내용도 기준으로 포함

검증 방식:
- 각 봇 의견에 대해 법령 조문 또는 기준과 대조하여 [맞음/틀림/확인필요] 판정
- 틀린 경우 어떤 법령 몇 조에 위배되는지 명시
- 확인필요인 경우 어떤 전문가 확인이 필요한지 명시"""
FIELD_SYS   = "웰파인 인사총무팀 실무 전문 AI.\n성격: 현장 경험 많은 선배.\n- '이론은 맞는데 실제로 가능해?' 관점으로 접근\n- 직원 입장에서 이 결정을 받아들일 수 있는지 시뮬레이션\n- 강원도 횡성 제조업 현장 특성 감안\n- 현실적으로 실행 가능한 방향 제시"
FINAL_SYS   = "웰파인 인사총무팀 AI 회의 최종 정리 AI. 냉철한 회의 진행자.\n- 모든 봇 의견 종합해 결론 도출\n- 의견 충돌한 부분은 양쪽 모두 명시\n- 구체적 액션 아이템을 우선순위 순서로 제시\n- 전문가 확인 반드시 필요한 사항 명시\n\n다음 형식으로 작성:\n## 핵심 결론\n## 주요 리스크\n## 액션 아이템 (우선순위 순)\n## 전문가 확인 필요 사항"

BOT_COLORS = {
    "노무봇":     ["#3B6FD4","#2756B8"],
    "HRM봇":      ["#2E9E55","#1E7D3E"],
    "채용봇":     ["#E07B00","#B86000"],
    "계약봇":     ["#7048E8","#5030C8"],
    "총무봇":     ["#546E8A","#3D5570"],
    "급여봇":     ["#C79800","#A07800"],
    "교육봇":     ["#0A9E7A","#087D60"],
    "팩트체크봇": ["#C92A2A","#A01E1E"],
    "실무봇":     ["#7B5E3C","#5A4228"],
    "최종정리봇": ["#1565C0","#0D47A0"],
}

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

def render_html(statuses, results):
    data_json = json.dumps({"statuses": statuses, "results": results,
                            "colors": BOT_COLORS}, ensure_ascii=False)
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#f5f1eb;font-family:-apple-system,sans-serif;padding:8px;}
.room{background:linear-gradient(180deg,#e8e2d6,#dfd9cd);border-radius:16px;
  padding:18px 10px 12px;border:1px solid #cec8be;}
.row{display:flex;justify-content:center;align-items:flex-end;gap:6px;}
.top-row{align-items:flex-end;margin-bottom:0;}
.bot-row{align-items:flex-start;margin-top:0;}
.mid{display:flex;justify-content:center;align-items:center;gap:8px;margin:2px 0;}
.table{flex:0 0 auto;width:280px;height:78px;
  background:linear-gradient(160deg,#6B4423,#8B5E3C 40%,#9B6B45 60%,#6B4423);
  border-radius:10px;border:3px solid #4A2E18;
  box-shadow:0 6px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.12);
  display:flex;align-items:center;justify-content:center;}
.table-lbl{color:rgba(255,255,255,.5);font-size:10px;letter-spacing:2px;text-transform:uppercase;}
.bot{display:flex;flex-direction:column;align-items:center;width:62px;position:relative;
  cursor:pointer;transition:transform .15s;}
.bot:hover{transform:scale(1.05);}
.bot-name{font-size:9.5px;font-weight:700;color:#3a3530;margin-top:3px;text-align:center;}
.dot{width:7px;height:7px;border-radius:50%;margin-top:2px;background:#bbb;}
.idle .dot{background:#bbb;}
.active .dot{background:#f5c842;box-shadow:0 0 6px #f5c842;animation:blink .9s infinite;}
.done .dot{background:#52c463;box-shadow:0 0 4px #52c463;}
.error .dot{background:#e05555;}
.bubble{position:absolute;bottom:calc(100% + 4px);left:50%;transform:translateX(-50%);
  background:#fff9e6;border:1.5px solid #f5c842;border-radius:8px;padding:3px 7px;
  font-size:9px;font-weight:800;color:#6B4A00;white-space:nowrap;
  box-shadow:0 3px 8px rgba(0,0,0,.15);animation:float 1.5s ease-in-out infinite;z-index:5;}
.bubble::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);
  border:5px solid transparent;border-top-color:#f5c842;}
.chair-area{display:flex;justify-content:center;margin-top:8px;
  padding-top:8px;border-top:1px dashed #c0b8ae;}
.chair-wrap{background:rgba(255,255,255,.6);border-radius:10px;padding:5px 14px;
  display:inline-flex;align-items:center;gap:8px;border:1px solid #d8d0c8;
  cursor:pointer;transition:transform .15s;}
.chair-wrap:hover{transform:scale(1.03);}
.chair-info{display:flex;flex-direction:column;}
.chair-title{font-size:11px;font-weight:700;color:#3a3530;}
.chair-sub{font-size:9px;color:#aaa;font-style:italic;}
.overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;
  background:rgba(0,0,0,.55);z-index:100;align-items:center;justify-content:center;}
.overlay.show{display:flex;}
.modal{background:#fff;border-radius:14px;padding:20px 22px;width:90%;max-width:520px;
  max-height:80vh;overflow-y:auto;position:relative;
  box-shadow:0 12px 40px rgba(0,0,0,.3);}
.modal h2{font-size:14px;font-weight:700;margin-bottom:12px;color:#333;
  padding-bottom:8px;border-bottom:1px solid #eee;}
.modal-body{font-size:13px;line-height:1.7;color:#444;}
.modal-body h2,.modal-body h3{font-size:13px;font-weight:700;margin:10px 0 4px;}
.modal-body p{margin:4px 0;}
.modal-body ul,.modal-body ol{padding-left:18px;margin:4px 0;}
.modal-body li{margin:2px 0;}
.close-btn{position:absolute;top:10px;right:14px;cursor:pointer;
  font-size:18px;color:#999;background:none;border:none;line-height:1;}
.no-result{font-size:12px;color:#aaa;font-style:italic;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.3;}}
@keyframes float{0%,100%{transform:translateX(-50%) translateY(0);}
  50%{transform:translateX(-50%) translateY(-3px);}}
</style>
</head><body>
<div class="room" id="room"></div>
<div class="overlay" id="overlay" onclick="maybeClose(event)">
  <div class="modal" id="modal">
    <button class="close-btn" onclick="closeModal()">&#x2715;</button>
    <h2 id="modal-title"></h2>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>
<script>
const DATA=""" + data_json + """;
const COLORS=DATA.colors;

function svgRobot(name){
  const c=(COLORS[name]||["#666","#444"]);
  const C=c[0],D=c[1];
  return `<svg width="46" height="54" viewBox="0 0 46 54" xmlns="http://www.w3.org/2000/svg">
    <line x1="23" y1="0" x2="23" y2="8" stroke="${C}" stroke-width="3.5" stroke-linecap="round"/>
    <circle cx="23" cy="0" r="4" fill="${C}"/>
    <rect x="4" y="8" width="38" height="27" rx="7" fill="${C}"/>
    <circle cx="2.5" cy="21" r="3.5" fill="${D}"/>
    <circle cx="43.5" cy="21" r="3.5" fill="${D}"/>
    <rect x="9" y="14" width="11" height="9" rx="3" fill="white"/>
    <rect x="26" y="14" width="11" height="9" rx="3" fill="white"/>
    <circle cx="14.5" cy="18.5" r="3.2" fill="#1a1a2e"/>
    <circle cx="31.5" cy="18.5" r="3.2" fill="#1a1a2e"/>
    <circle cx="16" cy="17.2" r="1.2" fill="white"/>
    <circle cx="33" cy="17.2" r="1.2" fill="white"/>
    <rect x="14" y="28" width="18" height="3.5" rx="1.7" fill="rgba(255,255,255,0.4)"/>
    <rect x="17" y="35" width="12" height="5" fill="${C}"/>
    <rect x="2" y="40" width="42" height="14" rx="7 7 0 0" fill="${D}"/>
    <rect x="14" y="42" width="18" height="6" rx="3" fill="${C}" opacity="0.45"/>
  </svg>`;
}

function botCard(name,status){
  const bubble = status==='active' ? '<div class="bubble">💬 발언 중</div>' : '';
  const canClick = !!(DATA.results && DATA.results[name]);
  const title = canClick ? `title="클릭해서 의견 보기"` : (status==='active'?`title="발언 중..."`:`title="${name}"`);
  return `<div class="bot ${status}" onclick="showBot('${name}')" ${title}>
    ${bubble}
    <div>${svgRobot(name)}</div>
    <div class="bot-name">${name}</div>
    <div class="dot"></div>
  </div>`;
}

function render(){
  const st=DATA.statuses;
  const g=n=>st[n]||'idle';
  const top=['노무봇','HRM봇','채용봇','계약봇'].map(n=>botCard(n,g(n))).join('');
  const btm=['총무봇','급여봇','교육봇'].map(n=>botCard(n,g(n))).join('');
  const cs=g('최종정리봇');
  const cColor={'idle':'#bbb','active':'#f5c842','done':'#52c463','error':'#e05555'}[cs]||'#bbb';
  const cBubble=cs==='active'?'<div class="bubble">💬 발언 중</div>':'';
  document.getElementById('room').innerHTML=`
    <div class="row top-row">${top}</div>
    <div class="mid">
      ${botCard('팩트체크봇',g('팩트체크봇'))}
      <div class="table"><div class="table-lbl">WELLFINE HR AI</div></div>
      ${botCard('실무봇',g('실무봇'))}
    </div>
    <div class="row bot-row">${btm}</div>
    <div class="chair-area">
      <div class="chair-wrap" onclick="showBot('최종정리봇')" title="최종정리봇 의견 보기">
        ${cBubble}
        ${svgRobot('최종정리봇')}
        <div class="chair-info">
          <div class="chair-title">최종정리봇</div>
          <div class="chair-sub">회의 진행자</div>
        </div>
        <div class="dot" style="background:${cColor};${cs!=='idle'?'box-shadow:0 0 6px '+cColor:''};"></div>
      </div>
    </div>`;
}

function showBot(name){
  const result=DATA.results&&DATA.results[name];
  document.getElementById('modal-title').textContent=name+' 의견';
  if(result){
    document.getElementById('modal-body').innerHTML=marked.parse(result);
  } else {
    document.getElementById('modal-body').innerHTML='<div class="no-result">아직 의견이 없습니다.</div>';
  }
  document.getElementById('overlay').classList.add('show');
}

function closeModal(){
  document.getElementById('overlay').classList.remove('show');
}
function maybeClose(e){
  if(e.target===document.getElementById('overlay')) closeModal();
}

render();
</script>
</body></html>"""

# ── 세션 초기화 ────────────────────────────────────────────
_cfg = load_cfg()
for k, v in [
    ("bot_statuses", {}), ("bot_results", {}), ("case_notes", ""),
    ("stop_requested", False), ("meeting_running", False),
    ("meeting_history", []),
    ("saved_provider", _cfg.get("provider", list(PROVIDERS.keys())[0])),
    ("saved_model",    _cfg.get("model", "")),
    ("saved_api_key",  _cfg.get("api_key", "")),
]:
    if k not in st.session_state:
        st.session_state[k] = v
if "bot_prompts" not in st.session_state:
    bp = {b["name"]: b["system"] for b in BOTS}
    bp.update({"팩트체크봇": FACTCHECK_SYS, "실무봇": FIELD_SYS, "최종정리봇": FINAL_SYS})
    st.session_state.bot_prompts = bp

# ── 사이드바 ───────────────────────────────────────────────
with st.sidebar:
    with st.expander("⚙️ 설정", expanded=False):
        p_label = st.selectbox("AI 제공자", list(PROVIDERS.keys()),
            index=list(PROVIDERS.keys()).index(st.session_state.saved_provider)
                  if st.session_state.saved_provider in PROVIDERS else 0,
            label_visibility="collapsed", key="sel_provider")
        prov_tmp = PROVIDERS[p_label]
        pkey_tmp = prov_tmp["key"]
        model_list = list(prov_tmp["models"].keys())
        saved_m = st.session_state.saved_model
        m_idx = model_list.index(saved_m) if saved_m in model_list else 0
        m_label = st.selectbox("모델", model_list, index=m_idx,
                               label_visibility="collapsed", key="sel_model")
        ph = {"anthropic":"sk-ant-...","openai":"sk-...","gemini":"AIza..."}.get(pkey_tmp,"")
        api_in = st.text_input("API 키", type="password",
            value=st.session_state.saved_api_key, placeholder=ph,
            label_visibility="collapsed", key="inp_api")
        if st.button("\U0001f4be 저장 (팀 공유)", use_container_width=True):
            st.session_state.saved_provider = p_label
            st.session_state.saved_model    = m_label
            st.session_state.saved_api_key  = api_in
            save_cfg({"provider": p_label, "model": m_label, "api_key": api_in})
            st.success("저장됨!")

    p_label = st.session_state.saved_provider
    if p_label not in PROVIDERS: p_label = list(PROVIDERS.keys())[0]
    prov    = PROVIDERS[p_label]
    pkey    = prov["key"]
    m_label = st.session_state.saved_model
    if m_label not in prov["models"]: m_label = list(prov["models"].keys())[0]
    model   = prov["models"][m_label]
    api_key = st.session_state.saved_api_key
    if not api_key:
        try:
            smap = {"anthropic":"ANTHROPIC_API_KEY","openai":"OPENAI_API_KEY","gemini":"GEMINI_API_KEY"}
            api_key = st.secrets.get(smap[pkey], "")
        except Exception:
            api_key = ""
    st.caption(f"**{p_label}** · {m_label}")
    st.divider()

    st.markdown("### \U0001f916 봇 프롬프트 편집")
    all_names = [b["name"] for b in BOTS] + ["팩트체크봇", "실무봇", "최종정리봇"]
    bot_sel = st.selectbox("봇", all_names, label_visibility="collapsed")
    edited  = st.text_area("프롬프트", value=st.session_state.bot_prompts.get(bot_sel, ""),
                           height=160, label_visibility="collapsed")
    if st.button("\U0001f4be 저장", use_container_width=True):
        st.session_state.bot_prompts[bot_sel] = edited
        st.success("저장됨!")
    st.divider()

    st.markdown("### \U0001f4c2 누적 케이스")
    new_notes = st.text_area("케이스", value=st.session_state.case_notes, height=80,
        placeholder="예: 수습 불합격 시 면담 2회 이상 기록 필요\nE-9 계약서 이중언어 작성...",
        label_visibility="collapsed")
    if st.button("\U0001f4be 케이스 저장", use_container_width=True):
        st.session_state.case_notes = new_notes
        st.success("저장됨!")
    st.divider()

    # ── 회의 히스토리 ──────────────────────────────────────
    st.markdown("### \U0001f4dc 회의 히스토리")
    if st.session_state.get("meeting_history"):
        for i, h in enumerate(reversed(st.session_state.meeting_history)):
            idx = len(st.session_state.meeting_history) - i
            label = f"#{idx} {h['title'][:22]}..."  if len(h['title']) > 22 else f"#{idx} {h['title']}"
            with st.expander(label, expanded=False):
                st.caption(h["time"])
                if h.get("doc"):
                    st.markdown(f"📄 `{h['doc']}`")
                st.markdown(f"**질문:** {h['question']}")
                if h.get("ops1"):
                    st.markdown("---")
                    st.markdown("**📋 1차 전문 봇 의견**")
                    for bname, op in h["ops1"].items():
                        with st.expander(f"🤖 {bname}", expanded=False):
                            st.markdown(op)
                if h.get("fc1"):
                    with st.expander("🔍 팩트체크 1차", expanded=False):
                        st.markdown(h["fc1"])
                if h.get("ops2"):
                    st.markdown("**📋 2차 재발언**")
                    for bname, op in h["ops2"].items():
                        with st.expander(f"🤖 {bname} (2차)", expanded=False):
                            st.markdown(op)
                if h.get("fc2"):
                    with st.expander("🔍 팩트체크 최종", expanded=False):
                        st.markdown(h["fc2"])
                if h.get("final"):
                    st.markdown("---")
                    st.markdown("**🎯 최종 결론**")
                    st.markdown(h["final"])
    else:
        st.caption("회의를 진행하면 여기에 기록이 쌓입니다.")

# ── 메인 ───────────────────────────────────────────────────
st.markdown("## \U0001f3e2 웰파인 인사총무 AI 회의실")
st.divider()

table_slot = st.empty()
with table_slot:
    components.html(render_html(st.session_state.bot_statuses,
                                st.session_state.bot_results), height=480)

# 파일 업로드 — 테이블 바로 아래 (문서 트레이)
st.markdown('<div class="doc-tray-label">📄 검토할 문서를 테이블 위에 올려두세요</div>',
            unsafe_allow_html=True)
ufile = st.file_uploader("문서", type=["pdf","docx","txt"], label_visibility="collapsed")
if ufile:
    st.success(f"✅ {ufile.name} 올라감")

st.divider()

st.markdown("##### 💬 질문 / 검토 요청")
question = st.text_area("질문", height=80, label_visibility="collapsed",
    placeholder="예: 이 근로계약서 수습기간 조항이 법적으로 문제없나요?\n(문서 없이 질문만 해도 됩니다)")

btn_c1, btn_c2 = st.columns([3, 1])
with btn_c1:
    go = st.button("\U0001f680 회의 시작", type="primary", use_container_width=True,
                   disabled=st.session_state.meeting_running)
with btn_c2:
    if st.button("⏹ 중단", use_container_width=True,
                 disabled=not st.session_state.meeting_running):
        st.session_state.stop_requested = True
        st.session_state.meeting_running = False
        st.rerun()

def upd(statuses_update, results_update=None):
    st.session_state.bot_statuses.update(statuses_update)
    if results_update:
        st.session_state.bot_results.update(results_update)
    with table_slot:
        components.html(render_html(st.session_state.bot_statuses,
                                    st.session_state.bot_results), height=480)

def check_stop():
    if st.session_state.stop_requested:
        st.warning("⏹ 회의가 중단되었습니다. 완료된 결과는 테이블 봇을 클릭해서 확인하세요.")
        st.stop()

# ── 회의 진행 ──────────────────────────────────────────────
if go:
    if not api_key:
        st.error("⚙️ 설정에서 API 키를 입력하고 저장해주세요.")
        st.stop()
    if not ufile and not question.strip():
        st.error("문서를 업로드하거나 질문을 입력해주세요.")
        st.stop()

    st.session_state.bot_statuses = {}
    st.session_state.bot_results  = {}
    st.session_state.stop_requested = False
    st.session_state.meeting_running = True

    doc_text = extract_text(ufile) if ufile else ""
    content  = build_content(doc_text, question, st.session_state.case_notes)
    bp       = st.session_state.bot_prompts

    st.divider()
    st.markdown("### \U0001f4cb 회의 진행")

    # ── 1라운드: 병렬 동시 발언 ───────────────────────────
    st.markdown("**1라운드 — 전문 봇 7명 동시 발언**")
    upd({b["name"]: "active" for b in BOTS})

    ops1 = {}
    with st.spinner("\U0001f916 7명 동시 분석 중..."):
        def _call1(b):
            return b["name"], call_bot(pkey, api_key, model,
                bp.get(b["name"], b["system"]), content, 600)
        with ThreadPoolExecutor(max_workers=7) as ex:
            for name, res in ex.map(_call1, BOTS):
                ops1[name] = res

    upd({b["name"]: "done" for b in BOTS}, ops1)
    for b in BOTS:
        with st.expander(f"\U0001f916 {b['name']} 1차 의견", expanded=False):
            st.markdown(ops1[b["name"]])

    check_stop()

    # ── 팩트체크 1차 ──────────────────────────────────────
    st.markdown("**팩트체크 1차**")
    fc1_in = content + "\n\n[1차 의견]\n" + "\n\n".join(f"{n}:\n{o}" for n, o in ops1.items())
    upd({"팩트체크봇": "active"})
    with st.status("\U0001f916 팩트체크봇 1차 검증 중...", expanded=False) as stat:
        fc1 = call_bot(pkey, api_key, model, bp.get("팩트체크봇", FACTCHECK_SYS), fc1_in, 900)
        st.markdown(fc1)
        stat.update(label="\U0001f916 팩트체크봇 1차 ✅", state="complete", expanded=False)
    upd({"팩트체크봇": "done"}, {"팩트체크봇_1차": fc1})

    check_stop()

    # ── 2라운드: 병렬 재발언 ──────────────────────────────
    st.markdown("**2라운드 — 팩트체크 반영 재발언 (병렬)**")
    upd({b["name"]: "active" for b in BOTS})

    ops2 = {}
    with st.spinner("\U0001f916 7명 재검토 중..."):
        def _call2(b):
            r2_in = (content
                + f"\n\n[팩트체크 결과]\n{fc1}"
                + "\n\n[내 1차 의견]\n" + ops1.get(b["name"], "")
                + "\n\n팩트체크 반영해 의견을 보완하거나 수정해주세요. 맞다면 근거를 보강해주세요.")
            return b["name"], call_bot(pkey, api_key, model,
                bp.get(b["name"], b["system"]), r2_in, 600)
        with ThreadPoolExecutor(max_workers=7) as ex:
            for name, res in ex.map(_call2, BOTS):
                ops2[name] = res

    upd({b["name"]: "done" for b in BOTS}, ops2)
    for b in BOTS:
        with st.expander(f"\U0001f916 {b['name']} 2차 의견", expanded=False):
            st.markdown(ops2[b["name"]])

    check_stop()

    # ── 팩트체크 2차 ──────────────────────────────────────
    st.markdown("**팩트체크 2차 (최종 검증)**")
    fc2_in = (content
        + "\n\n[2차 의견]\n" + "\n\n".join(f"{n}:\n{o}" for n, o in ops2.items())
        + f"\n\n[1차 팩트체크]\n{fc1}")
    upd({"팩트체크봇": "active"})
    with st.status("\U0001f916 팩트체크봇 최종 검증 중...", expanded=False) as stat:
        fc2 = call_bot(pkey, api_key, model, bp.get("팩트체크봇", FACTCHECK_SYS), fc2_in, 900)
        st.markdown(fc2)
        stat.update(label="\U0001f916 팩트체크봇 최종 ✅", state="complete", expanded=False)
    upd({"팩트체크봇": "done"}, {"팩트체크봇_2차": fc2})

    check_stop()

    # ── 실무봇 3줄 ────────────────────────────────────────
    upd({"실무봇": "active"})
    field_in = (content
        + "\n\n[전문 봇 최종 의견]\n" + "\n".join(f"{n}: {o[:200]}" for n, o in ops2.items())
        + f"\n\n[팩트체크 최종]\n{fc2}"
        + "\n\n현장 실무 관점에서 딱 3줄 이내로 핵심 코멘트만 작성해주세요.")
    with st.spinner("\U0001f916 실무봇 코멘트 작성 중..."):
        field_brief = call_bot(pkey, api_key, model, bp.get("실무봇", FIELD_SYS), field_in, 200)
    upd({"실무봇": "done"}, {"실무봇": field_brief})

    # ── 최종 결론 ─────────────────────────────────────────
    st.divider()
    st.markdown("### \U0001f3af 최종 결론")
    final_in = (content
        + "\n\n[전문 봇 2차 최종 의견]\n" + "\n\n".join(f"{n}:\n{o}" for n, o in ops2.items())
        + f"\n\n[팩트체크 최종 결과]\n{fc2}"
        + f"\n\n[실무 현장 코멘트]\n{field_brief}")
    upd({"최종정리봇": "active"})
    with st.spinner("\U0001f916 최종정리봇 정리 중..."):
        final_res = call_bot(pkey, api_key, model, bp.get("최종정리봇", FINAL_SYS), final_in, 1500)
    upd({"최종정리봇": "done"}, {"최종정리봇": final_res})

    st.markdown(final_res)
    st.session_state.meeting_running = False

    # ── 히스토리 저장 ────────────────────────────────────
    from datetime import datetime
    title = (ufile.name if ufile else question.strip()[:30])
    st.session_state.meeting_history.append({
        "time":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title":    title,
        "doc":      ufile.name if ufile else "",
        "question": question.strip()[:100],
        "ops1":     ops1,
        "fc1":      fc1,
        "ops2":     ops2,
        "fc2":      fc2,
        "final":    final_res,
    })

    st.success("✅ 회의 완료! 테이블 봇 클릭 → 각 의견 확인 | 왼쪽 사이드바 → 히스토리")
