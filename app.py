import streamlit as st
import streamlit.components.v1 as components
import io, os, json, re
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="웹라인 AI 회의실", page_icon="🤖", layout="wide",
                   initial_sidebar_state="expanded")

CFG_FILE = "wellfine_config.json"
SHARED_HISTORY_FILE = "shared_history.json"

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

def load_shared_history():
    try:
        if os.path.exists(SHARED_HISTORY_FILE):
            with open(SHARED_HISTORY_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_shared_history(history):
    try:
        with open(SHARED_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False)
    except Exception:
        pass

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#f5f1eb;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#f3efe8; min-width:290px;}
[data-testid="stSidebarContent"]{padding:14px 10px 16px;}
#MainMenu,footer{visibility:hidden;}
[data-testid="stFileUploader"]{
  opacity:0 !important;height:0 !important;overflow:hidden !important;
  margin:0 !important;padding:0 !important;position:absolute !important;
}
.sidebar-brand{display:flex;align-items:center;gap:8px;margin:2px 4px 12px;
  font-size:18px;font-weight:800;color:#211c18;}
.sidebar-brand .mark{width:24px;height:24px;border-radius:8px;background:#26211c;
  color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:14px;}
.sidebar-section{font-size:11px;font-weight:800;color:#877d72;margin:18px 8px 7px;
  text-transform:uppercase;letter-spacing:.04em;}
.history-empty{font-size:12px;line-height:1.55;color:#8a8178;background:#fffaf2;
  border:1px dashed #d8cfc3;border-radius:10px;padding:12px;margin:8px 2px;}
[data-testid="stSidebar"] div[data-testid="stButton"] > button{
  min-height:34px;border-radius:10px;border:1px solid #ded4c7;background:#fbf7ef;
  color:#2a2520;font-weight:650;justify-content:flex-start;text-align:left;
  white-space:normal;}
[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover{
  border-color:#b9aa99;background:#eee6db;color:#111;}
[data-testid="stSidebar"] div[data-testid="stTextInput"] input{
  border-radius:10px;background:#fbf7ef;border-color:#ded4c7;}
</style>
""", unsafe_allow_html=True)

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
    {"name": "노무봇",  "system": "웹라인(강원도 횟성 건강기능식품 OEM/ODM) 인사총무팀 노무 전문 AI.\n성격: 보수적이고 까다로운 노무사 스타일.\n- 법 조문 근거 없이 괴다고 하지 마세요\n- 애매하면 반드시 전문가 확인 필요 명시\n- 에 노동관련 법령 관점으로 검토\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "HRM봇",  "system": "웹라인 인사총무팀 HRM 전문 AI.\n성격: 원칙주의자.\n- 사내 규정, 취업규칙과의 일치 여부 체크\n- 규정과 실제 운영 간의 괴리를 찾아내세요\n- 형평성 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "채용봇",  "system": "웹라인 인사총무팀 채용 전문 AI.\n성격: 현실주의자.\n- 강원도 횟성 지역의 지원자 풀이 제한적임 감안\n- JD의 모호한/차별적 표현 찾아내세요\n- 채용 과정의 법적 문제 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "계약봇",  "system": "웹라인 인사총무팀 계약 전문 AI.\n성격: 의심 많은 변호사 스타일.\n- 계약서 조항 꼼꼼하게 분석\n- 불리한 조항/모호한 표현 찾아내세요\n- 해지/갱신 조항 리스크 집중 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "총무봇",  "system": "웹라인 인사총무팀 총무 전문 AI.\n성격: 꼼꼼한 살림꼼.\n- 비용 처리, 시설, 물품 관련 규정 준수 체크\n- 세무적으로 문제없는지 검토\n- 내부 결재/승인 프로세스 확인\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "급여봇",  "system": "웹라인 인사총무팀 급여/4대보험 전문 AI.\n성격: 숫자에 목숙 거는 스타일.\n- 급여 계산과 공제 항목 정확성 체크\n- 4대보험 요율과 신고 기한 확인\n- E-9 비자 외국인 근로자의 특수한 처리 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "교육봇",  "system": "웹라인 인사총무팀 교육/OJT 전문 AI.\n성격: 실용주의 교육자.\n- 교육 내용이 실제 업무와 연결되는지 체크\n- OJT/수습평가 설계의 공정성 확인\n- 외국인 근로자 교육 시 언어/문화 차이 고려\n- 핵심 포인트 번호 목록으로 제시"},
]

FACTCHECK_SYS = (
    "웹라인 인사총무팀 팩트체크 AI. 감정 없는 검사 스타일.\n\n"
    "반드시 아래 실제 법령/규정 기준으로 검증하세요:\n"
    "- 근로기준법\n- 최저임금법\n- 근로자퇴직급여보장법\n"
    "- 고용보험법 / 산재보험법 / 국민연금법 / 국민건강보험법\n"
    "- 여성고용평등법\n- 외국인근로자 고용법 (E-9 비자)\n"
    "- 채용절차 공정화에 관한 법률\n- 개인정보 보호법\n\n"
    "각 봇 의견에 대해 [맞음/틀림/확인필요] 판정 후 근거 법령 조문 명시."
)

FIELD_SYS = (
    "웹라인 인사총무팀 실무 전문 AI. 성격: 현장 경험 많은 선배.\n"
    "- '이론은 맞는데 실제로 가능해?' 관점으로 접근\n"
    "- 직원 입장에서 이 결정을 받아들일 수 있는지 시뮬레이션\n"
    "- 강원도 횟성 제조업 현장 특성 감안\n"
    "- 현실적으로 실행 가능한 방향 제시"
)

FINAL_SYS = (
    "웹라인 인사총무팀 AI 회의 최종 정리 AI. 냉철한 회의 진행자.\n"
    "- 모든 봇 의견 종합해 결론 도출\n"
    "- 의견 충돌한 부분은 양쪽 모두 명시\n"
    "- 구체적 액션 아이템을 우선순위 순서로 제시\n"
    "- 전문가 확인 반드시 필요한 사항 명시\n\n"
    "다음 형식으로 작성:\n"
    "## 핵심 결론\n## 주요 리스크\n## 액션 아이템 (우선순위 순)\n## 전문가 확인 필요 사항"
)

SCREEN_SYS = (
    "웹라인 HR AI 회의 코디네이터. 이번 안건과 관련 있는 봇만 골라주세요.\n\n"
    "봇 전문 영역:\n"
    "- 노무봇: 근로기준법, 수습/해고/징계, 근로시간, 퇴직, 실업급여, 노동 법령\n"
    "- HRM봇: 인사관리, 사내규정, 취업규칙, 인사제도, 평가\n"
    "- 채용봇: 채용공고/JD, 면접, 지원자 선발, 채용 프로세스\n"
    "- 계약봇: 근로계약서, 용역계약, 협약서 등 계약 문서\n"
    "- 총무봇: 비용처리/법인카드, 시설관리, 물품/소모품, 세금계산서\n"
    "- 급여봇: 급여 계산, 임금, 4대보험, 원천징수, 퇴직금, 수당\n"
    "- 교육봇: OJT, 수습평가, 직원교육, 교육훈련\n\n"
    '{"\ub178\ubb34\ubd07":true,"HRM\ubd07":false,"\ucc44\uc6a9\ubd07":false,"\uacc4\uc57d\ubd07":false,'
    '"\ucd1d\ubb34\ubd07":false,"\uae09\uc5ec\ubd07":false,"\uad50\uc721\ubd07":false} \ud615\ud0dc\ub85c\ub9cc \uc751\ub2f5\ud558\uc138\uc694.'
)

MEMORY_SYS = (
    "웹라인 HR 회의 요약 AI. "
    "이번 회의에서 향후 참고할 핵심 사항 2-3줄로만 요약. "
    "날짜 불필요. 간결하게."
)

BOT_COLORS = {
    "\ub178\ubb34\ubd07":     ["#3B6FD4","#2756B8"],
    "HRM\ubd07":      ["#2E9E55","#1E7D3E"],
    "\ucc44\uc6a9\ubd07":     ["#E07B00","#B86000"],
    "\uacc4\uc57d\ubd07":     ["#7048E8","#5030C8"],
    "\ucd1d\ubb34\ubd07":     ["#546E8A","#3D5570"],
    "\uae09\uc5ec\ubd07":     ["#C79800","#A07800"],
    "\uad50\uc721\ubd07":     ["#0A9E7A","#087D60"],
    "\ud329\ud2b8\uccb4\ud06c\ubd07": ["#C92A2A","#A01E1E"],
    "\uc2e4\ubb34\ubd07":     ["#7B5E3C","#5A4228"],
    "\ucd5c\uc885\uc815\ub9ac\ubd07": ["#1565C0","#0D47A0"],
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
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": content}])
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
        elif ext in ("pptx", "ppt"):
            from pptx import Presentation
            prs = Presentation(io.BytesIO(f.read()))
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        texts.append(shape.text.strip())
            return "\n".join(texts)
    except Exception as e:
        return f"[파일 오류: {e}]"
    return ""

def build_content(doc_text, question, case_notes):
    parts = []
    if case_notes.strip():
        parts.append("[웹라인 누적 케이스]\n" + case_notes.strip())
    if doc_text.strip():
        parts.append("[문서]\n" + doc_text[:3000])
    if question.strip():
        parts.append("[질문/검토 요청]\n" + question.strip())
    return "\n\n".join(parts)


def render_html(statuses, results, doc_name=""):
    data_json = json.dumps({"statuses": statuses, "results": results,
                            "colors": BOT_COLORS, "doc": doc_name}, ensure_ascii=False)
    return ("""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#f5f1eb;font-family:-apple-system,sans-serif;padding:8px;}
.room{background:linear-gradient(180deg,#e8e2d6,#dfd9cd);border-radius:16px;
  padding:18px 8px 12px;border:1px solid #cec8be;}
.row{display:flex;justify-content:center;align-items:flex-end;gap:6px;}
.mid{display:flex;justify-content:center;align-items:center;gap:8px;margin:2px 0;}
.conf-wrap{display:flex;align-items:center;justify-content:center;gap:10px;}
.conf-main{flex:0 0 auto;}
.chair-col{flex:0 0 auto;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.table{flex:0 0 auto;width:290px;min-height:90px;
  background:linear-gradient(160deg,#6B4423,#8B5E3C 40%,#9B6B45 60%,#6B4423);
  border-radius:10px;border:3px solid #4A2E18;
  box-shadow:0 6px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.12);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;}
.table-lbl{color:rgba(255,255,255,.45);font-size:9px;letter-spacing:2px;text-transform:uppercase;}
.upload-zone{background:rgba(255,255,255,.12);border:1.5px dashed rgba(255,255,255,.5);
  border-radius:7px;padding:6px 20px;cursor:pointer;text-align:center;
  transition:all .2s;min-width:200px;}
.upload-zone:hover,.upload-zone.drag-over{background:rgba(255,255,255,.22);
  border-color:rgba(255,255,255,.85);}
.upload-plus{font-size:18px;color:rgba(255,255,255,.65);font-weight:300;line-height:1;}
.upload-txt{font-size:8.5px;color:rgba(255,255,255,.6);line-height:1.5;margin-top:2px;}
.doc-card{background:rgba(255,255,255,.88);border-radius:4px;padding:3px 10px;
  font-size:9px;color:#3a2800;max-width:230px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;border:1px solid rgba(255,255,255,.5);cursor:pointer;}
.doc-card:hover{background:rgba(255,255,255,.98);}
.bot{display:flex;flex-direction:column;align-items:center;width:70px;position:relative;
  cursor:pointer;transition:transform .15s,filter .15s;}
.bot:hover{transform:translateY(-2px) scale(1.04);}
.bot svg{display:block;overflow:visible;filter:drop-shadow(0 4px 8px rgba(40,32,24,.22));}
.bot-name{font-size:9.5px;font-weight:700;color:#3a3530;margin-top:3px;text-align:center;}
.dot{width:7px;height:7px;border-radius:50%;margin-top:2px;background:#bbb;}
.idle .dot{background:#bbb;}
.active .dot{background:#f5c842;box-shadow:0 0 8px #f5c842;animation:blink .9s infinite;}
.done .dot{background:#52c463;box-shadow:0 0 5px #52c463;}
.error .dot{background:#e05555;}
.skip{opacity:0.28;filter:grayscale(80%);cursor:default !important;}
.skip .dot{background:#ccc !important;box-shadow:none !important;}
.bubble{position:absolute;bottom:calc(100% + 4px);left:50%;transform:translateX(-50%);
  background:#fff9e6;border:1.5px solid #f5c842;border-radius:8px;padding:3px 7px;
  font-size:9px;font-weight:800;color:#6B4A00;white-space:nowrap;
  box-shadow:0 3px 8px rgba(0,0,0,.15);animation:float 1.5s ease-in-out infinite;z-index:5;}
.bubble::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);
  border:5px solid transparent;border-top-color:#f5c842;}
.chair-wrap{background:rgba(255,255,255,.65);border-radius:10px;padding:6px 16px;
  display:inline-flex;align-items:center;gap:8px;border:1px solid #d8d0c8;
  cursor:pointer;transition:transform .15s;}
.chair-wrap:hover{transform:scale(1.04);}
.chair-info{display:flex;flex-direction:column;}
.chair-title{font-size:11px;font-weight:700;color:#3a3530;}
.chair-sub{font-size:9px;color:#aaa;font-style:italic;}
.overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;
  background:rgba(0,0,0,.55);z-index:100;align-items:center;justify-content:center;}
.overlay.show{display:flex;}
.modal{background:#fff;border-radius:14px;padding:20px 22px;width:90%;max-width:540px;
  max-height:82vh;overflow-y:auto;position:relative;box-shadow:0 12px 40px rgba(0,0,0,.3);}
.modal-hdr{display:flex;align-items:center;gap:10px;margin-bottom:12px;
  padding-bottom:8px;border-bottom:2px solid #eee;}
.modal-hdr h2{font-size:14px;font-weight:700;color:#333;margin:0;}
.modal-body{font-size:13px;line-height:1.75;color:#444;}
.modal-body h2,.modal-body h3{font-size:13px;font-weight:700;margin:10px 0 4px;color:#222;}
.modal-body p{margin:4px 0;}
.modal-body ul,.modal-body ol{padding-left:18px;margin:4px 0;}
.modal-body li{margin:3px 0;}
.modal-body strong{color:#222;}
.close-btn{position:absolute;top:10px;right:14px;cursor:pointer;
  font-size:18px;color:#aaa;background:none;border:none;line-height:1;padding:2px 6px;border-radius:4px;}
.close-btn:hover{background:#f0f0f0;color:#333;}
.no-result{font-size:12px;color:#aaa;font-style:italic;padding:20px 0;text-align:center;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.3;}}
@keyframes float{0%,100%{transform:translateX(-50%) translateY(0);}50%{transform:translateX(-50%) translateY(-3px);}}
</style>
</head><body>
<div class="room" id="room"></div>
<div class="overlay" id="overlay" onclick="maybeClose(event)">
  <div class="modal" id="modal">
    <button class="close-btn" onclick="closeModal()">&#x2715;</button>
    <div class="modal-hdr"><div id="modal-icon"></div><h2 id="modal-title"></h2></div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>
<script>
const DATA=""" + data_json + """;
const COLORS=DATA.colors;

function robotFace(name,C,D){
  if(name.includes('\ub178\ubb34')){
    return `<path d="M21 31l8 2.4M43 31l-8 2.4" stroke="#273445" stroke-width="2.1" stroke-linecap="round"/>
      <circle cx="25" cy="37" r="3.6" fill="${C}"/><circle cx="39" cy="37" r="3.6" fill="${C}"/>
      <path d="M28.5 44.5h7" stroke="#273445" stroke-width="2.1" stroke-linecap="round"/>`;
  }
  if(name.includes('\uacc4\uc57d')){
    return `<path d="M21.5 31.5l7.2-.8M35.2 31.2l8 2.1" stroke="#273445" stroke-width="2" stroke-linecap="round"/>
      <circle cx="25" cy="37" r="3.7" fill="${C}"/><circle cx="39" cy="37" r="3.1" fill="${C}"/>
      <path d="M29 44c2.6 1.5 6.2 1.1 8-.7" fill="none" stroke="#273445" stroke-width="2" stroke-linecap="round"/>`;
  }
  if(name.includes('\ud329\ud2b8')){
    return `<rect x="20.5" y="33" width="9" height="6.5" rx="3.2" fill="${C}"/>
      <rect x="34.5" y="33" width="9" height="6.5" rx="3.2" fill="${C}"/>
      <path d="M29.5 36.2h5" stroke="${D}" stroke-width="1.8" stroke-linecap="round"/>
      <path d="M28.5 44h7" stroke="#273445" stroke-width="2.1" stroke-linecap="round"/>`;
  }
  if(name.includes('\uae09\uc5ec')){
    return `<circle cx="25" cy="36" r="3.9" fill="${C}"/><circle cx="39" cy="36" r="3.9" fill="${C}"/>
      <circle cx="26.4" cy="34.6" r="1.05" fill="#FFFFFF"/><circle cx="40.4" cy="34.6" r="1.05" fill="#FFFFFF"/>
      <path d="M29 43.5h6" stroke="#273445" stroke-width="2" stroke-linecap="round"/>`;
  }
  if(name.includes('\ucc44\uc6a9')||name.includes('\uad50\uc721')){
    return `<circle cx="25" cy="36" r="4" fill="${C}"/><circle cx="39" cy="36" r="4" fill="${C}"/>
      <circle cx="26.4" cy="34.4" r="1.15" fill="#FFFFFF"/><circle cx="40.4" cy="34.4" r="1.15" fill="#FFFFFF"/>
      <path d="M27 42.5c2.6 3 7.5 3 10 0" fill="none" stroke="#273445" stroke-width="2.2" stroke-linecap="round"/>`;
  }
  if(name.includes('\ucd5c\uc885')){
    return `<circle cx="25" cy="36" r="4" fill="${C}"/><circle cx="39" cy="36" r="4" fill="${C}"/>
      <circle cx="26.4" cy="34.4" r="1.15" fill="#FFFFFF"/><circle cx="40.4" cy="34.4" r="1.15" fill="#FFFFFF"/>
      <path d="M27.5 43c2.5 2.5 6.8 2.8 9.6.2" fill="none" stroke="#273445" stroke-width="2.2" stroke-linecap="round"/>`;
  }
  return `<circle cx="25" cy="36" r="4.2" fill="${C}"/><circle cx="39" cy="36" r="4.2" fill="${C}"/>
    <circle cx="26.5" cy="34.4" r="1.25" fill="#FFFFFF" opacity=".95"/>
    <circle cx="40.5" cy="34.4" r="1.25" fill="#FFFFFF" opacity=".95"/>
    <path d="M27 43c2.7 2.2 7.4 2.2 10 0" fill="none" stroke="#314052" stroke-width="2.2" stroke-linecap="round"/>`;
}

function robotAccessory(name,C,D){
  if(name.includes('\ub178\ubb34')){
    return `<g transform="translate(48 56)">
      <path d="M0-7l7 2.6v5.7c0 5.2-3 8-7 9.7-4-1.7-7-4.5-7-9.7v-5.7L0-7Z" fill="#FFFFFF" opacity=".88"/>
      <path d="M-3 .8l2.2 2.3L4-2.8" fill="none" stroke="${D}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
    </g>`;
  }
  if(name.includes('HRM')){
    return `<g transform="translate(43 52)">
      <rect x="0" y="0" width="15" height="17" rx="3.2" fill="#FFFFFF" opacity=".88"/>
      <path d="M4 5l1.5 1.5L8.5 3.5M4 10l1.5 1.5L8.5 8.5M10 5.2h2M10 10.2h2" stroke="${D}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </g>`;
  }
  if(name.includes('\ucc44\uc6a9')){
    return `<g transform="translate(47 56)">
      <rect x="-8" y="-6" width="16" height="15" rx="4" fill="#FFFFFF" opacity=".88"/>
      <circle cx="0" cy="-1.8" r="2.8" fill="${D}"/>
      <path d="M-5 6c1.3-3 8.7-3 10 0" fill="none" stroke="${D}" stroke-width="1.7" stroke-linecap="round"/>
    </g>`;
  }
  if(name.includes('\uacc4\uc57d')){
    return `<g transform="translate(43 51)">
      <rect x="0" y="0" width="14" height="18" rx="2.8" fill="#FFFFFF" opacity=".88"/>
      <path d="M4 5h6M4 9h6M4 13h4" stroke="${D}" stroke-width="1.4" stroke-linecap="round"/>
      <path d="M10 15l5-5" stroke="#273445" stroke-width="2" stroke-linecap="round"/>
    </g>`;
  }
  if(name.includes('\ucd1d\ubb34')){
    return `<g transform="translate(45 54)">
      <rect x="-5" y="4" width="17" height="10" rx="2.6" fill="#FFFFFF" opacity=".86"/>
      <path d="M-2 4V1.5c0-1.5 2-2.5 4.2-2.5s4.2 1 4.2 2.5V4" fill="none" stroke="${D}" stroke-width="1.6"/>
      <path d="M-1 9h10" stroke="${D}" stroke-width="1.7" stroke-linecap="round"/>
    </g>`;
  }
  if(name.includes('\uae09\uc5ec')){
    return `<g transform="translate(43 52)">
      <rect x="0" y="0" width="15" height="18" rx="3" fill="#FFFFFF" opacity=".9"/>
      <rect x="3" y="3" width="9" height="3" rx="1" fill="${D}" opacity=".75"/>
      <circle cx="4" cy="10" r="1.2" fill="${D}"/><circle cx="7.5" cy="10" r="1.2" fill="${D}"/><circle cx="11" cy="10" r="1.2" fill="${D}"/>
      <circle cx="4" cy="14" r="1.2" fill="${D}"/><circle cx="7.5" cy="14" r="1.2" fill="${D}"/><circle cx="11" cy="14" r="1.2" fill="${D}"/>
    </g>`;
  }
  if(name.includes('\uad50\uc721')){
    return `<g transform="translate(43 54)">
      <path d="M-1 0c3.8-2 7-1.1 10 1.2v12.5c-3-2.2-6.2-3.1-10-1.2V0Z" fill="#FFFFFF" opacity=".88"/>
      <path d="M9 1.2c3-2.3 6.2-3.2 10-1.2v12.5c-3.8-1.9-7-1-10 1.2V1.2Z" fill="#FFFFFF" opacity=".75"/>
      <path d="M9 1.2v12.5" stroke="${D}" stroke-width="1.4" stroke-linecap="round"/>
    </g>`;
  }
  if(name.includes('\ud329\ud2b8')){
    return `<g transform="translate(47 55)">
      <circle cx="0" cy="0" r="5.6" fill="#FFFFFF" opacity=".84" stroke="${D}" stroke-width="2"/>
      <path d="M4 4l6 6" stroke="${D}" stroke-width="2.4" stroke-linecap="round"/>
      <path d="M-2.7 0l1.8 1.9L3-2.4" fill="none" stroke="${D}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </g>`;
  }
  if(name.includes('\uc2e4\ubb34')){
    return `<g>
      <path d="M16.5 27c1.8-8.5 29.2-8.5 31 0H16.5Z" fill="#FFFFFF" opacity=".76"/>
      <path d="M24 20.8v6.2M32 19.5v7.5M40 20.8v6.2" stroke="${D}" stroke-width="1.6" stroke-linecap="round"/>
    </g>`;
  }
  if(name.includes('\ucd5c\uc885')){
    return `<g>
      <path d="M28 56l4 4 4-4 2.6 8.5-6.6 4.7-6.6-4.7L28 56Z" fill="#FFFFFF" opacity=".85"/>
      <path d="M31 59h2l1.2 5.2L32 66l-2.2-1.8L31 59Z" fill="${D}" opacity=".82"/>
    </g>`;
  }
  return '';
}

function svgRobot(name,sz){
  const s=sz||56;
  const c=(COLORS[name]||["#666","#444"]);
  const C=c[0],D=c[1];
  const uid='bot'+Array.from(name).reduce((a,ch)=>(a*31+ch.charCodeAt(0))>>>0,11);
  return `<svg width="${s}" height="${Math.round(s*1.18)}" viewBox="0 0 64 76" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="${uid}-body" x1="13" y1="10" x2="52" y2="67" gradientUnits="userSpaceOnUse">
        <stop stop-color="${C}"/><stop offset="1" stop-color="${D}"/>
      </linearGradient>
      <linearGradient id="${uid}-face" x1="16" y1="21" x2="48" y2="46" gradientUnits="userSpaceOnUse">
        <stop stop-color="#FFFFFF"/><stop offset="1" stop-color="#EEF4FF"/>
      </linearGradient>
      <linearGradient id="${uid}-shine" x1="20" y1="17" x2="44" y2="55" gradientUnits="userSpaceOnUse">
        <stop stop-color="#FFFFFF" stop-opacity=".48"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <ellipse cx="32" cy="69" rx="21" ry="4.5" fill="#2D241B" opacity=".16"/>
    <path d="M22 17c0-6.2 20-6.2 20 0" fill="none" stroke="${D}" stroke-width="3" stroke-linecap="round"/>
    <circle cx="32" cy="10" r="4.7" fill="url(#${uid}-body)" stroke="#fff" stroke-opacity=".72" stroke-width="1.2"/>
    <rect x="7.5" y="19" width="49" height="37" rx="15" fill="url(#${uid}-body)"/>
    <path d="M14 23c6-6 27-8 36 5v-2c0-4.5-3.6-8-8-8H22c-4.8 0-8 2.2-8 5Z" fill="url(#${uid}-shine)"/>
    <circle cx="8" cy="37" r="5.5" fill="${D}"/><circle cx="56" cy="37" r="5.5" fill="${D}"/>
    <rect x="15" y="25" width="34" height="22" rx="10" fill="url(#${uid}-face)" stroke="rgba(255,255,255,.78)" stroke-width="1.3"/>
    ${robotFace(name,C,D)}
    <path d="M19 55h26c7 0 12 5 12 12v1H7v-1c0-7 5-12 12-12Z" fill="url(#${uid}-body)"/>
    <rect x="23" y="51" width="18" height="10" rx="5" fill="${D}" opacity=".92"/>
    <circle cx="32" cy="61" r="3.3" fill="#FFFFFF" opacity=".72"/>
    <path d="M18 60h8M38 60h8" stroke="#FFFFFF" stroke-opacity=".36" stroke-width="2.4" stroke-linecap="round"/>
    ${robotAccessory(name,C,D)}
  </svg>`;
}

function botCard(name,status){
  const isSkip=status==='skip';
  const bubble=status==='active'?'<div class="bubble">&#x1F4AC; \ub2f5\ubcc0 \uc911</div>':'';
  const onclick=isSkip?'':('onclick="showBot(\'' + name + '\')"');
  return '<div class="bot ' + status + '" ' + onclick + '>'
    + bubble + svgRobot(name)
    + '<div class="bot-name">' + name + '</div>'
    + '<div class="dot"></div></div>';
}

function triggerUpload(){
  try{
    const fi=window.parent.document.querySelector('input[data-testid="stFileUploaderDropzoneInput"]');
    if(fi) fi.click();
  }catch(e){console.log('upload trigger error',e);}
}
function attachUploadHandlers(){
  const z=document.getElementById('uploadZone');
  if(!z)return;
  z.addEventListener('click',function(e){e.stopPropagation();triggerUpload();});
  z.addEventListener('dragover',function(e){e.preventDefault();z.classList.add('drag-over');});
  z.addEventListener('dragleave',function(){z.classList.remove('drag-over');});
  z.addEventListener('drop',function(e){
    e.preventDefault();z.classList.remove('drag-over');
    const files=e.dataTransfer.files;
    if(!files.length)return;
    try{
      const dt=new DataTransfer();dt.items.add(files[0]);
      const fi=window.parent.document.querySelector('input[data-testid="stFileUploaderDropzoneInput"]');
      if(fi){fi.files=dt.files;fi.dispatchEvent(new Event('change',{bubbles:true}));}
    }catch(err){console.log('drop error',err);}
  });
}

function render(){
  const st=DATA.statuses;
  const g=n=>st[n]||'idle';
  const topRow=['\ub178\ubb34\ubd07','HRM\ubd07','\ucc44\uc6a9\ubd07','\uacc4\uc57d\ubd07'].map(n=>botCard(n,g(n))).join('');
  const btmRow=['\ucd1d\ubb34\ubd07','\uae09\uc5ec\ubd07','\uad50\uc721\ubd07'].map(n=>botCard(n,g(n))).join('');
  const cs=g('\ucd5c\uc885\uc815\ub9ac\ubd07');
  const cColor={idle:'#bbb',active:'#f5c842',done:'#52c463',error:'#e05555'}[cs]||'#bbb';
  const cGlow=cs!=='idle'?'box-shadow:0 0 7px '+cColor+';':'';
  const cBubble=cs==='active'?'<div class="bubble">&#x1F4AC; \ub2f5\ubcc0 \uc911</div>':'';
  const tableInner=DATA.doc
    ?'<div class="doc-card" onclick="triggerUpload()">&#x1F4C4; '+DATA.doc+'</div>'
    :'<div class="upload-zone" id="uploadZone">'
      +'<div class="upload-plus">+</div>'
      +'<div class="upload-txt">\ubb38\uc11c \ub4dc\ub798\uadf8 or<br>\ud074\ub9ad\ud574\uc11c \uc5c5\ub85c\ub4dc</div>'
    +'</div>';
  const chairHtml=
    '<div class="chair-col">'
      +'<div class="chair-wrap" onclick="showBot(\'\ucd5c\uc885\uc815\ub9ac\ubd07\')">'
        +cBubble+svgRobot('\ucd5c\uc885\uc815\ub9ac\ubd07',44)
        +'<div class="chair-info">'
          +'<div class="chair-title">\ucd5c\uc885\uc815\ub9ac\ubd07</div>'
          +'<div class="chair-sub">\ud68c\uc758 \uc9c4\ud589\uc790</div>'
        +'</div>'
        +'<div class="dot" style="background:'+cColor+';'+cGlow+'"></div>'
      +'</div>'
    +'</div>';
  document.getElementById('room').innerHTML=
    '<div class="conf-wrap">'
      +'<div class="conf-main">'
        +'<div class="row">'+topRow+'</div>'
        +'<div class="mid">'
          +botCard('\ud329\ud2b8\uccb4\ud06c\ubd07',g('\ud329\ud2b8\uccb4\ud06c\ubd07'))
          +'<div class="table"><div class="table-lbl">WELLFINE HR AI</div>'+tableInner+'</div>'
          +botCard('\uc2e4\ubb34\ubd07',g('\uc2e4\ubb34\ubd07'))
        +'</div>'
        +'<div class="row">'+btmRow+'</div>'
      +'</div>'
      +chairHtml
    +'</div>';
  attachUploadHandlers();
}

function showBot(name){
  const result=DATA.results&&DATA.results[name];
  document.getElementById('modal-icon').innerHTML=svgRobot(name,32);
  document.getElementById('modal-title').textContent=name;
  if(result){
    document.getElementById('modal-body').innerHTML=marked.parse(result);
  } else {
    const st2=DATA.statuses[name]||'idle';
    const msg=st2==='active'?'\uc9c0\uae08 \ub2f5\ubcc0 \uc911\uc785\ub2c8\ub2e4...':'\uc544\uc9c1 \uc758\uacac\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.';
    document.getElementById('modal-body').innerHTML='<div class="no-result">'+msg+'</div>';
  }
  document.getElementById('overlay').classList.add('show');
}
function closeModal(){document.getElementById('overlay').classList.remove('show');}
function maybeClose(e){if(e.target===document.getElementById('overlay'))closeModal();}
render();
</script>
</body></html>""")

# ── 세션 초기화 ────────────────────────────────────────────
_cfg = load_cfg()
for k, v in [
    ("bot_statuses", {}), ("bot_results", {}), ("case_notes", ""),
    ("stop_requested", False), ("meeting_running", False),
    ("meeting_history", []), ("renaming_idx", None), ("current_doc", ""),
    ("show_result_panel", False), ("last_final", ""), ("selected_history_idx", None),
    ("current_question", ""), ("feedback_pending", ""),
    ("saved_provider", _cfg.get("provider", list(PROVIDERS.keys())[0])),
    ("saved_model",    _cfg.get("model", "")),
    ("saved_api_key",  _cfg.get("api_key", "")),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# 공유 히스토리: 세션 첫 로드 시 파일에서 불러옴
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = True
    _shared = load_shared_history()
    if _shared:
        st.session_state.meeting_history = _shared

if "bot_prompts" not in st.session_state:
    bp0 = {b["name"]: b["system"] for b in BOTS}
    bp0.update({"팩트체크봇": FACTCHECK_SYS, "실무봇": FIELD_SYS, "최종정리봇": FINAL_SYS})
    st.session_state.bot_prompts = bp0

# ── 현재 설정값 도출 ───────────────────────────────────────
_p = st.session_state.saved_provider
if _p not in PROVIDERS:
    _p = list(PROVIDERS.keys())[0]
_prov    = PROVIDERS[_p]
_pkey    = _prov["key"]
_ml      = st.session_state.saved_model
if _ml not in _prov["models"]:
    _ml = list(_prov["models"].keys())[0]
_model   = _prov["models"][_ml]
_api_key = st.session_state.saved_api_key
if not _api_key:
    try:
        smap = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}
        _api_key = st.secrets.get(smap[_pkey], "")
    except Exception:
        _api_key = ""

@st.dialog("⚙️ 설정", width="large")
def show_settings():
    tab1, tab2, tab3 = st.tabs(["🔌 AI 연결", "🤖 봇 프롬프트", "📂 케이스 메모"])
    with tab1:
        pl = st.selectbox("AI 제공자", list(PROVIDERS.keys()),
            index=(list(PROVIDERS.keys()).index(st.session_state.saved_provider)
                   if st.session_state.saved_provider in PROVIDERS else 0))
        pt = PROVIDERS[pl]; pkt = pt["key"]
        mll = list(pt["models"].keys())
        saved_m = st.session_state.saved_model
        ml = st.selectbox("모델", mll, index=mll.index(saved_m) if saved_m in mll else 0)
        ph = {"anthropic": "sk-ant-...", "openai": "sk-...", "gemini": "AIza..."}.get(pkt, "")
        ak = st.text_input("API 키 (팀 공유)", type="password",
                           value=st.session_state.saved_api_key, placeholder=ph)
        st.caption("팀원 모두가 이 키로 사용합니다.")
        if st.button("💾 저장", type="primary", use_container_width=True):
            st.session_state.saved_provider = pl
            st.session_state.saved_model    = ml
            st.session_state.saved_api_key  = ak
            save_cfg({"provider": pl, "model": ml, "api_key": ak})
            st.rerun()
    with tab2:
        all_names = ([b["name"] for b in BOTS] + ["팩트체크봇", "실무봇", "최종정리봇"])
        bs = st.selectbox("봇 선택", all_names)
        ed = st.text_area("프롬프트", value=st.session_state.bot_prompts.get(bs, ""), height=220)
        if st.button("💾 프롬프트 저장", use_container_width=True):
            st.session_state.bot_prompts[bs] = ed
            st.rerun()
    with tab3:
        st.caption("모든 회의에 기본 콘텍스트로 포함됩니다.")
        nn = st.text_area("누적 케이스", value=st.session_state.case_notes, height=200,
                          placeholder="수습 불합격 시 면담 2회 이상 기록 필요...")
        if st.button("💾 케이스 저장", use_container_width=True):
            st.session_state.case_notes = nn
            st.rerun()

def _short(text, limit=28):
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"

def _open_history(real_idx):
    h = st.session_state.meeting_history[real_idx]
    statuses = {}; results = {}
    for name, result in h.get("ops2", {}).items():
        statuses[name] = "done"; results[name] = result
    if h.get("fc2"):
        statuses["팩트체크봇"] = "done"; results["팩트체크봇"] = h["fc2"]
    if h.get("final"):
        statuses["최종정리봇"] = "done"; results["최종정리봇"] = h["final"]
    st.session_state.bot_statuses = statuses
    st.session_state.bot_results = results
    st.session_state.current_doc = h.get("doc", "")
    st.session_state.last_final = h.get("final", "")
    st.session_state.show_result_panel = bool(h.get("final"))
    st.session_state.selected_history_idx = real_idx
    st.session_state.meeting_running = False
    st.session_state.stop_requested = False

def _new_meeting():
    st.session_state.bot_statuses = {}
    st.session_state.bot_results = {}
    st.session_state.current_doc = ""
    st.session_state.last_final = ""
    st.session_state.show_result_panel = False
    st.session_state.selected_history_idx = None
    st.session_state.renaming_idx = None
    st.session_state.meeting_running = False
    st.session_state.stop_requested = False
    st.session_state.feedback_pending = ""

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><span class="mark">W</span><span>인사총무 에이전트 AI</span></div>',
        unsafe_allow_html=True)
    if st.button("＋ 새 회의", key="new_meeting", use_container_width=True):
        _new_meeting(); st.rerun()
    query = st.text_input("회의 검색", key="history_filter", placeholder="회의 검색",
                          label_visibility="collapsed")
    st.markdown('<div class="sidebar-section">최근 회의</div>', unsafe_allow_html=True)
    history = st.session_state.meeting_history
    if not history:
        st.markdown('<div class="history-empty">회의를 진행하면 이곳에 저장됩니다.</div>',
                    unsafe_allow_html=True)
    else:
        q = query.strip().lower()
        visible = []
        for real_idx, h in enumerate(history):
            haystack = " ".join([h.get("title",""), h.get("question",""),
                                 h.get("doc",""), h.get("final","")]).lower()
            if not q or q in haystack:
                visible.append(real_idx)
        if not visible:
            st.markdown('<div class="history-empty">검색 결과가 없습니다.</div>',
                        unsafe_allow_html=True)
        for real_idx in reversed(visible):
            h = history[real_idx]
            title = h.get("title") or h.get("question") or "새 회의"
            if h.get("partial"):
                title = "⏸ " + title
            meta_bits = [h.get("time","")]
            if h.get("doc"):
                meta_bits.append(h["doc"])
            elif h.get("question"):
                meta_bits.append(h["question"])
            meta = " · ".join(_short(x,22) for x in meta_bits if x)
            active = st.session_state.selected_history_idx == real_idx
            row_title = ("● " if active else "") + _short(title, 28)
            row_label = row_title + (f"\n{_short(meta,34)}" if meta else "")
            oc, rc, dc = st.columns([5.8, 1.1, 1.1])
            with oc:
                if st.button(row_label, key=f"hist_open_{real_idx}", use_container_width=True):
                    _open_history(real_idx); st.rerun()
            with rc:
                if st.button("✎", key=f"hist_ren_{real_idx}", use_container_width=True):
                    st.session_state.renaming_idx = real_idx; st.rerun()
            with dc:
                if st.button("×", key=f"hist_del_{real_idx}", use_container_width=True):
                    st.session_state.meeting_history.pop(real_idx)
                    save_shared_history(st.session_state.meeting_history)
                    if st.session_state.selected_history_idx == real_idx:
                        _new_meeting()
                    elif (st.session_state.selected_history_idx is not None
                          and st.session_state.selected_history_idx > real_idx):
                        st.session_state.selected_history_idx -= 1
                    st.session_state.renaming_idx = None; st.rerun()
            if st.session_state.renaming_idx == real_idx:
                new_name = st.text_input("이름 바꾸기", value=h.get("title",""),
                    key=f"hist_name_{real_idx}", label_visibility="collapsed")
                sc, cc = st.columns(2)
                with sc:
                    if st.button("저장", key=f"hist_s_{real_idx}", use_container_width=True):
                        st.session_state.meeting_history[real_idx]["title"] = (
                            new_name.strip() or h.get("title","회의"))
                        save_shared_history(st.session_state.meeting_history)
                        st.session_state.renaming_idx = None; st.rerun()
                with cc:
                    if st.button("취소", key=f"hist_cancel_{real_idx}", use_container_width=True):
                        st.session_state.renaming_idx = None; st.rerun()

# ── 메인 레이아웃 ──────────────────────────────────────────
if st.session_state.show_result_panel and st.session_state.last_final:
    main_col, result_col = st.columns([3, 2])
else:
    main_col = st.container(); result_col = None

with main_col:
    col_title, col_cfg = st.columns([5, 1])
    with col_title:
        st.markdown("## 🏢 웹라인 인사총무 AI 회의실")
        api_status = " ✅" if _api_key else " ⚠️ API키 미입력"
        st.caption(f"설정: {_p.split()[-1]} · {_ml}" + api_status)
    with col_cfg:
        st.write("")
        if st.button("⚙️ 설정", use_container_width=True):
            show_settings()

    st.divider()
    table_slot = st.empty()
    with table_slot:
        components.html(
            render_html(st.session_state.bot_statuses,
                        st.session_state.bot_results,
                        st.session_state.current_doc),
            height=470)

    ufile = st.file_uploader("문서", type=["pdf", "docx", "txt", "pptx"],
                             label_visibility="collapsed", key="doc_upload")
    if ufile:
        if st.session_state.current_doc != ufile.name:
            st.session_state.current_doc = ufile.name; st.rerun()

    st.divider()
    st.markdown("##### 💬 질문 / 검토 요청")
    question = st.text_area("질문", height=80, label_visibility="collapsed",
        placeholder="예: 이 근로계약서 수습기간 조항이 법적으로 문제없나요?")

    btn_c1, btn_c2 = st.columns([3, 1])
    with btn_c1:
        go = st.button("🚀 회의 시작", type="primary", use_container_width=True,
                       disabled=st.session_state.meeting_running)
    with btn_c2:
        if st.button("⏹ 중단", use_container_width=True,
                     disabled=not st.session_state.meeting_running):
            st.session_state.stop_requested = True
            st.session_state.meeting_running = False; st.rerun()

    # 피드백 섹션
    if st.session_state.last_final and not st.session_state.meeting_running:
        with st.expander("💬 최종 결론에 대한 추가 질문 / 피드백"):
            feedback_q = st.text_area("피드백 내용", key="feedback_input", height=80,
                placeholder="예: 수습 3개월 조항에 대해 더 자세히 알고 싶어요...")
            if st.button("🔄 피드백 반영 추가 회의", key="feedback_go"):
                st.session_state.feedback_pending = feedback_q; st.rerun()

    if st.session_state.get("feedback_pending"):
        go = True

# 최종 결론 패널
if result_col is not None:
    with result_col:
        st.markdown("### 🎯 최종 결론")
        if st.button("✕ 닫기", key="close_result"):
            st.session_state.show_result_panel = False; st.rerun()
        st.markdown("---")
        st.markdown(st.session_state.last_final)

# ── 헬퍼 ──────────────────────────────────────────────────
def upd(statuses_update, results_update=None):
    st.session_state.bot_statuses.update(statuses_update)
    if results_update:
        st.session_state.bot_results.update(results_update)
    with table_slot:
        components.html(
            render_html(st.session_state.bot_statuses,
                        st.session_state.bot_results,
                        st.session_state.current_doc),
            height=490)

def check_stop():
    if st.session_state.stop_requested:
        if st.session_state.bot_results:
            from datetime import datetime
            _q = st.session_state.get("current_question", "")
            _pt = "[중단] " + (_q[:25] if _q else st.session_state.current_doc or "회의")
            st.session_state.meeting_history.append({
                "time":     datetime.now().strftime("%Y-%m-%d %H:%M"),
                "title":    _pt,
                "doc":      st.session_state.current_doc,
                "question": _q,
                "ops1": {}, "fc1": "",
                "ops2":     st.session_state.bot_results,
                "fc2": "", "final": "",
                "partial":  True,
            })
            save_shared_history(st.session_state.meeting_history)
            st.session_state.selected_history_idx = len(st.session_state.meeting_history) - 1
        st.warning("⏹ 회의가 중단되었습니다. 테이블의 봇을 클릭하면 완료된 결과를 확인할 수 있습니다.")
        st.stop()

# ── 회의 진행 ──────────────────────────────────────────────
if go:
    if not _api_key:
        st.error("⚙️ 설정에서 API 키를 입력하고 저장해주세요.")
        st.stop()

    _fb = st.session_state.get("feedback_pending", "")
    st.session_state.feedback_pending = ""
    effective_question = question.strip()
    if _fb:
        prior_ctx = ""
        if st.session_state.last_final:
            prior_ctx = f"\n\n[이전 회의 결론 참고]\n{st.session_state.last_final[:600]}"
        effective_question = _fb + prior_ctx

    if not ufile and not effective_question.strip():
        st.error("문서를 업로드하거나 질문을 입력해주세요.")
        st.stop()

    st.session_state.bot_statuses    = {}
    st.session_state.bot_results     = {}
    st.session_state.stop_requested  = False
    st.session_state.meeting_running = True
    st.session_state.show_result_panel = False
    st.session_state.current_question = effective_question

    doc_text = extract_text(ufile) if ufile else ""
    content  = build_content(doc_text, effective_question, st.session_state.case_notes)
    bp       = st.session_state.bot_prompts

    st.divider()
    st.markdown("### 📋 회의 진행")

    active_bots = BOTS[:]
    skipped = []
    with st.spinner("🔍 안건 분석 — 관련 봇 선별 중..."):
        try:
            screen_res = call_bot(_pkey, _api_key, _model, SCREEN_SYS, content[:600], 150)
            m = re.search(r"\{[^{}]+\}", screen_res, re.DOTALL)
            relevant    = json.loads(m.group()) if m else {}
            active_bots = [b for b in BOTS if relevant.get(b["name"], True)]
            skipped     = [b["name"] for b in BOTS if not relevant.get(b["name"], True)]
        except Exception:
            pass
    if skipped:
        st.info("💤 제외된 봇: **" + ", ".join(skipped) + "**")
        upd({n: "skip" for n in skipped})
    n_active = len(active_bots)

    st.markdown(f"**1라운드 — 전문 봇 {n_active}명 동시 발언**")
    upd({b["name"]: "active" for b in active_bots})
    ops1 = {}
    with st.spinner(f"🤖 {n_active}명 동시 분석 중..."):
        def _call1(b):
            return b["name"], call_bot(_pkey, _api_key, _model, bp.get(b["name"], b["system"]), content, 600)
        with ThreadPoolExecutor(max_workers=max(1, n_active)) as ex:
            for name, res in ex.map(_call1, active_bots):
                ops1[name] = res
    upd({b["name"]: "done" for b in active_bots}, ops1)
    for b in active_bots:
        with st.expander(f"🤖 {b['name']} 1차 의견", expanded=False):
            st.markdown(ops1[b["name"]])

    check_stop()

    st.markdown("**팩트체크 1차**")
    fc1_in = content + "\n\n[1차 의견]\n" + "\n\n".join(f"{n}:\n{o}" for n, o in ops1.items())
    upd({"팩트체크봇": "active"})
    with st.status("🤖 팩트체크봇 1차 검증 중...", expanded=False) as stat:
        fc1 = call_bot(_pkey, _api_key, _model, bp.get("팩트체크봇", FACTCHECK_SYS), fc1_in, 900)
        st.markdown(fc1)
        stat.update(label="🤖 팩트체크봇 1차 ✅", state="complete", expanded=False)
    upd({"팩트체크봇": "done"}, {"팩트체크봇_1차": fc1})

    check_stop()

    st.markdown(f"**2라운드 — 팩트체크 반영 ({n_active}명 병렬)**")
    upd({b["name"]: "active" for b in active_bots})
    ops2 = {}
    with st.spinner(f"🤖 {n_active}명 재검토 중..."):
        def _call2(b):
            r2_in = (content + f"\n\n[팩트체크 결과]\n{fc1}"
                     + "\n\n[내 1차 의견]\n" + ops1.get(b["name"], "")
                     + "\n\n팩트체크 반영해 의견을 보완하거나 수정해주세요.")
            return b["name"], call_bot(_pkey, _api_key, _model, bp.get(b["name"], b["system"]), r2_in, 600)
        with ThreadPoolExecutor(max_workers=max(1, n_active)) as ex:
            for name, res in ex.map(_call2, active_bots):
                ops2[name] = res
    upd({b["name"]: "done" for b in active_bots}, ops2)
    for b in active_bots:
        with st.expander(f"🤖 {b['name']} 2차 의견", expanded=False):
            st.markdown(ops2[b["name"]])

    check_stop()

    st.markdown("**팩트체크 2차 (최종 검증)**")
    fc2_in = (content + "\n\n[2차 의견]\n"
              + "\n\n".join(f"{n}:\n{o}" for n, o in ops2.items())
              + f"\n\n[1차 팩트체크]\n{fc1}")
    upd({"팩트체크봇": "active"})
    with st.status("🤖 팩트체크봇 최종 검증 중...", expanded=False) as stat:
        fc2 = call_bot(_pkey, _api_key, _model, bp.get("팩트체크봇", FACTCHECK_SYS), fc2_in, 900)
        st.markdown(fc2)
        stat.update(label="🤖 팩트체크봇 최종 ✅", state="complete", expanded=False)
    upd({"팩트체크봇": "done"}, {"팩트체크봇_2차": fc2})

    check_stop()

    upd({"실무봇": "active"})
    field_in = (content + "\n\n[전문 봇 최종 의견]\n"
                + "\n".join(f"{n}: {o[:200]}" for n, o in ops2.items())
                + f"\n\n[팩트체크 최종]\n{fc2}"
                + "\n\n현장 실무 관점에서 3줄 이내로 핵심 코멘트만 작성해주세요.")
    with st.spinner("🤖 실무봇 코멘트 작성 중..."):
        field_brief = call_bot(_pkey, _api_key, _model, bp.get("실무봇", FIELD_SYS), field_in, 200)
    upd({"실무봇": "done"}, {"실무봇": field_brief})

    final_in = (content + "\n\n[전문 봇 2차 최종 의견]\n"
                + "\n\n".join(f"{n}:\n{o}" for n, o in ops2.items())
                + f"\n\n[팩트체크 최종 결과]\n{fc2}"
                + f"\n\n[실무 현장 코멘트]\n{field_brief}")
    upd({"최종정리봇": "active"})
    with st.spinner("🤖 최종정리봇 정리 중..."):
        final_res = call_bot(_pkey, _api_key, _model, bp.get("최종정리봇", FINAL_SYS), final_in, 1500)
    upd({"최종정리봇": "done"}, {"최종정리봇": final_res})

    st.session_state.meeting_running   = False
    st.session_state.last_final        = final_res
    st.session_state.show_result_panel = True

    from datetime import datetime
    title = (ufile.name if ufile else effective_question[:30])
    st.session_state.meeting_history.append({
        "time":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title":    title,
        "doc":      ufile.name if ufile else "",
        "question": effective_question[:100],
        "ops1": ops1, "fc1": fc1,
        "ops2": ops2, "fc2": fc2,
        "final": final_res,
    })
    st.session_state.selected_history_idx = len(st.session_state.meeting_history) - 1

    # 자동 메모리
    try:
        mem_in = f"[회의 주제] {title}\n\n[최종 결론 요약]\n{final_res[:800]}"
        memory_note = call_bot(_pkey, _api_key, _model, MEMORY_SYS, mem_in, 120)
        if memory_note and not memory_note.startswith("오류"):
            sep = "\n\n" if st.session_state.case_notes.strip() else ""
            st.session_state.case_notes += sep + f"• {memory_note}"
    except Exception:
        pass

    save_shared_history(st.session_state.meeting_history)
    st.success("✅ 회의 완료! 오른쪽에 최종 결론이 표시됩니다.")
    st.rerun()
